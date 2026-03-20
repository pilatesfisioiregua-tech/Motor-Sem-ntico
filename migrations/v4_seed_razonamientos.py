"""Seed tipos_razonamiento desde razonamientos.json."""
import asyncio
import json
from pathlib import Path
from src.db.client import get_pool

DATA = Path(__file__).parent.parent / "src" / "meta_red" / "razonamientos.json"

async def seed():
    with open(DATA) as f:
        rs = json.load(f)

    pool = await get_pool()
    async with pool.acquire() as conn:
        count = await conn.fetchval("SELECT count(*) FROM tipos_razonamiento")
        if count > 0:
            print(f"tipos_razonamiento ya tiene {count} filas — skip")
            return

        for r in rs.values():
            await conn.execute("""
                INSERT INTO tipos_razonamiento (id, nombre, descripcion, lente_preferente,
                    funciones_naturales, ints_compatibles, genera, limite,
                    pregunta_activadora)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (id) DO NOTHING
            """,
                r['id'], r['nombre'], r.get('descripcion'),
                r['lente_preferente'], r.get('funciones_naturales'),
                r.get('ints_compatibles'), r.get('genera'), r.get('limite'),
                r.get('pregunta_activadora'),
            )
        final = await conn.fetchval("SELECT count(*) FROM tipos_razonamiento")
        print(f"PASS: {final} razonamientos insertados")

if __name__ == "__main__":
    asyncio.run(seed())
