"""Vector-based intelligence routing for Motor vN.

Instead of static mapping (funcion → inteligencias), uses cosine similarity
between the input case and embeddings_inteligencias to find the most relevant INTs.

Plugs into: motor_vn.py _fase_compilacion() and reglas_compilador.py generar()

Usage:
    from core.vector_routing import route_by_similarity
    ranked = route_by_similarity("Mi socio quiere vender su parte del negocio")
    # → [('INT-07', 0.82), ('INT-06', 0.79), ('INT-17', 0.76), ...]
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def route_by_similarity(input_texto: str, top_k: int = 8, conn=None) -> list:
    """Find most relevant inteligencias by vector similarity to input.

    Args:
        input_texto: Case text in natural language
        top_k: Max inteligencias to return (pre-filter, before R01 rules)
        conn: DB connection (creates one if None)

    Returns:
        List of (int_id, similarity_score) tuples, sorted by similarity desc.
        Returns empty list on failure (caller falls back to static mapping).
    """
    own_conn = conn is None

    try:
        # 1. Embed the input
        from core.embedder import get_embedder
        embedder = get_embedder()
        query_vector = embedder.embed_one(input_texto)

        if not query_vector or not any(v != 0.0 for v in query_vector[:10]):
            logger.warning("Empty query vector, falling back to static routing")
            return []

        # 2. Query embeddings_inteligencias
        if own_conn:
            from core.db_pool import get_conn, put_conn
            conn = get_conn()
            if not conn:
                return []

        try:
            import psycopg2.extras
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, 1 - (embedding <=> %s::vector) AS similarity
                    FROM embeddings_inteligencias
                    WHERE embedding IS NOT NULL
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                """, [str(query_vector), str(query_vector), top_k])
                results = cur.fetchall()

            ranked = [(r["id"], round(r["similarity"], 4)) for r in results]

            if ranked:
                logger.info(
                    f"Vector routing: top={ranked[0][0]} ({ranked[0][1]}), "
                    f"bottom={ranked[-1][0]} ({ranked[-1][1]})"
                )

            return ranked

        finally:
            if own_conn and conn:
                put_conn(conn)

    except Exception as e:
        logger.warning(f"Vector routing failed: {e}, will use static mapping")
        return []


def route_questions_by_similarity(input_texto: str, top_k: int = 20,
                                   conn=None) -> list:
    """Find most relevant preguntas_matriz by embedding similarity.

    Instead of selecting questions only by celda, finds questions whose
    embedded text is semantically close to the input. Enables cross-celda
    question discovery.

    Args:
        input_texto: Case text
        top_k: Max questions to return

    Returns:
        List of dicts with pregunta_id, texto, inteligencia, similarity.
    """
    own_conn = conn is None

    try:
        from core.embedder import get_embedder
        embedder = get_embedder()
        query_vector = embedder.embed_one(input_texto)

        if not query_vector or not any(v != 0.0 for v in query_vector[:10]):
            return []

        if own_conn:
            from core.db_pool import get_conn, put_conn
            conn = get_conn()
            if not conn:
                return []

        try:
            # Search knowledge_base for question-type entries
            import psycopg2.extras
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT kb.id, kb.texto, kb.scope, kb.tipo,
                           1 - (kb.embedding <=> %s::vector) AS similarity
                    FROM knowledge_base kb
                    WHERE kb.embedding IS NOT NULL
                      AND kb.tipo IN ('documentation', 'schema', 'architecture')
                    ORDER BY kb.embedding <=> %s::vector
                    LIMIT %s
                """, [str(query_vector), str(query_vector), top_k])
                results = [dict(r) for r in cur.fetchall()]

            return results

        finally:
            if own_conn and conn:
                put_conn(conn)

    except Exception as e:
        logger.warning(f"Question routing by similarity failed: {e}")
        return []


def enrich_gap_routing(gaps_top: list, input_texto: str,
                        max_extra: int = 2) -> list:
    """Enrich static gap-based INT selection with vector suggestions.

    Takes the static mapping output (_ints_para_gaps) and adds
    vector-suggested INTs that the static mapping missed.

    Args:
        gaps_top: Output from _ints_para_gaps() — list of INT-XX ids
        input_texto: Original input text
        max_extra: Max additional INTs to add from vector routing

    Returns:
        Enriched list of INT-XX ids
    """
    vector_ranked = route_by_similarity(input_texto, top_k=8)
    if not vector_ranked:
        return gaps_top

    existing = set(gaps_top)
    enriched = list(gaps_top)

    added = 0
    for int_id, sim in vector_ranked:
        if int_id not in existing and sim > 0.3 and added < max_extra:
            enriched.append(int_id)
            existing.add(int_id)
            added += 1
            logger.info(f"Vector enrichment: added {int_id} (sim={sim})")

    return enriched
