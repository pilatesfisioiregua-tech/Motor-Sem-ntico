"""Cache Tier 0 — Lookup puro, sin LLM ($0).

Patrón 60661 (Enjambre Escalonado): El tier más barato es lookup puro.

Antes de llamar a cualquier modelo, busca en knowledge_base si existe
una respuesta cacheada para tareas comunes (edits conocidos, refactors
estándar, plantillas).
"""

import hashlib
import json
from typing import Optional, List


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


def _normalize_goal(goal: str) -> str:
    """Normalize goal for cache matching."""
    return " ".join(goal.lower().strip().split())


def _goal_hash(goal: str) -> str:
    """Deterministic hash of normalized goal."""
    return hashlib.sha256(_normalize_goal(goal).encode()).hexdigest()[:32]


def try_cache(goal: str, tool_history: list = None) -> Optional[dict]:
    """Busca en knowledge_base si hay una respuesta cacheada.

    Returns cached tool sequence dict or None (pass to LLM tier).
    Cache entries stored in knowledge_base with scope='cache:responses'.
    """
    conn = _get_conn()
    if not conn:
        return None

    try:
        goal_norm = _normalize_goal(goal)
        goal_h = _goal_hash(goal)

        with conn.cursor() as cur:
            # 1. Exact hash match (fastest)
            cur.execute("""
                SELECT texto, metadata
                FROM knowledge_base
                WHERE scope = 'cache:responses'
                  AND metadata->>'goal_hash' = %s
                  AND (metadata->>'success')::boolean = true
                ORDER BY created_at DESC
                LIMIT 1
            """, (goal_h,))
            row = cur.fetchone()
            if row:
                try:
                    cached = json.loads(row[0]) if isinstance(row[0], str) else row[0]
                    return {"source": "cache_exact", "data": cached}
                except (json.JSONDecodeError, TypeError):
                    pass

            # 2. Text similarity match (if pgvector available, use embedding; else ILIKE)
            cur.execute("""
                SELECT texto, metadata,
                       similarity(lower(tipo), %s) as sim
                FROM knowledge_base
                WHERE scope = 'cache:responses'
                  AND (metadata->>'success')::boolean = true
                  AND length(tipo) > 5
                ORDER BY sim DESC
                LIMIT 1
            """, (goal_norm[:100],))
            row = cur.fetchone()
            if row and row[2] and row[2] > 0.85:
                try:
                    cached = json.loads(row[0]) if isinstance(row[0], str) else row[0]
                    return {"source": "cache_similar", "similarity": row[2], "data": cached}
                except (json.JSONDecodeError, TypeError):
                    pass

        return None
    except Exception:
        return None
    finally:
        _put_conn(conn)


def save_to_cache(goal: str, tool_sequence: List[dict], result: str, success: bool) -> bool:
    """Guardar ejecución exitosa como cache entry.

    Only caches successful, short executions (< 5 tool calls).
    """
    if not success or len(tool_sequence) > 5:
        return False

    conn = _get_conn()
    if not conn:
        return False

    try:
        goal_h = _goal_hash(goal)
        goal_norm = _normalize_goal(goal)

        cache_data = json.dumps({
            "tool_sequence": tool_sequence[:5],
            "result_preview": result[:500] if result else "",
        })

        metadata = json.dumps({
            "goal_hash": goal_h,
            "success": True,
            "tool_count": len(tool_sequence),
        })

        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO knowledge_base (scope, tipo, texto, metadata)
                VALUES ('cache:responses', %s, %s, %s::jsonb)
                ON CONFLICT DO NOTHING
            """, (goal_norm[:200], cache_data, metadata))

        conn.commit()
        return True
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        return False
