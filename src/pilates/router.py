"""Exocortex Pilates — Endpoints CRUD + Lógica de Negocio.

Montado en /pilates/* en main.py.
Todas las operaciones usan tenant_id='authentic_pilates'.
Cadena causal: SESION > ASISTENCIA > CARGO > PAGO (FIFO).
"""
from __future__ import annotations

import structlog
from datetime import date, datetime, time, timedelta
from fastapi import APIRouter, HTTPException, Query
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


class SesionCreate(BaseModel):
    tipo: str = Field(pattern="^(individual|grupo)$")
    grupo_id: Optional[UUID] = None
    cliente_id: Optional[UUID] = None  # solo individual
    contrato_id: Optional[UUID] = None  # solo individual
    fecha: date = Field(default_factory=date.today)
    hora_inicio: str = "09:00"
    hora_fin: str = "10:00"
    instructor: str = "Jesus"


class MarcarAsistencia(BaseModel):
    cliente_id: UUID
    contrato_id: Optional[UUID] = None
    estado: str = Field(pattern="^(asistio|no_vino|cancelada)$")
    notas_instructor: Optional[str] = None


class MarcarAsistenciaGrupo(BaseModel):
    ausencias: list[UUID] = Field(default_factory=list)
    notas: Optional[dict[str, str]] = None  # {cliente_id: nota}


class PagoCreate(BaseModel):
    cliente_id: UUID
    metodo: str = Field(pattern="^(tpv|bizum|efectivo|transferencia|paygold)$")
    monto: float
    referencia_externa: Optional[str] = None
    notas: Optional[str] = None


class CargoManual(BaseModel):
    cliente_id: UUID
    contrato_id: Optional[UUID] = None
    tipo: str = Field(pattern="^(sesion_individual|cancelacion_tardia|suscripcion_grupo|producto|otro)$")
    descripcion: Optional[str] = None
    base_imponible: float
    iva_porcentaje: float = 21.00


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
    estado = estado or None
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
    estado = estado or None
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
    estado = estado or None  # tratar string vacío como sin filtro
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
    """Agenda de un grupo para una fecha. Default: hoy."""
    fecha = fecha or date.today()
    pool = await _get_pool()
    async with pool.acquire() as conn:
        # Buscar sesión de ese día
        sesion = await conn.fetchrow("""
            SELECT * FROM om_sesiones
            WHERE grupo_id = $1 AND fecha = $2 AND tenant_id = $3
        """, grupo_id, fecha, TENANT)

        if not sesion:
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


# ============================================================
# SESIONES
# ============================================================

