"""Seed estados_diagnosticos desde estados.json."""
import asyncio
import json
from pathlib import Path
from src.db.client import get_pool

DATA = Path(__file__).parent.parent / "src" / "tcf" / "estados.json"

async def seed():
    with open(DATA) as f:
        estados = json.load(f)

    pool = await get_pool()
    async with pool.acquire() as conn:
        count = await conn.fetchval("SELECT count(*) FROM estados_diagnosticos")
        if count > 0:
            print(f"estados_diagnosticos ya tiene {count} filas — skip")
            return

        for grupo in ('equilibrados', 'desequilibrados'):
            for e in estados[grupo].values():
                await conn.execute("""
                    INSERT INTO estados_diagnosticos (id, nombre, tipo, descripcion,
                        perfil_lentes, condiciones, flags, ints_tipicas_activas,
                        ints_tipicas_ausentes, prescripcion_ps, prescripcion_rs,
                        objetivo_prescripcion, transiciones)
                    VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7, $8, $9, $10, $11, $12, $13::jsonb)
                    ON CONFLICT (id) DO NOTHING
                """,
                    e['id'], e['nombre'], e['tipo'], e.get('descripcion'),
                    e.get('perfil_lentes'),
                    json.dumps(e.get('condicion', e.get('condiciones', {}))),
                    e.get('flags'),
                    e.get('ints_tipicas_activas'), e.get('ints_tipicas_ausentes'),
                    e.get('prescripcion_ps'), e.get('prescripcion_rs'),
                    e.get('objetivo_prescripcion'),
                    json.dumps(e.get('transiciones', [])) if e.get('transiciones') else None,
                )
        final = await conn.fetchval("SELECT count(*) FROM estados_diagnosticos")
        print(f"PASS: {final} estados insertados")

if __name__ == "__main__":
    asyncio.run(seed())
