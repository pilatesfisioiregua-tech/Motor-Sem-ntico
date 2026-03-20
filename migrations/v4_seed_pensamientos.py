"""Seed tipos_pensamiento desde pensamientos.json."""
import asyncio
import json
from pathlib import Path
from src.db.client import get_pool

DATA = Path(__file__).parent.parent / "src" / "meta_red" / "pensamientos.json"

async def seed():
    with open(DATA) as f:
        ps = json.load(f)

    pool = await get_pool()
    async with pool.acquire() as conn:
        count = await conn.fetchval("SELECT count(*) FROM tipos_pensamiento")
        if count > 0:
            print(f"tipos_pensamiento ya tiene {count} filas — skip")
            return

        for p in ps.values():
            await conn.execute("""
                INSERT INTO tipos_pensamiento (id, nombre, descripcion, lente_preferente,
                    funciones_naturales, razonamientos_asociados, nivel_logico,
                    ints_compatibles, ints_incompatibles, pregunta_activadora, cuando_usar)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                ON CONFLICT (id) DO NOTHING
            """,
                p['id'], p['nombre'], p.get('descripcion'),
                p['lente_preferente'], p.get('funciones_naturales'),
                p.get('razonamientos_asociados'), p.get('nivel_logico'),
                p.get('ints_compatibles'), p.get('ints_incompatibles'),
                p.get('pregunta_activadora'), p.get('cuando_usar'),
            )
        final = await conn.fetchval("SELECT count(*) FROM tipos_pensamiento")
        print(f"PASS: {final} pensamientos insertados")

if __name__ == "__main__":
    asyncio.run(seed())