@router.post("/sesiones", status_code=201)
async def crear_sesion(data: SesionCreate):
    """Crea sesión. Si es grupo, auto-crea asistencias 'confirmada' para cada miembro activo."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            h_inicio = time.fromisoformat(data.hora_inicio)
            h_fin = time.fromisoformat(data.hora_fin)

            row = await conn.fetchrow("""
                INSERT INTO om_sesiones (tenant_id, tipo, grupo_id, instructor, fecha,
                    hora_inicio, hora_fin)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id
            """, TENANT, data.tipo, data.grupo_id, data.instructor,
                data.fecha, h_inicio, h_fin)
            sesion_id = row["id"]

            asistencias_creadas = 0

            if data.tipo == "grupo" and data.grupo_id:
                # Auto-crear asistencias para todos los miembros activos del grupo
                miembros = await conn.fetch("""
                    SELECT cliente_id, id as contrato_id FROM om_contratos
                    WHERE grupo_id = $1 AND tenant_id = $2 AND estado = 'activo'
                """, data.grupo_id, TENANT)

                for m in miembros:
                    await conn.execute("""
                        INSERT INTO om_asistencias
                            (tenant_id, sesion_id, cliente_id, contrato_id, estado)
                        VALUES ($1, $2, $3, $4, 'confirmada')
                    """, TENANT, sesion_id, m["cliente_id"], m["contrato_id"])
                    asistencias_creadas += 1

            elif data.tipo == "individual" and data.cliente_id:
                await conn.execute("""
                    INSERT INTO om_asistencias
                        (tenant_id, sesion_id, cliente_id, contrato_id, estado)
                    VALUES ($1, $2, $3, $4, 'confirmada')
                """, TENANT, sesion_id, data.cliente_id, data.contrato_id)
                asistencias_creadas = 1

    log.info("sesion_creada", id=str(sesion_id), tipo=data.tipo,
             asistencias=asistencias_creadas)
    return {"id": str(sesion_id), "asistencias_creadas": asistencias_creadas}


@router.get("/sesiones/hoy")
async def agenda_hoy(fecha: Optional[date] = None):
    """Agenda del día: todas las sesiones con asistencias. Default: hoy."""
    dia = fecha or date.today()
    pool = await _get_pool()
    async with pool.acquire() as conn:
        sesiones = await conn.fetch("""
            SELECT s.*, g.nombre as grupo_nombre
            FROM om_sesiones s
            LEFT JOIN om_grupos g ON g.id = s.grupo_id
            WHERE s.tenant_id = $1 AND s.fecha = $2
            ORDER BY s.hora_inicio
        """, TENANT, dia)

        resultado = []
        for s in sesiones:
            asistencias = await conn.fetch("""
                SELECT a.*, c.nombre, c.apellidos
                FROM om_asistencias a
                JOIN om_clientes c ON c.id = a.cliente_id
                WHERE a.sesion_id = $1
                ORDER BY c.apellidos
            """, s["id"])
            resultado.append({
                **_row_to_dict(s),
                "asistentes": [_row_to_dict(a) for a in asistencias],
            })

    return {"fecha": str(dia), "sesiones": resultado}


@router.post("/sesiones/{sesion_id}/completar")
async def completar_sesion(sesion_id: UUID):
    """Marca sesión como completada. Asistencias 'confirmada' pasan a 'asistio'.
    Si es individual, genera cargo automático por sesión."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            sesion = await conn.fetchrow(
                "SELECT * FROM om_sesiones WHERE id = $1 AND tenant_id = $2",
                sesion_id, TENANT)
            if not sesion:
                raise HTTPException(404, "Sesión no encontrada")
            if sesion["estado"] == "completada":
                raise HTTPException(409, "Sesión ya completada")

            # Marcar sesión completada
            await conn.execute(
                "UPDATE om_sesiones SET estado = 'completada' WHERE id = $1",
                sesion_id)

            # Todas las confirmadas pasan a asistio
            await conn.execute("""
                UPDATE om_asistencias SET estado = 'asistio'
                WHERE sesion_id = $1 AND estado = 'confirmada'
            """, sesion_id)

            cargos_creados = 0

            # Si individual: generar cargo por cada asistencia
            if sesion["tipo"] == "individual":
                asistencias = await conn.fetch("""
                    SELECT a.cliente_id, a.contrato_id, a.id as asistencia_id
                    FROM om_asistencias a
                    WHERE a.sesion_id = $1 AND a.estado = 'asistio'
                """, sesion_id)

                for a in asistencias:
                    # Obtener precio del contrato
                    precio = 35.0  # default
                    if a["contrato_id"]:
                        contrato = await conn.fetchrow(
                            "SELECT precio_sesion FROM om_contratos WHERE id = $1",
                            a["contrato_id"])
                        if contrato and contrato["precio_sesion"]:
                            precio = float(contrato["precio_sesion"])

                    await conn.execute("""
                        INSERT INTO om_cargos (tenant_id, cliente_id, contrato_id,
                            tipo, descripcion, base_imponible, iva_porcentaje,
                            sesion_id, asistencia_id, fecha_cargo)
                        VALUES ($1, $2, $3, 'sesion_individual', $4, $5, 21.00,
                            $6, $7, $8)
                    """, TENANT, a["cliente_id"], a["contrato_id"],
                        f"Sesión individual {sesion['fecha']}",
                        precio, sesion_id, a["asistencia_id"], sesion["fecha"])
                    cargos_creados += 1

    log.info("sesion_completada", id=str(sesion_id), cargos=cargos_creados)
    return {"status": "completada", "cargos_creados": cargos_creados}


