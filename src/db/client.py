"""Pool de conexiones asyncpg para Postgres."""
from __future__ import annotations

import asyncpg
import structlog
from src.config.settings import DATABASE_URL

log = structlog.get_logger()

_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=2,
            max_size=10,
            command_timeout=60,
        )
        log.info("db_pool_created")
    return _pool


async def close_pool():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        log.info("db_pool_closed")


async def execute_schema():
    """Ejecuta schema.sql para crear tablas."""
    pool = await get_pool()
    import importlib.resources as pkg_resources
    from pathlib import Path
    schema_path = Path(__file__).parent / "schema.sql"
    schema = schema_path.read_text()
    async with pool.acquire() as conn:
        await conn.execute(schema)
    log.info("schema_executed")


async def execute_seed():
    """Ejecuta seed.sql para poblar datos."""
    pool = await get_pool()
    from pathlib import Path
    seed_path = Path(__file__).parent / "seed.sql"
    seed = seed_path.read_text()
    async with pool.acquire() as conn:
        await conn.execute(seed)
    log.info("seed_executed")


async def execute_migrations():
    """Ejecuta migrations SQL idempotentes (V4+)."""
    from pathlib import Path
    pool = await get_pool()
    migrations_dir = Path(__file__).parent.parent.parent / "migrations"
    if not migrations_dir.exists():
        return

    sql_files = sorted(migrations_dir.glob("*.sql"))
    async with pool.acquire() as conn:
        for sql_file in sql_files:
            try:
                sql = sql_file.read_text()
                await conn.execute(sql)
                log.info("migration_ok", file=sql_file.name)
            except Exception as e:
                log.warning("migration_skip", file=sql_file.name, error=str(e))


async def execute_seeds():
    """Ejecuta seeds Python idempotentes (V4+)."""
    import importlib.util
    import sys
    from pathlib import Path

    migrations_dir = Path(__file__).parent.parent.parent / "migrations"
    if not migrations_dir.exists():
        return

    # Añadir raíz del proyecto al path para imports
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
            log.warning("seed_skip", file=py_file.name, error=str(e))


async def fetch_all_inteligencias() -> list[dict]:
    """Carga todas las inteligencias de la DB."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM inteligencias ORDER BY id")
        return [dict(r) for r in rows]


async def fetch_aristas(tipo: str | None = None) -> list[dict]:
    """Carga aristas del grafo. Filtra por tipo si se indica."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        if tipo:
            rows = await conn.fetch(
                "SELECT * FROM aristas_grafo WHERE tipo = $1 ORDER BY peso DESC",
                tipo
            )
        else:
            rows = await conn.fetch("SELECT * FROM aristas_grafo ORDER BY peso DESC")
        return [dict(r) for r in rows]


async def log_ejecucion(data: dict) -> str:
    """Guarda una ejecución y devuelve su UUID."""
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
    """Carga las 8 operaciones del Marco Lingüístico."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM operaciones_sintacticas ORDER BY id")
        return [dict(r) for r in rows]


async def fetch_falacias() -> list[dict]:
    """Carga las falacias aritméticas."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM falacias_aritmeticas ORDER BY id")
        return [dict(r) for r in rows]


async def fetch_tipos_acople() -> list[dict]:
    """Carga los 6 tipos de acople."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM tipos_acople ORDER BY id")
        return [dict(r) for r in rows]


async def log_diagnostico(data: dict) -> str:
    """Guarda un diagnóstico ACD y devuelve su UUID.

    Args:
        data: dict con campos de la tabla diagnosticos.
              Campos obligatorios: caso_input, vector_pre, lentes_pre, estado_pre.
              Campos opcionales: ejecucion_id, flags_pre, repertorio_inferido,
                                 prescripcion, resultado, metricas.

    Returns:
        UUID del diagnóstico creado.
    """
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
