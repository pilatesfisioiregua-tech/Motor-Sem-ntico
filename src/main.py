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
