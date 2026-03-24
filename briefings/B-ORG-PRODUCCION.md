# B-ORG-PRODUCCION — Fase 0 Blindaje + Fase 1 Valor Inmediato

**Fecha:** 24 marzo 2026
**Estimación:** ~8h
**Prerequisito:** Nada — es la primera fase del Roadmap v4
**WIP:** 1 (secuencial, cada paso depende del anterior)

---

## OBJETIVO

Llevar el sistema de "prototipo funcional" a "producción segura que habla". Sin esto NO hay producto.

**Fase 0 — Blindaje:** Auth, cron state en DB, cobros Redsys en cron, rate limiting, RGPD mínimo, health profundo.
**Fase 1 — Valor inmediato:** Briefing WA, confirmaciones, cumpleaños, timezone correcto.

---

## ARCHIVOS A LEER ANTES DE EMPEZAR

```
src/main.py
src/pilates/cron.py
src/pilates/redsys_pagos.py
src/pilates/whatsapp.py
src/pilates/automatismos.py
src/pilates/router.py
src/pilates/portal.py
src/pilates/redsys_router.py
src/pilates/briefing.py
```

---

## PASO 0: MIGRACIÓN SQL (027_produccion.sql)

Crear archivo: `migrations/027_produccion.sql`

```sql
-- 027_produccion.sql — Blindaje + RGPD
-- Fase 0 del Roadmap v4

-- 1. Cron state en DB (reemplaza variables en memoria)
CREATE TABLE IF NOT EXISTS om_cron_state (
    id SERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'authentic_pilates',
    tarea TEXT NOT NULL,
    ultima_ejecucion TIMESTAMPTZ NOT NULL DEFAULT now(),
    resultado TEXT,
    UNIQUE(tenant_id, tarea)
);

-- 2. RGPD: campo consentimiento_revocado en datos clínicos
ALTER TABLE om_datos_clinicos
    ADD COLUMN IF NOT EXISTS consentimiento_revocado BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS fecha_revocacion TIMESTAMPTZ;

-- 3. Solicitudes de baja RGPD
CREATE TABLE IF NOT EXISTS om_solicitudes_baja (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'authentic_pilates',
    cliente_id UUID NOT NULL REFERENCES om_clientes(id),
    motivo TEXT,
    estado TEXT NOT NULL DEFAULT 'pendiente', -- pendiente, procesada, rechazada
    created_at TIMESTAMPTZ DEFAULT now(),
    procesada_at TIMESTAMPTZ
);

-- 4. Índice para cron state lookup
CREATE INDEX IF NOT EXISTS idx_cron_state_tarea ON om_cron_state(tenant_id, tarea);
```

**Test:** Migración ejecuta sin error. `SELECT count(*) FROM om_cron_state` → 0.

---

## PASO 1: AUTH MIDDLEWARE (src/main.py)

### 1.1 Añadir middleware de autenticación

Después de la línea `app = FastAPI(...)` y ANTES de `app.add_middleware(CORSMiddleware, ...)`, insertar:

```python
import os

# ============================================================
# AUTH MIDDLEWARE — API Key para endpoints protegidos
# ============================================================
API_KEY = os.getenv("OMNI_API_KEY", "")
PUBLIC_PREFIXES = (
    "/portal/", "/onboarding/", "/health", "/info", "/tarjeta/",
    "/pilates/redsys/notificacion", "/pilates/redsys/retorno",
    "/pilates/redsys/paygold-retorno",
    "/pilates/wa/webhook",
    "/conocimiento-proyecto/",
    "/assets/", "/estudio", "/profundo",
    "/openapi.json", "/favicon.ico",
)

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    path = request.url.path

    # Rutas públicas: no requieren auth
    if any(path.startswith(p) for p in PUBLIC_PREFIXES):
        return await call_next(request)

    # Verificar API key
    if API_KEY:
        key = request.headers.get("X-API-Key", "")
        if key != API_KEY:
            return JSONResponse(status_code=401, content={"detail": "API key requerida"})

    return await call_next(request)
```

### 1.2 Restringir CORS

Cambiar:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Por:
```python
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "https://motor-semantico-omni.fly.dev,http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["X-API-Key", "Content-Type", "Authorization"],
)
```

### 1.3 Proteger /docs y /redoc

Cambiar la línea de creación de la app:

De:
```python
app = FastAPI(title="Motor Semántico OMNI-MIND", version="0.2.0", lifespan=lifespan)
```