@router.post("/sesiones/{sesion_id}/marcar")
async def marcar_asistencia(sesion_id: UUID, data: MarcarAsistencia):
    """Marca asistencia individual. Si cancelada <12h, genera cargo por cancelación tardía."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            sesion = await conn.fetchrow(
                "SELECT * FROM om_sesiones WHERE id = $1 AND tenant_id = $2",
                sesion_id, TENANT)
            if not sesion:
                raise HTTPException(404, "Sesión no encontrada")

            # Buscar asistencia existente
            asistencia = await conn.fetchrow("""
                SELECT id FROM om_asistencias
                WHERE sesion_id = $1 AND cliente_id = $2
            """, sesion_id, data.cliente_id)

            cargo_creado = None

            if asistencia:
                await conn.execute("""
                    UPDATE om_asistencias SET estado = $1, notas_instructor = $2,
                        hora_cancelacion = CASE WHEN $1 = 'cancelada' THEN now() ELSE NULL END
                    WHERE id = $3
                """, data.estado, data.notas_instructor, asistencia["id"])
                asistencia_id = asistencia["id"]
            else:
                row = await conn.fetchrow("""
                    INSERT INTO om_asistencias (tenant_id, sesion_id, cliente_id,
                        contrato_id, estado, notas_instructor,
                        hora_cancelacion)
                    VALUES ($1, $2, $3, $4, $5, $6,
                        CASE WHEN $5 = 'cancelada' THEN now() ELSE NULL END)
                    RETURNING id
                """, TENANT, sesion_id, data.cliente_id, data.contrato_id,
                    data.estado, data.notas_instructor)
                asistencia_id = row["id"]

            # Cancelación tardía: <12h antes de la sesión
            if data.estado == "cancelada" and sesion["tipo"] == "individual":
                sesion_dt = datetime.combine(sesion["fecha"], sesion["hora_inicio"])
                horas_antes = (sesion_dt - datetime.now()).total_seconds() / 3600

                if horas_antes < 12:
                    # Obtener precio del contrato
                    precio = 35.0
                    if data.contrato_id:
                        contrato = await conn.fetchrow(
                            "SELECT precio_sesion FROM om_contratos WHERE id = $1",
                            data.contrato_id)
                        if contrato and contrato["precio_sesion"]:
                            precio = float(contrato["precio_sesion"])

                    await conn.execute("""
                        INSERT INTO om_cargos (tenant_id, cliente_id, contrato_id,
                            tipo, descripcion, base_imponible, iva_porcentaje,
                            sesion_id, asistencia_id, fecha_cargo)
                        VALUES ($1, $2, $3, 'cancelacion_tardia',
                            $4, $5, 21.00, $6, $7, $8)
                    """, TENANT, data.cliente_id, data.contrato_id,
                        f"Cancelación tardía sesión {sesion['fecha']}",
                        precio, sesion_id, asistencia_id, sesion["fecha"])
                    cargo_creado = "cancelacion_tardia"

                    await conn.execute("""
                        UPDATE om_asistencias SET genera_cargo = true, cargo_monto = $1
                        WHERE id = $2
                    """, precio, asistencia_id)

    log.info("asistencia_marcada", sesion=str(sesion_id),
             cliente=str(data.cliente_id), estado=data.estado, cargo=cargo_creado)
    return {"status": "marcada", "estado": data.estado, "cargo_creado": cargo_creado}


@router.post("/sesiones/{sesion_id}/marcar-grupo")
async def marcar_grupo(sesion_id: UUID, data: MarcarAsistenciaGrupo):
    """Marca asistencia grupal. Default=viene. Solo se envían las ausencias."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            sesion = await conn.fetchrow(
                "SELECT * FROM om_sesiones WHERE id = $1 AND tenant_id = $2",
                sesion_id, TENANT)
            if not sesion:
                raise HTTPException(404, "Sesión no encontrada")
            if sesion["tipo"] != "grupo":
                raise HTTPException(400, "Esta sesión no es de grupo")

            # Todos los que no están en ausencias -> asistio
            await conn.execute("""
                UPDATE om_asistencias SET estado = 'asistio'
                WHERE sesion_id = $1 AND estado = 'confirmada'
            """, sesion_id)

            # Los de la lista de ausencias -> no_vino
            marcados_ausentes = 0
            for cliente_id in data.ausencias:
                result = await conn.execute("""
                    UPDATE om_asistencias SET estado = 'no_vino'
                    WHERE sesion_id = $1 AND cliente_id = $2
                """, sesion_id, cliente_id)
                if result != "UPDATE 0":
                    marcados_ausentes += 1

            # Notas por alumno
            if data.notas:
                for cid_str, nota in data.notas.items():
                    await conn.execute("""
                        UPDATE om_asistencias SET notas_instructor = $1
                        WHERE sesion_id = $2 AND cliente_id = $3
                    """, nota, sesion_id, UUID(cid_str))

            # Contar asistentes finales
            conteo = await conn.fetchrow("""
                SELECT
                    count(*) FILTER (WHERE estado = 'asistio') as asistieron,
                    count(*) FILTER (WHERE estado = 'no_vino') as no_vinieron,
                    count(*) as total
                FROM om_asistencias WHERE sesion_id = $1
            """, sesion_id)

    log.info("grupo_marcado", sesion=str(sesion_id),
             asistieron=conteo["asistieron"], ausentes=conteo["no_vinieron"])
    return {
        "status": "marcado",
        "asistieron": conteo["asistieron"],
        "no_vinieron": conteo["no_vinieron"],
        "total": conteo["total"],
    }


