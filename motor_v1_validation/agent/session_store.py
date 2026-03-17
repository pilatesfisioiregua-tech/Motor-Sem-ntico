"""Session store — persist chat sessions to Postgres."""

import json
from typing import Optional


def _get_conn():
    """Get DB connection via database tool's helper."""
    from tools.database import _get_conn as db_conn
    return db_conn()


def save_session(session_id: str, title: str, phase: str,
                 history: list, briefing: Optional[dict] = None,
                 metadata: Optional[dict] = None,
                 protocol: Optional[dict] = None) -> bool:
    """Save or update a chat session (UPSERT). Protocol state stored in metadata."""
    try:
        conn = _get_conn()
        try:
            # Filter history: strip system messages to save space
            save_history = [
                msg for msg in history
                if msg.get("role") != "system"
            ]
            # Merge protocol into metadata
            meta = metadata or {}
            if protocol:
                meta["protocol"] = protocol
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO chat_sessions (id, title, phase, history, briefing, metadata, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (id) DO UPDATE SET
                        title = EXCLUDED.title,
                        phase = EXCLUDED.phase,
                        history = EXCLUDED.history,
                        briefing = EXCLUDED.briefing,
                        metadata = EXCLUDED.metadata,
                        updated_at = NOW()
                """, [
                    session_id,
                    title,
                    phase,
                    json.dumps(save_history, ensure_ascii=False),
                    json.dumps(briefing, ensure_ascii=False) if briefing else None,
                    json.dumps(meta, ensure_ascii=False),
                ])
            conn.commit()
            return True
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    except Exception:
        return False


def load_session(session_id: str) -> Optional[dict]:
    """Load a chat session from DB. Returns None if not found."""
    try:
        import psycopg2.extras
        conn = _get_conn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, title, phase, history, briefing, metadata, created_at, updated_at
                    FROM chat_sessions WHERE id = %s
                """, [session_id])
                row = cur.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()
    except Exception:
        return None


def list_sessions(limit: int = 20) -> list:
    """List recent chat sessions, ordered by last update."""
    try:
        import psycopg2.extras
        conn = _get_conn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, title, phase, created_at, updated_at,
                           jsonb_array_length(history) as message_count
                    FROM chat_sessions
                    ORDER BY updated_at DESC
                    LIMIT %s
                """, [limit])
                rows = cur.fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()
    except Exception:
        return []


def update_title(session_id: str, title: str) -> bool:
    """Update session title."""
    try:
        conn = _get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE chat_sessions SET title = %s, updated_at = NOW()
                    WHERE id = %s
                """, [title, session_id])
            conn.commit()
            return True
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    except Exception:
        return False


def delete_session(session_id: str) -> bool:
    """Delete a chat session."""
    try:
        conn = _get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM chat_sessions WHERE id = %s", [session_id])
                deleted = cur.rowcount > 0
            conn.commit()
            return deleted
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    except Exception:
        return False
