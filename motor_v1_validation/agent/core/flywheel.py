"""Flywheel — feedback activo que cierra el loop ejecución→mejora.

Patrón Flywheel (60668): Cada ciclo produce señal que mejora el siguiente.
Patrón Adaptive Control (83759): Ajustar parámetros del controlador en tiempo real.

Flujo: Ejecutar → Capturar señal → Actualizar scores → Recalibrar routing
"""

from typing import Optional


def _get_conn():
    try:
        from .db_pool import get_conn
        return get_conn()
    except Exception:
        return None


def _put_conn(conn):
    try:
        from .db_pool import put_conn
        put_conn(conn)
    except Exception:
        pass


def after_session(session_summary: dict) -> None:
    """Update model scores in observatory after each session.

    Called at end of agent_loop or chat session.
    Adjusts quality_score and roi_score based on outcome.
    """
    conn = _get_conn()
    if not conn:
        return

    model_id = session_summary.get("model_used", "")
    success = session_summary.get("success", False)
    cost = session_summary.get("cost_usd", 0)

    if not model_id:
        _put_conn(conn)
        return

    try:
        with conn.cursor() as cur:
            # Update quality score (bounded 0-100)
            if success:
                delta = 0.5  # Small positive for success
            else:
                delta = -1.0  # Larger negative for failure (learn faster from mistakes)

            cur.execute("""
                UPDATE model_registry
                SET quality_score = GREATEST(0, LEAST(100, COALESCE(quality_score, 50) + %s)),
                    roi_score = CASE
                        WHEN cost_output_per_m > 0
                        THEN GREATEST(0, LEAST(100,
                            COALESCE(quality_score, 50) + %s) / (cost_output_per_m / 5.0))
                        ELSE COALESCE(roi_score, 50)
                    END,
                    updated_at = NOW()
                WHERE model_id = %s
            """, (delta, delta, model_id))

            # Log the flywheel event
            cur.execute("""
                INSERT INTO tool_evolution_log (event_type, tool_name, details)
                VALUES ('flywheel', %s, %s)
            """, (model_id, str({
                "success": success,
                "cost": cost,
                "delta": delta,
                "iterations": session_summary.get("iterations", 0),
                "error_rate": session_summary.get("error_rate", 0),
                "mode": session_summary.get("mode", "standard"),
            })[:500]))

        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
    finally:
        _put_conn(conn)


def check_promotion() -> Optional[dict]:
    """Check if any candidate model should be promoted to replace an underperforming active.

    Returns promotion recommendation or None.
    """
    conn = _get_conn()
    if not conn:
        return None

    try:
        with conn.cursor() as cur:
            # Find active models with quality < 70
            cur.execute("""
                SELECT model_id, tier, quality_score
                FROM model_registry
                WHERE status = 'active' AND tier IS NOT NULL
                  AND quality_score < 70
                ORDER BY quality_score ASC
                LIMIT 1
            """)
            weak = cur.fetchone()
            if not weak:
                return None

            # Find candidates with quality > 80
            cur.execute("""
                SELECT model_id, quality_score, roi_score
                FROM model_registry
                WHERE status = 'candidate' AND quality_score > 80
                ORDER BY roi_score DESC
                LIMIT 1
            """)
            candidate = cur.fetchone()
            if not candidate:
                return None

            return {
                "action": "promote",
                "replace": {"model": weak[0], "tier": weak[1], "quality": weak[2]},
                "with": {"model": candidate[0], "quality": candidate[1], "roi": candidate[2]},
            }
    except Exception:
        return None
    finally:
        _put_conn(conn)