# ============================================================
# CARGOS
# ============================================================

@router.get("/cargos")
async def listar_cargos(
    estado: Optional[str] = None,
    cliente_id: Optional[UUID] = None,
    mes: Optional[str] = None,
    limit: int = Query(default=50, le=200),
):
    """Lista cargos. Filtrable por estado, cliente, mes (YYYY-MM)."""
    pool = await _get_pool()
    conditions = ["c.tenant_id = $1"]
    params: list = [TENANT]
    idx = 2

    if estado:
        conditions.append(f"c.estado = ${idx}")
        params.append(estado)
        idx += 1
    if cliente_id:
        conditions.append(f"c.cliente_id = ${idx}")
        params.append(cliente_id)
        idx += 1
    if mes:
        conditions.append(f"to_char(c.fecha_cargo, 'YYYY-MM') = ${idx}")
        params.append(mes)
        idx += 1

    conditions.append(f"1=1")  # ensure valid SQL
    where = " AND ".join(conditions)

    async with pool.acquire() as conn:
        rows = await conn.fetch(f"""
            SELECT c.*, cl.nombre, cl.apellidos
            FROM om_cargos c
            JOIN om_clientes cl ON cl.id = c.cliente_id
            WHERE {where}
            ORDER BY c.fecha_cargo DESC, c.created_at DESC
            LIMIT ${idx}
        """, *params, limit)

    return [_row_to_dict(r) for r in rows]


@router.post("/cargos", status_code=201)
async def crear_cargo_manual(data: CargoManual):
    """Crea cargo manual (producto, otro, etc.)."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO om_cargos (tenant_id, cliente_id, contrato_id,
                tipo, descripcion, base_imponible, iva_porcentaje, fecha_cargo)
            VALUES ($1, $2, $3, $4, $5, $6, $7, CURRENT_DATE)
            RETURNING id, total
        """, TENANT, data.cliente_id, data.contrato_id,
            data.tipo, data.descripcion, data.base_imponible, data.iva_porcentaje)

    log.info("cargo_manual", id=str(row["id"]), tipo=data.tipo,
             total=float(row["total"]))
    return {"id": str(row["id"]), "total": float(row["total"])}


