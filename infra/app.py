"""App factory — crea la aplicacion FastAPI con todos los routers.

Entry point de produccion:
  uvicorn infra.app:create_app --factory --host 0.0.0.0 --port 8080
"""
from __future__ import annotations

import structlog
from fastapi import FastAPI

log = structlog.get_logger()


def create_app() -> FastAPI:
    """Crea la aplicacion FastAPI completa."""
    app = FastAPI(
        title="OMNI-MIND Motor Semantico",
        version="4.0.0",
        description="Exocortex multi-tenant — 5 niveles Matrioska",
    )

    # Middleware tenant
    from tenant.tenant_context import tenant_middleware
    tenant_middleware(app)

    # Health checks
    from infra.health import router as health_router
    app.include_router(health_router)

    # Cockpit frontend
    from frontend.api.router_cockpit import router as cockpit_router
    app.include_router(cockpit_router)

    # Admin
    from frontend.api.router_admin import router as admin_router
    app.include_router(admin_router)

    # Incluir routers existentes de src/ si existen
    try:
        from src.routers.router_clientes import router as clientes_router
        app.include_router(clientes_router)
    except ImportError:
        pass

    try:
        from src.routers.router_voz import router as voz_router
        app.include_router(voz_router)
    except ImportError:
        pass

    @app.on_event("startup")
    async def startup():
        log.info("app.startup", version="4.0.0")

    @app.on_event("shutdown")
    async def shutdown():
        log.info("app.shutdown")

    return app
