# B-PIL-03: Backend FastAPI — CRUD Clientes + Contratos + Grupos

**Fecha:** 2026-03-20
**Ejecutor:** Claude Code
**Dependencia:** B-PIL-01 (tablas), B-PIL-02 (seed grupos)
**Coste:** $0

---

## CONTEXTO

Las 29 tablas om_* y los 16 grupos están en producción. Ahora necesitamos endpoints CRUD para operar. Todo el backend Pilates vive en `src/pilates/` como módulo separado, montado en main.py como router.

**Principio Modo Estudio:** Cada endpoint <30s de latencia. El frontend necesita endpoints simples y rápidos. Sin paginación compleja en MVP — el estudio tiene <100 clientes.

---

## FASE A: Estructura del módulo

### A1. Crear `src/pilates/__init__.py`

```python
"""Módulo Pilates — Backend Exocortex Authentic Pilates."""
```

### A2. Crear `src/pilates/router.py`

Este es el archivo principal. Contiene el APIRouter y todos los endpoints CRUD.

```python
"""Exocortex Pilates — Endpoints CRUD.

Montado en /pilates/* en main.py.
Todas las operaciones usan tenant_id='authentic_pilates'.
"""
from __future__ import annotations

import structlog
from datetime import date
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID

log = structlog.get_logger()

router = APIRouter(prefix="/pilates", tags=["pilates"])

TENANT = "authentic_pilates"


# ============================================================
# SCHEMAS Pydantic
# ============================================================

class ClienteCreate(BaseModel):
    nombre: str
    apellidos: str
    telefono: Optional[str] = None
    email: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    nif: Optional[str] = None
    direccion: Optional[str] = None
    consentimiento_datos: bool = False
    consentimiento_marketing: bool = False
    consentimiento_compartir_tenants: bool = False


class ClienteUpdate(BaseModel):
    nombre: Optional[str] = None
    apellidos: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    nif: Optional[str] = None
    direccion: Optional[str] = None
    metodo_pago_habitual: Optional[str] = None
    consentimiento_datos: Optional[bool] = None
    consentimiento_marketing: Optional[bool] = None
    consentimiento_compartir_tenants: Optional[bool] = None


class ContratoCreate(BaseModel):
    cliente_id: UUID
    tipo: str = Field(pattern="^(individual|grupo)$")
    # Individual
    frecuencia_semanal: Optional[int] = None
    precio_sesion: Optional[float] = None
    ciclo_cobro: Optional[str] = None
    # Grupo
    grupo_id: Optional[UUID] = None
    precio_mensual: Optional[float] = None
    dia_fijo: Optional[int] = None
    # Vigencia
    fecha_inicio: Optional[date] = None


class ContratoUpdate(BaseModel):
    estado: Optional[str] = None
    precio_sesion: Optional[float] = None
    precio_mensual: Optional[float] = None
    ciclo_cobro: Optional[str] = None
    fecha_fin: Optional[date] = None


# ============================================================
# HELPERS
# ============================================================

async def _get_pool():
    from src.db.client import get_pool
    return await get_pool()


def _row_to_dict(row) -> dict:
    """Convierte asyncpg.Record a dict serializable."""
    d = dict(row)
    for k, v in d.items():
        if isinstance(v, UUID):
            d[k] = str(v)
    return d


# ============================================================
# CLIENTES
# ============================================================

@router.get("/clientes")
async def listar_clientes(estado: Optional[str] = None):
    """Lista clientes del tenant. Filtro opcional por estado en om_cliente_tenant."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        if estado:
            rows = await conn.fetch("""
                SELECT c.*, ct.estado as estado_tenant, ct.fecha_alta, ct.fuente_captacion
                FROM om_clientes c
                JOIN om_cliente_tenant ct ON ct.cliente_id = c.id
                WHERE ct.tenant_id = $1 AND ct.estado = $2
                ORDER BY c.apellidos, c.nombre
            """, TENANT, estado)
        else:
            rows = await conn.fetch("""
                SELECT c.*, ct.estado as estado_tenant, ct.fecha_alta, ct.fuente_captacion
                FROM om_clientes c
                JOIN om_cliente_tenant ct ON ct.cliente_id = c.id
                WHERE ct.tenant_id = $1
                ORDER BY c.apellidos, c.nombre
            """, TENANT)
    return [_row_to_dict(r) for r in rows]


@router.get("/clientes/{cliente_id}")
async def obtener_cliente(cliente_id: UUID):
    """Detalle de un cliente con contratos y saldo."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        cliente = await conn.fetchrow(
            "SELECT * FROM om_clientes WHERE id = $1", cliente_id)
        if not cliente:
            raise HTTPException(404, "Cliente no encontrado")

        contratos = await conn.fetch(
            "SELECT * FROM om_contratos WHERE cliente_id = $1 AND tenant_id = $2 ORDER BY fecha_inicio DESC",
            cliente_id, TENANT)

        # Saldo: cargos pendientes
        saldo = await conn.fetchval("""
            SELECT COALESCE(SUM(total), 0) FROM om_cargos
            WHERE cliente_id = $1 AND tenant_id = $2 AND estado = 'pendiente'
        """, cliente_id, TENANT)

        tenant = await conn.fetchrow(
            "SELECT * FROM om_cliente_tenant WHERE cliente_id = $1 AND tenant_id = $2",
            cliente_id, TENANT)

    return {
        **_row_to_dict(cliente),
        "estado_tenant": tenant["estado"] if tenant else None,
        "contratos": [_row_to_dict(c) for c in contratos],
        "saldo_pendiente": float(saldo),
    }


@router.post("/clientes", status_code=201)
async def crear_cliente(data: ClienteCreate):
    """Crea cliente + relación con tenant."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            # Crear cliente
            row = await conn.fetchrow("""
                INSERT INTO om_clientes (nombre, apellidos, telefono, email,
                    fecha_nacimiento, nif, direccion,
                    consentimiento_datos, consentimiento_marketing,
                    consentimiento_compartir_tenants,
                    fecha_consentimiento)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, now())
                RETURNING id
            """, data.nombre, data.apellidos, data.telefono, data.email,
                data.fecha_nacimiento, data.nif, data.direccion,
                data.consentimiento_datos, data.consentimiento_marketing,
                data.consentimiento_compartir_tenants)

            cliente_id = row["id"]

            # Crear relación tenant
            await conn.execute("""
                INSERT INTO om_cliente_tenant (cliente_id, tenant_id, estado)
                VALUES ($1, $2, 'activo')
            """, cliente_id, TENANT)

    log.info("cliente_creado", id=str(cliente_id), nombre=f"{data.nombre} {data.apellidos}")
    return {"id": str(cliente_id), "status": "created"}


@router.patch("/clientes/{cliente_id}")
async def actualizar_cliente(cliente_id: UUID, data: ClienteUpdate):
    """Actualiza campos del cliente (solo los enviados)."""
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(400, "Nada que actualizar")

    pool = await _get_pool()
    set_clauses = ", ".join(f"{k} = ${i+2}" for i, k in enumerate(updates.keys()))
    values = [cliente_id] + list(updates.values())

    async with pool.acquire() as conn:
        result = await conn.execute(
            f"UPDATE om_clientes SET {set_clauses}, updated_at = now() WHERE id = $1",
            *values)
        if result == "UPDATE 0":
            raise HTTPException(404, "Cliente no encontrado")

    log.info("cliente_actualizado", id=str(cliente_id), campos=list(updates.keys()))
    return {"status": "updated"}


# ============================================================
# CONTRATOS
# ============================================================

@router.get("/contratos")
async def listar_contratos(estado: Optional[str] = "activo"):
    """Lista contratos del tenant. Default: solo activos."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        if estado:
            rows = await conn.fetch("""
                SELECT co.*, c.nombre, c.apellidos, g.nombre as grupo_nombre
                FROM om_contratos co
                JOIN om_clientes c ON c.id = co.cliente_id
                LEFT JOIN om_grupos g ON g.id = co.grupo_id
                WHERE co.tenant_id = $1 AND co.estado = $2
                ORDER BY c.apellidos, c.nombre
            """, TENANT, estado)
        else:
            rows = await conn.fetch("""
                SELECT co.*, c.nombre, c.apellidos, g.nombre as grupo_nombre
                FROM om_contratos co
                JOIN om_clientes c ON c.id = co.cliente_id
                LEFT JOIN om_grupos g ON g.id = co.grupo_id
                WHERE co.tenant_id = $1
                ORDER BY c.apellidos, c.nombre
            """, TENANT)
    return [_row_to_dict(r) for r in rows]


@router.post("/contratos", status_code=201)
async def crear_contrato(data: ContratoCreate):
    """Crea contrato. Si es grupo, valida plaza disponible."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            # Validar cliente existe
            cliente = await conn.fetchval(
                "SELECT 1 FROM om_clientes WHERE id = $1", data.cliente_id)
            if not cliente:
                raise HTTPException(404, "Cliente no encontrado")

            # Si grupo: validar plaza
            if data.tipo == "grupo" and data.grupo_id:
                grupo = await conn.fetchrow(
                    "SELECT capacidad_max FROM om_grupos WHERE id = $1 AND tenant_id = $2",
                    data.grupo_id, TENANT)
                if not grupo:
                    raise HTTPException(404, "Grupo no encontrado")

                ocupados = await conn.fetchval("""
                    SELECT count(*) FROM om_contratos
                    WHERE grupo_id = $1 AND tenant_id = $2 AND estado = 'activo'
                """, data.grupo_id, TENANT)
                if ocupados >= grupo["capacidad_max"]:
                    raise HTTPException(409, f"Grupo lleno ({ocupados}/{grupo['capacidad_max']})")

            row = await conn.fetchrow("""
                INSERT INTO om_contratos (tenant_id, cliente_id, tipo,
                    frecuencia_semanal, precio_sesion, ciclo_cobro,
                    grupo_id, precio_mensual, dia_fijo, fecha_inicio)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                RETURNING id
            """, TENANT, data.cliente_id, data.tipo,
                data.frecuencia_semanal, data.precio_sesion, data.ciclo_cobro,
                data.grupo_id, data.precio_mensual, data.dia_fijo,
                data.fecha_inicio or date.today())

    contrato_id = row["id"]
    log.info("contrato_creado", id=str(contrato_id), tipo=data.tipo)
    return {"id": str(contrato_id), "status": "created"}


@router.patch("/contratos/{contrato_id}")
async def actualizar_contrato(contrato_id: UUID, data: ContratoUpdate):
    """Actualiza contrato (estado, precios, fecha_fin)."""
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(400, "Nada que actualizar")

    pool = await _get_pool()
    set_clauses = ", ".join(f"{k} = ${i+2}" for i, k in enumerate(updates.keys()))
    values = [contrato_id] + list(updates.values())

    async with pool.acquire() as conn:
        result = await conn.execute(
            f"UPDATE om_contratos SET {set_clauses}, updated_at = now() WHERE id = $1 AND tenant_id = '{TENANT}'",
            *values)
        if result == "UPDATE 0":
            raise HTTPException(404, "Contrato no encontrado")

    log.info("contrato_actualizado", id=str(contrato_id))
    return {"status": "updated"}


# ============================================================
# GRUPOS
# ============================================================

@router.get("/grupos")
async def listar_grupos(estado: Optional[str] = "activo"):
    """Lista grupos con plazas ocupadas."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT g.*,
                   (SELECT count(*) FROM om_contratos c
                    WHERE c.grupo_id = g.id AND c.estado = 'activo') as plazas_ocupadas
            FROM om_grupos g
            WHERE g.tenant_id = $1 AND ($2::text IS NULL OR g.estado = $2)
            ORDER BY g.nombre
        """, TENANT, estado)
    return [_row_to_dict(r) for r in rows]


@router.get("/grupos/{grupo_id}")
async def obtener_grupo(grupo_id: UUID):
    """Detalle grupo con miembros actuales."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        grupo = await conn.fetchrow(
            "SELECT * FROM om_grupos WHERE id = $1 AND tenant_id = $2",
            grupo_id, TENANT)
        if not grupo:
            raise HTTPException(404, "Grupo no encontrado")

        miembros = await conn.fetch("""
            SELECT c.id, c.nombre, c.apellidos, c.telefono, co.id as contrato_id,
                   co.estado as contrato_estado, co.fecha_inicio
            FROM om_contratos co
            JOIN om_clientes c ON c.id = co.cliente_id
            WHERE co.grupo_id = $1 AND co.tenant_id = $2 AND co.estado = 'activo'
            ORDER BY c.apellidos, c.nombre
        """, grupo_id, TENANT)

    return {
        **_row_to_dict(grupo),
        "miembros": [_row_to_dict(m) for m in miembros],
        "plazas_ocupadas": len(miembros),
    }


@router.get("/grupos/{grupo_id}/agenda")
async def agenda_grupo(grupo_id: UUID, fecha: Optional[date] = None):
    """Agenda de un grupo para una fecha. Default: hoy.

    Devuelve la sesión del día (si existe) con lista de asistentes
    y su estado de asistencia.
    """
    fecha = fecha or date.today()
    pool = await _get_pool()
    async with pool.acquire() as conn:
        # Buscar sesión de ese día
        sesion = await conn.fetchrow("""
            SELECT * FROM om_sesiones
            WHERE grupo_id = $1 AND fecha = $2 AND tenant_id = $3
        """, grupo_id, fecha, TENANT)

        if not sesion:
            # No hay sesión creada para hoy — devolver miembros sin asistencia
            miembros = await conn.fetch("""
                SELECT c.id as cliente_id, c.nombre, c.apellidos
                FROM om_contratos co
                JOIN om_clientes c ON c.id = co.cliente_id
                WHERE co.grupo_id = $1 AND co.tenant_id = $2 AND co.estado = 'activo'
                ORDER BY c.apellidos
            """, grupo_id, TENANT)
            return {
                "fecha": str(fecha),
                "sesion": None,
                "asistentes": [{"cliente_id": str(m["cliente_id"]),
                                "nombre": m["nombre"], "apellidos": m["apellidos"],
                                "estado": "sin_sesion"} for m in miembros],
            }

        # Sesión existe — cargar asistencias
        asistencias = await conn.fetch("""
            SELECT a.*, c.nombre, c.apellidos
            FROM om_asistencias a
            JOIN om_clientes c ON c.id = a.cliente_id
            WHERE a.sesion_id = $1
            ORDER BY c.apellidos
        """, sesion["id"])

    return {
        "fecha": str(fecha),
        "sesion": _row_to_dict(sesion),
        "asistentes": [_row_to_dict(a) for a in asistencias],
    }


# ============================================================
# BÚSQUEDA RÁPIDA (Modo Estudio: F3)
# ============================================================

@router.get("/buscar")
async def buscar(q: str):
    """Búsqueda rápida por nombre/apellidos/teléfono. Para typeahead del Modo Estudio."""
    if len(q) < 2:
        return []

    pool = await _get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT c.id, c.nombre, c.apellidos, c.telefono,
                   ct.estado as estado_tenant
            FROM om_clientes c
            JOIN om_cliente_tenant ct ON ct.cliente_id = c.id AND ct.tenant_id = $1
            WHERE (c.nombre ILIKE $2 OR c.apellidos ILIKE $2 OR c.telefono ILIKE $2)
            ORDER BY c.apellidos, c.nombre
            LIMIT 10
        """, TENANT, f"%{q}%")
    return [_row_to_dict(r) for r in rows]
```