@router.post("/cargos/suscripciones-mes")
async def generar_suscripciones_mes(mes: Optional[date] = None):
    """Genera cargos de suscripción mensual para todos los contratos grupo activos.
    Idempotente: no duplica si ya existen cargos del mismo periodo."""
    periodo = mes or date.today().replace(day=1)
    pool = await _get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            contratos = await conn.fetch("""
                SELECT co.id, co.cliente_id, co.grupo_id, co.precio_mensual,
                       g.nombre as grupo_nombre
                FROM om_contratos co
                JOIN om_grupos g ON g.id = co.grupo_id
                WHERE co.tenant_id = $1 AND co.tipo = 'grupo'
                  AND co.estado = 'activo' AND co.precio_mensual IS NOT NULL
            """, TENANT)

            creados = 0
            omitidos = 0

            for co in contratos:
                # Idempotencia: verificar si ya existe cargo de suscripción para este periodo
                existente = await conn.fetchval("""
                    SELECT 1 FROM om_cargos
                    WHERE contrato_id = $1 AND tipo = 'suscripcion_grupo'
                      AND periodo_mes = $2 AND tenant_id = $3
                """, co["id"], periodo, TENANT)

                if existente:
                    omitidos += 1
                    continue

                await conn.execute("""
                    INSERT INTO om_cargos (tenant_id, cliente_id, contrato_id,
                        tipo, descripcion, base_imponible, iva_porcentaje,
                        periodo_mes, fecha_cargo)
                    VALUES ($1, $2, $3, 'suscripcion_grupo', $4, $5, 21.00, $6, $7)
                """, TENANT, co["cliente_id"], co["id"],
                    f"Suscripción {co['grupo_nombre']} {periodo.strftime('%B %Y')}",
                    float(co["precio_mensual"]), periodo, periodo)
                creados += 1

    log.info("suscripciones_mes", periodo=str(periodo), creados=creados,
             omitidos=omitidos)
    return {"periodo": str(periodo), "creados": creados, "omitidos": omitidos}


# ============================================================
# PAGOS
# ============================================================

