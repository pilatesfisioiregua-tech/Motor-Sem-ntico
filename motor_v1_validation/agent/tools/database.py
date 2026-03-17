"""Database tools — db_query, db_insert, analyze_schema via psycopg2."""

import os
import json
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from . import ToolRegistry

QUERY_TIMEOUT = 30
MAX_ROWS = 500


def _get_conn():
    """Get a psycopg2 connection from DATABASE_URL."""
    import psycopg2
    import psycopg2.extras
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        raise ValueError("DATABASE_URL not set. Add it to .env")
    conn = psycopg2.connect(url, connect_timeout=10)
    conn.autocommit = False
    return conn


def tool_db_query(sql: str, params: list = None) -> str:
    """Execute a read-only SQL query and return results as JSON."""
    sql_upper = sql.strip().upper()
    # Block mutations via db_query — use db_insert for those
    if any(sql_upper.startswith(kw) for kw in ("INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", "CREATE")):
        return "ERROR: db_query is read-only. Use db_insert for mutations."
    try:
        import psycopg2.extras
        conn = _get_conn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                if params:
                    cur.execute(sql, params)
                else:
                    cur.execute(sql)
                rows = cur.fetchmany(MAX_ROWS)
                count = cur.rowcount
                columns = [desc[0] for desc in cur.description] if cur.description else []
            return json.dumps({
                "rows": rows,
                "count": count,
                "columns": columns,
                "truncated": count > MAX_ROWS,
            }, indent=2, default=str)
        finally:
            conn.close()
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {e}"


def tool_db_insert(sql: str, params: list = None) -> str:
    """Execute a mutation (INSERT/UPDATE/DELETE/TRUNCATE/CREATE) with auto-commit."""
    sql_upper = sql.strip().upper()
    # Block only DROP (destructive and irreversible)
    if sql_upper.startswith("DROP"):
        return "ERROR: DROP blocked for safety. Use raw psql if needed."
    # Safety check: protected tables
    try:
        from core.safety import validate_mutation
        warning = validate_mutation(sql)
        if warning:
            return f"BLOCKED: {warning}"
    except ImportError:
        pass
    try:
        conn = _get_conn()
        try:
            with conn.cursor() as cur:
                if params:
                    cur.execute(sql, params)
                else:
                    cur.execute(sql)
                affected = cur.rowcount
                # Try to get RETURNING results
                returning_rows = None
                if cur.description:
                    returning_rows = cur.fetchall()
                    columns = [desc[0] for desc in cur.description]
                    returning_rows = [
                        dict(zip(columns, row)) for row in returning_rows
                    ]
            conn.commit()
            result = {"status": "OK", "affected_rows": affected}
            if returning_rows:
                result["returning"] = returning_rows
            return json.dumps(result, indent=2, default=str)
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {e}"


def tool_analyze_schema(schema_name: str = "public") -> str:
    """Analyze database schema: tables, columns, types, indexes."""
    sql = """
    SELECT
        t.table_name,
        c.column_name,
        c.data_type,
        c.is_nullable,
        c.column_default,
        c.character_maximum_length
    FROM information_schema.tables t
    JOIN information_schema.columns c
        ON t.table_name = c.table_name AND t.table_schema = c.table_schema
    WHERE t.table_schema = %s AND t.table_type = 'BASE TABLE'
    ORDER BY t.table_name, c.ordinal_position;
    """
    try:
        import psycopg2.extras
        conn = _get_conn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(sql, [schema_name])
                rows = cur.fetchall()

            # Group by table
            tables = {}
            for row in rows:
                tbl = row["table_name"]
                if tbl not in tables:
                    tables[tbl] = {"columns": []}
                tables[tbl]["columns"].append({
                    "name": row["column_name"],
                    "type": row["data_type"],
                    "nullable": row["is_nullable"] == "YES",
                    "default": row["column_default"],
                    "max_length": row["character_maximum_length"],
                })
            return json.dumps(tables, indent=2, default=str)
        finally:
            conn.close()
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {e}"


def register_tools(registry: 'ToolRegistry', sandbox_dir: str = "") -> None:
    registry.register("db_query", {
        "name": "db_query",
        "description": "Execute a read-only SQL query against the project database (fly.io Postgres). Returns JSON rows. Use for SELECT queries.",
        "parameters": {"type": "object", "properties": {
            "sql": {"type": "string", "description": "SQL SELECT query to execute"},
            "params": {"type": "array", "items": {}, "description": "Query parameters for %s placeholders"},
        }, "required": ["sql"]}
    }, lambda a: tool_db_query(a["sql"], a.get("params")), category="database")

    registry.register("db_insert", {
        "name": "db_insert",
        "description": "Execute a mutation (INSERT/UPDATE/DELETE) against the project database. Auto-commits on success, rollback on error. Use RETURNING to get inserted rows.",
        "parameters": {"type": "object", "properties": {
            "sql": {"type": "string", "description": "SQL mutation to execute (INSERT/UPDATE/DELETE/CREATE)"},
            "params": {"type": "array", "items": {}, "description": "Query parameters for %s placeholders"},
        }, "required": ["sql"]}
    }, lambda a: tool_db_insert(a["sql"], a.get("params")), category="database")

    registry.register("analyze_schema", {
        "name": "analyze_schema",
        "description": "Analyze database schema: list all tables, columns, types, and defaults.",
        "parameters": {"type": "object", "properties": {
            "schema_name": {"type": "string", "description": "Schema to analyze. Default: public"},
        }, "required": []}
    }, lambda a: tool_analyze_schema(a.get("schema_name", "public")), category="database")
