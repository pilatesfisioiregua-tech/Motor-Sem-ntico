"""Tool Evolution Engine — telemetry, gap detection, auto-creation, compositions."""

import os
import json
import time
from typing import Optional


def _get_conn():
    """Get DB connection from shared pool."""
    from .db_pool import get_conn
    return get_conn()


def _put_conn(conn):
    """Return connection to pool."""
    from .db_pool import put_conn
    put_conn(conn)


class ToolEvolutionEngine:
    """Tracks tool usage, detects gaps, suggests compositions."""

    def __init__(self):
        self._queue = []       # buffered telemetry entries
        self._queue_max = 10   # flush every N entries
        self._last_flush = time.time()
        self._flush_interval = 5.0  # or every 5 seconds

    # --- Telemetry (batched) --- #

    def log_invocation(self, tool_name: str, session_id: str = "",
                       success: bool = True, latency_ms: int = 0,
                       error_message: str = None, cost_usd: float = 0.0,
                       context: dict = None) -> None:
        """Buffer a tool invocation for batch insert."""
        self._queue.append((
            tool_name, session_id, success, error_message,
            latency_ms, cost_usd,
            json.dumps(context or {}, ensure_ascii=False),
        ))
        # Auto-flush if buffer full or interval elapsed
        if (len(self._queue) >= self._queue_max or
                time.time() - self._last_flush >= self._flush_interval):
            self._flush_telemetry()

    def _flush_telemetry(self) -> None:
        """Batch insert all buffered telemetry entries."""
        if not self._queue:
            return
        batch = self._queue[:]
        self._queue.clear()
        self._last_flush = time.time()

        conn = _get_conn()
        if not conn:
            return
        try:
            with conn.cursor() as cur:
                from psycopg2.extras import execute_values
                execute_values(cur, """
                    INSERT INTO tool_telemetry
                        (tool_name, session_id, success, error_message,
                         latency_ms, cost_usd, context)
                    VALUES %s
                """, batch)
            conn.commit()
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
        finally:
            _put_conn(conn)

    def flush(self) -> None:
        """Force flush — call at end of session."""
        self._flush_telemetry()

    def get_tool_stats(self, tool_name: str = None, days: int = 30) -> dict:
        """Get usage stats for one or all tools."""
        conn = _get_conn()
        if not conn:
            return {"error": "No DB connection"}
        try:
            import psycopg2.extras
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                if tool_name:
                    cur.execute("""
                        SELECT tool_name,
                               count(*) as total_calls,
                               count(*) FILTER (WHERE success) as successes,
                               count(*) FILTER (WHERE NOT success) as failures,
                               ROUND(avg(latency_ms)::numeric, 0) as avg_latency_ms,
                               ROUND(sum(cost_usd)::numeric, 4) as total_cost,
                               ROUND((count(*) FILTER (WHERE success))::numeric / NULLIF(count(*), 0) * 100, 1) as success_rate
                        FROM tool_telemetry
                        WHERE tool_name = %s
                          AND created_at > NOW() - MAKE_INTERVAL(days => %s)
                        GROUP BY tool_name
                    """, [tool_name, days])
                else:
                    cur.execute("""
                        SELECT tool_name,
                               count(*) as total_calls,
                               count(*) FILTER (WHERE success) as successes,
                               count(*) FILTER (WHERE NOT success) as failures,
                               ROUND(avg(latency_ms)::numeric, 0) as avg_latency_ms,
                               ROUND(sum(cost_usd)::numeric, 4) as total_cost,
                               ROUND((count(*) FILTER (WHERE success))::numeric / NULLIF(count(*), 0) * 100, 1) as success_rate
                        FROM tool_telemetry
                        WHERE created_at > NOW() - MAKE_INTERVAL(days => %s)
                        GROUP BY tool_name
                        ORDER BY total_calls DESC
                    """, [days])
                rows = cur.fetchall()
            return {"tools": [dict(r) for r in rows], "period_days": days}
        except Exception as e:
            return {"error": str(e)}
        finally:
            _put_conn(conn)

    def get_tool_rankings(self) -> dict:
        """Rankings: most used, most effective, most costly, slowest."""
        conn = _get_conn()
        if not conn:
            return {"error": "No DB connection"}
        try:
            import psycopg2.extras
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Most used
                cur.execute("""
                    SELECT tool_name, count(*) as calls
                    FROM tool_telemetry
                    WHERE created_at > NOW() - INTERVAL '30 days'
                    GROUP BY tool_name ORDER BY calls DESC LIMIT 10
                """)
                most_used = cur.fetchall()

                # Highest success rate (min 5 calls)
                cur.execute("""
                    SELECT tool_name,
                           ROUND((count(*) FILTER (WHERE success))::numeric / count(*) * 100, 1) as success_rate,
                           count(*) as calls
                    FROM tool_telemetry
                    WHERE created_at > NOW() - INTERVAL '30 days'
                    GROUP BY tool_name HAVING count(*) >= 5
                    ORDER BY success_rate DESC LIMIT 10
                """)
                most_effective = cur.fetchall()

                # Most costly
                cur.execute("""
                    SELECT tool_name, ROUND(sum(cost_usd)::numeric, 4) as total_cost, count(*) as calls
                    FROM tool_telemetry
                    WHERE created_at > NOW() - INTERVAL '30 days'
                    GROUP BY tool_name ORDER BY total_cost DESC LIMIT 10
                """)
                most_costly = cur.fetchall()

                # Slowest
                cur.execute("""
                    SELECT tool_name, ROUND(avg(latency_ms)::numeric, 0) as avg_latency, count(*) as calls
                    FROM tool_telemetry
                    WHERE created_at > NOW() - INTERVAL '30 days'
                    GROUP BY tool_name HAVING count(*) >= 3
                    ORDER BY avg_latency DESC LIMIT 10
                """)
                slowest = cur.fetchall()

            return {
                "most_used": [dict(r) for r in most_used],
                "most_effective": [dict(r) for r in most_effective],
                "most_costly": [dict(r) for r in most_costly],
                "slowest": [dict(r) for r in slowest],
            }
        except Exception as e:
            return {"error": str(e)}
        finally:
            _put_conn(conn)

    # --- Gap Detection --- #

    def detect_gap(self, description: str, attempted_tools: list = None,
                   failure_reason: str = "") -> int:
        """Record a tool gap. If similar exists, increment frequency."""
        conn = _get_conn()
        if not conn:
            return -1
        try:
            with conn.cursor() as cur:
                # Check if similar gap exists
                cur.execute("""
                    SELECT id, frequency FROM tool_gaps
                    WHERE description ILIKE %s AND status != 'rejected'
                    LIMIT 1
                """, [f"%{description[:50]}%"])
                existing = cur.fetchone()

                if existing:
                    cur.execute("""
                        UPDATE tool_gaps SET frequency = frequency + 1, updated_at = NOW()
                        WHERE id = %s RETURNING id
                    """, [existing[0]])
                    gap_id = existing[0]
                else:
                    cur.execute("""
                        INSERT INTO tool_gaps (description, attempted_tools, failure_reason)
                        VALUES (%s, %s, %s) RETURNING id
                    """, [description, attempted_tools or [], failure_reason])
                    gap_id = cur.fetchone()[0]

                    # Log evolution event
                    cur.execute("""
                        INSERT INTO tool_evolution_log (event_type, details)
                        VALUES ('gap_detected', %s)
                    """, [json.dumps({"gap_id": gap_id, "description": description})])

            conn.commit()

            # Emit estigmergia mark for reactor consumption
            try:
                from .mejora_continua import crear_marca_estigmergica
                crear_marca_estigmergica('tool_gap', 'tool_evolution', {
                    'gap_id': gap_id,
                    'description': description,
                    'attempted_tools': attempted_tools or [],
                    'failure_reason': failure_reason,
                }, conn=conn)
            except Exception:
                pass

            return gap_id
        except Exception:
            conn.rollback()
            return -1
        finally:
            _put_conn(conn)

    def get_top_gaps(self, limit: int = 10) -> list:
        """Top gaps by frequency — candidates for auto-creation."""
        conn = _get_conn()
        if not conn:
            return []
        try:
            import psycopg2.extras
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM tool_gaps
                    WHERE status IN ('detected', 'designing')
                    ORDER BY frequency DESC
                    LIMIT %s
                """, [limit])
                rows = cur.fetchall()
            return [dict(r) for r in rows]
        except Exception:
            return []
        finally:
            _put_conn(conn)

    # --- Compositions --- #

    def create_composition(self, name: str, description: str,
                          steps: list, trigger: str = None) -> dict:
        """Create a workflow composition of multiple tools."""
        conn = _get_conn()
        if not conn:
            return {"error": "No DB connection"}
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO tool_compositions (name, description, steps, trigger_pattern)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                """, [name, description, json.dumps(steps), trigger])
                comp_id = cur.fetchone()[0]

                cur.execute("""
                    INSERT INTO tool_evolution_log (event_type, tool_name, details)
                    VALUES ('composition_created', %s, %s)
                """, [name, json.dumps({"steps": len(steps)})])
            conn.commit()
            return {"id": comp_id, "name": name}
        except Exception as e:
            conn.rollback()
            return {"error": str(e)}
        finally:
            _put_conn(conn)

    def get_compositions(self) -> list:
        """List active tool compositions."""
        conn = _get_conn()
        if not conn:
            return []
        try:
            import psycopg2.extras
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM tool_compositions
                    WHERE status = 'active'
                    ORDER BY usage_count DESC
                """)
                rows = cur.fetchall()
            return [dict(r) for r in rows]
        except Exception:
            return []
        finally:
            _put_conn(conn)

    def suggest_compositions(self) -> list:
        """Analyze telemetry for recurring tool sequences."""
        conn = _get_conn()
        if not conn:
            return []
        try:
            with conn.cursor() as cur:
                # Find common tool pairs called in same session
                cur.execute("""
                    WITH session_tools AS (
                        SELECT session_id, array_agg(tool_name ORDER BY created_at) as tools
                        FROM tool_telemetry
                        WHERE session_id IS NOT NULL
                          AND created_at > NOW() - INTERVAL '30 days'
                        GROUP BY session_id
                        HAVING count(*) >= 3
                    )
                    SELECT tools, count(*) as occurrences
                    FROM session_tools
                    GROUP BY tools
                    HAVING count(*) >= 2
                    ORDER BY occurrences DESC
                    LIMIT 5
                """)
                rows = cur.fetchall()
            return [{"tools": r[0], "occurrences": r[1]} for r in rows]
        except Exception:
            return []
        finally:
            _put_conn(conn)

    # --- Evolution Report --- #

    def evolution_report(self) -> dict:
        """Complete report: tools, gaps, compositions, trends."""
        conn = _get_conn()
        if not conn:
            return {"error": "No DB connection"}
        try:
            import psycopg2.extras
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Summary stats
                cur.execute("""
                    SELECT count(DISTINCT tool_name) as unique_tools,
                           count(*) as total_calls,
                           ROUND(avg(latency_ms)::numeric, 0) as avg_latency,
                           ROUND(sum(cost_usd)::numeric, 4) as total_cost,
                           ROUND((count(*) FILTER (WHERE success))::numeric / NULLIF(count(*), 0) * 100, 1) as overall_success_rate
                    FROM tool_telemetry
                    WHERE created_at > NOW() - INTERVAL '30 days'
                """)
                summary = cur.fetchone()

                # Gap count
                cur.execute("SELECT count(*) as cnt FROM tool_gaps WHERE status = 'detected'")
                open_gaps = cur.fetchone()["cnt"]

                # Composition count
                cur.execute("SELECT count(*) as cnt FROM tool_compositions WHERE status = 'active'")
                active_compositions = cur.fetchone()["cnt"]

                # Recent evolution events
                cur.execute("""
                    SELECT event_type, tool_name, created_at
                    FROM tool_evolution_log
                    ORDER BY created_at DESC LIMIT 10
                """)
                recent_events = cur.fetchall()

            events = []
            for e in recent_events:
                d = dict(e)
                if d.get("created_at"):
                    d["created_at"] = str(d["created_at"])
                events.append(d)

            return {
                "summary": dict(summary) if summary else {},
                "open_gaps": open_gaps,
                "active_compositions": active_compositions,
                "recent_events": events,
            }
        except Exception as e:
            return {"error": str(e)}
        finally:
            _put_conn(conn)


# Singleton
_engine = None

def get_tool_evolution() -> ToolEvolutionEngine:
    global _engine
    if _engine is None:
        _engine = ToolEvolutionEngine()
    return _engine
