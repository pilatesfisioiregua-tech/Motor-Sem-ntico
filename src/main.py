"""Motor Semántico OMNI-MIND — API endpoint."""
import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.dev.ConsoleRenderer(),
    ]
)

log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: pool DB + cargar inteligencias en memoria."""
    log.info("startup_begin")
    try:
        from src.db.client import get_pool, execute_schema, execute_migrations, execute_seeds
        await get_pool()
        await execute_schema()
        log.info("startup_db_ready")
        await execute_migrations()
        log.info("startup_migrations_done")
        await execute_seeds()
        log.info("startup_seeds_done")
    except Exception as e:
        log.warning("startup_db_unavailable", error=str(e))
    from src.meta_red import load_inteligencias
    load_inteligencias()
    log.info("startup_complete")
    yield
    try:
        from src.db.client import close_pool
        await close_pool()
    except Exception:
        pass
    log.info("shutdown_complete")


app = FastAPI(title="Motor Semántico OMNI-MIND", version="0.2.0", lifespan=lifespan)

from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Pilates router
try:
    from src.pilates.router import router as pilates_router
    app.include_router(pilates_router)
    log.info("pilates_router_mounted")
except Exception as e:
    log.warning("pilates_router_mount_failed", error=str(e))

# Mount Portal router (público, sin auth)
try:
    from src.pilates.portal import router as portal_router
    app.include_router(portal_router)
    log.info("portal_router_mounted")
except Exception as e:
    log.warning("portal_router_mount_failed", error=str(e))

# Mount Code OS sub-app (agent endpoints at /code-os/*)
try:
    from motor_v1_validation.agent.api import app as code_os_app
    app.mount("/code-os", code_os_app)
    log.info("code_os_mounted")
except Exception as e:
    log.warning("code_os_mount_failed", error=str(e))


class MotorConfig(BaseModel):
    presupuesto_max: float = 1.50
    tiempo_max_s: int = 120
    profundidad: str = Field(default="normal", pattern="^(normal|profunda|maxima)$")
    modo: str = Field(default="analisis", pattern="^(analisis|generacion|conversacion|confrontacion)$")
    inteligencias_forzadas: list[str] = []
    inteligencias_excluidas: list[str] = []


class MotorRequest(BaseModel):
    input: str
    contexto: Optional[str] = None
    config: MotorConfig = MotorConfig()


class MotorResponse(BaseModel):
    algoritmo_usado: dict
    resultado: dict
    meta: dict


@app.get("/health")
async def health():
    """Health check ampliado con estado de componentes."""
    status = {"status": "ok", "version": "0.2.0"}
    try:
        from src.db.client import get_pool
        pool = await get_pool()
        async with pool.acquire() as conn:
            status["db"] = "ok"
            count = await conn.fetchval(
                "SELECT count(*) FROM pg_tables WHERE tablename LIKE 'om_%'")
            status["om_tables"] = count
            clientes = await conn.fetchval(
                "SELECT count(*) FROM om_cliente_tenant WHERE estado = 'activo'")
            status["clientes_activos"] = clientes
    except Exception as e:
        status["db"] = f"error: {str(e)[:50]}"
    endpoints = [r.path for r in app.routes if hasattr(r, 'methods')]
    status["endpoints"] = len(endpoints)
    return status


@app.get("/endpoints")
async def listar_endpoints():
    """Lista todos los endpoints disponibles."""
    endpoints = []
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            for method in route.methods:
                if method not in ('HEAD', 'OPTIONS'):
                    endpoints.append({
                        "method": method,
                        "path": route.path,
                        "name": route.name,
                    })
    return sorted(endpoints, key=lambda e: (e["path"], e["method"]))


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    log.error("unhandled_error", path=request.url.path, error=str(exc))
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor", "path": request.url.path},
    )


@app.post("/reactor/ejecutar")
async def ejecutar_reactor():
    """Ejecuta el Reactor v1 — generador de datos sintéticos."""
    log.info("reactor_ejecutar")
    try:
        from src.reactor.runner import run
        result = await run()
        return {"status": "ok", **result}
    except Exception as e:
        log.error("reactor_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/motor/ejecutar", response_model=MotorResponse)
async def ejecutar(request: MotorRequest):
    """Ejecuta el pipeline completo del motor semántico."""
    log.info("motor_ejecutar", input_preview=request.input[:100], modo=request.config.modo)
    try:
        from src.pipeline.orchestrator import run_pipeline
        result = await run_pipeline(request)
        return result
    except Exception as e:
        log.error("motor_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/models/entrenar")
async def entrenar_modelos():
    """Entrena los 4 modelos ligeros C1-C4 desde datos Reactor v1."""
    log.info("models_entrenar")
    try:
        from src.models.trainer import train_all
        result = train_all()
        return {"status": "ok", **result}
    except Exception as e:
        log.error("models_entrenar_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/models/explorar-c1")
async def explorar_c1():
    """Prueba múltiples configuraciones de C1 y reporta resultados."""
    log.info("models_explorar_c1")
    try:
        from src.models.trainer import _load_json
        from src.models.router_embeddings import explore
        b1 = _load_json("b1_casos.json")
        b2 = _load_json("b2_peticiones.json")
        results = explore(b1, b2)
        return {"status": "ok", "configs_probadas": len(results), "resultados": results}
    except Exception as e:
        log.error("explorar_c1_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/models/evaluar")
async def evaluar_modelos():
    """Evalúa métricas de los 4 modelos entrenados."""
    log.info("models_evaluar")
    try:
        from src.models.evaluate import evaluate_all
        result = evaluate_all()
        return {"status": "ok", **result}
    except Exception as e:
        log.error("models_evaluar_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/gestor/analizar")
async def analizar_gestor():
    """Ejecuta el loop lento del Gestor — análisis de patrones."""
    log.info("gestor_analizar")
    try:
        from src.gestor.analizador import analizar
        informe = await analizar()
        return {"status": "ok", **informe.to_dict()}
    except Exception as e:
        log.error("gestor_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Serve frontend static files (Modo Estudio)
from pathlib import Path
frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    from fastapi.staticfiles import StaticFiles
    from starlette.responses import FileResponse

    @app.get("/estudio")
    async def estudio():
        return FileResponse(frontend_dist / "index.html")

    @app.get("/onboarding/{token}")
    async def onboarding_page(token: str):
        """Sirve el HTML del formulario de onboarding."""
        return FileResponse(frontend_dist / "index.html")

    @app.get("/portal/{token}")
    async def portal_page(token: str):
        return FileResponse(frontend_dist / "index.html")

    @app.get("/profundo")
    async def profundo_page():
        return FileResponse(frontend_dist / "index.html")

    app.mount("/assets", StaticFiles(directory=frontend_dist / "assets"), name="assets")
    log.info("frontend_mounted", path=str(frontend_dist))


@app.post("/reactor/telemetria")
async def reactor_telemetria():
    """Reactor v4 — Detecta patrones en datos reales."""
    log.info("reactor_telemetria")
    try:
        from src.reactor.v4_telemetria import detectar_patrones
        informe = await detectar_patrones()
        return {"status": "ok", **informe.to_dict()}
    except Exception as e:
        log.error("reactor_telemetria_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/reactor/v5")
async def reactor_v5():
    """Reactor v5 — Genera datos empíricos ACD con casos semilla."""
    log.info("reactor_v5_ejecutar")
    try:
        from src.reactor.v5_empirico import run
        result = await run()
        return {"status": "ok", **result}
    except Exception as e:
        log.error("reactor_v5_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
