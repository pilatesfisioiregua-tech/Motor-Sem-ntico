"""Backfill embeddings for existing knowledge_base rows.

Processes rows where embedding IS NULL in batches.
Idempotent: safe to re-run (skips rows that already have embeddings).

Usage:
    python3 embed_pipeline.py                    # backfill all
    python3 embed_pipeline.py --scope repo       # only repo scope
    python3 embed_pipeline.py --limit 100        # process max 100 rows
    python3 embed_pipeline.py --dry-run          # count without processing

Requires: OPENROUTER_API_KEY and DATABASE_URL in environment.
"""

import os
import sys
import time
import json
import argparse
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger(__name__)

# Add parent to path so we can import core.embedder
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _get_conn():
    import psycopg2
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        url = "postgres://chief_os_omni:77qJGeKtMTgCYhz@localhost:15432/omni_mind"
    conn = psycopg2.connect(url, connect_timeout=15)
    conn.autocommit = False
    return conn


def count_pending(conn, scope_filter: str = None) -> int:
    """Count rows needing embeddings."""
    with conn.cursor() as cur:
        if scope_filter:
            cur.execute(
                "SELECT count(*) FROM knowledge_base WHERE embedding IS NULL AND scope LIKE %s",
                [f"{scope_filter}%"]
            )
        else:
            cur.execute("SELECT count(*) FROM knowledge_base WHERE embedding IS NULL")
        return cur.fetchone()[0]


def count_done(conn) -> int:
    """Count rows with embeddings."""
    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM knowledge_base WHERE embedding IS NOT NULL")
        return cur.fetchone()[0]


def backfill(conn, scope_filter: str = None, limit: int = None,
             batch_size: int = 50) -> dict:
    """Generate embeddings for rows missing them.

    Returns stats dict.
    """
    from core.embedder import get_embedder

    embedder = get_embedder()
    stats = {"processed": 0, "errors": 0, "batches": 0, "total_tokens": 0}

    # Fetch IDs + text for rows missing embeddings
    with conn.cursor() as cur:
        query = "SELECT id, texto FROM knowledge_base WHERE embedding IS NULL"
        params = []
        if scope_filter:
            query += " AND scope LIKE %s"
            params.append(f"{scope_filter}%")
        query += " ORDER BY id"
        if limit:
            query += " LIMIT %s"
            params.append(limit)

        cur.execute(query, params)
        rows = cur.fetchall()

    total = len(rows)
    logger.info(f"Found {total} rows needing embeddings")

    if total == 0:
        return stats

    # Process in batches
    for i in range(0, total, batch_size):
        batch = rows[i:i + batch_size]
        ids = [r[0] for r in batch]
        texts = [r[1] or "" for r in batch]

        try:
            vectors = embedder.embed_batch(texts)

            # Update rows with embeddings
            with conn.cursor() as cur:
                for row_id, vector in zip(ids, vectors):
                    cur.execute(
                        "UPDATE knowledge_base SET embedding = %s::vector WHERE id = %s",
                        [str(vector), row_id]
                    )

            conn.commit()
            stats["processed"] += len(batch)
            stats["batches"] += 1

            # Progress
            pct = (stats["processed"] / total) * 100
            emb_stats = embedder.get_stats()
            logger.info(
                f"  Batch {stats['batches']}: {stats['processed']}/{total} "
                f"({pct:.1f}%) — ${emb_stats['estimated_cost_usd']:.4f}"
            )

        except Exception as e:
            logger.error(f"  Batch error at offset {i}: {e}")
            stats["errors"] += 1
            try:
                conn.rollback()
            except Exception:
                pass

    # Final stats
    emb_stats = embedder.get_stats()
    stats["total_tokens"] = emb_stats["total_tokens"]
    stats["estimated_cost_usd"] = emb_stats["estimated_cost_usd"]

    return stats


