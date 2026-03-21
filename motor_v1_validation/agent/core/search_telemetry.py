"""Search telemetry — tracks vector vs FTS quality for comparison.

Instruments neural_db.semantic_search() to record quality metrics.
Data feeds search_quality_comparison materialized view.

Usage:
    from core.search_telemetry import track_search, track_click
    
    # After a search
    track_search(query, results, has_vector=True, latency_ms=45)
    
    # When user clicks/uses a result
    track_click(search_id, result_id, rank, feedback="relevant")
"""

import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def track_search(query: str, results: list, has_vector: bool = False,
                  scope: str = None, session_id: str = None,
                  latency_ms: int = None, embedding_latency_ms: int = None) -> Optional[int]:
    """Record a search event for quality tracking.

    Returns search_telemetry.id for later click tracking.
    """
    try:
        from core.db_pool import get_conn, put_conn
        conn = get_conn()
        if not conn:
            return None

        try:
            top_score = results[0].get("combined_score", 0) if results else None
            top_vector = results[0].get("vector_rank", 0) if results else None
            top_fts = results[0].get("fts_rank", 0) if results else None
            has_fts = any(r.get("fts_rank", 0) > 0 for r in results) if results else False
            has_hebbian = any(r.get("hebbian_boost", 0) > 0 for r in results) if results else False

            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO search_telemetry
                        (query, scope, session_id, has_vector, has_fts, has_hebbian,
                         n_results, top_score, top_vector_rank, top_fts_rank,
                         latency_ms, embedding_latency_ms)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, [
                    query[:500], scope, session_id,
                    has_vector, has_fts, has_hebbian,
                    len(results), top_score, top_vector, top_fts,
                    latency_ms, embedding_latency_ms,
                ])
                row = cur.fetchone()
                search_id = row[0] if row else None

            conn.commit()
            return search_id

        finally:
            put_conn(conn)

    except Exception as e:
        logger.warning(f"Search telemetry failed: {e}")
        return None


def track_click(search_id: int, result_id: int, rank: int,
                feedback: str = "relevant") -> None:
    """Record which search result was actually used."""
    try:
        from core.db_pool import get_conn, put_conn
        conn = get_conn()
        if not conn:
            return

        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE search_telemetry
                    SET result_clicked_id = %s,
                        result_clicked_rank = %s,
                        feedback = %s
                    WHERE id = %s
                """, [result_id, rank, feedback, search_id])
            conn.commit()
        finally:
            put_conn(conn)

    except Exception as e:
        logger.warning(f"Click tracking failed: {e}")


def get_quality_report() -> dict:
    """Compare vector vs non-vector search quality."""
    try:
        from core.db_pool import get_conn, put_conn
        conn = get_conn()
        if not conn:
            return {}

        try:
            import psycopg2.extras
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Try materialized view first
                try:
                    cur.execute("SELECT * FROM search_quality_comparison")
                    rows = [dict(r) for r in cur.fetchall()]
                    if rows:
                        return {"comparison": rows, "source": "materialized_view"}
                except Exception:
                    pass

                # Fallback: live query
                cur.execute("""
                    SELECT
                        has_vector,
                        count(*) as n_searches,
                        round(avg(n_results)::numeric, 1) as avg_results,
                        round(avg(top_score)::numeric, 4) as avg_top_score,
                        round(avg(latency_ms)::numeric, 0) as avg_latency_ms
                    FROM search_telemetry
                    WHERE created_at > NOW() - INTERVAL '7 days'
                    GROUP BY has_vector
                """)
                rows = [dict(r) for r in cur.fetchall()]
                return {"comparison": rows, "source": "live_query"}

        finally:
            put_conn(conn)

    except Exception as e:
        return {"error": str(e)}
