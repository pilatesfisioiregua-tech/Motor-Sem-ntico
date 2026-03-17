"""Neural DB Layer — hybrid search (FTS + Hebbian) over PostgreSQL."""

import os
import json
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def _get_conn():
    """Get DB connection from shared pool."""
    from .db_pool import get_conn
    return get_conn()


def _put_conn(conn):
    """Return connection to pool."""
    from .db_pool import put_conn
    put_conn(conn)


class NeuralDB:
    """Hybrid search with Hebbian learning on knowledge_base."""

    def __init__(self):
        self._session_accesses = {}  # session_id -> [knowledge_ids]
        self._max_sessions = 100     # evict oldest when exceeded

    def semantic_search(self, query: str, limit: int = 10,
                        scope: str = None, session_id: str = None) -> list:
        """Search knowledge_base using hybrid_search() SQL function.

        Combines: full-text search (tsvector) + scope filtering + Hebbian graph boost.
        Returns list of dicts with id, scope, tipo, texto, fts_rank, hebbian_boost, combined_score.
        """
        conn = _get_conn()
        if not conn:
            return []

        try:
            import psycopg2.extras
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT * FROM hybrid_search(%s, %s, %s, %s)",
                    [query, scope, session_id, limit]
                )
                results = [dict(r) for r in cur.fetchall()]

            # Log accesses for Hebbian learning
            if session_id and results:
                ids = [r["id"] for r in results[:5]]
                self._log_accesses(conn, ids, session_id, "search", query)

            logger.info(f"hybrid_search('{query}', scope={scope}) → {len(results)} results")

            # Telemetry (SN-03)
            try:
                from core.telemetria import registrar_metrica
                registrar_metrica('neural_db', 'busqueda', {
                    'query': query[:100],
                    'scope': scope,
                    'resultados': len(results),
                    'top_score': results[0].get('combined_score', 0) if results else 0,
                    'session_id': session_id,
                })
            except Exception:
                pass

            return results
        except Exception as e:
            logger.warning(f"hybrid_search failed: {e}, falling back to ILIKE")
            # Fallback to basic ILIKE if hybrid_search function doesn't exist yet
            try:
                return self._ilike_fallback(conn, query, limit, scope)
            except Exception:
                return []
        finally:
            _put_conn(conn)

    def _ilike_fallback(self, conn, query: str, limit: int, scope: str = None) -> list:
        """Emergency fallback if hybrid_search() SQL function not available."""
        import psycopg2.extras
        conditions = ["(texto ILIKE %s OR tipo ILIKE %s OR scope ILIKE %s)"]
        params = [f"%{query}%", f"%{query}%", f"%{query}%"]
        if scope:
            conditions.append("(scope = %s OR scope LIKE %s)")
            params.extend([scope, f"{scope}:%"])
        params.append(limit)
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(f"""
                SELECT id, scope, tipo, texto,
                       0.1::float as fts_rank, 0.0::float as hebbian_boost, 0.1::float as combined_score
                FROM knowledge_base
                WHERE {' AND '.join(conditions)}
                ORDER BY relevancia DESC, created_at DESC
                LIMIT %s
            """, params)
            return [dict(r) for r in cur.fetchall()]

    def _log_accesses(self, conn, knowledge_ids: list, session_id: str,
                      access_type: str, context: str = None) -> None:
        """Log accesses and strengthen Hebbian connections."""
        try:
            if session_id not in self._session_accesses:
                self._session_accesses[session_id] = []
            prior_ids = self._session_accesses[session_id]

            with conn.cursor() as cur:
                for kid in knowledge_ids:
                    cur.execute("""
                        INSERT INTO knowledge_access_log
                            (knowledge_id, session_id, access_type, context, co_accessed)
                        VALUES (%s, %s, %s, %s, %s)
                    """, [kid, session_id, access_type, context,
                          prior_ids[-10:] if prior_ids else []])

                    # Strengthen Hebbian connections with prior accesses
                    for prior_id in prior_ids[-10:]:
                        if prior_id == kid:
                            continue
                        cur.execute("""
                            INSERT INTO knowledge_connections (source_id, target_id, strength, co_access_count)
                            VALUES (%s, %s, 0.1, 1)
                            ON CONFLICT (source_id, target_id) DO UPDATE SET
                                strength = LEAST(1.0, knowledge_connections.strength + 0.05),
                                co_access_count = knowledge_connections.co_access_count + 1,
                                last_strengthened = NOW()
                        """, [min(prior_id, kid), max(prior_id, kid)])

            conn.commit()
            self._session_accesses[session_id].extend(knowledge_ids)
            self._session_accesses[session_id] = self._session_accesses[session_id][-50:]
            # Evict oldest sessions to prevent memory leak
            if len(self._session_accesses) > self._max_sessions:
                oldest = list(self._session_accesses.keys())[:len(self._session_accesses) - self._max_sessions]
                for k in oldest:
                    del self._session_accesses[k]
        except Exception as e:
            logger.warning(f"Hebbian log failed: {e}")
            try:
                conn.rollback()
            except Exception:
                pass

    def log_access(self, knowledge_id: int, session_id: str,
                   access_type: str, context: str = None) -> None:
        """Public interface to log a single access."""
        conn = _get_conn()
        if not conn:
            return
        try:
            self._log_accesses(conn, [knowledge_id], session_id, access_type, context)
        finally:
            _put_conn(conn)

    def strengthen(self, source_id: int, target_id: int, amount: float = 0.1) -> float:
        """Explicitly strengthen a connection."""
        conn = _get_conn()
        if not conn:
            return 0.0
        try:
            with conn.cursor() as cur:
                s, t = min(source_id, target_id), max(source_id, target_id)
                cur.execute("""
                    INSERT INTO knowledge_connections (source_id, target_id, strength, connection_type)
                    VALUES (%s, %s, %s, 'explicit')
                    ON CONFLICT (source_id, target_id) DO UPDATE SET
                        strength = LEAST(1.0, knowledge_connections.strength + %s),
                        last_strengthened = NOW()
                    RETURNING strength
                """, [s, t, amount, amount])
                new_strength = cur.fetchone()[0]
            conn.commit()
            return new_strength
        except Exception:
            conn.rollback()
            return 0.0
        finally:
            _put_conn(conn)

    def decay_connections(self) -> int:
        """Apply weekly decay to all connections. Remove dead ones."""
        conn = _get_conn()
        if not conn:
            return 0
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE knowledge_connections
                    SET strength = GREATEST(0.0, strength - decay_rate)
                    WHERE last_strengthened < NOW() - INTERVAL '7 days'
                """)
                decayed = cur.rowcount
                cur.execute("DELETE FROM knowledge_connections WHERE strength < 0.01")
            conn.commit()
            return decayed
        except Exception:
            conn.rollback()
            return 0
        finally:
            _put_conn(conn)

    def get_related(self, knowledge_id: int, min_strength: float = 0.2,
                    limit: int = 10) -> list:
        """Get knowledge related by connection strength."""
        conn = _get_conn()
        if not conn:
            return []
        try:
            import psycopg2.extras
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT kb.id, kb.scope, kb.tipo, kb.texto, kc.strength, kc.connection_type
                    FROM knowledge_connections kc
                    JOIN knowledge_base kb ON kb.id = CASE
                        WHEN kc.source_id = %s THEN kc.target_id
                        ELSE kc.source_id
                    END
                    WHERE (kc.source_id = %s OR kc.target_id = %s)
                      AND kc.strength >= %s
                    ORDER BY kc.strength DESC
                    LIMIT %s
                """, [knowledge_id, knowledge_id, knowledge_id, min_strength, limit])
                return [dict(r) for r in cur.fetchall()]
        except Exception:
            return []
        finally:
            _put_conn(conn)

    def get_connection_stats(self) -> dict:
        """Stats about the neural connection network."""
        conn = _get_conn()
        if not conn:
            return {}
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT count(*) as total_connections,
                           avg(strength) as avg_strength,
                           max(strength) as max_strength,
                           count(*) FILTER (WHERE strength > 0.5) as strong_connections,
                           count(*) FILTER (WHERE connection_type = 'hebbian') as hebbian,
                           count(*) FILTER (WHERE connection_type = 'explicit') as explicit_conn
                    FROM knowledge_connections
                """)
                row = cur.fetchone()
            return {
                "total_connections": row[0],
                "avg_strength": round(row[1] or 0, 3),
                "max_strength": round(row[2] or 0, 3),
                "strong_connections": row[3],
                "hebbian": row[4],
                "explicit": row[5],
            }
        except Exception:
            return {}
        finally:
            _put_conn(conn)


# Singleton
_neural_db = None

def get_neural_db() -> NeuralDB:
    global _neural_db
    if _neural_db is None:
        _neural_db = NeuralDB()
    return _neural_db