def backfill_inteligencias(conn) -> int:
    """Generate embeddings for the 18 inteligencias."""
    from core.embedder import get_embedder

    embedder = get_embedder()

    with conn.cursor() as cur:
        # Get all inteligencias
        cur.execute("SELECT id, nombre, firma, punto_ciego, preguntas FROM inteligencias")
        rows = cur.fetchall()

    if not rows:
        logger.warning("No inteligencias found in DB")
        return 0

    count = 0
    for row in rows:
        int_id, nombre, firma, punto_ciego, preguntas = row

        # Build rich text for embedding
        preguntas_text = ""
        if isinstance(preguntas, dict):
            for lente, funcs in preguntas.items():
                if isinstance(funcs, dict):
                    for func, qs in funcs.items():
                        if isinstance(qs, list):
                            preguntas_text += " ".join(qs) + " "
        elif isinstance(preguntas, str):
            preguntas_text = preguntas

        texto_base = f"{nombre}. {firma}. Punto ciego: {punto_ciego}. Preguntas: {preguntas_text[:2000]}"

        try:
            vector = embedder.embed_one(texto_base)

            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO embeddings_inteligencias (id, embedding, texto_base, updated_at)
                    VALUES (%s, %s::vector, %s, NOW())
                    ON CONFLICT (id) DO UPDATE SET
                        embedding = EXCLUDED.embedding,
                        texto_base = EXCLUDED.texto_base,
                        updated_at = NOW()
                """, [int_id, str(vector), texto_base[:5000]])

            conn.commit()
            count += 1
            logger.info(f"  Embedded {int_id}: {nombre}")

        except Exception as e:
            logger.error(f"  Error embedding {int_id}: {e}")
            try:
                conn.rollback()
            except Exception:
                pass

    return count


def main():
    parser = argparse.ArgumentParser(description="Backfill embeddings in knowledge_base")
    parser.add_argument("--scope", default=None, help="Filter by scope prefix")
    parser.add_argument("--limit", type=int, default=None, help="Max rows to process")
    parser.add_argument("--batch-size", type=int, default=50, help="Batch size (default: 50)")
    parser.add_argument("--dry-run", action="store_true", help="Just count, don't process")
    parser.add_argument("--inteligencias", action="store_true",
                        help="Also embed the 18 inteligencias")
    args = parser.parse_args()

    conn = _get_conn()

    # Count
    pending = count_pending(conn, args.scope)
    done = count_done(conn)
    logger.info(f"knowledge_base: {done} with embeddings, {pending} pending")

    if args.dry_run:
        logger.info("Dry run — no changes made")
        conn.close()
        return

    if pending > 0:
        logger.info(f"\n=== Backfilling {min(pending, args.limit or pending)} rows ===\n")
        t0 = time.time()
        stats = backfill(conn, args.scope, args.limit, args.batch_size)
        elapsed = time.time() - t0

        logger.info(f"\n=== Backfill complete ===")
        logger.info(f"  Processed:  {stats['processed']}")
        logger.info(f"  Errors:     {stats['errors']}")
        logger.info(f"  Batches:    {stats['batches']}")
        logger.info(f"  Tokens:     {stats.get('total_tokens', 0):,}")
        logger.info(f"  Cost:       ${stats.get('estimated_cost_usd', 0):.4f}")
        logger.info(f"  Time:       {elapsed:.1f}s")
        logger.info(f"  Speed:      {stats['processed'] / max(elapsed, 0.1):.0f} rows/s")
    else:
        logger.info("All rows already have embeddings!")

    if args.inteligencias:
        logger.info(f"\n=== Embedding 18 inteligencias ===\n")
        n = backfill_inteligencias(conn)
        logger.info(f"  Embedded {n} inteligencias")

    # Final count
    done_after = count_done(conn)
    pending_after = count_pending(conn, args.scope)
    logger.info(f"\nFinal state: {done_after} with embeddings, {pending_after} pending")

    conn.close()


if __name__ == "__main__":
    main()
