"""Health checks para produccion.

Endpoints:
  GET /health       — Liveness (app responde)
  GET /health/ready — Readiness (DB + motor ok)
  GET /health/deep  — Deep check (gomas + presupuesto + tenant)
"""
from __future__ import annotations

import structlog
from fastapi import APIRouter

log = structlog.get_logger()
router = APIRouter(tags=["health"])


@router.get("/health")
async def liveness():
    """Liveness probe — la app responde."""
    return {"status": "ok"}


@router.get("/health/ready")
async def readiness():
    """Readiness probe — DB conectada."""
    try:
        from src.db.client import get_pool
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return {"status": "ready", "db": "ok"}
    except Exception as e:
        return {"status": "not_ready", "db": str(e)[:80]}


@router.get("/health/deep")
async def deep_check():
    """Deep check — estado completo del sistema."""
    checks = {}

    # DB
    try:
        from src.db.client import get_pool
        pool = await get_pool()
        async with pool.acquire() as conn:
            count = await conn.fetchval(
                "SELECT count(*) FROM om_pizarra WHERE tipo = 'dominio'")
        checks["db"] = "ok"
        checks["tenants"] = count
    except Exception as e:
        checks["db"] = str(e)[:80]

    # Presupuesto
    try:
        from motor.pensar import presupuesto_restante
        checks["presupuesto_restante"] = round(presupuesto_restante(), 2)
    except Exception as e:
        checks["presupuesto"] = str(e)[:80]

    # OpenRouter
    import os
    checks["openrouter_key"] = "configured" if os.getenv("OPENROUTER_API_KEY") else "missing"

    return {"status": "ok" if checks.get("db") == "ok" else "degraded", "checks": checks}
