# B-ORG-01: Bus de Señales Unificado + OBSERVADOR

**Fecha:** 22 marzo 2026
**Objetivo:** Crear la infraestructura de bus de señales que conecta los dos sistemas (src/ y agent/core/) y el OBSERVADOR que genera señales desde CRUD existente.
**Archivos a crear/modificar:** 4 nuevos + 2 modificados
**Tiempo estimado:** 30-45 min

---

## PASO 1: Migración 015 — tabla om_senales_agentes

**Crear archivo:** `migrations/015_bus_senales.sql`

```sql
-- =================================================================
-- Migration 015: Bus de señales inter-agente
-- Tabla unificada para señales entre todos los agentes del organismo.
-- Usada tanto por src/ (asyncpg) como por agent/core/ (psycopg2).
-- =================================================================

CREATE TABLE IF NOT EXISTS om_senales_agentes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT now(),
    tipo TEXT NOT NULL CHECK (tipo IN ('DATO', 'ALERTA', 'DIAGNOSTICO', 'OPORTUNIDAD', 'PRESCRIPCION', 'ACCION')),
    origen TEXT NOT NULL,               -- agente que emite: "OBSERVADOR", "VIGIA", "AF1", etc.
    destino TEXT,                        -- agente destino (NULL = broadcast)
    prioridad INTEGER DEFAULT 5 CHECK (prioridad BETWEEN 1 AND 10),  -- 1=max, 10=min
    payload JSONB NOT NULL DEFAULT '{}', -- datos específicos de la señal
    estado TEXT NOT NULL DEFAULT 'pendiente' CHECK (estado IN ('pendiente', 'procesando', 'procesada', 'error')),
    procesada_por TEXT,                  -- agente que procesó
    procesada_at TIMESTAMPTZ,
    tenant_id TEXT NOT NULL DEFAULT 'authentic_pilates',
    error_detalle TEXT                   -- si estado='error', qué pasó
);

-- Índices para queries frecuentes
CREATE INDEX IF NOT EXISTS idx_senales_pendientes
    ON om_senales_agentes(estado, prioridad, created_at)
    WHERE estado = 'pendiente';

CREATE INDEX IF NOT EXISTS idx_senales_tipo_origen
    ON om_senales_agentes(tipo, origen, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_senales_tenant
    ON om_senales_agentes(tenant_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_senales_destino
    ON om_senales_agentes(destino, estado)
    WHERE destino IS NOT NULL;
```

**TEST 1:** Tras deploy, verificar que la tabla existe:
```bash
curl -s https://motor-semantico-omni.fly.dev/health | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if d.get('om_tables',0) >= 23 else 'FAIL: tables=' + str(d.get('om_tables')))"
```

---

## PASO 2: Módulo bus de señales — src/pilates/bus.py

**Crear archivo:** `motor-semantico/src/pilates/bus.py`