A:
```python
_docs_enabled = os.getenv("ENABLE_DOCS", "false").lower() == "true"
app = FastAPI(
    title="Motor Semántico OMNI-MIND",
    version="0.3.0",
    lifespan=lifespan,
    docs_url="/docs" if _docs_enabled else None,
    redoc_url="/redoc" if _docs_enabled else None,
)
```

### 1.4 WA verify token desde env var

En `src/pilates/whatsapp.py`, la línea ya está correcta:
```python
WA_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "omni_mind_verify_2026")
```
Pero hay que asegurar que en fly.io se setee como secret:
```bash
fly secrets set WHATSAPP_VERIFY_TOKEN="$(openssl rand -hex 16)" --app chief-os-omni
```

**Test 1.1:** `curl https://motor-semantico-omni.fly.dev/pilates/clientes -H "X-API-Key: wrong"` → HTTP 401
**Test 1.2:** `curl https://motor-semantico-omni.fly.dev/pilates/clientes -H "X-API-Key: $OMNI_API_KEY"` → HTTP 200
**Test 1.3:** `curl https://motor-semantico-omni.fly.dev/health` → HTTP 200 (sin API key)
**Test 1.4:** `curl https://motor-semantico-omni.fly.dev/portal/test` → HTTP 200 (sin API key)
**Test 1.5:** `curl https://motor-semantico-omni.fly.dev/docs` → HTTP 404 (docs deshabilitado)

---

## PASO 2: CRON STATE EN DB (src/pilates/cron.py)

### 2.1 Reemplazar timezone

De:
```python
from datetime import datetime, time, timedelta

# Zona horaria: Madrid = UTC+1 (invierno) / UTC+2 (verano)
# Simplificación: usamos UTC+1 fijo. Suficiente para un cron de SMB.
MADRID_OFFSET = timedelta(hours=1)


def _hora_madrid() -> datetime:
    """Devuelve datetime actual en hora de Madrid (aprox)."""
    from datetime import timezone
    utc_now = datetime.now(timezone.utc)
    return utc_now + MADRID_OFFSET
```

A:
```python
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

MADRID_TZ = ZoneInfo("Europe/Madrid")


def _hora_madrid() -> datetime:
    """Devuelve datetime actual en hora de Madrid (con DST correcto)."""
    return datetime.now(MADRID_TZ)
```

### 2.2 Añadir funciones de cron state

Después de `_hora_madrid()`, añadir:

```python
async def _ya_ejecutado(tarea: str, periodo: str) -> bool:
    """Consulta om_cron_state para saber si la tarea ya se ejecutó en este periodo.

    periodo: 'dia' (hoy), 'semana' (esta semana ISO), 'mes' (este mes)
    """
    from src.db.client import get_pool
    pool = await get_pool()
    ahora = _hora_madrid()

    if periodo == "dia":
        inicio = ahora.replace(hour=0, minute=0, second=0, microsecond=0)
    elif periodo == "semana":
        inicio = ahora - timedelta(days=ahora.weekday())
        inicio = inicio.replace(hour=0, minute=0, second=0, microsecond=0)
    elif periodo == "mes":
        inicio = ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        return False

    async with pool.acquire() as conn:
        row = await conn.fetchval("""
            SELECT 1 FROM om_cron_state
            WHERE tenant_id = 'authentic_pilates' AND tarea = $1
                AND ultima_ejecucion >= $2
        """, tarea, inicio)
    return row is not None


async def _marcar_ejecutado(tarea: str, resultado: str = "ok"):
    """Marca tarea como ejecutada en om_cron_state."""
    from src.db.client import get_pool
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO om_cron_state (tenant_id, tarea, ultima_ejecucion, resultado)
            VALUES ('authentic_pilates', $1, now(), $2)
            ON CONFLICT (tenant_id, tarea)
            DO UPDATE SET ultima_ejecucion = now(), resultado = $2
        """, tarea, resultado)
```

### 2.3 Reemplazar cron_loop completo

El `cron_loop()` actual usa `ultima_diaria = None` y `ultima_semanal = None` en memoria. Reemplazar todo `cron_loop()` por:

