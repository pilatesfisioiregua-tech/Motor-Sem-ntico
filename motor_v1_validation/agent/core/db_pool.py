"""Shared DB connection pool — singleton, thread-safe."""

import os
import threading
from typing import Optional

_pool = None
_lock = threading.Lock()


def get_pool():
    """Get or create the shared connection pool (lazy, thread-safe)."""
    global _pool
    if _pool is not None:
        return _pool

    with _lock:
        if _pool is not None:
            return _pool

        url = os.environ.get("DATABASE_URL", "")
        if not url:
            return None

        try:
            from psycopg2.pool import ThreadedConnectionPool
            _pool = ThreadedConnectionPool(
                minconn=2,
                maxconn=20,
                dsn=url,
            )
            return _pool
        except Exception:
            return None


def get_conn():
    """Get a connection from the pool. Caller MUST call put_conn() when done."""
    global _pool
    pool = get_pool()
    if pool is None:
        # Fallback: direct connection (no pool available)
        try:
            import psycopg2
            url = os.environ.get("DATABASE_URL", "")
            if not url:
                return None
            return psycopg2.connect(url)
        except Exception:
            return None
    try:
        conn = pool.getconn()
        # Verify connection is alive (handles stale connections after DB restart)
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        except Exception:
            # Connection is dead — try to put it back marked as closed, then reset pool
            try:
                pool.putconn(conn, close=True)
            except Exception:
                pass
            try:
                pool.closeall()
            except Exception:
                pass
            _pool = None
            # Single retry with fresh pool (no recursion loop)
            new_pool = get_pool()
            if new_pool is not None:
                try:
                    return new_pool.getconn()
                except Exception:
                    pass
            # Final fallback: direct connection
            try:
                import psycopg2
                url = os.environ.get("DATABASE_URL", "")
                if url:
                    return psycopg2.connect(url)
            except Exception:
                pass
            return None
        return conn
    except Exception:
        # Pool exhausted or broken — direct connection fallback
        try:
            import psycopg2
            url = os.environ.get("DATABASE_URL", "")
            if url:
                return psycopg2.connect(url)
        except Exception:
            pass
        return None


def put_conn(conn, close: bool = False):
    """Return connection to pool. If close=True or no pool, closes it."""
    if conn is None:
        return
    pool = get_pool()
    if pool is not None and not close:
        try:
            pool.putconn(conn)
            return
        except Exception:
            pass
    # Fallback: close directly
    try:
        conn.close()
    except Exception:
        pass


class pooled_conn:
    """Context manager for pooled DB connections.

    Usage:
        with pooled_conn() as conn:
            cur = conn.cursor()
            cur.execute(...)
            conn.commit()
    """

    def __init__(self):
        self.conn = None

    def __enter__(self):
        self.conn = get_conn()
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn is not None:
            if exc_type is not None:
                try:
                    self.conn.rollback()
                except Exception:
                    pass
            put_conn(self.conn)
            self.conn = None
        return False
