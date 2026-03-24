"""Pool de conexiones asyncpg para Postgres — production-grade."""
from __future__ import annotations

import asyncio
import hashlib
import asyncpg
import structlog
from src.config.settings import DATABASE_URL

log = structlog.get_logger()

_pool: asyncpg.Pool | None = None

# ============================================================
# POOL con retry + health check
# ============================================================

async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None or _pool._closed:
        _pool = await _create_pool_with_retry()
    return _pool


async def _create_pool_with_retry(max_retries: int = 3) -> asyncpg.Pool:
    """Crea pool con retry + backoff exponencial."""
    for attempt in range(max_retries):
        try:
            pool = await asyncpg.create_pool(
                DATABASE_URL,
                min_size=2,
                max_size=10,
                command_timeout=60,
                server_settings={'application_name': 'omni-mind'},
            )
            log.info("db_pool_created", attempt=attempt + 1)
            return pool
        except Exception as e:
            wait = 2 ** attempt
            log.warning("db_pool_retry", attempt=attempt + 1, error=str(e)[:100], wait_s=wait)
            if attempt < max_retries - 1:
                await asyncio.sleep(wait)
            else:
                raise


async def close_pool():
    global _pool
    if _pool and not _pool._closed:
        await _pool.close()
        _pool = None
        log.info("db_pool_closed")


async def health_check() -> dict:
    """Verifica que el pool funciona."""
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            result = await conn.fetchval("SELECT 1")
            size = pool.get_size()
            idle = pool.get_idle_size()
        return {"ok": True, "pool_size": size, "pool_idle": idle}
    except Exception as e:
        return {"ok": False, "error": str(e)[:100]}


# ============================================================
# SCHEMA + MIGRATIONS con tracking
# ============================================================

async def execute_schema():
    """Ejecuta schema.sql para crear tablas."""
    pool = await get_pool()
    from pathlib import Path
    schema_path = Path(__file__).parent / "schema.sql"
    schema = schema_path.read_text()
    async with pool.acquire() as conn:
        await conn.execute(schema)
    log.info("schema_executed")


async def execute_migrations():
    """Ejecuta migrations SQL con tracking (no repite las ya aplicadas)."""
    from pathlib import Path
    pool = await get_pool()
    migrations_dir = Path(__file__).parent.parent.parent / "migrations"
    if not migrations_dir.exists():
        return

    sql_files = sorted(migrations_dir.glob("*.sql"))
    async with pool.acquire() as conn:
        # Asegurar tabla de tracking
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS om_schema_migrations (
                version TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                applied_at TIMESTAMPTZ DEFAULT now(),
                checksum TEXT
            )
        """)

        # Obtener migraciones ya aplicadas
        applied = set()
        rows = await conn.fetch("SELECT version FROM om_schema_migrations")
        for r in rows:
            applied.add(r["version"])

        for sql_file in sql_files:
            version = sql_file.stem
            if version in applied:
                continue

            try:
                sql = sql_file.read_text()
                checksum = hashlib.md5(sql.encode()).hexdigest()
                await conn.execute(sql)
                await conn.execute("""
                    INSERT INTO om_schema_migrations (version, filename, checksum)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (version) DO NOTHING
                """, version, sql_file.name, checksum)
                log.info("migration_ok", file=sql_file.name)
            except Exception as e:
                log.error("migration_error", file=sql_file.name, error=str(e)[:200])
                # No continuar si una migración falla — DB puede quedar inconsistente
                break


async def execute_seeds():
    """Ejecuta seeds Python idempotentes (V4+)."""
    import importlib.util
    import sys
    from pathlib import Path

    migrations_dir = Path(__file__).parent.parent.parent / "migrations"
    if not migrations_dir.exists():
        return

    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    py_files = sorted(
        list(migrations_dir.glob("v4_seed_*.py")) +
        list(migrations_dir.glob("om_seed_*.py"))
    )
    for py_file in py_files:
        try:
            spec = importlib.util.spec_from_file_location(py_file.stem, py_file)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            if hasattr(mod, 'seed'):
                await mod.seed()
                log.info("seed_ok", file=py_file.name)
        except Exception as e:
            log.warning("seed_skip", file=py_file.name, error=str(e)[:100])


# ============================================================
# QUERIES MOTOR SEMÁNTICO
# ============================================================

async def fetch_all_inteligencias() -> list[dict]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, nombre, descripcion, tipo, red_preguntas FROM inteligencias ORDER BY id")
        return [dict(r) for r in rows]


async def fetch_aristas(tipo: str | None = None) -> list[dict]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        if tipo:
            rows = await conn.fetch(
                "SELECT origen, destino, tipo, peso, justificacion FROM aristas_grafo WHERE tipo = $1 ORDER BY peso DESC", tipo)
        else:
            rows = await conn.fetch("SELECT origen, destino, tipo, peso, justificacion FROM aristas_grafo ORDER BY peso DESC")
        return [dict(r) for r in rows]


async def log_ejecucion(data: dict) -> str:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO ejecuciones (input, contexto, modo, huecos_detectados, algoritmo_usado, resultado, coste_usd, tiempo_s, score_calidad, falacias_detectadas)
            VALUES ($1, $2, $3, $4::jsonb, $5::jsonb, $6::jsonb, $7, $8, $9, $10::jsonb)
            RETURNING id
        """, data['input'], data.get('contexto'), data['modo'],
            data.get('huecos_detectados'), data['algoritmo_usado'], data['resultado'],
            data.get('coste_usd'), data.get('tiempo_s'), data.get('score_calidad'),
            data.get('falacias_detectadas'))
        return str(row['id'])


async def fetch_operaciones_sintacticas() -> list[dict]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, nombre, descripcion, tipo FROM operaciones_sintacticas ORDER BY id")
        return [dict(r) for r in rows]


async def fetch_falacias() -> list[dict]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, nombre, descripcion, tipo FROM falacias_aritmeticas ORDER BY id")
        return [dict(r) for r in rows]


async def fetch_tipos_acople() -> list[dict]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, nombre, descripcion FROM tipos_acople ORDER BY id")
        return [dict(r) for r in rows]


async def log_diagnostico(data: dict) -> str:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO diagnosticos (
                caso_input, ejecucion_id,
                vector_pre, lentes_pre, estado_pre, flags_pre,
                repertorio_inferido, prescripcion, resultado, metricas
            )
            VALUES ($1, $2, $3::jsonb, $4::jsonb, $5, $6, $7::jsonb, $8::jsonb, $9, $10::jsonb)
            RETURNING id
        """,
            data.get('caso_input'),
            data.get('ejecucion_id'),
            data.get('vector_pre'),
            data.get('lentes_pre'),
            data.get('estado_pre'),
            data.get('flags_pre'),
            data.get('repertorio_inferido'),
            data.get('prescripcion'),
            data.get('resultado', 'pendiente'),
            data.get('metricas'),
        )
        return str(row['id'])