```python
async def cron_loop():
    """Loop principal del cron. Se ejecuta como background task.

    Revisa cada 15 minutos si hay tareas pendientes.
    Usa om_cron_state en DB para no repetir tras restart/deploy.
    """
    log.info("cron_iniciado")

    while True:
        try:
            ahora = _hora_madrid()
            hoy = ahora.date()
            hora = ahora.time()

            # Tarea diaria: después de las 06:00, una vez al día
            if hora >= time(6, 0) and not await _ya_ejecutado("diaria", "dia"):
                log.info("cron_ejecutando_diaria", hora=str(hora))
                await _tarea_diaria()
                await _marcar_ejecutado("diaria")

            # Tarea semanal: lunes después de las 07:00, una vez por semana
            if ahora.weekday() == 0 and hora >= time(7, 0):
                if not await _ya_ejecutado("semanal", "semana"):
                    log.info("cron_ejecutando_semanal", semana=hoy.isocalendar()[1])
                    await _tarea_semanal()
                    await _marcar_ejecutado("semanal")

            # Tarea mensual: día 1 después de las 08:00
            if hoy.day == 1 and hora >= time(8, 0):
                if not await _ya_ejecutado("mensual", "mes"):
                    log.info("cron_ejecutando_mensual", mes=f"{hoy.year}-{hoy.month:02d}")
                    await _tarea_mensual()
                    await _marcar_ejecutado("mensual")

        except Exception as e:
            log.error("cron_loop_error", error=str(e))

        # Vigía + Mecánico: cada iteración (cada 15 min) — sin state, siempre corre
        try:
            from src.pilates.vigia import vigilar
            vigia_result = await vigilar()
            if vigia_result.get("alertas_emitidas", 0) > 0:
                from src.pilates.mecanico import procesar_alertas
                mec_result = await procesar_alertas()
                log.info("cron_mecanico_ok",
                    fixes=mec_result.get("fixes_fontaneria", 0),
                    arq=mec_result.get("arquitecturales", 0))
        except Exception as e:
            log.error("cron_vigia_error", error=str(e))

        # Dormir 15 minutos
        await asyncio.sleep(900)
```

**Test 2.1:** Deploy → la tarea diaria se ejecuta. Restart inmediato → la tarea NO se re-ejecuta.
**Test 2.2:** `SELECT * FROM om_cron_state` → filas con `diaria`, `semanal`, etc.

---

## PASO 3: COBROS REDSYS EN CRON (src/pilates/cron.py)

En `_tarea_diaria()`, DESPUÉS del bloque de propiocepción, añadir:

```python
    # Cobros recurrentes Redsys (día del mes correcto)
    try:
        from src.pilates.redsys_pagos import cron_cobros_recurrentes, is_configured
        if is_configured():
            cobros = await cron_cobros_recurrentes()
            log.info("cron_diaria_cobros_ok", cobrados=cobros.get("cobrados", 0))
        else:
            log.debug("cron_diaria_cobros_skip", razon="redsys_no_configurado")
    except Exception as e:
        log.error("cron_diaria_cobros_error", error=str(e))

    # Confirmaciones pre-sesión (24h antes)
    try:
        from src.pilates.whatsapp import enviar_confirmaciones_manana, is_configured as wa_configured
        if wa_configured():
            conf = await enviar_confirmaciones_manana()
            log.info("cron_diaria_confirmaciones_ok", enviados=conf.get("enviados", 0))
    except Exception as e:
        log.error("cron_diaria_confirmaciones_error", error=str(e))

    # Cumpleaños automáticos
    try:
        from src.pilates.automatismos import felicitar_cumpleanos
        cumple = await felicitar_cumpleanos()
        log.info("cron_diaria_cumpleanos_ok", enviados=cumple.get("felicitaciones_enviadas", 0))
    except Exception as e:
        log.error("cron_diaria_cumpleanos_error", error=str(e))
```

**Test 3.1:** `grep "cron_cobros_recurrentes" src/pilates/cron.py` → match
**Test 3.2:** `grep "enviar_confirmaciones_manana" src/pilates/cron.py` → match
**Test 3.3:** `grep "felicitar_cumpleanos" src/pilates/cron.py` → match

---

## PASO 4: FIX STRIPE→REDSYS EN AUTOMATISMOS (src/pilates/automatismos.py)

En la función `ejecutar_cron(tipo='diario')`, hay un import muerto:

De:
```python
    elif tipo == "diario":
        resultados["cumpleanos"] = await felicitar_cumpleanos()
        from src.pilates.stripe_pagos import cron_cobros_recurrentes
        resultados["cobros"] = await cron_cobros_recurrentes()
```

A:
```python
    elif tipo == "diario":
        resultados["cumpleanos"] = await felicitar_cumpleanos()
        from src.pilates.redsys_pagos import cron_cobros_recurrentes
        resultados["cobros"] = await cron_cobros_recurrentes()
```

