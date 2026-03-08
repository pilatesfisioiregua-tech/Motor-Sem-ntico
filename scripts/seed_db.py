"""Ejecuta schema + seed en la DB."""
import asyncio
import sys
sys.path.insert(0, '.')
from src.db.client import execute_schema, execute_seed, close_pool

async def main():
    print("Ejecutando schema...")
    await execute_schema()
    print("Ejecutando seed...")
    await execute_seed()
    print("Done.")
    await close_pool()

if __name__ == "__main__":
    asyncio.run(main())
