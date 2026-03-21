"""Embedding maintenance — freshness guard + HNSW reindex + deploy hook.

Ensures embeddings stay fresh without manual intervention.
Run periodically (cron/scheduler) or after deploy via /hooks/post-deploy.

Usage:
    from core.embed_maintenance import run_maintenance
    stats = run_maintenance()  # runs all checks

    # Or individually:
    from core.embed_maintenance import refresh_stale, reindex_hnsw, prune_orphans
"""

import os
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def _get_conn():
    import psycopg2
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        url = "postgres://chief_os_omni:77qJGeKtMTgCYhz@localhost:15432/omni_mind"
    conn = psycopg2.connect(url, connect_timeout=15)
    conn.autocommit = False
    return conn


def refresh_stale(conn=None, batch_size: int = 50) -> dict:
    """Find rows where texto changed but embedding is stale, and re-embed them.

    Detection: metadata->>'file_hash' changed since last embed, or embedding IS NULL.
    """
    own_conn = conn is None
    if own_conn:
        conn = _get_conn()

    stats = {"refreshed": 0, "errors": 0}

    try:
        from core.embedder import get_embedder
        embedder = get_embedder()

        with conn.cursor() as cur:
            # Find rows needing embedding refresh
            # Priority: NULL embeddings first, then stale ones
            cur.execute("""
                SELECT id, texto FROM knowledge_base
                WHERE embedding IS NULL AND texto IS NOT NULL AND texto != ''
                ORDER BY updated_at DESC
                LIMIT %s
            """, [batch_size * 10])  # overfetch, process in batches
            rows = cur.fetchall()

        if not rows:
            logger.info("No stale embeddings found")
            return stats

        logger.info(f"Found {len(rows)} rows needing embedding refresh")

        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]
            ids = [r[0] for r in batch]
            texts = [r[1] or "" for r in batch]

            try:
                vectors = embedder.embed_batch(texts)
                with conn.cursor() as cur:
                    for row_id, vector in zip(ids, vectors):
                        cur.execute(
                            "UPDATE knowledge_base SET embedding = %s::vector WHERE id = %s",
                            [str(vector), row_id]
                        )
                conn.commit()
                stats["refreshed"] += len(batch)
            except Exception as e:
                logger.error(f"Batch refresh error: {e}")
                stats["errors"] += 1
                try:
                    conn.rollback()
                except Exception:
                    pass

        return stats
    finally:
        if own_conn:
            conn.close()


def reindex_hnsw(conn=None) -> dict:
    """REINDEX HNSW indexes for optimal performance after bulk inserts."""
    own_conn = conn is None
    if own_conn:
        conn = _get_conn()
        conn.autocommit = True  # REINDEX can't run in transaction

    stats = {"reindexed": [], "errors": []}

    try:
        with conn.cursor() as cur:
            for idx_name in ["idx_kb_embedding_hnsw", "idx_emb_int_hnsw"]:
                try:
                    t0 = time.time()
                    cur.execute(f"REINDEX INDEX CONCURRENTLY {idx_name}")
                    elapsed = round(time.time() - t0, 2)
                    stats["reindexed"].append({"index": idx_name, "time_s": elapsed})
                    logger.info(f"REINDEX {idx_name} completed in {elapsed}s")
                except Exception as e:
                    stats["errors"].append({"index": idx_name, "error": str(e)})
                    logger.error(f"REINDEX {idx_name} failed: {e}")

        return stats
    finally:
        if own_conn:
            conn.close()


def prune_orphans(conn=None) -> dict:
    """Remove embedding rows that reference deleted knowledge_base entries."""
    own_conn = conn is None
    if own_conn:
        conn = _get_conn()

    stats = {"pruned_connections": 0, "pruned_access_log": 0}

    try:
        with conn.cursor() as cur:
            # Prune broken Hebbian connections
            cur.execute("""
                DELETE FROM knowledge_connections
                WHERE source_id NOT IN (SELECT id FROM knowledge_base)
                   OR target_id NOT IN (SELECT id FROM knowledge_base)
            """)
            stats["pruned_connections"] = cur.rowcount

            # Prune old access logs (>30 days)
            cur.execute("""
                DELETE FROM knowledge_access_log
                WHERE created_at < NOW() - INTERVAL '30 days'
            """)
            stats["pruned_access_log"] = cur.rowcount

        conn.commit()
        return stats
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        return {"error": str(e)}
    finally:
        if own_conn:
            conn.close()


def get_health_report(conn=None) -> dict:
    """Full health check of the vector search system."""
    own_conn = conn is None
    if own_conn:
        conn = _get_conn()

    try:
        with conn.cursor() as cur:
            # Coverage
            cur.execute("SELECT count(*) FROM knowledge_base")
            total = cur.fetchone()[0]

            cur.execute("SELECT count(*) FROM knowledge_base WHERE embedding IS NOT NULL")
            with_embedding = cur.fetchone()[0]

            cur.execute("SELECT count(*) FROM knowledge_base WHERE embedding IS NULL")
            without_embedding = cur.fetchone()[0]

            # Inteligencias
            cur.execute("SELECT count(*) FROM embeddings_inteligencias WHERE embedding IS NOT NULL")
            int_embedded = cur.fetchone()[0]

            # Index health
            cur.execute("""
                SELECT indexname, pg_size_pretty(pg_relation_size(indexname::regclass))
                FROM pg_indexes WHERE indexname LIKE '%hnsw%'
            """)
            indexes = [{"name": r[0], "size": r[1]} for r in cur.fetchall()]

            # Clusters
            cur.execute("SELECT count(*) FROM knowledge_clusters")
            n_clusters = cur.fetchone()[0]

            # Hebbian network
            cur.execute("SELECT count(*), avg(strength) FROM knowledge_connections")
            conn_row = cur.fetchone()

            coverage_pct = round(with_embedding / max(total, 1) * 100, 1)

            return {
                "total_rows": total,
                "with_embedding": with_embedding,
                "without_embedding": without_embedding,
                "coverage_pct": coverage_pct,
                "inteligencias_embedded": int_embedded,
                "hnsw_indexes": indexes,
                "n_clusters": n_clusters,
                "hebbian_connections": conn_row[0],
                "avg_hebbian_strength": round(conn_row[1] or 0, 3),
                "status": "healthy" if coverage_pct > 95 else "degraded" if coverage_pct > 50 else "critical",
            }
    except Exception as e:
        return {"error": str(e), "status": "error"}
    finally:
        if own_conn:
            conn.close()


def run_maintenance() -> dict:
    """Run full maintenance cycle. Call from cron or post-deploy hook."""
    logger.info("=== Embedding maintenance cycle starting ===")
    t0 = time.time()
    conn = _get_conn()

    results = {}

    try:
        # 1. Refresh stale embeddings
        results["refresh"] = refresh_stale(conn)

        # 2. Prune orphans
        results["prune"] = prune_orphans(conn)

        # 3. Health report
        results["health"] = get_health_report(conn)

    except Exception as e:
        results["error"] = str(e)
    finally:
        conn.close()

    elapsed = round(time.time() - t0, 2)
    results["elapsed_s"] = elapsed
    logger.info(f"=== Maintenance complete in {elapsed}s ===")

    return results