**Test 4.1:** `grep "stripe_pagos" src/pilates/automatismos.py` → NO match (0 resultados)
**Test 4.2:** `grep "redsys_pagos" src/pilates/automatismos.py` → match

---

## PASO 5: RATE LIMITING ENDPOINTS COSTOSOS (src/main.py)

Después del auth middleware y antes de los routers, añadir:

```python
# ============================================================
# RATE LIMITING — Semáforos para endpoints costosos
# ============================================================
import asyncio as _asyncio
_semaforo_opus = _asyncio.Semaphore(1)      # Director Opus: $0.40/llamada
_semaforo_metacog = _asyncio.Semaphore(1)   # Metacognitivo: $0.50/llamada
_semaforo_motor = _asyncio.Semaphore(2)     # Motor pipeline: concurrencia limitada
```

Luego, en los endpoints costosos, envolver con semáforo. Buscar el endpoint `/motor/ejecutar` y cambiarlo:

De:
```python
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
```

A:
```python
@app.post("/motor/ejecutar", response_model=MotorResponse)
async def ejecutar(request: MotorRequest):
    """Ejecuta el pipeline completo del motor semántico."""
    if _semaforo_motor.locked():
        raise HTTPException(status_code=429, detail="Motor ocupado, reintenta en unos segundos")
    async with _semaforo_motor:
        log.info("motor_ejecutar", input_preview=request.input[:100], modo=request.config.modo)
        try:
            from src.pipeline.orchestrator import run_pipeline
            result = await run_pipeline(request)
            return result
        except Exception as e:
            log.error("motor_error", error=str(e))
            raise HTTPException(status_code=500, detail=str(e))
```

**Nota:** Los endpoints de ACD (`/acd/director-opus`, `/acd/metacognitivo`) están en `router.py`. Aplicar el mismo patrón allí, pasando los semáforos como dependencias o importándolos desde main. La solución más sencilla: crear `src/pilates/rate_limit.py`:

```python
"""Rate limiting — semáforos globales para endpoints costosos."""
import asyncio

semaforo_opus = asyncio.Semaphore(1)       # $0.40/llamada
semaforo_metacog = asyncio.Semaphore(1)    # $0.50/llamada
semaforo_motor = asyncio.Semaphore(2)      # pipeline costoso
```

Y en `router.py`, para los endpoints de director-opus y metacognitivo, envolver:

```python
from src.pilates.rate_limit import semaforo_opus, semaforo_metacog

# En el endpoint director-opus:
if semaforo_opus.locked():
    raise HTTPException(status_code=429, detail="Director Opus ocupado")
async with semaforo_opus:
    # ... código existente ...

# En el endpoint metacognitivo:
if semaforo_metacog.locked():
    raise HTTPException(status_code=429, detail="Metacognitivo ocupado")
async with semaforo_metacog:
    # ... código existente ...
```

**Test 5.1:** Dos requests simultáneas a `/motor/ejecutar` → la segunda devuelve 429 si la primera no ha terminado.

---

## PASO 6: RGPD MÍNIMO (src/pilates/portal.py)

Añadir 2 endpoints al router de portal (que es público, sin auth):

