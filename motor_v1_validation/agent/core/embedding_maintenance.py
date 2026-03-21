"""Embedding Maintenance — autonomía total para pgvector.

Fase 2A: el sistema mantiene sus embeddings solo.

Componentes:
  1. FreshnessGuard — detecta embeddings obsoletos (hash cambió pero embedding viejo)
  2. auto_reembed() — re-genera embeddings stale en background
  3. warmup_hnsw() — REINDEX CONCURRENTLY post-backfill
  4. post_deploy_check() — hook para verificar/reparar embeddings tras deploy

Uso:
    from core.embedding_maintenance import get_maintenance
    maint = get_maintenance()
    maint.run_full_cycle()  # detectar stale + re-embed + report
"""

import os
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def _get_conn():
    from .db_pool import get_conn
    return get_conn()

def _put_conn(conn):
    from .db_pool import put_conn
    put_conn(conn)


class EmbeddingMaintenance:
    """Mantiene embeddings fresh y el índice HNSW sano."""

    def __init__(self):
        self._last_cycle = 0
        self._cycle_interval = 3600  # 1 hora entre ciclos

    # ── 1. Freshness Guard ────────────────────────────────────────────────

    def count_stale(self, conn=None) -> dict:
        """Detecta rows con embedding potencialmente obsoleto.

        Stale = metadata->>'file_hash' cambió pero embedding sigue siendo el viejo.
        Missing = embedding IS NULL.
        """
        own_conn = conn is None
        if own_conn:
            conn = _get_conn()
        if not conn:
            return {"missing": 0, "total": 0}

        try:
            with conn.cursor() as cur:
                # Missing embeddings
                cur.execute("SELECT count(*) FROM knowledge_base WHERE embedding IS NULL")
                missing = cur.fetchone()[0]

                # Total
                cur.execute("SELECT count(*) FROM knowledge_base")
                total = cur.fetchone()[0]

                # With embeddings
                cur.execute("SELECT count(*) FROM knowledge_base WHERE embedding IS NOT NULL")
                with_emb = cur.fetchone()[0]

                # Stale: embedding exists but marked for refresh
                # (We track staleness via metadata->>'embedding_hash' != metadata->>'file_hash')
                cur.execute("""
                    SELECT count(*) FROM knowledge_base 
                    WHERE embedding IS NOT NULL 
                      AND metadata->>'embedding_hash' IS NOT NULL
                      AND metadata->>'file_hash' IS NOT NULL
                      AND metadata->>'embedding_hash' != metadata->>'file_hash'
                """)
                stale = cur.fetchone()[0]

            return {
                "total": total,
                "with_embedding": with_emb,
                "missing": missing,
                "stale": stale,
                "coverage_pct": round((with_emb / max(total, 1)) * 100, 1),
            }
        except Exception as e:
            logger.warning(f"count_stale failed: {e}")
            return {"error": str(e)}
        finally:
            if own_conn:
                _put_conn(conn)

    # ── 2. Auto Re-embed ─────────────────────────────────────────────────

    def reembed_stale(self, limit: int = 200, batch_size: int = 50) -> dict:
        """Re-genera embeddings para rows missing o stale.

        Prioridad: missing primero, luego stale.
        """
        conn = _get_conn()
        if not conn:
            return {"error": "no_connection"}

        try:
            from .embedder import get_embedder
            embedder = get_embedder()
        except Exception as e:
            _put_conn(conn)
            return {"error": f"embedder_init_failed: {e}"}

        stats = {"reembedded": 0, "errors": 0}

        try:
            import psycopg2.extras

            # Fetch rows needing embeddings
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, texto, metadata->>'file_hash' as file_hash
                    FROM knowledge_base 
                    WHERE embedding IS NULL
                       OR (metadata->>'embedding_hash' IS NOT NULL 
                           AND metadata->>'file_hash' IS NOT NULL
                           AND metadata->>'embedding_hash' != metadata->>'file_hash')
                    ORDER BY 
                        CASE WHEN embedding IS NULL THEN 0 ELSE 1 END,
                        id
                    LIMIT %s
                """, [limit])
                rows = cur.fetchall()

            if not rows:
                return {"reembedded": 0, "message": "all_fresh"}

            # Process in batches
            for i in range(0, len(rows), batch_size):
                batch = rows[i:i + batch_size]
                ids = [r[0] for r in batch]
                texts = [r[1] or "" for r in batch]
                hashes = [r[2] for r in batch]

                try:
                    vectors = embedder.embed_batch(texts)

                    with conn.cursor() as cur:
                        for row_id, vector, file_hash in zip(ids, vectors, hashes):
                            # Update embedding + mark embedding_hash = file_hash
                            cur.execute("""
                                UPDATE knowledge_base 
                                SET embedding = %s::vector,
                                    metadata = jsonb_set(
                                        coalesce(metadata, '{}'::jsonb),
                                        '{embedding_hash}',
                                        to_jsonb(%s::text)
                                    )
                                WHERE id = %s
                            """, [str(vector), file_hash or "", row_id])

                    conn.commit()
                    stats["reembedded"] += len(batch)

                except Exception as e:
                    logger.error(f"Batch reembed error: {e}")
                    stats["errors"] += 1
                    try:
                        conn.rollback()
                    except Exception:
                        pass

            logger.info(f"reembed_stale: {stats['reembedded']} updated, {stats['errors']} errors")
            return stats

        except Exception as e:
            logger.error(f"reembed_stale failed: {e}")
            return {"error": str(e)}
        finally:
            _put_conn(conn)

    # ── 3. HNSW Warmup ───────────────────────────────────────────────────

    def warmup_hnsw(self) -> dict:
        """REINDEX CONCURRENTLY el índice HNSW para optimizar post-backfill.

        Solo necesario una vez después de un backfill masivo.
        CONCURRENTLY = no bloquea reads/writes.
        """
        conn = _get_conn()
        if not conn:
            return {"error": "no_connection"}

        try:
            # REINDEX CONCURRENTLY requires autocommit
            conn.autocommit = True
            with conn.cursor() as cur:
                t0 = time.time()
                cur.execute("REINDEX INDEX CONCURRENTLY idx_kb_embedding_hnsw")
                elapsed = time.time() - t0

            logger.info(f"HNSW warmup complete in {elapsed:.1f}s")
            return {"status": "ok", "elapsed_s": round(elapsed, 1)}

        except Exception as e:
            logger.error(f"HNSW warmup failed: {e}")
            return {"error": str(e)}
        finally:
            try:
                conn.autocommit = False
            except Exception:
                pass
            _put_conn(conn)

    # ── 4. Post-deploy Check ─────────────────────────────────────────────

    def post_deploy_check(self) -> dict:
        """Health check post-deploy: verifica cobertura de embeddings.

        Si cobertura < 90%, dispara reembed_stale automáticamente.
        """
        status = self.count_stale()
        if "error" in status:
            return status

        result = {
            "status": status,
            "action": "none",
        }

        coverage = status.get("coverage_pct", 0)

        if coverage < 90:
            logger.warning(f"Embedding coverage {coverage}% < 90% — triggering auto-reembed")
            reembed_result = self.reembed_stale(limit=500)
            result["action"] = "auto_reembed"
            result["reembed"] = reembed_result
        elif status.get("stale", 0) > 0:
            logger.info(f"Found {status['stale']} stale embeddings — refreshing")
            reembed_result = self.reembed_stale(limit=100)
            result["action"] = "refresh_stale"
            result["reembed"] = reembed_result
        else:
            logger.info(f"Embeddings healthy: {coverage}% coverage, 0 stale")

        return result

    # ── 5. Full Cycle ─────────────────────────────────────────────────────

    def run_full_cycle(self) -> dict:
        """Ciclo completo de mantenimiento.

        Ejecutar periódicamente (cada hora) o post-deploy.
        """
        now = time.time()
        if now - self._last_cycle < self._cycle_interval:
            return {"skipped": True, "reason": "too_soon"}

        self._last_cycle = now

        result = {
            "timestamp": now,
            "status": self.count_stale(),
        }

        # Auto-reembed if needed
        missing = result["status"].get("missing", 0)
        stale = result["status"].get("stale", 0)

        if missing > 0 or stale > 0:
            result["reembed"] = self.reembed_stale(limit=200)

        # Telemetry
        try:
            from .telemetria import registrar_metrica
            registrar_metrica('embedding_maintenance', 'cycle', result["status"])
        except Exception:
            pass

        return result


# ── Singleton ─────────────────────────────────────────────────────────────

_maintenance: Optional[EmbeddingMaintenance] = None

def get_maintenance() -> EmbeddingMaintenance:
    global _maintenance
    if _maintenance is None:
        _maintenance = EmbeddingMaintenance()
    return _maintenance
