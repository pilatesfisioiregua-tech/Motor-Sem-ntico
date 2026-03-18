"""Motor Semántico OMNI-MIND — API endpoint."""
import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
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
        from src.db.client import get_pool, execute_schema
        await get_pool()
        await execute_schema()
        log.info("startup_db_ready")
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


app = FastAPI(title="Motor Semántico OMNI-MIND", version="0.1.0", lifespan=lifespan)

# Mount Code OS sub-app (agent endpoints at /code-os/*)
try:
    from motor_v1_validation.agent.api import app as code_os_app
    app.mount("", code_os_app)
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
    return {"status": "ok", "version": "0.1.0"}


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