```python
@router.get("/portal/{token}/mis-datos")
async def mis_datos(token: str):
    """RGPD: El cliente puede ver todos sus datos."""
    from src.db.client import get_pool
    pool = await get_pool()

    async with pool.acquire() as conn:
        # Verificar token
        cliente = await conn.fetchrow("""
            SELECT c.* FROM om_clientes c
            JOIN om_portal_tokens pt ON pt.cliente_id = c.id
            WHERE pt.token = $1 AND pt.activo = true
        """, token)
        if not cliente:
            raise HTTPException(status_code=404, detail="Token no válido")

        cliente_id = cliente["id"]

        # Datos del cliente
        datos = dict(cliente)
        # Convertir UUIDs y dates a string
        for k, v in datos.items():
            if hasattr(v, 'isoformat'):
                datos[k] = v.isoformat()
            elif hasattr(v, 'hex'):
                datos[k] = str(v)

        # Contratos
        contratos = await conn.fetch(
            "SELECT * FROM om_contratos WHERE cliente_id=$1", cliente_id)
        datos["contratos"] = [dict(c) for c in contratos]

        # Pagos
        pagos = await conn.fetch(
            "SELECT * FROM om_pagos WHERE cliente_id=$1 ORDER BY fecha_pago DESC LIMIT 50",
            cliente_id)
        datos["pagos"] = [dict(p) for p in pagos]

        # Asistencias
        asistencias = await conn.fetch("""
            SELECT a.*, s.fecha, s.hora_inicio FROM om_asistencias a
            JOIN om_sesiones s ON s.id = a.sesion_id
            WHERE a.cliente_id=$1 ORDER BY s.fecha DESC LIMIT 100
        """, cliente_id)
        datos["asistencias"] = [dict(a) for a in asistencias]

        # Serializar todo a JSON-safe
        import json
        return json.loads(json.dumps(datos, default=str))


@router.post("/portal/{token}/solicitar-baja")
async def solicitar_baja(token: str, motivo: str = ""):
    """RGPD: El cliente solicita eliminación de datos."""
    from src.db.client import get_pool
    pool = await get_pool()

    async with pool.acquire() as conn:
        cliente = await conn.fetchrow("""
            SELECT c.id, c.nombre FROM om_clientes c
            JOIN om_portal_tokens pt ON pt.cliente_id = c.id
            WHERE pt.token = $1 AND pt.activo = true
        """, token)
        if not cliente:
            raise HTTPException(status_code=404, detail="Token no válido")

        await conn.execute("""
            INSERT INTO om_solicitudes_baja (tenant_id, cliente_id, motivo)
            VALUES ('authentic_pilates', $1, $2)
        """, cliente["id"], motivo or "Sin motivo especificado")

        # Notificar a Jesús por WA
        try:
            from src.pilates.whatsapp import enviar_texto
            telefono_jesus = os.getenv("JESUS_TELEFONO", "")
            if telefono_jesus:
                await enviar_texto(
                    telefono_jesus,
                    f"⚠️ Solicitud de baja RGPD de {cliente['nombre']}. Revisar en admin.",
                )
        except Exception:
            pass

    return {"status": "ok", "mensaje": "Solicitud registrada. Te contactaremos en 48h."}
```

**Nota:** Importar `os` y `HTTPException` si no están ya importados en portal.py.

**Test 6.1:** `curl /portal/TOKEN_VALIDO/mis-datos` → JSON con datos del cliente
**Test 6.2:** `curl -X POST /portal/TOKEN_VALIDO/solicitar-baja` → `{"status": "ok"}`

---

## PASO 7: HEALTH CHECK PROFUNDO (src/main.py)

Reemplazar el endpoint `/health` actual:

De:
```python
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
```

A:
```python
@app.get("/health")
async def health():
    """Health check profundo — verifica componentes reales del sistema."""
    from datetime import datetime, timedelta
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
                ahora = datetime.now(ZoneInfo("Europe/Madrid"))
                horas_desde_cron = (ahora - ultima).total_seconds() / 3600
                checks["cron_last_run_hours_ago"] = round(horas_desde_cron, 1)
                if horas_desde_cron > 36:
                    checks["cron"] = "stale"
                    status = "degraded"
                else:
                    checks["cron"] = "ok"
            else:
                checks["cron"] = "never_run"
                # No degradar si es primer deploy

            # 3. Bus no saturado (señales pendientes < 100)
            try:
                pendientes = await conn.fetchval("""
                    SELECT count(*) FROM om_bus_senales
                    WHERE tenant_id = 'authentic_pilates' AND procesada = false
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

    # Status code: 200 para healthy/degraded, 503 para unhealthy (DB caída → Fly.io reinicia)
    code = 503 if status == "unhealthy" else 200
    return JSONResponse(
        status_code=code,
        content={"status": status, "version": "0.3.0", "checks": checks}
    )
```

**Test 7.1:** `curl /health` → JSON con `status`, `checks.db`, `checks.cron`, `checks.bus`
**Test 7.2:** Si DB caída → HTTP 503

---

## PASO 8: BRIEFING WA SEMANAL (src/pilates/cron.py)

En `_tarea_semanal()`, al FINAL (después de todo el bloque existente, antes del except), añadir:

```python
        # 10. Briefing semanal por WA a Jesús
        try:
            from src.pilates.briefing import generar_briefing
            from src.pilates.whatsapp import enviar_texto, is_configured as wa_configured
            briefing = await generar_briefing()
            telefono_jesus = os.getenv("JESUS_TELEFONO", "")
            if wa_configured() and telefono_jesus and briefing.get("texto_wa"):
                await enviar_texto(telefono_jesus, briefing["texto_wa"])
                log.info("cron_semanal_briefing_wa_ok")
        except Exception as e:
            log.error("cron_semanal_briefing_wa_error", error=str(e))
```

