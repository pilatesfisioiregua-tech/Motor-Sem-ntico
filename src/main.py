"""Motor Semántico OMNI-MIND — API endpoint."""
import asyncio
import os
import uuid as _uuid
import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
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
    # Iniciar cron de tareas programadas
    try:
        from src.pilates.cron import cron_loop
        asyncio.create_task(cron_loop())
        log.info("startup_cron_started")
    except Exception as e:
        log.warning("startup_cron_failed", error=str(e))
    yield
    try:
        from src.db.client import close_pool
        await close_pool()
    except Exception as e:
        log.debug("silenced_exception", exc=str(e))
    log.info("shutdown_complete")


_docs_enabled = os.getenv("ENABLE_DOCS", "true").lower() == "true"
app = FastAPI(
    title="Motor Semántico OMNI-MIND",
    version="0.3.0",
    lifespan=lifespan,
    docs_url="/docs" if _docs_enabled else None,
    redoc_url="/redoc" if _docs_enabled else None,
    openapi_tags=[
        {"name": "clientes", "description": "Gestión de clientes"},
        {"name": "sesiones", "description": "Sesiones, asistencias, calendario"},
        {"name": "pagos", "description": "Pagos, cargos, facturación, Redsys"},
        {"name": "voz", "description": "Bloque Voz: estrategia, propuestas, ISP"},
        {"name": "organismo", "description": "Pizarras, bus, director, agentes"},
        {"name": "sistema", "description": "Health, diagnóstico, cron, backups"},
        {"name": "motor", "description": "Motor semántico, telemetría, caché"},
        {"name": "redsys", "description": "Webhooks Redsys (público)"},
        {"name": "portal", "description": "Portal cliente (público)"},
    ],
)

# ============================================================
# AUTH MIDDLEWARE — API Key para endpoints protegidos
# ============================================================
API_KEY = os.getenv("OMNI_API_KEY", "")
PUBLIC_PREFIXES = (
    "/portal/", "/onboarding/", "/health", "/info", "/tarjeta/",
    "/pilates/redsys/notificacion", "/pilates/redsys/retorno",
    "/pilates/redsys/paygold-retorno",
    "/pilates/wa/webhook", "/pilates/webhook/whatsapp",
    "/conocimiento-proyecto/",
    "/assets/", "/estudio", "/profundo",
    "/openapi.json", "/favicon.ico",
    "/pilates/publico/",
)

# Endpoints caros que SIEMPRE requieren API key (incluso same-origin)
PROTECTED_PREFIXES = (
    "/pilates/sistema/", "/pilates/af/",
    "/pilates/cron/", "/pilates/collectors",
)

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    path = request.url.path

    # Rutas publicas: nunca requieren auth
    if path == "/" or any(path.startswith(p) for p in PUBLIC_PREFIXES):
        return await call_next(request)

    if API_KEY:
        key = request.headers.get("X-API-Key", "")

        # Endpoints protegidos: siempre requieren API key
        if any(path.startswith(p) for p in PROTECTED_PREFIXES):
            if key != API_KEY:
                return JSONResponse(status_code=401, content={"detail": "API key requerida"})
            return await call_next(request)

        # Resto: permitir si viene del mismo origen (browser) o tiene API key
        origin = request.headers.get("origin", "")
        referer = request.headers.get("referer", "")
        is_same_origin = any(
            origin.startswith(o) or referer.startswith(o)
            for o in ALLOWED_ORIGINS if o
        )

        if not is_same_origin and key != API_KEY:
            return JSONResponse(status_code=401, content={"detail": "API key requerida"})

    return await call_next(request)


@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    """Añade correlation ID a cada request para trazabilidad."""
    correlation_id = request.headers.get("X-Correlation-ID", str(_uuid.uuid4())[:8])
    request.state.correlation_id = correlation_id

    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(correlation_id=correlation_id)

    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response


@app.middleware("http")
async def tenant_middleware(request: Request, call_next):
    """Resuelve el tenant desde header o pizarra dominio."""
    tenant_id = request.headers.get("X-Tenant-ID", "authentic_pilates")

    try:
        from src.pilates.pizarras import leer_dominio
        config = await leer_dominio(tenant_id)
        request.state.tenant_id = config["tenant_id"]
        request.state.tenant_config = config
    except Exception:
        request.state.tenant_id = "authentic_pilates"
        request.state.tenant_config = None

    return await call_next(request)


ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "https://motor-semantico-omni.fly.dev,http://localhost:5173").split(",")
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["X-API-Key", "X-Tenant-ID", "X-Correlation-ID", "Content-Type", "Authorization"],
)

# Mount Pilates router
try:
    from src.pilates.router import router as pilates_router
    app.include_router(pilates_router)
    log.info("pilates_router_mounted")
except Exception as e:
    log.warning("pilates_router_mount_failed", error=str(e))

# Mount Redsys router (pagos Caja Rural)
try:
    from src.pilates.redsys_router import router as redsys_router
    app.include_router(redsys_router)
    log.info("redsys_router_mounted")
except Exception as e:
    log.warning("redsys_router_mount_failed", error=str(e))

# Mount Portal router (público, sin auth)
try:
    from src.pilates.portal import router as portal_router
    app.include_router(portal_router)
    log.info("portal_router_mounted")