### A3. Montar router en main.py

**Archivo:** `@project/src/main.py` — LEER PRIMERO.

Después de la línea `app = FastAPI(...)` y antes de montar code_os, AÑADIR:

```python
# Mount Pilates router
try:
    from src.pilates.router import router as pilates_router
    app.include_router(pilates_router)
    log.info("pilates_router_mounted")
except Exception as e:
    log.warning("pilates_router_mount_failed", error=str(e))
```

---

## FASE B: Tests

### B1. Test local (imports)

```bash
cd @project/ && python3 -c "
from src.pilates.router import router
routes = [(r.path, list(r.methods)) for r in router.routes if hasattr(r, 'methods')]
for path, methods in sorted(routes):
    print(f'  {methods} /pilates{path}')
print(f'PASS: {len(routes)} endpoints Pilates')
"
```

Resultado esperado:
```
  ['GET'] /pilates/buscar
  ['GET'] /pilates/clientes
  ['GET'] /pilates/clientes/{cliente_id}
  ['PATCH'] /pilates/clientes/{cliente_id}
  ['POST'] /pilates/clientes
  ['GET'] /pilates/contratos
  ['PATCH'] /pilates/contratos/{contrato_id}
  ['POST'] /pilates/contratos
  ['GET'] /pilates/grupos
  ['GET'] /pilates/grupos/{grupo_id}
  ['GET'] /pilates/grupos/{grupo_id}/agenda
  PASS: 11 endpoints Pilates
```

