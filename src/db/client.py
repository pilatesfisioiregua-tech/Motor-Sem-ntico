"""Pool de conexiones asyncpg para Postgres."""
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