**Nota:** Añadir `import os` al inicio de cron.py si no está.

**Test 8.1:** `grep "generar_briefing" src/pilates/cron.py` → match
**Test 8.2:** `grep "JESUS_TELEFONO" src/pilates/cron.py` → match

---

## PASO 9: CREAR rate_limit.py

Crear archivo: `src/pilates/rate_limit.py`

```python
"""Rate limiting — semáforos globales para endpoints costosos."""
import asyncio

semaforo_opus = asyncio.Semaphore(1)       # Director Opus: $0.40/llamada, max 1 concurrente
semaforo_metacog = asyncio.Semaphore(1)    # Metacognitivo: $0.50/llamada, max 1 concurrente
semaforo_motor = asyncio.Semaphore(2)      # Motor pipeline, max 2 concurrentes
```

---

## PASO 10: FLY.IO SECRETS

Después del deploy, setear los secrets necesarios:

```bash
fly secrets set OMNI_API_KEY="$(openssl rand -hex 32)" --app chief-os-omni
fly secrets set JESUS_TELEFONO="34607466631" --app chief-os-omni
fly secrets set ALLOWED_ORIGINS="https://motor-semantico-omni.fly.dev" --app chief-os-omni
```

**NO ejecutar automáticamente** — Jesús debe proporcionar su teléfono y confirmar el API key generado.

---

## RESUMEN DE CAMBIOS

| Archivo | Cambio | Paso |
|---------|--------|------|
| `migrations/027_produccion.sql` | **NUEVO** — om_cron_state + RGPD | 0 |
| `src/main.py` | Auth middleware + CORS + docs off + health profundo + rate limit + version 0.3.0 | 1, 5, 7 |
| `src/pilates/cron.py` | ZoneInfo + cron state DB + cobros + confirmaciones + cumpleaños + briefing WA | 2, 3, 8 |
| `src/pilates/automatismos.py` | stripe_pagos → redsys_pagos | 4 |
| `src/pilates/rate_limit.py` | **NUEVO** — semáforos globales | 9 |
| `src/pilates/portal.py` | +2 endpoints RGPD | 6 |
| `src/pilates/router.py` | Importar y aplicar semáforos en director-opus y metacognitivo | 5 |

## TESTS FINALES (PASS/FAIL)

```
T1: curl /health → HTTP 200, JSON con checks.db, checks.cron, checks.bus          [PASS/FAIL]
T2: curl /pilates/clientes sin X-API-Key → HTTP 401                                [PASS/FAIL]
T3: curl /pilates/clientes con X-API-Key → HTTP 200                                [PASS/FAIL]
T4: curl /portal/TOKEN → HTTP 200 sin API key                                      [PASS/FAIL]
T5: curl /pilates/redsys/notificacion (POST form) → HTTP 200 sin API key           [PASS/FAIL]
T6: grep "stripe_pagos" src/pilates/ → 0 resultados                                [PASS/FAIL]
T7: grep "cron_cobros_recurrentes" src/pilates/cron.py → match                     [PASS/FAIL]
T8: grep "enviar_confirmaciones_manana" src/pilates/cron.py → match                [PASS/FAIL]
T9: grep "felicitar_cumpleanos" src/pilates/cron.py → match                        [PASS/FAIL]
T10: SELECT count(*) FROM om_cron_state → tabla existe (0 o más filas)             [PASS/FAIL]
T11: Deploy + restart → cron no re-ejecuta tareas del mismo periodo                [PASS/FAIL]
T12: curl /docs → 404 (deshabilitado por defecto)                                  [PASS/FAIL]
```

## ORDEN DE EJECUCIÓN

1. Crear `migrations/027_produccion.sql` (Paso 0)
2. Crear `src/pilates/rate_limit.py` (Paso 9)
3. Editar `src/main.py` (Pasos 1, 5, 7)
4. Editar `src/pilates/cron.py` (Pasos 2, 3, 8)
5. Editar `src/pilates/automatismos.py` (Paso 4)
6. Editar `src/pilates/portal.py` (Paso 6)
7. Editar `src/pilates/router.py` (Paso 5 — semáforos)
8. Deploy a fly.io
9. Setear secrets (Paso 10) — **con intervención de Jesús**
10. Verificar tests T1-T12