except Exception as e:
    log.warning("portal_router_mount_failed", error=str(e))

# Mount Conocimiento router (MCP endpoint)
try:
    from src.conocimiento import router as conocimiento_router
    app.include_router(conocimiento_router)
    log.info("conocimiento_router_mounted")
except Exception as e:
    log.warning("conocimiento_router_mount_failed", error=str(e))

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
    """Health check profundo — verifica componentes reales del sistema."""
    from datetime import datetime as _dt
    from zoneinfo import ZoneInfo
    checks = {}
    status = "healthy"

    # 1. DB connection
    try:
        from src.db.client import get_pool
        pool = await get_pool()
        async with pool.acquire() as conn:
            checks["db"] = "ok"
            count = await conn.fetchval(
                "SELECT count(*) FROM pg_tables WHERE tablename LIKE 'om_%'")
            checks["om_tables"] = count
            clientes = await conn.fetchval(
                "SELECT count(*) FROM om_cliente_tenant WHERE estado = 'activo'")
            checks["clientes_activos"] = clientes

            # 2. Cron staleness: última ejecución < 36h
            ultima = await conn.fetchval("""
                SELECT MAX(ultima_ejecucion) FROM om_cron_state
                WHERE tenant_id = 'authentic_pilates'
            """)
            if ultima:
                ahora = _dt.now(ZoneInfo("Europe/Madrid"))
                horas_desde_cron = (ahora - ultima).total_seconds() / 3600
                checks["cron_last_run_hours_ago"] = round(horas_desde_cron, 1)
                if horas_desde_cron > 36:
                    checks["cron"] = "stale"
                    status = "degraded"
                else:
                    checks["cron"] = "ok"
            else:
                checks["cron"] = "never_run"

            # 3. Bus no saturado (señales pendientes < 100)
            try:
                pendientes = await conn.fetchval("""
                    SELECT count(*) FROM om_senales_agentes
                    WHERE tenant_id = 'authentic_pilates' AND estado = 'pendiente'
                """)
                checks["bus_pendientes"] = pendientes
                if pendientes and pendientes > 100:
                    checks["bus"] = "saturated"
                    status = "degraded"
                else:
                    checks["bus"] = "ok"
            except Exception:
                checks["bus"] = "table_missing"

    except Exception as e:
        checks["db"] = f"error: {str(e)[:80]}"
        status = "unhealthy"

    code = 503 if status == "unhealthy" else 200
    return JSONResponse(
        status_code=code,
        content={"status": status, "version": "0.3.0", "checks": checks}
    )


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
    from src.pilates.rate_limit import semaforo_motor
    if semaforo_motor.locked():
        raise HTTPException(status_code=429, detail="Motor ocupado, reintenta en unos segundos")
    async with semaforo_motor:
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

    @app.get("/")
    async def root_page():
        return FileResponse(frontend_dist / "index.html")

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

    @app.get("/info")
    async def info_page():
        return FileResponse(frontend_dist / "index.html")

    @app.get("/tarjeta/{token}")
    async def tarjeta_cumpleanos(token: str):
        """Página HTML bonita con felicitación personalizada."""
        import json as _json
        from src.db.client import get_pool
        from starlette.responses import HTMLResponse
        pool = await get_pool()
        async with pool.acquire() as conn:
            evento = await conn.fetchrow("""
                SELECT metadata FROM om_cliente_eventos
                WHERE tipo='cumpleanos_felicitado'
                    AND metadata->>'token_tarjeta' = $1
                ORDER BY created_at DESC LIMIT 1
            """, token)
        if not evento:
            raise HTTPException(404, "Tarjeta no encontrada")
        meta = evento["metadata"] if isinstance(evento["metadata"], dict) else _json.loads(evento["metadata"])
        nombre = meta.get("nombre", "")
        html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Feliz cumpleaños {nombre}</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{
    min-height:100vh; display:flex; align-items:center; justify-content:center;
    font-family:'Georgia',serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 20px;
  }}
  .card {{
    background: white; border-radius: 24px; padding: 48px 36px;
    max-width: 400px; width: 100%; text-align: center;
    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
  }}
  .emoji {{ font-size: 64px; margin-bottom: 16px; }}
  h1 {{ font-size: 28px; color: #1a1a2e; margin-bottom: 8px; }}
  .nombre {{ font-size: 36px; color: #6366f1; font-style: italic; margin-bottom: 24px; }}
  p {{ font-size: 16px; color: #555; line-height: 1.6; margin-bottom: 16px; }}
  .firma {{ font-size: 14px; color: #999; margin-top: 32px; }}
  .firma strong {{ color: #6366f1; }}
</style></head>
<body>
<div class="card">
  <div class="emoji">🎂</div>
  <h1>Feliz cumpleaños,</h1>
  <div class="nombre">{nombre}!</div>
  <p>Hoy es un día especial y queríamos que supieras
  lo mucho que nos alegra tenerte en el estudio.</p>
  <p>Gracias por confiar en nosotros para cuidarte.
  A por un año más lleno de fuerza y equilibrio!</p>
  <div class="firma">Con cariño,<br><strong>Authentic Pilates</strong><br>Albelda de Iregua</div>
</div>
</body></html>"""
        return HTMLResponse(html)

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