### B2. Deploy

```bash
cd @project/ && fly deploy --strategy immediate
```

### B3. Smoke test

```bash
# Health
curl https://motor-semantico-omni.fly.dev/health

# Listar grupos
curl https://motor-semantico-omni.fly.dev/pilates/grupos | python3 -m json.tool

# Detalle primer grupo
GRUPO_ID=$(curl -s https://motor-semantico-omni.fly.dev/pilates/grupos | python3 -c "import json,sys; print(json.load(sys.stdin)[0]['id'])")
curl "https://motor-semantico-omni.fly.dev/pilates/grupos/$GRUPO_ID" | python3 -m json.tool

# Listar clientes (vacío por ahora)
curl https://motor-semantico-omni.fly.dev/pilates/clientes | python3 -m json.tool

# Crear cliente de prueba
curl -X POST https://motor-semantico-omni.fly.dev/pilates/clientes \
  -H "Content-Type: application/json" \
  -d '{"nombre":"Test","apellidos":"Pilates","telefono":"600000000","consentimiento_datos":true}' | python3 -m json.tool

# Verificar que aparece
curl https://motor-semantico-omni.fly.dev/pilates/clientes | python3 -m json.tool

# Búsqueda
curl "https://motor-semantico-omni.fly.dev/pilates/buscar?q=Test" | python3 -m json.tool
```

**Pass/fail:**
- `src/pilates/__init__.py` y `src/pilates/router.py` creados
- Router montado en main.py
- 11 endpoints disponibles
- POST /pilates/clientes crea cliente + relación tenant
- GET /pilates/grupos devuelve 16 grupos con plazas_ocupadas=0
- GET /pilates/buscar?q=Test devuelve el cliente de prueba

---

## NOTAS

- Todos los endpoints usan TENANT='authentic_pilates' hardcoded (multi-tenant vendrá después)
- No hay autenticación en MVP — el frontend es local en el estudio
- GET /pilates/grupos/{id}/agenda es clave para Modo Estudio (pantalla principal)
- La búsqueda usa ILIKE (case-insensitive) con wildcard — suficiente para <100 clientes
- El PATCH de clientes construye SET dinámico — solo actualiza campos enviados
- POST /pilates/contratos valida plaza disponible en grupo antes de crear