```python
"""Bus de señales inter-agente — infraestructura del sistema nervioso.

Tabla: om_senales_agentes
Tipos: DATO, ALERTA, DIAGNOSTICO, OPORTUNIDAD, PRESCRIPCION, ACCION
Prioridad: 1 (máx) a 10 (mín)

Uso:
    from src.pilates.bus import emitir, leer_pendientes, marcar_procesada

    # Emitir señal
    await emitir("DATO", "OBSERVADOR", {"entidad": "asistencia", "accion": "crear", "id": str(id)})

    # Leer pendientes para un agente
    señales = await leer_pendientes(destino="DIAGNOSTICADOR", limite=20)

    # Marcar como procesada
    await marcar_procesada(señal_id, "DIAGNOSTICADOR")
"""
from __future__ import annotations

import structlog
from datetime import datetime, timezone
from uuid import UUID

from src.db.client import get_pool

log = structlog.get_logger()

TENANT = "authentic_pilates"

TIPOS_VALIDOS = {"DATO", "ALERTA", "DIAGNOSTICO", "OPORTUNIDAD", "PRESCRIPCION", "ACCION"}


async def emitir(
    tipo: str,
    origen: str,
    payload: dict,
    destino: str | None = None,
    prioridad: int = 5,
) -> str:
    """Emite una señal al bus. Devuelve UUID de la señal creada."""
    if tipo not in TIPOS_VALIDOS:
        raise ValueError(f"Tipo inválido: {tipo}. Válidos: {TIPOS_VALIDOS}")

    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO om_senales_agentes (tipo, origen, destino, prioridad, payload, tenant_id)
            VALUES ($1, $2, $3, $4, $5::jsonb, $6)
            RETURNING id
        """, tipo, origen, destino, prioridad, __import__('json').dumps(payload), TENANT)

    señal_id = str(row["id"])
    log.info("bus_emitir", tipo=tipo, origen=origen, destino=destino, prioridad=prioridad, id=señal_id)
    return señal_id


async def leer_pendientes(
    destino: str | None = None,
    tipo: str | None = None,
    limite: int = 20,
) -> list[dict]:
    """Lee señales pendientes, ordenadas por prioridad y antigüedad.

    Args:
        destino: Filtrar por agente destino. None = broadcast (destino IS NULL) + dirigidas.
        tipo: Filtrar por tipo de señal. None = todos.
        limite: Máximo de señales a devolver.
    """
    pool = await get_pool()
    conditions = ["estado = 'pendiente'", "tenant_id = $1"]
    params: list = [TENANT]
    idx = 2

    if destino:
        conditions.append(f"(destino = ${idx} OR destino IS NULL)")
        params.append(destino)
        idx += 1

    if tipo:
        conditions.append(f"tipo = ${idx}")
        params.append(tipo)
        idx += 1

    where = " AND ".join(conditions)
    params.append(limite)

    query = f"""
        SELECT id, created_at, tipo, origen, destino, prioridad, payload, estado
        FROM om_senales_agentes
        WHERE {where}
        ORDER BY prioridad ASC, created_at ASC
        LIMIT ${idx}
    """

    async with pool.acquire() as conn:
        rows = await conn.fetch(query, *params)

    return [dict(r) for r in rows]


async def marcar_procesada(señal_id: str | UUID, procesada_por: str) -> bool:
    """Marca una señal como procesada. Devuelve True si se actualizó."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute("""
            UPDATE om_senales_agentes
            SET estado = 'procesada', procesada_por = $1, procesada_at = now()
            WHERE id = $2 AND estado = 'pendiente'
        """, procesada_por, señal_id if isinstance(señal_id, UUID) else UUID(str(señal_id)))

    actualizado = result == "UPDATE 1"
    if actualizado:
        log.info("bus_procesada", id=str(señal_id), por=procesada_por)
    return actualizado


async def marcar_error(señal_id: str | UUID, procesada_por: str, detalle: str) -> bool:
    """Marca una señal como error."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute("""
            UPDATE om_senales_agentes
            SET estado = 'error', procesada_por = $1, procesada_at = now(), error_detalle = $2
            WHERE id = $3 AND estado IN ('pendiente', 'procesando')
        """, procesada_por, detalle[:500], señal_id if isinstance(señal_id, UUID) else UUID(str(señal_id)))
    return result == "UPDATE 1"


async def historial(
    limite: int = 50,
    tipo: str | None = None,
    origen: str | None = None,
) -> list[dict]:
    """Devuelve historial de señales recientes."""
    pool = await get_pool()
    conditions = ["tenant_id = $1"]
    params: list = [TENANT]
    idx = 2

    if tipo:
        conditions.append(f"tipo = ${idx}")
        params.append(tipo)
        idx += 1

    if origen:
        conditions.append(f"origen = ${idx}")
        params.append(origen)
        idx += 1

    where = " AND ".join(conditions)
    params.append(limite)

    query = f"""
        SELECT id, created_at, tipo, origen, destino, prioridad, payload, estado, procesada_por, procesada_at
        FROM om_senales_agentes
        WHERE {where}
        ORDER BY created_at DESC
        LIMIT ${idx}
    """

    async with pool.acquire() as conn:
        rows = await conn.fetch(query, *params)

    return [dict(r) for r in rows]


async def contar_pendientes() -> dict:
    """Cuenta señales pendientes agrupadas por tipo."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT tipo, count(*) as n
            FROM om_senales_agentes
            WHERE estado = 'pendiente' AND tenant_id = $1
            GROUP BY tipo
        """, TENANT)
    return {r["tipo"]: r["n"] for r in rows}
```

---

## PASO 3: Endpoints REST del bus — añadir a router.py

**Modificar archivo:** `motor-semantico/src/pilates/router.py`