@router.post("/pagos", status_code=201)
async def registrar_pago(data: PagoCreate):
    """Registra pago y concilia FIFO con cargos pendientes más antiguos."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            # Crear pago
            row = await conn.fetchrow("""
                INSERT INTO om_pagos (tenant_id, cliente_id, metodo, monto,
                    referencia_externa, notas)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
            """, TENANT, data.cliente_id, data.metodo, data.monto,
                data.referencia_externa, data.notas)
            pago_id = row["id"]

            # FIFO: obtener cargos pendientes ordenados por antigüedad
            cargos_pendientes = await conn.fetch("""
                SELECT id, total FROM om_cargos
                WHERE cliente_id = $1 AND tenant_id = $2 AND estado = 'pendiente'
                ORDER BY fecha_cargo ASC, created_at ASC
            """, data.cliente_id, TENANT)

            remanente = data.monto
            cargos_conciliados = 0

            for cargo in cargos_pendientes:
                if remanente <= 0:
                    break

                cargo_total = float(cargo["total"])
                aplicado = min(remanente, cargo_total)

                # Registrar relación pago-cargo
                await conn.execute("""
                    INSERT INTO om_pago_cargos (pago_id, cargo_id, monto_aplicado)
                    VALUES ($1, $2, $3)
                """, pago_id, cargo["id"], aplicado)

                # Si cubre el cargo completo, marcarlo como cobrado
                if aplicado >= cargo_total:
                    await conn.execute("""
                        UPDATE om_cargos SET estado = 'cobrado', fecha_cobro = CURRENT_DATE
                        WHERE id = $1
                    """, cargo["id"])

                remanente -= aplicado
                cargos_conciliados += 1

    log.info("pago_registrado", id=str(pago_id), monto=data.monto,
             cargos_conciliados=cargos_conciliados, remanente=round(remanente, 2))
    return {
        "id": str(pago_id),
        "monto": data.monto,
        "cargos_conciliados": cargos_conciliados,
        "remanente": round(remanente, 2),
    }


@router.get("/pagos")
async def listar_pagos(
    cliente_id: Optional[UUID] = None,
    limit: int = Query(default=50, le=200),
):
    """Lista pagos recientes."""
    pool = await _get_pool()
    conditions = ["p.tenant_id = $1"]
    params: list = [TENANT]
    idx = 2

    if cliente_id:
        conditions.append(f"p.cliente_id = ${idx}")
        params.append(cliente_id)
        idx += 1

    where = " AND ".join(conditions)

    async with pool.acquire() as conn:
        rows = await conn.fetch(f"""
            SELECT p.*, cl.nombre, cl.apellidos
            FROM om_pagos p
            JOIN om_clientes cl ON cl.id = p.cliente_id
            WHERE {where}
            ORDER BY p.fecha_pago DESC, p.created_at DESC
            LIMIT ${idx}
        """, *params, limit)

    return [_row_to_dict(r) for r in rows]


# ============================================================
# RESUMEN / DASHBOARD
# ============================================================

@router.get("/resumen")
async def resumen_mes(mes: Optional[str] = None):
    """Dashboard del mes: ingresos, deuda, sesiones, asistencia.
    mes formato YYYY-MM. Default: mes actual."""
    if mes:
        inicio = date.fromisoformat(f"{mes}-01")
    else:
        hoy = date.today()
        inicio = hoy.replace(day=1)

    if inicio.month == 12:
        fin = inicio.replace(year=inicio.year + 1, month=1)
    else:
        fin = inicio.replace(month=inicio.month + 1)

    pool = await _get_pool()
    async with pool.acquire() as conn:
        # Ingresos (pagos del mes)
        ingresos = await conn.fetchval("""
            SELECT COALESCE(SUM(monto), 0) FROM om_pagos
            WHERE tenant_id = $1 AND fecha_pago >= $2 AND fecha_pago < $3
        """, TENANT, inicio, fin)

        # Deuda pendiente total
        deuda = await conn.fetchval("""
            SELECT COALESCE(SUM(total), 0) FROM om_cargos
            WHERE tenant_id = $1 AND estado = 'pendiente'
        """, TENANT)

        # Cargos del mes
        cargos_mes = await conn.fetchrow("""
            SELECT
                COALESCE(SUM(total), 0) as total_facturado,
                count(*) as n_cargos,
                count(*) FILTER (WHERE estado = 'cobrado') as cobrados,
                count(*) FILTER (WHERE estado = 'pendiente') as pendientes
            FROM om_cargos
            WHERE tenant_id = $1 AND fecha_cargo >= $2 AND fecha_cargo < $3
        """, TENANT, inicio, fin)

        # Sesiones del mes
        sesiones_mes = await conn.fetchrow("""
            SELECT
                count(*) as total,
                count(*) FILTER (WHERE estado = 'completada') as completadas,
                count(*) FILTER (WHERE tipo = 'individual') as individuales,
                count(*) FILTER (WHERE tipo = 'grupo') as grupo
            FROM om_sesiones
            WHERE tenant_id = $1 AND fecha >= $2 AND fecha < $3
        """, TENANT, inicio, fin)

        # Asistencia del mes
        asistencia = await conn.fetchrow("""
            SELECT
                count(*) as total,
                count(*) FILTER (WHERE a.estado = 'asistio') as asistieron,
                count(*) FILTER (WHERE a.estado = 'no_vino') as no_vinieron,
                count(*) FILTER (WHERE a.estado = 'cancelada') as canceladas
            FROM om_asistencias a
            JOIN om_sesiones s ON s.id = a.sesion_id
            WHERE a.tenant_id = $1 AND s.fecha >= $2 AND s.fecha < $3
        """, TENANT, inicio, fin)

        # Gastos del mes
        gastos = await conn.fetchval("""
            SELECT COALESCE(SUM(total), 0) FROM om_gastos
            WHERE tenant_id = $1 AND fecha_gasto >= $2 AND fecha_gasto < $3
        """, TENANT, inicio, fin)

        # Clientes activos
        clientes_activos = await conn.fetchval("""
            SELECT count(*) FROM om_cliente_tenant
            WHERE tenant_id = $1 AND estado = 'activo'
        """, TENANT)

    pct_asist = 0
    if asistencia["total"] > 0:
        pct_asist = round(asistencia["asistieron"] / asistencia["total"] * 100, 1)

    return {
        "mes": str(inicio),
        "ingresos": float(ingresos),
        "gastos": float(gastos),
        "resultado_neto": float(ingresos) - float(gastos),
        "deuda_pendiente_total": float(deuda),
        "cargos": {
            "total_facturado": float(cargos_mes["total_facturado"]),
            "n_cargos": cargos_mes["n_cargos"],
            "cobrados": cargos_mes["cobrados"],
            "pendientes": cargos_mes["pendientes"],
        },
        "sesiones": {
            "total": sesiones_mes["total"],
            "completadas": sesiones_mes["completadas"],
            "individuales": sesiones_mes["individuales"],
            "grupo": sesiones_mes["grupo"],
        },
        "asistencia": {
            "total": asistencia["total"],
            "asistieron": asistencia["asistieron"],
            "no_vinieron": asistencia["no_vinieron"],
            "canceladas": asistencia["canceladas"],
            "pct_asistencia": pct_asist,
        },
        "clientes_activos": clientes_activos,
    }