Buscar la última línea antes de las funciones de utilidad (o al final del archivo) y añadir:

```python
# ============================================================
# BUS DE SEÑALES — Sistema nervioso del organismo
# ============================================================

class SenalCreate(BaseModel):
    tipo: str = Field(pattern="^(DATO|ALERTA|DIAGNOSTICO|OPORTUNIDAD|PRESCRIPCION|ACCION)$")
    origen: str
    destino: Optional[str] = None
    prioridad: int = Field(default=5, ge=1, le=10)
    payload: dict = {}


@router.post("/bus/emitir")
async def bus_emitir(data: SenalCreate):
    """Emite una señal al bus de agentes."""
    from src.pilates.bus import emitir
    señal_id = await emitir(
        tipo=data.tipo,
        origen=data.origen,
        payload=data.payload,
        destino=data.destino,
        prioridad=data.prioridad,
    )
    return {"id": señal_id, "status": "emitida"}


@router.get("/bus/pendientes")
async def bus_pendientes(
    destino: Optional[str] = None,
    tipo: Optional[str] = None,
    limite: int = Query(default=20, le=100),
):
    """Lee señales pendientes del bus."""
    from src.pilates.bus import leer_pendientes
    señales = await leer_pendientes(destino=destino, tipo=tipo, limite=limite)
    return {"señales": señales, "total": len(señales)}


@router.patch("/bus/{senal_id}/procesar")
async def bus_procesar(senal_id: UUID, procesada_por: str = Query(...)):
    """Marca una señal como procesada."""
    from src.pilates.bus import marcar_procesada
    ok = await marcar_procesada(senal_id, procesada_por)
    if not ok:
        raise HTTPException(404, "Señal no encontrada o ya procesada")
    return {"status": "procesada"}


@router.get("/bus/historial")
async def bus_historial(
    limite: int = Query(default=50, le=200),
    tipo: Optional[str] = None,
    origen: Optional[str] = None,
):
    """Historial de señales del bus."""
    from src.pilates.bus import historial
    señales = await historial(limite=limite, tipo=tipo, origen=origen)
    return {"señales": señales, "total": len(señales)}
```

---

## PASO 4: OBSERVADOR — hooks en CRUD existente

**Crear archivo:** `motor-semantico/src/pilates/observador.py`

```python
"""OBSERVADOR — Agente G1: datos → señales DATO al bus.

Hooks ligeros que se llaman DESPUÉS de operaciones CRUD exitosas.
No bloquean la respuesta al usuario. Fire-and-forget.

Uso en router.py:
    from src.pilates.observador import observar
    # Al final de un endpoint CRUD exitoso:
    asyncio.create_task(observar("asistencia", "crear", {"id": str(id), "cliente_id": str(cid)}))
"""
from __future__ import annotations

import asyncio
import structlog

log = structlog.get_logger()

ORIGEN = "OBSERVADOR"


async def observar(entidad: str, accion: str, datos: dict):
    """Emite señal DATO al bus tras operación CRUD.

    Args:
        entidad: "asistencia", "pago", "cliente", "contrato", "sesion", "wa_mensaje"
        accion: "crear", "actualizar", "eliminar"
        datos: dict con IDs y campos relevantes
    """
    try:
        from src.pilates.bus import emitir

        payload = {
            "entidad": entidad,
            "accion": accion,
            **datos,
        }

        # Prioridad según entidad
        prioridad_map = {
            "pago": 2,         # pagos = alta prioridad
            "asistencia": 3,   # asistencia = importante
            "contrato": 3,     # contratos = importante
            "cliente": 4,      # clientes = normal-alto
            "sesion": 5,       # sesiones = normal
            "wa_mensaje": 6,   # WA = normal-bajo
        }
        prioridad = prioridad_map.get(entidad, 5)

        await emitir("DATO", ORIGEN, payload, prioridad=prioridad)

    except Exception as e:
        # NUNCA bloquear CRUD por error en observador
        log.warning("observador_error", entidad=entidad, accion=accion, error=str(e))
```

---

## PASO 5: Inyectar OBSERVADOR en endpoints CRUD clave

**Modificar archivo:** `motor-semantico/src/pilates/router.py`

Añadir import al inicio del archivo (junto a los otros imports):

```python
import asyncio
```

Luego, en los siguientes endpoints, añadir una línea al final (ANTES del return), usando `asyncio.create_task`:

### 5.1 — En el endpoint POST de marcar_asistencia (buscar `marcar_asistencia` o `asistencia`):

Añadir antes del return exitoso:
```python
asyncio.create_task(_observar_crud("asistencia", "crear", {"id": str(asist_id), "cliente_id": str(data.cliente_id), "sesion_id": str(data.sesion_id)}))
```

### 5.2 — En el endpoint POST de registrar_pago:

Añadir antes del return exitoso:
```python
asyncio.create_task(_observar_crud("pago", "crear", {"id": str(pago_id), "cliente_id": str(data.cliente_id), "importe": str(data.importe)}))
```

### 5.3 — En el endpoint POST de crear_cliente:

Añadir antes del return exitoso:
```python
asyncio.create_task(_observar_crud("cliente", "crear", {"id": str(cliente_id), "nombre": data.nombre}))
```

### 5.4 — En el endpoint POST de crear_contrato:

Añadir antes del return exitoso:
```python
asyncio.create_task(_observar_crud("contrato", "crear", {"id": str(contrato_id), "cliente_id": str(data.cliente_id), "tipo": data.tipo}))
```

### Función helper (añadir después de los imports en router.py):

```python
async def _observar_crud(entidad: str, accion: str, datos: dict):
    """Helper para fire-and-forget al observador."""
    try:
        from src.pilates.observador import observar
        await observar(entidad, accion, datos)
    except Exception:
        pass  # Nunca bloquear CRUD
```

---

## TESTS PASS/FAIL

Ejecutar todos en orden tras deploy:

### TEST 1: Tabla existe
```bash
curl -s https://motor-semantico-omni.fly.dev/health | python3 -c "
import sys,json
d=json.load(sys.stdin)
print('PASS' if d.get('om_tables',0) >= 23 else 'FAIL')
"
```

### TEST 2: Emitir señal
```bash
curl -s -X POST https://motor-semantico-omni.fly.dev/pilates/bus/emitir \
  -H 'Content-Type: application/json' \
  -d '{"tipo":"DATO","origen":"TEST","payload":{"test":true}}' \
  | python3 -c "
import sys,json
d=json.load(sys.stdin)
print('PASS' if d.get('id') and d.get('status')=='emitida' else 'FAIL:', d)
"
```

### TEST 3: Leer pendientes
```bash
curl -s 'https://motor-semantico-omni.fly.dev/pilates/bus/pendientes?destino=TEST' \
  | python3 -c "
import sys,json
d=json.load(sys.stdin)
print('PASS' if d.get('total',0) >= 0 else 'FAIL:', d)
"
```

### TEST 4: Marcar procesada (usar el ID del TEST 2)
```bash
# Primero obtener el ID
ID=$(curl -s -X POST https://motor-semantico-omni.fly.dev/pilates/bus/emitir \
  -H 'Content-Type: application/json' \
  -d '{"tipo":"DATO","origen":"TEST","payload":{"test_procesar":true}}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

curl -s -X PATCH "https://motor-semantico-omni.fly.dev/pilates/bus/${ID}/procesar?procesada_por=TEST" \
  | python3 -c "
import sys,json
d=json.load(sys.stdin)
print('PASS' if d.get('status')=='procesada' else 'FAIL:', d)
"
```

### TEST 5: OBSERVADOR — crear asistencia genera señal
```bash
# Marcar asistencia de un cliente real → verificar que aparece señal DATO del OBSERVADOR
# (Necesita IDs reales de sesión y cliente — usar los de test o producción)
curl -s 'https://motor-semantico-omni.fly.dev/pilates/bus/historial?tipo=DATO&origen=OBSERVADOR&limite=5' \
  | python3 -c "
import sys,json
d=json.load(sys.stdin)
# Si hay al menos una señal del OBSERVADOR, PASS
print('PASS' if d.get('total',0) > 0 else 'PENDIENTE: necesita operación CRUD real para generar señal')
"
```

---

## CRITERIO PASS/FAIL

**PASS = Tests 1-4 devuelven PASS.** Test 5 se validará con la primera operación CRUD real post-deploy.

**FAIL = Cualquier test 1-4 devuelve FAIL.** Revisar logs con `fly logs -a chief-os-omni`.
