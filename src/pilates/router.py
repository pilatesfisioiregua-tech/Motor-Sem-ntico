"""Exocortex Pilates — Endpoints CRUD + Lógica de Negocio.

Montado en /pilates/* en main.py.
Todas las operaciones usan tenant_id='authentic_pilates'.
Cadena causal: SESION > ASISTENCIA > CARGO > PAGO (FIFO).
"""
from __future__ import annotations

import json
import structlog
from datetime import date, datetime, time, timedelta
from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field
import asyncio
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


class FacturaCreate(BaseModel):
    """Crear factura desde cargos cobrados de un cliente."""
    cliente_id: UUID
    cargo_ids: list[UUID]  # cargos a incluir en la factura
    fecha_operacion: Optional[date] = None


class FacturaAnular(BaseModel):
    motivo: str


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


class ConsejoRequest(BaseModel):
    pregunta: str
    profundidad: str = Field(default="normal", pattern="^(rapida|normal|profunda)$")
    ints_forzadas: Optional[list[str]] = None


class DecisionTernaria(BaseModel):
    sesion_id: UUID
    decision: str = Field(pattern="^(cierre|inerte|toxico)$")
    confianza: float = Field(ge=0, le=1)
    razon: Optional[str] = None


# ============================================================
# SCHEMAS — ADN + PROCESOS + CONOCIMIENTO + TENSIONES + DEPURACIÓN
# ============================================================

class ADNCreate(BaseModel):
    categoria: str = Field(pattern="^(principio_innegociable|principio_flexible|metodo|filosofia|antipatron|criterio_depuracion)$")
    titulo: str
    descripcion: str
    ejemplos: Optional[list[str]] = None
    contra_ejemplos: Optional[list[str]] = None
    funcion_l07: Optional[str] = None
    lente: Optional[str] = None


class ADNUpdate(BaseModel):
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    ejemplos: Optional[list[str]] = None
    contra_ejemplos: Optional[list[str]] = None
    activo: Optional[bool] = None


class ProcesoCreate(BaseModel):
    area: str = Field(pattern="^(operativa_diaria|sesion|cliente|emergencia|administrativa|instructor)$")
    titulo: str
    descripcion: str
    pasos: list[dict]  # [{"orden": 1, "accion": "...", "detalle": "..."}]
    notas: Optional[str] = None
    funcion_l07: Optional[str] = None
    vinculado_a_adn: Optional[UUID] = None


class ConocimientoCreate(BaseModel):
    tipo: str = Field(pattern="^(tecnica|cliente|negocio|mercado|metodo)$")
    titulo: str
    descripcion: str
    evidencia: Optional[list[str]] = None
    confianza: str = Field(default="hipotesis", pattern="^(hipotesis|validado|consolidado)$")
    origen: Optional[str] = None


class TensionCreate(BaseModel):
    tipo: str = Field(pattern="^(competencia_nueva|perdida_recurso|crisis_demanda|crecimiento|regulatorio|personal|estacional|mercado)$")
    descripcion: str
    funciones_afectadas: list[str]
    severidad: str = Field(pattern="^(baja|media|alta|critica)$")
    duracion_estimada_dias: Optional[int] = None


class DepuracionCreate(BaseModel):
    tipo: str = Field(pattern="^(servicio_eliminar|cliente_toxico|gasto_innecesario|proceso_redundante|canal_inefectivo|habito_operativo|creencia_limitante)$")
    descripcion: str
    impacto_estimado: Optional[str] = None
    funcion_l07: Optional[str] = None
    lente: Optional[str] = None
    origen: str = Field(default="manual", pattern="^(diagnostico_acd|sesion_consejo|manual|automatizacion)$")
    diagnostico_id: Optional[UUID] = None


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


async def _observar_crud(entidad: str, accion: str, datos: dict):
    """Helper fire-and-forget: emite señal DATO al bus vía OBSERVADOR."""
    try:
        from src.pilates.observador import observar
        await observar(entidad, accion, datos)
    except Exception:
        pass  # Nunca bloquear CRUD


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
    asyncio.create_task(_observar_crud("cliente", "crear", {"id": str(cliente_id), "nombre": data.nombre}))
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
    asyncio.create_task(_observar_crud("contrato", "crear", {"id": str(contrato_id), "cliente_id": str(data.cliente_id), "tipo": data.tipo}))
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


@router.get("/sesiones/semana")
async def sesiones_semana(fecha: Optional[date] = None):
    """Sesiones de una semana completa (L-V) con asistentes y estado."""
    if fecha is None:
        fecha = date.today()
    lunes = fecha - timedelta(days=fecha.weekday())
    viernes = lunes + timedelta(days=4)

    pool = await _get_pool()
    async with pool.acquire() as conn:
        sesiones = await conn.fetch("""
            SELECT s.id, s.tipo, s.grupo_id, s.fecha, s.hora_inicio, s.hora_fin, s.estado,
                   g.nombre as grupo_nombre, g.tipo as grupo_tipo, g.capacidad_max,
                   (SELECT count(*) FROM om_asistencias a
                    WHERE a.sesion_id = s.id AND a.estado IN ('confirmada','asistio','recuperacion')) as presentes,
                   (SELECT count(*) FROM om_asistencias a
                    WHERE a.sesion_id = s.id AND a.estado = 'no_vino') as ausentes,
                   (SELECT count(*) FROM om_asistencias a
                    WHERE a.sesion_id = s.id) as total_asistencias
            FROM om_sesiones s
            LEFT JOIN om_grupos g ON g.id = s.grupo_id
            WHERE s.tenant_id = $1 AND s.fecha >= $2 AND s.fecha <= $3
            ORDER BY s.fecha, s.hora_inicio
        """, TENANT, lunes, viernes)

    dias_nombre = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']
    dias = []
    for i in range(5):
        dia_fecha = lunes + timedelta(days=i)
        sesiones_dia = [_row_to_dict(s) for s in sesiones if s["fecha"] == dia_fecha]
        dias.append({
            "fecha": str(dia_fecha),
            "dia_nombre": dias_nombre[i],
            "es_hoy": dia_fecha == date.today(),
            "sesiones": sesiones_dia,
        })

    return {
        "semana_inicio": str(lunes),
        "semana_fin": str(viernes),
        "dias": dias,
        "total_sesiones": len(sesiones),
    }


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

            # Side-effect: actualizar días esperados
            try:
                from src.pilates.automatismos import actualizar_dias_esperados_asistencia
                await actualizar_dias_esperados_asistencia(sesion_id)
            except Exception as e:
                log.warning("dias_esperados_update_failed", error=str(e))

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
    asyncio.create_task(_observar_crud("asistencia", "crear", {"sesion_id": str(sesion_id), "cliente_id": str(data.cliente_id), "estado": data.estado}))
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

    # Side-effect: actualizar días esperados
    try:
        from src.pilates.automatismos import actualizar_dias_esperados_asistencia
        await actualizar_dias_esperados_asistencia(sesion_id)
    except Exception as e:
        log.warning("dias_esperados_update_failed", error=str(e))

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
    asyncio.create_task(_observar_crud("pago", "crear", {"id": str(pago_id), "cliente_id": str(data.cliente_id), "monto": str(data.monto)}))
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


# ============================================================
# AUTOMATISMOS / CRON
# ============================================================

@router.post("/cron/generar-sesiones")
async def generar_sesiones_endpoint(fecha_inicio: Optional[date] = None):
    """Genera sesiones de la semana para todos los grupos."""
    from src.pilates.automatismos import generar_sesiones_semana
    return await generar_sesiones_semana(fecha_inicio)


@router.post("/cron/{tipo}")
async def ejecutar_cron_endpoint(tipo: str):
    """Ejecuta batch automático. Tipos: inicio_semana, inicio_mes, diario."""
    from src.pilates.automatismos import ejecutar_cron
    result = await ejecutar_cron(tipo)
    if result.get("status") == "error":
        raise HTTPException(400, result["detail"])
    return result


@router.get("/alertas")
async def alertas_retencion():
    """Devuelve alertas de retención actuales."""
    from src.pilates.automatismos import detectar_alertas_retencion
    return await detectar_alertas_retencion()


class BizumEntrante(BaseModel):
    telefono: str
    monto: float
    referencia: Optional[str] = None


class OnboardingLinkCreate(BaseModel):
    """Jesús crea un enlace para un lead."""
    nombre_provisional: str
    telefono: str


class OnboardingComplete(BaseModel):
    """El cliente completa el formulario de onboarding."""
    nombre: str
    apellidos: str
    telefono: str
    email: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    nif: Optional[str] = None
    direccion: Optional[str] = None
    lesiones: Optional[str] = None
    patologias: Optional[str] = None
    medicacion: Optional[str] = None
    restricciones: Optional[str] = None
    medico_derivante: Optional[str] = None
    tipo_contrato: str = Field(pattern="^(grupo|individual)$")
    grupo_id: Optional[UUID] = None
    frecuencia_semanal: Optional[int] = None
    precio_sesion: Optional[float] = None
    ciclo_cobro: Optional[str] = None
    consentimiento_datos: bool = True
    consentimiento_marketing: bool = False
    consentimiento_compartir_tenants: bool = False
    acepta_normas: bool = True
    metodo_pago: Optional[str] = None


@router.post("/bizum-entrante")
async def bizum_entrante(data: BizumEntrante):
    """Registra Bizum entrante: busca cliente por teléfono + concilia FIFO."""
    from src.pilates.automatismos import conciliar_bizum_entrante
    result = await conciliar_bizum_entrante(data.telefono, data.monto, data.referencia)
    if result.get("status") == "error":
        raise HTTPException(404, result["detail"])
    return result


# ============================================================
# ONBOARDING SELF-SERVICE
# ============================================================

@router.post("/onboarding/crear-enlace", status_code=201)
async def crear_enlace_onboarding(data: OnboardingLinkCreate):
    """Jesús crea enlace de onboarding para un lead."""
    import secrets
    pool = await _get_pool()
    token = secrets.token_urlsafe(32)

    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO om_onboarding_links (tenant_id, token, nombre_provisional, telefono,
                fecha_expiracion)
            VALUES ($1, $2, $3, $4, now() + interval '7 days')
            RETURNING id, token
        """, TENANT, token, data.nombre_provisional, data.telefono)

    base_url = "https://motor-semantico-omni.fly.dev"
    enlace = f"{base_url}/onboarding/{token}"

    log.info("onboarding_enlace_creado", token=token[:8],
             nombre=data.nombre_provisional)
    return {
        "id": str(row["id"]),
        "token": token,
        "enlace": enlace,
        "wa_mensaje": f"Hola {data.nombre_provisional}! Para inscribirte en Authentic Pilates, "
                      f"rellena esta ficha: {enlace}",
        "expira_en": "7 días",
    }


@router.get("/onboarding/enlaces")
async def listar_enlaces_onboarding(estado: Optional[str] = None):
    """Lista enlaces de onboarding creados (para Jesús)."""
    pool = await _get_pool()
    estado = estado or None
    async with pool.acquire() as conn:
        if estado:
            rows = await conn.fetch("""
                SELECT l.*, c.nombre, c.apellidos
                FROM om_onboarding_links l
                LEFT JOIN om_clientes c ON c.id = l.cliente_id
                WHERE l.tenant_id = $1 AND l.estado = $2
                ORDER BY l.created_at DESC
            """, TENANT, estado)
        else:
            rows = await conn.fetch("""
                SELECT l.*, c.nombre, c.apellidos
                FROM om_onboarding_links l
                LEFT JOIN om_clientes c ON c.id = l.cliente_id
                WHERE l.tenant_id = $1
                ORDER BY l.created_at DESC
            """, TENANT)
    return [_row_to_dict(r) for r in rows]


@router.get("/onboarding/{token}")
async def obtener_onboarding(token: str):
    """Endpoint público: devuelve datos del enlace + grupos disponibles."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        link = await conn.fetchrow("""
            SELECT * FROM om_onboarding_links WHERE token = $1 AND tenant_id = $2
        """, token, TENANT)

        if not link:
            raise HTTPException(404, "Enlace no encontrado")
        if link["estado"] == "completado":
            raise HTTPException(410, "Este enlace ya fue utilizado")
        if link["estado"] == "expirado" or (link["fecha_expiracion"] and
            link["fecha_expiracion"] < datetime.now(link["fecha_expiracion"].tzinfo)):
            raise HTTPException(410, "Este enlace ha expirado")

        grupos = await conn.fetch("""
            SELECT g.id, g.nombre, g.tipo, g.capacidad_max, g.dias_semana,
                   g.precio_mensual, g.frecuencia_semanal,
                   (SELECT count(*) FROM om_contratos c
                    WHERE c.grupo_id = g.id AND c.estado = 'activo') as ocupadas
            FROM om_grupos g
            WHERE g.tenant_id = $1 AND g.estado = 'activo'
            ORDER BY g.nombre
        """, TENANT)

        grupos_disponibles = []
        for g in grupos:
            if g["ocupadas"] < g["capacidad_max"]:
                grupos_disponibles.append({
                    "id": str(g["id"]),
                    "nombre": g["nombre"],
                    "tipo": g["tipo"],
                    "precio_mensual": float(g["precio_mensual"]),
                    "frecuencia_semanal": g["frecuencia_semanal"],
                    "plazas_libres": g["capacidad_max"] - g["ocupadas"],
                    "dias_semana": g["dias_semana"],
                })

    return {
        "nombre_provisional": link["nombre_provisional"],
        "telefono": link["telefono"],
        "grupos_disponibles": grupos_disponibles,
        "precios": {
            "individual_1x": 35.00,
            "individual_2x": 30.00,
            "grupo_estandar": 105.00,
            "grupo_mat": 55.00,
            "grupo_1x": 60.00,
        },
    }


@router.post("/onboarding/{token}/completar")
async def completar_onboarding(token: str, data: OnboardingComplete):
    """Endpoint público: el cliente completa el formulario.
    Crea: om_clientes + om_cliente_tenant + om_datos_clinicos + om_contratos."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        link = await conn.fetchrow("""
            SELECT * FROM om_onboarding_links WHERE token = $1 AND tenant_id = $2
        """, token, TENANT)

        if not link:
            raise HTTPException(404, "Enlace no encontrado")
        if link["estado"] != "pendiente":
            raise HTTPException(410, "Este enlace ya no es válido")

        async with conn.transaction():
            # 1. Crear cliente
            cliente_row = await conn.fetchrow("""
                INSERT INTO om_clientes (nombre, apellidos, telefono, email,
                    fecha_nacimiento, nif, direccion,
                    metodo_pago_habitual,
                    consentimiento_datos, consentimiento_marketing,
                    consentimiento_compartir_tenants, fecha_consentimiento)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, now())
                RETURNING id
            """, data.nombre, data.apellidos, data.telefono, data.email,
                data.fecha_nacimiento, data.nif, data.direccion,
                data.metodo_pago,
                data.consentimiento_datos, data.consentimiento_marketing,
                data.consentimiento_compartir_tenants)

            cliente_id = cliente_row["id"]

            # 2. Crear relación tenant
            await conn.execute("""
                INSERT INTO om_cliente_tenant (cliente_id, tenant_id, estado, fuente_captacion)
                VALUES ($1, $2, 'activo', 'onboarding_selfservice')
            """, cliente_id, TENANT)

            # 3. Datos clínicos (si hay)
            datos_clinicos = []
            if data.lesiones:
                datos_clinicos.append(("restriccion", "Lesiones", data.lesiones))
            if data.patologias:
                datos_clinicos.append(("diagnostico", "Patologías", data.patologias))
            if data.medicacion:
                datos_clinicos.append(("medicacion", "Medicación", data.medicacion))
            if data.restricciones:
                datos_clinicos.append(("restriccion", "Restricciones", data.restricciones))
            if data.medico_derivante:
                datos_clinicos.append(("derivacion_medica", "Derivado por", data.medico_derivante))

            for tipo, titulo, contenido in datos_clinicos:
                await conn.execute("""
                    INSERT INTO om_datos_clinicos (cliente_id, tenant_id, tipo, titulo,
                        contenido, autor, visible_para, consentimiento_registrado, base_legal)
                    VALUES ($1, $2, $3, $4, $5, 'cliente_autoregistro', $6, true, 'consentimiento')
                """, cliente_id, TENANT, tipo, titulo, contenido,
                    [TENANT])

            # 4. Crear contrato
            contrato_id = None
            if data.tipo_contrato == "grupo" and data.grupo_id:
                grupo = await conn.fetchrow("""
                    SELECT capacidad_max FROM om_grupos WHERE id = $1 AND tenant_id = $2
                """, data.grupo_id, TENANT)
                if not grupo:
                    raise HTTPException(404, "Grupo no encontrado")

                ocupados = await conn.fetchval("""
                    SELECT count(*) FROM om_contratos
                    WHERE grupo_id = $1 AND tenant_id = $2 AND estado = 'activo'
                """, data.grupo_id, TENANT)
                if ocupados >= grupo["capacidad_max"]:
                    raise HTTPException(409, "Grupo lleno, selecciona otro")

                precio = await conn.fetchval(
                    "SELECT precio_mensual FROM om_grupos WHERE id = $1", data.grupo_id)

                contrato_row = await conn.fetchrow("""
                    INSERT INTO om_contratos (tenant_id, cliente_id, tipo, grupo_id,
                        precio_mensual, fecha_inicio)
                    VALUES ($1, $2, 'grupo', $3, $4, CURRENT_DATE)
                    RETURNING id
                """, TENANT, cliente_id, data.grupo_id, precio)
                contrato_id = contrato_row["id"]

            elif data.tipo_contrato == "individual":
                precio = data.precio_sesion or 35.00
                contrato_row = await conn.fetchrow("""
                    INSERT INTO om_contratos (tenant_id, cliente_id, tipo,
                        frecuencia_semanal, precio_sesion, ciclo_cobro, fecha_inicio)
                    VALUES ($1, $2, 'individual', $3, $4, $5, CURRENT_DATE)
                    RETURNING id
                """, TENANT, cliente_id,
                    data.frecuencia_semanal or 1, precio,
                    data.ciclo_cobro or 'sesion')
                contrato_id = contrato_row["id"]

            # 5. Marcar enlace como completado
            await conn.execute("""
                UPDATE om_onboarding_links
                SET estado = 'completado', cliente_id = $1,
                    fecha_completado = now()
                WHERE token = $2
            """, cliente_id, token)

            # 6. Activar portal del cliente
            from src.pilates.portal import activar_portal
            portal_token = await activar_portal(cliente_id)

    log.info("onboarding_completado", cliente_id=str(cliente_id),
             nombre=f"{data.nombre} {data.apellidos}",
             tipo=data.tipo_contrato)

    return {
        "status": "ok",
        "cliente_id": str(cliente_id),
        "contrato_id": str(contrato_id) if contrato_id else None,
        "mensaje": f"Bienvenido/a {data.nombre}! Tu inscripción está completa.",
        "portal_url": f"https://motor-semantico-omni.fly.dev/portal/{portal_token}",
    }


# ============================================================
# FACTURACIÓN
# ============================================================

@router.post("/facturas", status_code=201)
async def crear_factura(data: FacturaCreate):
    """Crea factura desde cargos cobrados. Numera secuencialmente. VeriFactu ready."""
    import hashlib
    pool = await _get_pool()

    async with pool.acquire() as conn:
        async with conn.transaction():
            # Verificar cliente
            cliente = await conn.fetchrow(
                "SELECT * FROM om_clientes WHERE id = $1", data.cliente_id)
            if not cliente:
                raise HTTPException(404, "Cliente no encontrado")

            # Obtener cargos
            cargos = await conn.fetch("""
                SELECT * FROM om_cargos
                WHERE id = ANY($1::uuid[]) AND cliente_id = $2 AND tenant_id = $3
            """, data.cargo_ids, data.cliente_id, TENANT)
            if len(cargos) != len(data.cargo_ids):
                raise HTTPException(400, "Algunos cargos no encontrados o no pertenecen al cliente")

            # Calcular totales
            base_total = sum(float(c["base_imponible"]) for c in cargos)
            iva_pct = 21.00  # Pilates = 21% IVA
            iva_total = round(base_total * iva_pct / 100, 2)
            total = round(base_total + iva_total, 2)

            # Siguiente número de factura
            year = date.today().year
            serie = "AP"
            ultimo_num = await conn.fetchval("""
                SELECT MAX(CAST(SPLIT_PART(numero_factura, '-', 3) AS INT))
                FROM om_facturas
                WHERE tenant_id = $1 AND serie = $2
                    AND EXTRACT(YEAR FROM fecha_emision) = $3
            """, TENANT, serie, year)
            siguiente = (ultimo_num or 0) + 1
            numero = f"{serie}-{year}-{siguiente:04d}"

            # Hash VeriFactu (encadenado con factura anterior)
            hash_anterior = await conn.fetchval("""
                SELECT verifactu_hash FROM om_facturas
                WHERE tenant_id = $1 AND serie = $2
                ORDER BY created_at DESC LIMIT 1
            """, TENANT, serie)

            datos_hash = f"{numero}|{date.today()}|{total}|{hash_anterior or 'GENESIS'}"
            verifactu_hash = hashlib.sha256(datos_hash.encode()).hexdigest()

            # Crear factura con snapshot fiscal
            factura_row = await conn.fetchrow("""
                INSERT INTO om_facturas (
                    tenant_id, cliente_id, numero_factura, serie,
                    fecha_emision, fecha_operacion,
                    base_imponible, iva_porcentaje, iva_monto, total,
                    verifactu_hash, verifactu_hash_anterior,
                    cliente_nif, cliente_nombre_fiscal, cliente_direccion
                ) VALUES ($1,$2,$3,$4, CURRENT_DATE,$5, $6,$7,$8,$9, $10,$11, $12,$13,$14)
                RETURNING id
            """, TENANT, data.cliente_id, numero, serie,
                data.fecha_operacion,
                base_total, iva_pct, iva_total, total,
                verifactu_hash, hash_anterior,
                cliente["nif"],
                f"{cliente['nombre']} {cliente['apellidos']}",
                cliente["direccion"])

            factura_id = factura_row["id"]

            # Crear líneas de factura
            for cargo in cargos:
                bi = float(cargo["base_imponible"])
                iva_m = round(bi * iva_pct / 100, 2)
                await conn.execute("""
                    INSERT INTO om_factura_lineas (
                        factura_id, cargo_id, concepto, cantidad,
                        precio_unitario, base_imponible,
                        iva_porcentaje, iva_monto, total
                    ) VALUES ($1,$2,$3,1,$4,$5,$6,$7,$8)
                """, factura_id, cargo["id"],
                    cargo["descripcion"] or cargo["tipo"],
                    bi, bi, iva_pct, iva_m, round(bi + iva_m, 2))

    log.info("factura_creada", numero=numero, total=total, lineas=len(cargos))
    return {"id": str(factura_id), "numero": numero, "total": total, "status": "created"}


@router.get("/facturas")
async def listar_facturas(
    estado: Optional[str] = None,
    cliente_id: Optional[UUID] = None,
    year: Optional[int] = None,
    limit: int = 50
):
    """Lista facturas con filtros."""
    estado = estado or None
    pool = await _get_pool()
    async with pool.acquire() as conn:
        conditions = ["f.tenant_id = $1"]
        params: list = [TENANT]
        idx = 2

        if estado:
            conditions.append(f"f.estado = ${idx}"); params.append(estado); idx += 1
        if cliente_id:
            conditions.append(f"f.cliente_id = ${idx}"); params.append(cliente_id); idx += 1
        if year:
            conditions.append(f"EXTRACT(YEAR FROM f.fecha_emision) = ${idx}"); params.append(year); idx += 1

        where = " AND ".join(conditions)
        rows = await conn.fetch(f"""
            SELECT f.*, cl.nombre, cl.apellidos
            FROM om_facturas f
            JOIN om_clientes cl ON cl.id = f.cliente_id
            WHERE {where}
            ORDER BY f.fecha_emision DESC, f.numero_factura DESC
            LIMIT ${idx}
        """, *params, limit)
    return [_row_to_dict(r) for r in rows]


@router.get("/facturas/paquete-gestor")
async def paquete_gestor(trimestre: Optional[int] = None, year: Optional[int] = None):
    """Resumen trimestral para la gestoría."""
    import calendar
    year = year or date.today().year
    if trimestre is None:
        trimestre = (date.today().month - 1) // 3 + 1

    mes_inicio = (trimestre - 1) * 3 + 1
    mes_fin = trimestre * 3
    fecha_inicio = date(year, mes_inicio, 1)
    fecha_fin = date(year, mes_fin, calendar.monthrange(year, mes_fin)[1])

    pool = await _get_pool()
    async with pool.acquire() as conn:
        # Facturas emitidas
        facturas = await conn.fetch("""
            SELECT * FROM om_facturas
            WHERE tenant_id = $1 AND fecha_emision >= $2 AND fecha_emision <= $3
                AND estado = 'emitida'
            ORDER BY numero_factura
        """, TENANT, fecha_inicio, fecha_fin)

        iva_repercutido = sum(float(f["iva_monto"]) for f in facturas)
        base_ingresos = sum(float(f["base_imponible"]) for f in facturas)
        total_ingresos = sum(float(f["total"]) for f in facturas)

        # Gastos del trimestre
        gastos = await conn.fetch("""
            SELECT * FROM om_gastos
            WHERE tenant_id = $1 AND fecha_gasto >= $2 AND fecha_gasto <= $3
            ORDER BY fecha_gasto
        """, TENANT, fecha_inicio, fecha_fin)

        iva_soportado = sum(float(g["iva_soportado"] or 0) for g in gastos)
        base_gastos = sum(float(g["base_imponible"]) for g in gastos)
        total_gastos = sum(float(g["total"]) for g in gastos)

        # Gastos por categoría
        gastos_por_cat: dict = {}
        for g in gastos:
            cat = g["categoria"]
            gastos_por_cat[cat] = gastos_por_cat.get(cat, 0) + float(g["total"])

    return {
        "trimestre": f"Q{trimestre} {year}",
        "periodo": f"{fecha_inicio} a {fecha_fin}",
        "ingresos": {
            "facturas_emitidas": len(facturas),
            "base_imponible": round(base_ingresos, 2),
            "iva_repercutido": round(iva_repercutido, 2),
            "total": round(total_ingresos, 2),
        },
        "gastos": {
            "total_gastos": len(gastos),
            "base_imponible": round(base_gastos, 2),
            "iva_soportado": round(iva_soportado, 2),
            "total": round(total_gastos, 2),
            "por_categoria": gastos_por_cat,
        },
        "iva_liquidar": round(iva_repercutido - iva_soportado, 2),
        "resultado_neto": round(base_ingresos - base_gastos, 2),
    }


@router.get("/facturas/{factura_id}")
async def obtener_factura(factura_id: UUID):
    """Detalle de factura con líneas."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        factura = await conn.fetchrow(
            "SELECT * FROM om_facturas WHERE id = $1 AND tenant_id = $2",
            factura_id, TENANT)
        if not factura:
            raise HTTPException(404, "Factura no encontrada")

        lineas = await conn.fetch("""
            SELECT * FROM om_factura_lineas WHERE factura_id = $1 ORDER BY created_at
        """, factura_id)

        cliente = await conn.fetchrow(
            "SELECT * FROM om_clientes WHERE id = $1", factura["cliente_id"])

    return {
        **_row_to_dict(factura),
        "lineas": [_row_to_dict(l) for l in lineas],
        "cliente": _row_to_dict(cliente) if cliente else None,
    }


@router.post("/facturas/{factura_id}/anular")
async def anular_factura(factura_id: UUID, data: FacturaAnular):
    """Anula factura. No se borra — se marca como anulada (VeriFactu)."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute("""
            UPDATE om_facturas SET estado = 'anulada'
            WHERE id = $1 AND tenant_id = $2 AND estado = 'emitida'
        """, factura_id, TENANT)
        if result == "UPDATE 0":
            raise HTTPException(404, "Factura no encontrada o ya anulada")

    log.info("factura_anulada", id=str(factura_id), motivo=data.motivo)
    return {"status": "anulada"}


@router.post("/facturas/{factura_id}/pdf")
async def generar_pdf_factura(factura_id: UUID):
    """Genera PDF/HTML de la factura."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        factura = await conn.fetchrow(
            "SELECT * FROM om_facturas WHERE id = $1 AND tenant_id = $2",
            factura_id, TENANT)
        if not factura:
            raise HTTPException(404, "Factura no encontrada")

        lineas = await conn.fetch(
            "SELECT * FROM om_factura_lineas WHERE factura_id = $1", factura_id)

    # Generar HTML de la factura
    html = _generar_html_factura(factura, lineas)

    # Intentar generar PDF con weasyprint
    try:
        from weasyprint import HTML as WeasyHTML
        pdf_filename = f"factura_{factura['numero_factura'].replace('-','_')}.pdf"
        pdf_path = f"/tmp/{pdf_filename}"
        WeasyHTML(string=html).write_pdf(pdf_path)

        # Guardar path en DB
        async with pool.acquire() as conn2:
            await conn2.execute(
                "UPDATE om_facturas SET pdf_path = $1 WHERE id = $2",
                pdf_path, factura_id)

        return {"status": "ok", "pdf_path": pdf_path, "filename": pdf_filename}
    except ImportError:
        # Sin weasyprint: devolver HTML para window.print() del navegador
        return {"status": "html_only", "html": html,
                "nota": "Instalar weasyprint para PDF nativo"}


@router.post("/facturas/auto-facturar")
async def auto_facturar():
    """Lista candidatos para facturación automática."""
    pool = await _get_pool()

    async with pool.acquire() as conn:
        clientes_con_cargos = await conn.fetch("""
            SELECT DISTINCT c.cliente_id, cl.nombre, cl.apellidos
            FROM om_cargos c
            JOIN om_clientes cl ON cl.id = c.cliente_id
            LEFT JOIN om_factura_lineas fl ON fl.cargo_id = c.id
            WHERE c.tenant_id = $1 AND c.estado = 'cobrado' AND fl.id IS NULL
            GROUP BY c.cliente_id, cl.nombre, cl.apellidos
        """, TENANT)

    return {
        "status": "ok",
        "clientes_con_cargos_sin_factura": len(clientes_con_cargos),
        "clientes": [{"id": str(c["cliente_id"]),
                       "nombre": f"{c['nombre']} {c['apellidos']}"}
                      for c in clientes_con_cargos],
        "nota": "Auto-facturación pendiente de campo preferencia_facturacion en om_clientes"
    }


# ============================================================
# PORTAL CLIENTE
# ============================================================

@router.post("/portal/generar-todos")
async def generar_portales():
    """Genera portales para todos los clientes activos que no tienen uno."""
    from src.pilates.portal import activar_portal
    pool = await _get_pool()
    generados = 0

    async with pool.acquire() as conn:
        clientes = await conn.fetch("""
            SELECT ct.cliente_id FROM om_cliente_tenant ct
            LEFT JOIN om_onboarding_links l ON l.cliente_id = ct.cliente_id AND l.es_portal = true
            WHERE ct.tenant_id = $1 AND ct.estado = 'activo' AND l.id IS NULL
        """, TENANT)

    for c in clientes:
        await activar_portal(c["cliente_id"])
        generados += 1

    return {"status": "ok", "portales_generados": generados}


# ============================================================
# WHATSAPP
# ============================================================

@router.get("/webhook/whatsapp")
async def webhook_verify(request: Request):
    """Verificación del webhook de WhatsApp (GET).
    Meta envía esto al configurar el webhook.
    """
    from src.pilates.whatsapp import WA_VERIFY_TOKEN
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == WA_VERIFY_TOKEN:
        log.info("wa_webhook_verificado")
        from starlette.responses import PlainTextResponse
        return PlainTextResponse(challenge)
    raise HTTPException(403, "Token inválido")


@router.post("/webhook/whatsapp")
async def webhook_recibir(request: Request):
    """Recibe mensajes de WhatsApp (POST webhook). B2.9: emite señales al bus."""
    body = await request.json()
    from src.pilates.whatsapp import procesar_webhook
    result = await procesar_webhook(body)

    # B2.9 Reactivo: emitir señales al bus tras procesar el mensaje
    if result.get("mensaje_guardado"):
        asyncio.create_task(_wa_reactivo(result))

    return {"status": "ok", **result}


async def _wa_reactivo(result: dict):
    """Fire-and-forget: WA webhook → señales al bus."""
    try:
        from src.pilates.voz_reactivo import procesar_mensaje_wa_reactivo
        await procesar_mensaje_wa_reactivo(
            telefono=result.get("telefono", ""),
            mensaje_texto=result.get("contenido", ""),
            mensaje_id=result.get("mensaje_id"),
            cliente_id=result.get("cliente_id"),
            es_cliente_existente=result.get("es_cliente", False),
            intencion=result.get("intencion", "otro"),
        )
    except Exception as e:
        import structlog
        structlog.get_logger().warning("wa_reactivo_error", error=str(e))


@router.get("/whatsapp/mensajes")
async def listar_mensajes_wa(
    direccion: Optional[str] = None,
    cliente_id: Optional[UUID] = None,
    no_leidos: bool = False,
    limit: int = 50
):
    """Lista mensajes WA. Para el panel del Modo Estudio."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        conditions = ["m.tenant_id = $1"]
        params = [TENANT]
        idx = 2

        if direccion:
            conditions.append(f"m.direccion = ${idx}"); params.append(direccion); idx += 1
        if cliente_id:
            conditions.append(f"m.cliente_id = ${idx}"); params.append(cliente_id); idx += 1
        if no_leidos:
            conditions.append("m.leido = false")

        where = " AND ".join(conditions)
        rows = await conn.fetch(f"""
            SELECT m.*, c.nombre, c.apellidos
            FROM om_mensajes_wa m
            LEFT JOIN om_clientes c ON c.id = m.cliente_id
            WHERE {where}
            ORDER BY m.created_at DESC
            LIMIT ${idx}
        """, *params, limit)
    return [_row_to_dict(r) for r in rows]


@router.post("/whatsapp/enviar")
async def enviar_mensaje_wa(data: dict):
    """Envía mensaje de texto por WhatsApp."""
    from src.pilates.whatsapp import enviar_texto
    telefono = data.get("telefono")
    mensaje = data.get("mensaje")
    cliente_id = data.get("cliente_id")
    if not telefono or not mensaje:
        raise HTTPException(400, "telefono y mensaje requeridos")
    result = await enviar_texto(telefono, mensaje, cliente_id)
    if result["status"] == "error":
        raise HTTPException(503, result["detail"])
    return result


@router.post("/whatsapp/marcar-leido/{mensaje_id}")
async def marcar_leido(mensaje_id: UUID):
    """Marca mensaje como leído."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE om_mensajes_wa SET leido = true WHERE id = $1", mensaje_id)
    return {"status": "ok"}


@router.post("/whatsapp/confirmar-manana")
async def confirmar_sesiones_manana():
    """Envía confirmaciones pre-sesión para mañana."""
    from src.pilates.whatsapp import enviar_confirmaciones_manana
    return await enviar_confirmaciones_manana()


@router.post("/whatsapp/responder-lead")
async def responder_lead(data: dict):
    """Respuesta automática a lead nuevo: precios + enlace onboarding."""
    from src.pilates.whatsapp import respuesta_lead_automatico
    telefono = data.get("telefono")
    nombre = data.get("nombre", "")
    if not telefono:
        raise HTTPException(400, "telefono requerido")
    return await respuesta_lead_automatico(telefono, nombre)


@router.post("/whatsapp/respuesta-sugerida")
async def respuesta_sugerida_wa(data: dict):
    """Genera respuesta sugerida para un mensaje WA entrante."""
    from src.pilates.wa_respuestas import generar_respuesta
    intencion = data.get("intencion", "otro")
    cliente_id = UUID(data["cliente_id"]) if data.get("cliente_id") else None
    contenido = data.get("contenido_original", "")
    result = await generar_respuesta(intencion, cliente_id, contenido)
    return result


@router.post("/whatsapp/procesar-boton")
async def procesar_boton_wa(data: dict):
    """Procesa respuesta a botón interactivo (confirmación pre-sesión)."""
    from src.pilates.wa_respuestas import procesar_respuesta_boton
    from src.pilates.whatsapp import enviar_texto
    cliente_id = UUID(data["cliente_id"])
    boton_id = data.get("boton_id", "")
    result = await procesar_respuesta_boton(cliente_id, boton_id)
    # Auto-enviar respuesta si hay mensaje
    if result.get("mensaje"):
        pool = await _get_pool()
        async with pool.acquire() as conn:
            tel = await conn.fetchval(
                "SELECT telefono FROM om_clientes WHERE id = $1", cliente_id)
        if tel:
            await enviar_texto(tel, result["mensaje"], cliente_id)
    return result


# ============================================================
# MODO PROFUNDO — BRIEFING + DASHBOARD + ACD
# ============================================================

@router.get("/briefing")
async def obtener_briefing(semana: Optional[date] = None):
    """Genera briefing semanal bajo demanda."""
    from src.pilates.briefing import generar_briefing
    return await generar_briefing(semana)


@router.post("/briefing/enviar-wa")
async def enviar_briefing_wa():
    """Genera briefing y lo envía por WhatsApp a Jesús."""
    from src.pilates.briefing import generar_briefing
    briefing = await generar_briefing()

    import os
    tel_jesus = os.getenv("JESUS_TELEFONO", "")
    if tel_jesus:
        from src.pilates.whatsapp import enviar_texto
        await enviar_texto(tel_jesus, briefing["texto_wa"])
        return {"status": "enviado", "texto": briefing["texto_wa"]}
    return {"status": "generado_sin_envio", "texto": briefing["texto_wa"],
            "nota": "Configurar JESUS_TELEFONO en fly.io secrets"}


@router.post("/acd/diagnosticar")
async def diagnosticar_negocio():
    """Ejecuta diagnóstico ACD del negocio con datos reales (~$0.01)."""
    from src.pilates.briefing import generar_diagnostico_acd_tenant
    return await generar_diagnostico_acd_tenant()


@router.get("/acd/historial")
async def historial_acd(limit: int = 10):
    """Historial de diagnósticos ACD del negocio."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, trigger, estado, estado_tipo, lentes, gap,
                   prescripcion, resultado, coste_usd, created_at
            FROM om_diagnosticos_tenant
            WHERE tenant_id = $1
            ORDER BY created_at DESC
            LIMIT $2
        """, TENANT, limit)
    return [_row_to_dict(r) for r in rows]


@router.get("/dashboard")
async def dashboard_profundo():
    """Dashboard completo Modo Profundo: briefing + ACD + tendencias."""
    from src.pilates.briefing import generar_briefing
    briefing = await generar_briefing()

    pool = await _get_pool()
    async with pool.acquire() as conn:
        grupos = await conn.fetch("""
            SELECT g.nombre, g.tipo, g.capacidad_max, g.precio_mensual,
                (SELECT count(*) FROM om_contratos c
                 WHERE c.grupo_id = g.id AND c.estado = 'activo') as ocupadas
            FROM om_grupos g
            WHERE g.tenant_id = $1 AND g.estado = 'activo'
            ORDER BY g.nombre
        """, TENANT)

        ingresos_mensuales = await conn.fetch("""
            SELECT date_trunc('month', fecha_pago)::date as mes,
                   SUM(monto) as total
            FROM om_pagos
            WHERE tenant_id = $1 AND fecha_pago >= CURRENT_DATE - interval '6 months'
            GROUP BY mes ORDER BY mes
        """, TENANT)

        depuraciones = await conn.fetch("""
            SELECT * FROM om_depuracion
            WHERE tenant_id = $1 AND estado IN ('propuesta', 'aprobada')
            ORDER BY created_at DESC LIMIT 5
        """, TENANT)

    briefing["grupos_detalle"] = [_row_to_dict(g) for g in grupos]
    briefing["ingresos_mensuales"] = [
        {"mes": str(r["mes"]), "total": float(r["total"])} for r in ingresos_mensuales
    ]
    briefing["depuraciones"] = [_row_to_dict(d) for d in depuraciones]

    # Readiness de replicación
    try:
        briefing["readiness"] = await _calcular_readiness()
    except Exception:
        briefing["readiness"] = None

    return briefing


# ============================================================
# SÉQUITO DE ASESORES
# ============================================================

@router.post("/consejo")
async def convocar_consejo_endpoint(data: ConsejoRequest):
    """Convoca el Consejo de Asesores. Coste: ~$0.05-0.50 según profundidad."""
    from src.pilates.sequito import convocar_consejo
    sesion = await convocar_consejo(
        pregunta=data.pregunta,
        profundidad=data.profundidad,
        ints_forzadas=data.ints_forzadas,
    )
    return {
        "status": "ok",
        "estado_acd": sesion.estado_acd_pre,
        "asesores_convocados": len(sesion.asesores),
        "respuestas": [{
            "int_id": r.int_id, "nombre": r.nombre,
            "P": r.pensamiento, "R": r.razonamiento,
            "respuesta": r.respuesta,
        } for r in sesion.asesores],
        "sintesis": sesion.sintesis,
        "puntos_ciegos": sesion.puntos_ciegos,
        "prescripcion_acd": sesion.prescripcion,
        "coste_usd": sesion.coste_total,
        "tiempo_s": sesion.tiempo_total,
    }


@router.get("/consejo/historial")
async def historial_consejo(limit: int = 10):
    """Historial de sesiones del Consejo."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, pregunta, profundidad, estado_acd_pre,
                   inteligencias_convocadas, sintesis,
                   puntos_ciegos_cruzados, decision_ternaria,
                   coste_api, tiempo_ejecucion_s, created_at
            FROM om_sesiones_consejo
            WHERE tenant_id = $1
            ORDER BY created_at DESC LIMIT $2
        """, TENANT, limit)
    return [_row_to_dict(r) for r in rows]


@router.get("/consejo/{sesion_id}")
async def detalle_consejo(sesion_id: UUID):
    """Detalle completo de una sesión del Consejo."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT * FROM om_sesiones_consejo WHERE id = $1 AND tenant_id = $2
        """, sesion_id, TENANT)
        if not row:
            raise HTTPException(404, "Sesión no encontrada")
    return _row_to_dict(row)


@router.post("/consejo/{sesion_id}/decision")
async def registrar_decision(sesion_id: UUID, data: DecisionTernaria):
    """Registra decisión ternaria post-consejo: cierre/inerte/tóxico."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute("""
            UPDATE om_sesiones_consejo
            SET decision_ternaria = $1, decision_confianza = $2,
                decision_razon = $3, decision_fecha = CURRENT_DATE
            WHERE id = $4 AND tenant_id = $5
        """, data.decision, data.confianza, data.razon, sesion_id, TENANT)
        if result == "UPDATE 0":
            raise HTTPException(404, "Sesión no encontrada")
    return {"status": "ok"}


@router.get("/asesores")
async def listar_asesores():
    """Lista los 24 asesores disponibles."""
    from src.pilates.sequito import ASESORES
    return [{"id": k, **v} for k, v in ASESORES.items()]


# ============================================================
# ADN DEL NEGOCIO (F5 Identidad)
# ============================================================

@router.get("/adn")
async def listar_adn(categoria: Optional[str] = None, activo: bool = True):
    """Lista principios ADN. Filtro por categoría y estado activo."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        conditions = ["tenant_id = $1"]
        params = [TENANT]
        idx = 2
        if activo:
            conditions.append("activo = true")
        if categoria:
            conditions.append(f"categoria = ${idx}"); params.append(categoria); idx += 1
        where = " AND ".join(conditions)
        rows = await conn.fetch(f"""
            SELECT * FROM om_adn WHERE {where} ORDER BY categoria, titulo
        """, *params)
    return [_row_to_dict(r) for r in rows]


@router.get("/adn/{adn_id}")
async def obtener_adn(adn_id: UUID):
    pool = await _get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM om_adn WHERE id = $1 AND tenant_id = $2", adn_id, TENANT)
        if not row:
            raise HTTPException(404, "Principio ADN no encontrado")
    return _row_to_dict(row)


@router.post("/adn", status_code=201)
async def crear_adn(data: ADNCreate):
    """Crea un principio ADN del negocio."""
    import json
    pool = await _get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO om_adn (tenant_id, categoria, titulo, descripcion,
                ejemplos, contra_ejemplos, funcion_l07, lente)
            VALUES ($1,$2,$3,$4,$5::jsonb,$6::jsonb,$7,$8) RETURNING id
        """, TENANT, data.categoria, data.titulo, data.descripcion,
            json.dumps(data.ejemplos) if data.ejemplos else None,
            json.dumps(data.contra_ejemplos) if data.contra_ejemplos else None,
            data.funcion_l07, data.lente)
    log.info("adn_creado", titulo=data.titulo, categoria=data.categoria)
    return {"id": str(row["id"]), "status": "created"}


@router.patch("/adn/{adn_id}")
async def actualizar_adn(adn_id: UUID, data: ADNUpdate):
    import json
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(400, "Nada que actualizar")
    pool = await _get_pool()
    for k in ("ejemplos", "contra_ejemplos"):
        if k in updates and isinstance(updates[k], list):
            updates[k] = json.dumps(updates[k])
    set_clauses = ", ".join(f"{k} = ${i+2}" for i, k in enumerate(updates.keys()))
    values = [adn_id] + list(updates.values())
    async with pool.acquire() as conn:
        await conn.execute(
            f"UPDATE om_adn SET {set_clauses}, version = version + 1, fecha_modificacion = CURRENT_DATE WHERE id = $1 AND tenant_id = '{TENANT}'",
            *values)
    return {"status": "updated"}


@router.delete("/adn/{adn_id}")
async def desactivar_adn(adn_id: UUID):
    """No borra — marca como inactivo (historial)."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE om_adn SET activo = false WHERE id = $1 AND tenant_id = $2",
            adn_id, TENANT)
    return {"status": "desactivado"}


# ============================================================
# PROCESOS DOCUMENTADOS (F7 Replicación)
# ============================================================

@router.get("/procesos")
async def listar_procesos(area: Optional[str] = None):
    pool = await _get_pool()
    async with pool.acquire() as conn:
        if area:
            rows = await conn.fetch("""
                SELECT * FROM om_procesos WHERE tenant_id = $1 AND area = $2 ORDER BY area, titulo
            """, TENANT, area)
        else:
            rows = await conn.fetch("""
                SELECT * FROM om_procesos WHERE tenant_id = $1 ORDER BY area, titulo
            """, TENANT)
    return [_row_to_dict(r) for r in rows]


@router.get("/procesos/{proceso_id}")
async def obtener_proceso(proceso_id: UUID):
    pool = await _get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM om_procesos WHERE id = $1 AND tenant_id = $2", proceso_id, TENANT)
        if not row:
            raise HTTPException(404, "Proceso no encontrado")
        await conn.execute("""
            UPDATE om_procesos SET veces_consultado = veces_consultado + 1, ultima_consulta = now()
            WHERE id = $1
        """, proceso_id)
    return _row_to_dict(row)


@router.post("/procesos", status_code=201)
async def crear_proceso(data: ProcesoCreate):
    import json
    pool = await _get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO om_procesos (tenant_id, area, titulo, descripcion, pasos,
                notas, funcion_l07, vinculado_a_adn, documentado_por)
            VALUES ($1,$2,$3,$4,$5::jsonb,$6,$7,$8,'Jesus') RETURNING id
        """, TENANT, data.area, data.titulo, data.descripcion,
            json.dumps(data.pasos), data.notas, data.funcion_l07, data.vinculado_a_adn)
    log.info("proceso_creado", titulo=data.titulo, area=data.area)
    return {"id": str(row["id"]), "status": "created"}


@router.patch("/procesos/{proceso_id}")
async def actualizar_proceso(proceso_id: UUID, data: dict):
    """Actualiza proceso. Incrementa versión."""
    import json
    pool = await _get_pool()
    async with pool.acquire() as conn:
        actual = await conn.fetchrow(
            "SELECT * FROM om_procesos WHERE id = $1 AND tenant_id = $2", proceso_id, TENANT)
        if not actual:
            raise HTTPException(404, "Proceso no encontrado")
        titulo = data.get("titulo", actual["titulo"])
        descripcion = data.get("descripcion", actual["descripcion"])
        pasos = json.dumps(data["pasos"]) if "pasos" in data else actual["pasos"]
        notas = data.get("notas", actual["notas"])
        await conn.execute("""
            UPDATE om_procesos SET titulo=$1, descripcion=$2, pasos=$3::jsonb, notas=$4,
                version = version + 1, ultima_revision = CURRENT_DATE
            WHERE id = $5
        """, titulo, descripcion, pasos if isinstance(pasos, str) else json.dumps(pasos),
            notas, proceso_id)
    return {"status": "updated"}


# ============================================================
# CONOCIMIENTO EMERGENTE (F2 Sentido)
# ============================================================

@router.get("/conocimiento")
async def listar_conocimiento(tipo: Optional[str] = None, confianza: Optional[str] = None):
    pool = await _get_pool()
    async with pool.acquire() as conn:
        conditions = ["tenant_id = $1"]
        params = [TENANT]
        idx = 2
        if tipo:
            conditions.append(f"tipo = ${idx}"); params.append(tipo); idx += 1
        if confianza:
            conditions.append(f"confianza = ${idx}"); params.append(confianza); idx += 1
        where = " AND ".join(conditions)
        rows = await conn.fetch(f"""
            SELECT * FROM om_conocimiento WHERE {where} ORDER BY fecha_descubrimiento DESC
        """, *params)
    return [_row_to_dict(r) for r in rows]


@router.post("/conocimiento", status_code=201)
async def crear_conocimiento(data: ConocimientoCreate):
    import json
    pool = await _get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO om_conocimiento (tenant_id, tipo, titulo, descripcion,
                evidencia, confianza, origen)
            VALUES ($1,$2,$3,$4,$5::jsonb,$6,$7) RETURNING id
        """, TENANT, data.tipo, data.titulo, data.descripcion,
            json.dumps(data.evidencia) if data.evidencia else None,
            data.confianza, data.origen)
    log.info("conocimiento_creado", titulo=data.titulo, tipo=data.tipo)
    return {"id": str(row["id"]), "status": "created"}


@router.post("/conocimiento/{conocimiento_id}/promover-adn")
async def promover_a_adn(conocimiento_id: UUID, data: ADNCreate):
    """Promueve conocimiento consolidado a principio ADN.

    F2→F5: lo que se aprende (conocimiento) sube a lo que se es (ADN).
    """
    pool = await _get_pool()
    import json
    async with pool.acquire() as conn:
        conoc = await conn.fetchrow(
            "SELECT * FROM om_conocimiento WHERE id = $1 AND tenant_id = $2",
            conocimiento_id, TENANT)
        if not conoc:
            raise HTTPException(404, "Conocimiento no encontrado")

        adn_row = await conn.fetchrow("""
            INSERT INTO om_adn (tenant_id, categoria, titulo, descripcion,
                ejemplos, contra_ejemplos, funcion_l07, lente)
            VALUES ($1,$2,$3,$4,$5::jsonb,$6::jsonb,$7,$8) RETURNING id
        """, TENANT, data.categoria, data.titulo, data.descripcion,
            json.dumps(data.ejemplos) if data.ejemplos else None,
            json.dumps(data.contra_ejemplos) if data.contra_ejemplos else None,
            data.funcion_l07, data.lente)

        await conn.execute("""
            UPDATE om_conocimiento SET promovido_a_adn = $1, confianza = 'consolidado'
            WHERE id = $2
        """, adn_row["id"], conocimiento_id)

    log.info("conocimiento_promovido", conocimiento=str(conocimiento_id), adn=str(adn_row["id"]))
    return {"status": "promovido", "adn_id": str(adn_row["id"])}


# ============================================================
# TENSIONES (F6 Adaptación)
# ============================================================

@router.get("/tensiones")
async def listar_tensiones(estado: Optional[str] = "activa"):
    pool = await _get_pool()
    estado = estado or None
    async with pool.acquire() as conn:
        if estado:
            rows = await conn.fetch("""
                SELECT * FROM om_tensiones WHERE tenant_id = $1 AND estado = $2
                ORDER BY severidad DESC, fecha_inicio DESC
            """, TENANT, estado)
        else:
            rows = await conn.fetch("""
                SELECT * FROM om_tensiones WHERE tenant_id = $1 ORDER BY fecha_inicio DESC
            """, TENANT)
    return [_row_to_dict(r) for r in rows]


@router.post("/tensiones", status_code=201)
async def crear_tension(data: TensionCreate):
    pool = await _get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO om_tensiones (tenant_id, tipo, descripcion, funciones_afectadas,
                severidad, duracion_estimada_dias, detectada_por)
            VALUES ($1,$2,$3,$4,$5,$6,'manual') RETURNING id
        """, TENANT, data.tipo, data.descripcion, data.funciones_afectadas,
            data.severidad, data.duracion_estimada_dias)
    log.info("tension_creada", tipo=data.tipo, severidad=data.severidad)
    return {"id": str(row["id"]), "status": "created"}


@router.patch("/tensiones/{tension_id}")
async def actualizar_tension(tension_id: UUID, data: dict):
    """Actualiza tensión: resolver, marcar crónica, etc."""
    pool = await _get_pool()
    estado = data.get("estado")
    async with pool.acquire() as conn:
        if estado:
            if estado == "resuelta":
                await conn.execute("""
                    UPDATE om_tensiones SET estado = $1, fecha_fin = CURRENT_DATE
                    WHERE id = $2 AND tenant_id = $3
                """, estado, tension_id, TENANT)
            else:
                await conn.execute("""
                    UPDATE om_tensiones SET estado = $1 WHERE id = $2 AND tenant_id = $3
                """, estado, tension_id, TENANT)
    return {"status": "updated"}


# ============================================================
# DEPURACIÓN (F3 — "deja de hacer esto")
# ============================================================

@router.get("/depuracion")
async def listar_depuracion(estado: Optional[str] = None):
    pool = await _get_pool()
    estado = estado or None
    async with pool.acquire() as conn:
        if estado:
            rows = await conn.fetch("""
                SELECT d.*, dt.estado as diagnostico_estado
                FROM om_depuracion d
                LEFT JOIN om_diagnosticos_tenant dt ON dt.id = d.diagnostico_id
                WHERE d.tenant_id = $1 AND d.estado = $2
                ORDER BY d.created_at DESC
            """, TENANT, estado)
        else:
            rows = await conn.fetch("""
                SELECT d.*, dt.estado as diagnostico_estado
                FROM om_depuracion d
                LEFT JOIN om_diagnosticos_tenant dt ON dt.id = d.diagnostico_id
                WHERE d.tenant_id = $1
                ORDER BY d.created_at DESC
            """, TENANT)
    return [_row_to_dict(r) for r in rows]


@router.post("/depuracion", status_code=201)
async def crear_depuracion(data: DepuracionCreate):
    pool = await _get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO om_depuracion (tenant_id, tipo, descripcion, impacto_estimado,
                funcion_l07, lente, origen, diagnostico_id)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8) RETURNING id
        """, TENANT, data.tipo, data.descripcion, data.impacto_estimado,
            data.funcion_l07, data.lente, data.origen, data.diagnostico_id)
    log.info("depuracion_creada", tipo=data.tipo, descripcion=data.descripcion[:50])
    return {"id": str(row["id"]), "status": "created"}


@router.patch("/depuracion/{depuracion_id}")
async def actualizar_depuracion(depuracion_id: UUID, data: dict):
    """Cambiar estado: propuesta → aprobada → ejecutada / descartada."""
    pool = await _get_pool()
    estado = data.get("estado")
    resultado = data.get("resultado")
    async with pool.acquire() as conn:
        updates = []
        params = [depuracion_id]
        idx = 2
        if estado:
            updates.append(f"estado = ${idx}"); params.append(estado); idx += 1
            if estado == "aprobada":
                updates.append("fecha_decision = CURRENT_DATE")
            elif estado == "ejecutada":
                updates.append("fecha_ejecucion = CURRENT_DATE")
        if resultado:
            updates.append(f"resultado = ${idx}"); params.append(resultado); idx += 1
        if not updates:
            raise HTTPException(400, "Nada que actualizar")
        set_clause = ", ".join(updates)
        await conn.execute(
            f"UPDATE om_depuracion SET {set_clause} WHERE id = $1 AND tenant_id = '{TENANT}'",
            *params)
    return {"status": "updated"}


# ============================================================
# READINESS DE REPLICACIÓN
# ============================================================

async def _calcular_readiness():
    """Calcula readiness de replicación del negocio (función reutilizable)."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        procesos = await conn.fetchval(
            "SELECT count(*) FROM om_procesos WHERE tenant_id = $1", TENANT)
        areas_total = 6
        areas_cubiertas = await conn.fetchval("""
            SELECT count(DISTINCT area) FROM om_procesos WHERE tenant_id = $1
        """, TENANT)
        pct_procesos = round(min(areas_cubiertas / areas_total, 1) * 100, 0)

        adn_total = await conn.fetchval(
            "SELECT count(*) FROM om_adn WHERE tenant_id = $1 AND activo = true", TENANT)
        cats_cubiertas = await conn.fetchval("""
            SELECT count(DISTINCT categoria) FROM om_adn WHERE tenant_id = $1 AND activo = true
        """, TENANT)
        cats_total = 6
        pct_adn = round(min(cats_cubiertas / cats_total, 1) * 100, 0)

        onboarding = await conn.fetchrow("""
            SELECT grado_absorcion FROM om_onboarding_instructor
            WHERE tenant_id = $1 ORDER BY created_at DESC LIMIT 1
        """, TENANT)
        grado_absorcion = float(onboarding["grado_absorcion"]) / 10 if onboarding and onboarding["grado_absorcion"] else 0

        total_conoc = await conn.fetchval(
            "SELECT count(*) FROM om_conocimiento WHERE tenant_id = $1", TENANT)
        consolidado = await conn.fetchval(
            "SELECT count(*) FROM om_conocimiento WHERE tenant_id = $1 AND confianza = 'consolidado'", TENANT)
        pct_conocimiento = round(consolidado / max(total_conoc, 1) * 100, 0)

        depuraciones_ejecutadas = await conn.fetchval(
            "SELECT count(*) FROM om_depuracion WHERE tenant_id = $1 AND estado = 'ejecutada'", TENANT)
        depuraciones_propuestas = await conn.fetchval(
            "SELECT count(*) FROM om_depuracion WHERE tenant_id = $1", TENANT)

    readiness = round(
        (pct_procesos / 100) * (pct_adn / 100) * max(grado_absorcion, 0.1) * max(pct_conocimiento / 100, 0.1) * 100, 1
    )

    return {
        "readiness_pct": readiness,
        "componentes": {
            "procesos": {"pct": pct_procesos, "total": procesos, "areas_cubiertas": areas_cubiertas, "areas_total": areas_total},
            "adn": {"pct": pct_adn, "total": adn_total, "categorias_cubiertas": cats_cubiertas, "categorias_total": cats_total},
            "absorcion_instructor": {"valor": round(grado_absorcion * 100, 0), "tiene_onboarding": onboarding is not None},
            "conocimiento": {"pct": pct_conocimiento, "total": total_conoc, "consolidado": consolidado},
            "depuracion": {"ejecutadas": depuraciones_ejecutadas, "propuestas": depuraciones_propuestas},
        },
        "prescripcion_c": "Documentar procesos y codificar ADN para subir Continuidad (C)" if readiness < 50
            else "Readiness aceptable — foco en absorción instructor" if readiness < 80
            else "Readiness alto — listo para replicar",
    }


@router.get("/readiness")
async def readiness_replicacion():
    """Calcula readiness de replicación del negocio."""
    return await _calcular_readiness()


# ============================================================
# BLOQUE VOZ
# ============================================================


@router.post("/voz/generar-propuestas")
async def generar_propuestas_voz():
    """Genera propuestas de comunicación basadas en datos internos."""
    from src.pilates.voz import generar_propuestas
    propuestas = await generar_propuestas()
    return {"status": "ok", "propuestas_generadas": len(propuestas), "propuestas": propuestas}


@router.get("/voz/propuestas")
async def listar_propuestas_voz(estado: Optional[str] = "pendiente", canal: Optional[str] = None):
    """Lista propuestas de Voz."""
    pool = await _get_pool()
    estado = estado or None
    async with pool.acquire() as conn:
        conditions = ["tenant_id = $1"]
        params = [TENANT]
        idx = 2
        if estado:
            conditions.append(f"estado = ${idx}"); params.append(estado); idx += 1
        if canal:
            conditions.append(f"canal = ${idx}"); params.append(canal); idx += 1
        where = " AND ".join(conditions)
        rows = await conn.fetch(f"""
            SELECT * FROM om_voz_propuestas WHERE {where}
            ORDER BY fecha_propuesta DESC LIMIT 50
        """, *params)
    return [_row_to_dict(r) for r in rows]


@router.patch("/voz/propuestas/{propuesta_id}")
async def decidir_propuesta(propuesta_id: UUID, data: dict):
    """Aprobar, descartar o editar propuesta."""
    pool = await _get_pool()
    estado = data.get("estado")
    async with pool.acquire() as conn:
        updates = ["fecha_decision = now()"]
        params = [propuesta_id]
        idx = 2
        if estado:
            updates.append(f"estado = ${idx}"); params.append(estado); idx += 1
        if data.get("contenido_editado"):
            updates.append(f"contenido_propuesto = ${idx}::jsonb")
            params.append(json.dumps(data["contenido_editado"])); idx += 1
        set_clause = ", ".join(updates)
        await conn.execute(
            f"UPDATE om_voz_propuestas SET {set_clause} WHERE id = $1 AND tenant_id = '{TENANT}'",
            *params)
    return {"status": "updated"}


@router.post("/voz/propuestas/{propuesta_id}/ejecutar")
async def ejecutar_propuesta(propuesta_id: UUID):
    """Ejecuta propuesta aprobada: envía WA, publica contenido, etc."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        prop = await conn.fetchrow("""
            SELECT * FROM om_voz_propuestas WHERE id = $1 AND tenant_id = $2
        """, propuesta_id, TENANT)
        if not prop:
            raise HTTPException(404, "Propuesta no encontrada")
        if prop["estado"] not in ("aprobada", "editada"):
            raise HTTPException(400, "Solo se pueden ejecutar propuestas aprobadas")

        contenido = prop["contenido_propuesto"]
        resultado = {}

        # Ejecutar según canal
        if prop["canal"] == "whatsapp" and contenido.get("telefono"):
            from src.pilates.whatsapp import enviar_texto
            resultado = await enviar_texto(
                contenido["telefono"], contenido.get("texto", ""),
                UUID(contenido["cliente_id"]) if contenido.get("cliente_id") else None)
        else:
            resultado = {"status": "manual", "nota": f"Canal {prop['canal']} requiere ejecución manual"}

        # Marcar ejecutada
        await conn.execute("""
            UPDATE om_voz_propuestas SET estado = 'ejecutada', fecha_ejecucion = now(),
                resultado = $1::jsonb WHERE id = $2
        """, json.dumps(resultado), propuesta_id)

    return {"status": "ejecutada", "resultado": resultado}


@router.post("/voz/capa-a")
async def consultar_capa_a_endpoint(data: dict):
    """Consulta fuente externa de Capa A."""
    from src.pilates.voz import consultar_capa_a
    fuente = data.get("fuente", "perplexity")
    query = data.get("query", "")
    return await consultar_capa_a(fuente, query)


@router.get("/voz/capa-a/datos")
async def listar_datos_capa_a(fuente: Optional[str] = None, limit: int = 20):
    """Lista datos externos almacenados."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        if fuente:
            rows = await conn.fetch("""
                SELECT * FROM om_voz_capa_a WHERE tenant_id = $1 AND fuente = $2
                ORDER BY created_at DESC LIMIT $3
            """, TENANT, fuente, limit)
        else:
            rows = await conn.fetch("""
                SELECT * FROM om_voz_capa_a WHERE tenant_id = $1
                ORDER BY created_at DESC LIMIT $2
            """, TENANT, limit)
    return [_row_to_dict(r) for r in rows]


@router.get("/voz/isp/{canal}")
async def obtener_checklist_isp(canal: str):
    """Obtiene checklist ISP para un canal."""
    from src.pilates.voz import calcular_isp
    return await calcular_isp(canal)


@router.post("/voz/isp/{canal}")
async def guardar_auditoria_isp(canal: str, data: dict):
    """Guarda resultado de auditoría ISP."""
    from src.pilates.voz import guardar_isp
    return await guardar_isp(
        canal, data.get("elementos_cumplidos", []), data.get("score", 0))


@router.get("/voz/isp")
async def historial_isp():
    """Historial de auditorías ISP por canal."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT * FROM om_voz_isp WHERE tenant_id = $1
            ORDER BY fecha_auditoria DESC LIMIT 20
        """, TENANT)
    return [_row_to_dict(r) for r in rows]


@router.get("/voz/telemetria")
async def telemetria_voz(canal: Optional[str] = None):
    """Telemetría de canales de voz."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        if canal:
            rows = await conn.fetch("""
                SELECT * FROM om_voz_telemetria WHERE tenant_id = $1 AND canal = $2
                ORDER BY fecha DESC LIMIT 30
            """, TENANT, canal)
        else:
            rows = await conn.fetch("""
                SELECT * FROM om_voz_telemetria WHERE tenant_id = $1
                ORDER BY fecha DESC LIMIT 30
            """, TENANT)
    return [_row_to_dict(r) for r in rows]


# ============================================================
# COCKPIT — Interfaz generativa
# ============================================================

@router.get("/cockpit")
async def cockpit():
    """Contexto del día + módulos sugeridos para el Modo Estudio."""
    from src.pilates.cockpit import contexto_del_dia
    return await contexto_del_dia()

@router.post("/cockpit/config")
async def guardar_config_cockpit(data: dict):
    """Guarda qué módulos ha elegido Jesús (aprende preferencias)."""
    from src.pilates.cockpit import guardar_configuracion
    await guardar_configuracion(data.get("modulos", []))
    return {"status": "ok"}

@router.post("/cockpit/chat")
async def cockpit_chat(data: dict):
    """Chat conversacional para controlar la interfaz del cockpit."""
    from src.pilates.cockpit import chat_cockpit
    mensaje = data.get("mensaje", "")
    modulos_activos = data.get("modulos_activos", [])
    historial = data.get("historial", [])
    if not mensaje:
        return {"respuesta": "", "acciones": {"montar": [], "desmontar": [], "desmontar_todos": False}}
    return await chat_cockpit(mensaje, modulos_activos, historial)

# Engagement resumen (para módulo cockpit)
@router.get("/engagement")
async def get_engagement():
    """Resumen engagement: clientes en riesgo + top rachas."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        riesgo = await conn.fetch("""
            SELECT cp.cliente_id, c.nombre, c.apellidos, cp.engagement_score,
                   cp.riesgo_churn, cp.engagement_tendencia, cp.racha_actual
            FROM om_cliente_perfil cp
            JOIN om_clientes c ON c.id = cp.cliente_id
            WHERE cp.tenant_id = $1 AND cp.riesgo_churn IN ('alto','critico')
            ORDER BY cp.engagement_score ASC LIMIT 10
        """, TENANT)
        rachas = await conn.fetch("""
            SELECT cp.cliente_id, c.nombre, cp.racha_actual, cp.engagement_score
            FROM om_cliente_perfil cp
            JOIN om_clientes c ON c.id = cp.cliente_id
            WHERE cp.tenant_id = $1 AND cp.racha_actual >= 4
            ORDER BY cp.racha_actual DESC LIMIT 5
        """, TENANT)
    return {
        "en_riesgo": [_row_to_dict(r) for r in riesgo],
        "top_rachas": [_row_to_dict(r) for r in rachas],
    }


# ============================================================
# PORTAL PÚBLICO — Chat captación
# ============================================================

class ChatPublicoRequest(BaseModel):
    mensaje: str
    historial: Optional[list] = None

@router.post("/publico/chat")
async def chat_publico(data: ChatPublicoRequest):
    """Chat público de captación — sin autenticación."""
    from src.pilates.portal_publico import chat_captacion
    return await chat_captacion(data.mensaje, historial=data.historial)


# ============================================================
# COBROS RECURRENTES
# ============================================================


@router.get("/cobros-recurrentes")
async def get_cobros_recurrentes(limite: int = 20):
    """Lista últimos cobros automáticos."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT ca.*, c.nombre, c.apellidos
            FROM om_cobros_automaticos ca
            LEFT JOIN om_clientes c ON c.id = ca.cliente_id
            WHERE ca.tenant_id = $1
            ORDER BY ca.created_at DESC LIMIT $2
        """, TENANT, limite)
    return [_row_to_dict(r) for r in rows]


# ============================================================
# FEED DEL ESTUDIO
# ============================================================

@router.get("/feed")
async def get_feed(limit: int = 20, solo_no_leidos: bool = False):
    """Timeline de noticias del estudio."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        if solo_no_leidos:
            rows = await conn.fetch("""
                SELECT * FROM om_feed_estudio
                WHERE tenant_id = $1 AND leido = FALSE
                ORDER BY created_at DESC LIMIT $2
            """, TENANT, limit)
        else:
            rows = await conn.fetch("""
                SELECT * FROM om_feed_estudio
                WHERE tenant_id = $1
                ORDER BY created_at DESC LIMIT $2
            """, TENANT, limit)
    return [_row_to_dict(r) for r in rows]


class MarcarLeidoRequest(BaseModel):
    ids: Optional[list] = None
    todos: bool = False

@router.post("/feed/marcar-leido")
async def feed_marcar_leido(data: MarcarLeidoRequest):
    """Marcar noticias como leídas."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        if data.todos:
            result = await conn.execute("""
                UPDATE om_feed_estudio SET leido = TRUE
                WHERE tenant_id = $1 AND leido = FALSE
            """, TENANT)
        elif data.ids:
            from uuid import UUID as _UUID
            uuids = [_UUID(i) for i in data.ids]
            result = await conn.execute("""
                UPDATE om_feed_estudio SET leido = TRUE
                WHERE tenant_id = $1 AND id = ANY($2)
            """, TENANT, uuids)
        else:
            return {"marcadas": 0}
    return {"status": "ok"}


@router.get("/feed/count")
async def feed_count():
    """Badge: número de noticias no leídas."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        count = await conn.fetchval("""
            SELECT count(*) FROM om_feed_estudio
            WHERE tenant_id = $1 AND leido = FALSE
        """, TENANT)
    return {"no_leidos": count}


# ============================================================
# HELPERS
# ============================================================

def _generar_html_factura(factura, lineas) -> str:
    """Genera HTML de factura para PDF o visualización."""
    lineas_html = ""
    for l in lineas:
        lineas_html += f"""
        <tr>
            <td>{l['concepto']}</td>
            <td style="text-align:right">{l['cantidad']}</td>
            <td style="text-align:right">{float(l['precio_unitario']):.2f}</td>
            <td style="text-align:right">{float(l['base_imponible']):.2f}</td>
            <td style="text-align:right">{float(l['iva_porcentaje']):.0f}%</td>
            <td style="text-align:right">{float(l['total']):.2f}</td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
  body {{ font-family: 'Helvetica', sans-serif; font-size: 12px; color: #333; margin: 40px; }}
  .header {{ display: flex; justify-content: space-between; margin-bottom: 30px; }}
  .emisor {{ font-size: 11px; color: #666; }}
  .titulo {{ font-size: 22px; font-weight: bold; color: #111; }}
  .numero {{ font-size: 14px; color: #6366f1; margin-top: 4px; }}
  .receptor {{ background: #f9fafb; padding: 16px; border-radius: 8px; margin: 20px 0; }}
  table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
  th {{ text-align: left; padding: 8px; border-bottom: 2px solid #e5e7eb; font-size: 11px;
       text-transform: uppercase; color: #6b7280; }}
  td {{ padding: 8px; border-bottom: 1px solid #f3f4f6; }}
  .totales {{ text-align: right; margin-top: 20px; }}
  .totales .total {{ font-size: 18px; font-weight: bold; }}
  .verifactu {{ font-size: 9px; color: #9ca3af; margin-top: 40px; border-top: 1px solid #e5e7eb;
               padding-top: 8px; }}
</style></head><body>
  <div class="header">
    <div>
      <div class="titulo">FACTURA</div>
      <div class="numero">{factura['numero_factura']}</div>
      <div style="margin-top:8px">Fecha: {factura['fecha_emision']}</div>
    </div>
    <div class="emisor">
      <strong>Authentic Pilates</strong><br>
      Jesus Fernandez Dominguez<br>
      Logrono, La Rioja<br>
    </div>
  </div>

  <div class="receptor">
    <strong>Cliente:</strong> {factura['cliente_nombre_fiscal'] or 'Sin datos fiscales'}<br>
    {f"NIF: {factura['cliente_nif']}<br>" if factura['cliente_nif'] else ''}
    {f"Direccion: {factura['cliente_direccion']}" if factura['cliente_direccion'] else ''}
  </div>

  <table>
    <thead>
      <tr><th>Concepto</th><th style="text-align:right">Cant.</th>
          <th style="text-align:right">Precio</th><th style="text-align:right">Base</th>
          <th style="text-align:right">IVA</th><th style="text-align:right">Total</th></tr>
    </thead>
    <tbody>{lineas_html}</tbody>
  </table>

  <div class="totales">
    <div>Base imponible: {float(factura['base_imponible']):.2f} EUR</div>
    <div>IVA ({float(factura['iva_porcentaje']):.0f}%): {float(factura['iva_monto']):.2f} EUR</div>
    <div class="total">TOTAL: {float(factura['total']):.2f} EUR</div>
  </div>

  <div class="verifactu">
    VeriFactu hash: {factura['verifactu_hash'][:16]}...<br>
    Este documento es una factura simplificada. Preparado para VeriFactu (La Rioja ~2027).
  </div>
</body></html>"""


# ============================================================
# VOZ ESTRATÉGICO — Identidad + IRC + PCA + Diagnóstico
# B-PIL-20a
# ============================================================

@router.post("/voz/seed")
async def seed_voz_completo():
    """Seed completo: identidad + IRC + PCA + competidores.
    Idempotente — se puede ejecutar múltiples veces sin duplicar datos.
    """
    from src.pilates.voz_identidad import (
        seed_identidad, seed_irc_inicial,
        seed_pca_inicial, seed_competidores,
    )
    r1 = await seed_identidad()
    r2 = await seed_irc_inicial()
    r3 = await seed_pca_inicial()
    r4 = await seed_competidores()
    return {"identidad": r1, "irc": r2, "pca": r3, "competidores": r4}

@router.get("/voz/identidad")
async def get_identidad():
    from src.pilates.voz_identidad import obtener_identidad
    return await obtener_identidad()

@router.get("/voz/irc")
async def get_irc():
    from src.pilates.voz_identidad import obtener_irc
    return await obtener_irc()

@router.get("/voz/pca")
async def get_pca(segmento: Optional[str] = None):
    from src.pilates.voz_identidad import obtener_pca
    return await obtener_pca(segmento)

@router.get("/voz/competidores")
async def get_competidores():
    from src.pilates.voz_identidad import obtener_competidores
    return await obtener_competidores()

@router.get("/voz/diagnostico")
async def get_diagnostico():
    """Diagnóstico cruzado de presencia digital.
    Cruza Identidad x IRC x PCA x Competidores.
    """
    from src.pilates.voz_identidad import diagnosticar_presencia
    return await diagnosticar_presencia()


# ============================================================
# VOZ ESTRATÉGICO — Motor Tridimensional + Calendario
# B-PIL-20b
# ============================================================

@router.post("/voz/estrategia/calcular")
async def calcular_estrategia_endpoint():
    """Calcula estrategia semanal cruzando IRC x Matriz x PCA.
    Genera calendario de contenido con justificación de 3 ejes.
    ~5 seg (1 LLM call).
    """
    from src.pilates.voz_estrategia import calcular_estrategia
    return await calcular_estrategia()

@router.get("/voz/estrategia")
async def get_estrategia():
    """Devuelve estrategia activa + calendario de la semana."""
    from src.pilates.voz_estrategia import obtener_estrategia_activa
    return await obtener_estrategia_activa()

@router.post("/voz/calendario/{item_id}/aprobar")
async def aprobar_item(item_id: str):
    """Jesús aprueba una pieza de contenido del calendario."""
    from src.pilates.voz_estrategia import aprobar_item_calendario
    return await aprobar_item_calendario(item_id)

@router.post("/voz/calendario/{item_id}/descartar")
async def descartar_item(item_id: str):
    """Jesús descarta una pieza de contenido del calendario."""
    from src.pilates.voz_estrategia import descartar_item_calendario
    return await descartar_item_calendario(item_id)

# ============================================================
# VOZ ESTRATÉGICO — Arquitecto de Presencia
# B-PIL-20c
# ============================================================

@router.post("/voz/perfil/{canal}/generar")
async def generar_perfil_canal(canal: str):
    """Genera configuración completa del perfil de un canal.
    Canales: whatsapp, google_business, instagram, facebook.
    ~5 seg (1 LLM call).
    """
    from src.pilates.voz_arquitecto import generar_perfil
    return await generar_perfil(canal)

@router.post("/voz/perfiles/generar")
async def generar_todos_perfiles():
    """Genera perfiles para todos los canales con IRC >= 0.3.
    ~20 seg (4 LLM calls secuenciales).
    """
    from src.pilates.voz_arquitecto import generar_todos_los_perfiles
    return await generar_todos_los_perfiles()

@router.get("/voz/perfil/{canal}")
async def get_perfil_canal(canal: str):
    """Devuelve plantillas del perfil de un canal, agrupadas por tipo."""
    from src.pilates.voz_arquitecto import obtener_perfil
    return await obtener_perfil(canal)

@router.post("/voz/plantilla/{plantilla_id}/aprobar")
async def aprobar_plantilla_endpoint(plantilla_id: str):
    """Jesús aprueba una plantilla de perfil."""
    from src.pilates.voz_arquitecto import aprobar_plantilla
    return await aprobar_plantilla(plantilla_id)

@router.post("/voz/plantilla/{plantilla_id}/aplicada")
async def marcar_aplicada_endpoint(plantilla_id: str):
    """Jesús confirma que aplicó la plantilla al canal real."""
    from src.pilates.voz_arquitecto import marcar_aplicada
    return await marcar_aplicada(plantilla_id)

# ============================================================
# VOZ ESTRATÉGICO — 5 Ciclos + ISP + Telemetría
# B-PIL-20d
# ============================================================

@router.post("/voz/ciclo/escuchar")
async def ciclo_escuchar():
    """Detecta señales de las 3 capas (A, B, C)."""
    from src.pilates.voz_ciclos import escuchar
    return await escuchar()

@router.get("/voz/senales")
async def get_senales():
    """Devuelve señales pendientes priorizadas."""
    from src.pilates.voz_ciclos import priorizar
    return await priorizar()

@router.post("/voz/senales/{senal_id}/procesada")
async def senal_procesada(senal_id: str):
    """Marca una señal como procesada."""
    from src.pilates.voz_ciclos import marcar_procesada
    return await marcar_procesada(senal_id)

@router.post("/voz/telemetria")
async def registrar_telemetria_endpoint(request: Request):
    """Registra métricas de un canal. Body: {canal, periodo, metricas: {...}}"""
    from src.pilates.voz_ciclos import registrar_telemetria
    body = await request.json()
    return await registrar_telemetria(
        body["canal"], body["periodo"], body.get("metricas", {})
    )

@router.post("/voz/irc/recalcular")
async def recalcular_irc_endpoint():
    """Recalcula IRC de todos los canales con datos de telemetría."""
    from src.pilates.voz_ciclos import recalcular_irc
    return await recalcular_irc()

@router.get("/voz/isp-automatico")
async def get_isp_automatico():
    """Calcula y devuelve ISP automático de todos los canales."""
    from src.pilates.voz_ciclos import calcular_isp_automatico
    return await calcular_isp_automatico()

@router.post("/voz/ciclo/completo")
async def ciclo_completo():
    """Ejecuta los 5 ciclos en secuencia (ESCUCHAR→PRIORIZAR→PROPONER→EJECUTAR→APRENDER)."""
    from src.pilates.voz_ciclos import ejecutar_ciclo_completo
    return await ejecutar_ciclo_completo()

# ============================================================
# VOZ ESTRATÉGICO — Cron manual
# B-PIL-20e
# ============================================================

@router.post("/voz/cron/diaria")
async def cron_diaria_manual():
    """Dispara la tarea diaria manualmente (escuchar señales)."""
    from src.pilates.cron import _tarea_diaria
    await _tarea_diaria()
    return {"status": "ok", "tarea": "diaria"}

@router.post("/voz/cron/semanal")
async def cron_semanal_manual():
    """Dispara la tarea semanal manualmente (ciclo completo + estrategia)."""
    from src.pilates.cron import _tarea_semanal
    await _tarea_semanal()
    return {"status": "ok", "tarea": "semanal"}


# ============================================================
# BUS DE SEÑALES — Sistema nervioso del organismo
# ============================================================

class SenalCreate(BaseModel):
    tipo: str = Field(pattern="^(DATO|ALERTA|DIAGNOSTICO|OPORTUNIDAD|PRESCRIPCION|ACCION|PERCEPCION|PERCEPCION_CAUSAL|PRESCRIPCION_ESTRATEGICA|RECOMPILACION|BRIEFING_PENDIENTE)$")
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


# ============================================================
# DIAGNOSTICADOR + BUSCADOR — Agentes autónomos ACD
# ============================================================

@router.post("/acd/diagnosticar-tenant")
async def acd_diagnosticar_tenant():
    """Ejecuta diagnóstico ACD sobre datos reales de Authentic Pilates."""
    from src.pilates.diagnosticador import diagnosticar_tenant
    return await diagnosticar_tenant()


@router.post("/acd/buscar-por-gaps")
async def acd_buscar_por_gaps():
    """Busca información dirigida por gaps ACD vía Perplexity."""
    from src.pilates.buscador import buscar_por_gaps
    return await buscar_por_gaps()


@router.post("/acd/enjambre")
async def acd_enjambre():
    """Ejecuta el enjambre cognitivo v2: modelo causal 4 niveles (3 secuenciales + 6 clusters paralelos)."""
    from src.pilates.enjambre import ejecutar_enjambre
    return await ejecutar_enjambre()


@router.post("/acd/g4")
async def acd_g4():
    """Ejecuta G4 completa: Enjambre → Compositor → Estratega → Orquestador."""
    from src.pilates.compositor import ejecutar_g4
    return await ejecutar_g4()


@router.post("/acd/g4-recompilar")
async def acd_g4_recompilar():
    """G4 + Recompilador: diagnostica y reconfigura agentes automáticamente."""
    from src.pilates.recompilador import ejecutar_g4_con_recompilacion
    return await ejecutar_g4_con_recompilacion()


@router.post("/acd/recompilar")
async def acd_recompilar(request: Request):
    """Recompila configs de agentes desde prescripción manual."""
    body = await request.json()
    from src.pilates.recompilador import recompilar
    return await recompilar(body.get("prescripcion", body))


@router.post("/acd/director-opus")
async def acd_director_opus():
    """Director Opus: lee manual, comprende estado, diseña prompts D_híbrido."""
    from src.pilates.rate_limit import semaforo_opus
    if semaforo_opus.locked():
        raise HTTPException(status_code=429, detail="Director Opus ocupado")
    async with semaforo_opus:
        from src.pilates.director_opus import dirigir_orquesta
        return await dirigir_orquesta()


@router.post("/acd/metacognitivo")
async def acd_metacognitivo():
    """Meta-Cognitivo Opus: evalúa el sistema cognitivo mensualmente."""
    from src.pilates.rate_limit import semaforo_metacog
    if semaforo_metacog.locked():
        raise HTTPException(status_code=429, detail="Metacognitivo ocupado")
    async with semaforo_metacog:
        from src.pilates.metacognitivo import ejecutar_metacognitivo
        return await ejecutar_metacognitivo()


@router.post("/acd/ingeniero")
async def acd_ingeniero():
    """Ingeniero: procesa instrucciones pendientes del Meta-Cognitivo."""
    from src.pilates.ingeniero import procesar_instrucciones_pendientes
    return await procesar_instrucciones_pendientes()


@router.get("/acd/config-agentes")
async def acd_config_agentes(agente: Optional[str] = None):
    """Lista configs dinámicas activas de agentes."""
    from src.db.client import get_pool
    pool = await get_pool()
    conditions = ["tenant_id = $1", "activa = TRUE"]
    params: list = [TENANT]
    idx = 2
    if agente:
        conditions.append(f"agente = ${idx}")
        params.append(agente)
    where = " AND ".join(conditions)
    async with pool.acquire() as conn:
        rows = await conn.fetch(f"""
            SELECT agente, version, config, aprobada_por, created_at
            FROM om_config_agentes WHERE {where}
            ORDER BY agente, version DESC
        """, *params)
    return [_row_to_dict(r) for r in rows]


# ============================================================
# VIGÍA + MECÁNICO + AUTÓFAGO — Goma META del organismo
# ============================================================

@router.post("/sistema/vigilar")
async def sistema_vigilar():
    """Ejecuta health checks del Vigía. Emite ALERTAs al bus."""
    from src.pilates.vigia import vigilar
    return await vigilar()


@router.post("/sistema/mecanico")
async def sistema_mecanico():
    """Ejecuta el Mecánico: procesa ALERTAs pendientes."""
    from src.pilates.mecanico import procesar_alertas
    return await procesar_alertas()


@router.post("/sistema/autofagia")
async def sistema_autofagia():
    """Ejecuta autofagia: detecta código muerto, datos caducados, archivos obsoletos.
    NO borra nada. Solo registra propuestas en om_mejoras_pendientes."""
    from src.pilates.autofago import ejecutar_autofagia
    return await ejecutar_autofagia()


# ============================================================
# G4 — Motor Cognitivo (Enjambre + Compositor + Recompilador)
# ============================================================

@router.post("/sistema/enjambre")
async def sistema_enjambre():
    """Ejecuta enjambre cognitivo: 9 agentes diagnostican INT×P×R."""
    from src.pilates.enjambre import ejecutar_enjambre
    return await ejecutar_enjambre()


@router.post("/sistema/g4")
async def sistema_g4():
    """G4 completa: enjambre + compositor + estratega + orquestador."""
    from src.pilates.compositor import ejecutar_g4
    return await ejecutar_g4()


@router.post("/sistema/g4-recompilar")
async def sistema_g4_recompilar():
    """G4 + recompilación: diagnostica, prescribe y reconfigura agentes."""
    from src.pilates.recompilador import ejecutar_g4_con_recompilacion
    return await ejecutar_g4_con_recompilacion()


@router.post("/sistema/evaluador")
async def sistema_evaluador():
    """Evaluador: compara prescripción anterior con resultados actuales."""
    from src.pilates.evaluador_organismo import evaluar_semana
    return await evaluar_semana()


@router.post("/sistema/metacognitivo")
async def sistema_metacognitivo():
    """Meta-Cognitivo Opus: evalúa si la capa cognitiva funciona."""
    from src.pilates.metacognitivo import ejecutar_metacognitivo
    return await ejecutar_metacognitivo()


@router.post("/sistema/ingeniero")
async def sistema_ingeniero():
    """Ingeniero: procesa instrucciones pendientes del Meta-Cognitivo."""
    from src.pilates.ingeniero import procesar_instrucciones_pendientes
    return await procesar_instrucciones_pendientes()


@router.get("/sistema/estado")
async def sistema_estado():
    """Estado completo del sistema: checks + bus + diagnóstico + mejoras pendientes."""
    from src.pilates.vigia import ejecutar_checks
    from src.pilates.bus import contar_pendientes

    checks = await ejecutar_checks()
    bus = await contar_pendientes()

    from src.db.client import get_pool
    pool = await get_pool()
    async with pool.acquire() as conn:
        ultimo_diag = await conn.fetchrow("""
            SELECT estado_pre, lentes_pre, created_at FROM diagnosticos
            WHERE caso_input LIKE 'Diagnóstico autónomo%'
            ORDER BY created_at DESC LIMIT 1
        """)

        mejoras_pend = 0
        try:
            mejoras_pend = await conn.fetchval("""
                SELECT count(*) FROM om_mejoras_pendientes
                WHERE estado = 'pendiente' AND tenant_id = 'authentic_pilates'
            """) or 0
        except Exception:
            pass

        autofagia_pend = 0
        try:
            autofagia_pend = await conn.fetchval("""
                SELECT count(*) FROM om_mejoras_pendientes
                WHERE estado = 'pendiente' AND tipo = 'AUTOFAGIA' AND tenant_id = 'authentic_pilates'
            """) or 0
        except Exception:
            pass

    return {
        "health": [{"subsistema": c.subsistema, "estado": c.estado, "mensaje": c.mensaje}
                   for c in checks],
        "bus_pendientes": bus,
        "ultimo_diagnostico": {
            "estado": ultimo_diag["estado_pre"] if ultimo_diag else None,
            "lentes": ultimo_diag["lentes_pre"] if ultimo_diag else None,
            "fecha": str(ultimo_diag["created_at"])[:10] if ultimo_diag else None,
        } if ultimo_diag else None,
        "mejoras_arquitecturales_pendientes": mejoras_pend,
        "propuestas_autofagia_pendientes": autofagia_pend,
    }


@router.get("/sistema/mejoras")
async def sistema_mejoras(
    estado: Optional[str] = "pendiente",
    tipo: Optional[str] = None,
    limite: int = Query(default=30, le=100),
):
    """Lista mejoras pendientes (ARQUITECTURAL + AUTOFAGIA). Para revisión CR1."""
    from src.db.client import get_pool
    pool = await get_pool()
    conditions = ["tenant_id = $1"]
    params: list = [TENANT]
    idx = 2

    if estado:
        conditions.append(f"estado = ${idx}")
        params.append(estado)
        idx += 1

    if tipo:
        conditions.append(f"tipo = ${idx}")
        params.append(tipo)
        idx += 1

    where = " AND ".join(conditions)
    params.append(limite)

    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(f"""
                SELECT id, created_at, tipo, estado, origen, descripcion, metadata
                FROM om_mejoras_pendientes
                WHERE {where}
                ORDER BY created_at DESC
                LIMIT ${idx}
            """, *params)
        return [_row_to_dict(r) for r in rows]
    except Exception:
        return []


@router.patch("/sistema/mejoras/{mejora_id}")
async def sistema_mejora_decidir(
    mejora_id: UUID,
    decision: str = Query(..., pattern="^(aprobada|rechazada|completada)$"),
):
    """CR1: Aprobar, rechazar o completar una mejora pendiente."""
    from src.db.client import get_pool
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute("""
            UPDATE om_mejoras_pendientes SET estado = $1
            WHERE id = $2 AND tenant_id = $3
        """, decision, mejora_id, TENANT)
        if result == "UPDATE 0":
            raise HTTPException(404, "Mejora no encontrada")

    log.info("mejora_decidida", id=str(mejora_id), decision=decision)
    return {"status": decision, "id": str(mejora_id)}


# ============================================================
# AF1 CONSERVACIÓN + AF3 DEPURACIÓN — Agentes funcionales
# ============================================================

@router.post("/af/conservacion")
async def af_conservacion():
    """AF1: Detecta clientes en riesgo de abandono. Emite ALERTAs al bus."""
    from src.pilates.af1_conservacion import ejecutar_af1
    return await ejecutar_af1()


@router.post("/af/depuracion")
async def af_depuracion():
    """AF3: Detecta sesiones y servicios ineficientes. Emite ALERTAs + VETOs al bus."""
    from src.pilates.af3_depuracion import ejecutar_af3
    return await ejecutar_af3()


@router.post("/af/identidad")
async def af_identidad():
    """AF5: Detecta gaps de identidad, coherencia de canales, diferenciación."""
    from src.pilates.af5_identidad import ejecutar_af5
    return await ejecutar_af5()


# ============================================================
# PROPIOCEPCIÓN — El organismo se mide a sí mismo
# ============================================================

@router.post("/sistema/propiocepcion")
async def sistema_propiocepcion(periodo: str = Query(default="diario", pattern="^(diario|semanal)$")):
    """Genera snapshot de telemetría del organismo."""
    from src.pilates.propiocepcion import snapshot
    return await snapshot(periodo)


@router.get("/sistema/tendencia")
async def sistema_tendencia(n: int = Query(default=10, le=30)):
    """Últimos N snapshots de telemetría para visualizar tendencia."""
    from src.pilates.propiocepcion import obtener_tendencia
    snapshots = await obtener_tendencia(n)
    return {"snapshots": snapshots, "total": len(snapshots)}


# ============================================================
# B2.9 VOZ REACTIVO — Sub-circuito de señales AF5
# ============================================================

@router.post("/voz/propagar-diagnostico")
async def voz_propagar_diagnostico():
    """Propaga cambio de diagnóstico ACD a la estrategia de voz."""
    from src.pilates.voz_reactivo import propagar_diagnostico_a_voz
    return await propagar_diagnostico_a_voz()


@router.post("/voz/cross-af")
async def voz_cross_af():
    """AF5 emite señales cross-AF: leads sin atender, canales bajo IRC."""
    from src.pilates.voz_reactivo import emitir_señales_cross_af
    return await emitir_señales_cross_af()


# ============================================================
# AF2 + AF4 + AF6 + AF7 — Agentes funcionales restantes
# ============================================================

@router.post("/af/captacion")
async def af_captacion():
    """AF2: Detecta leads perdidos + tasa conversión. Respeta VETOs de AF3."""
    from src.pilates.af_restantes import ejecutar_af2
    return await ejecutar_af2()


@router.post("/af/distribucion")
async def af_distribucion():
    """AF4: Detecta desequilibrios horarios y ratio individual/grupo."""
    from src.pilates.af_restantes import ejecutar_af4
    return await ejecutar_af4()


@router.post("/af/adaptacion")
async def af_adaptacion():
    """AF6: Detecta tensiones sin resolver y señala necesidad de adaptación."""
    from src.pilates.af_restantes import ejecutar_af6
    return await ejecutar_af6()


@router.post("/af/replicacion")
async def af_replicacion():
    """AF7: Detecta gaps en documentación y readiness de replicación."""
    from src.pilates.af_restantes import ejecutar_af7
    return await ejecutar_af7()


@router.post("/af/todos")
async def af_todos():
    """Ejecuta TODOS los AF restantes (AF2+AF4+AF6+AF7) de una vez."""
    from src.pilates.af_restantes import ejecutar_af_restantes
    return await ejecutar_af_restantes()


# ============================================================
# EJECUTOR + CONVERGENCIA + GESTOR — Cierre del circuito
# ============================================================

@router.post("/sistema/ejecutor")
async def sistema_ejecutor():
    """Ejecutor: lee prescripciones del bus y emite ACCIONes a AF."""
    from src.pilates.ejecutor_convergencia import ejecutar_prescripciones
    return await ejecutar_prescripciones()


@router.post("/sistema/convergencia")
async def sistema_convergencia():
    """Detecta cuando 2+ AF señalan el mismo cliente/grupo."""
    from src.pilates.ejecutor_convergencia import detectar_convergencia
    return await detectar_convergencia()


@router.post("/sistema/gestor")
async def sistema_gestor():
    """Gestor: limpia bus + resumen de actividad."""
    from src.pilates.ejecutor_convergencia import gestionar_bus
    return await gestionar_bus()


@router.post("/sistema/circuito")
async def sistema_circuito():
    """Ejecuta Ejecutor + Convergencia + Gestor de una vez."""
    from src.pilates.ejecutor_convergencia import ejecutar_circuito_completo
    return await ejecutar_circuito_completo()


# ============================================================
# COLLECTORS — Pull métricas de canales
# ============================================================

@router.post("/collectors")
async def run_collectors():
    """Ejecuta collectors: Instagram, Google Business, WhatsApp."""
    from src.pilates.collectors import collect_all
    return await collect_all()


# ============================================================
# ORGANISMO — Dashboard del sistema cognitivo
# ============================================================

@router.get("/organismo/dashboard")
async def organismo_dashboard():
    """Dashboard completo del organismo: gomas, agentes, diagnóstico, bus."""
    from src.db.client import get_pool
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Último diagnóstico ACD
        diag = await conn.fetchrow("""
            SELECT estado_pre, lentes_pre, vector_pre, metricas, created_at
            FROM diagnosticos
            WHERE caso_input LIKE 'Diagnóstico autónomo%'
            ORDER BY created_at DESC LIMIT 1
        """)

        # Último enjambre G4
        g4 = await conn.fetchrow("""
            SELECT estado_acd_base, resultado_lentes, resultado_funciones,
                   resultado_clusters, señales_emitidas, tiempo_total_s, created_at
            FROM om_enjambre_diagnosticos
            ORDER BY created_at DESC LIMIT 1
        """)

        # Configs activas de agentes (recompilador)
        configs = await conn.fetch("""
            SELECT agente, version, created_at, aprobada_por
            FROM om_config_agentes
            WHERE tenant_id='authentic_pilates' AND activa=TRUE
            ORDER BY agente
        """)

        # Bus: resumen últimas 48h
        bus_resumen = await conn.fetch("""
            SELECT tipo, count(*) as total, max(prioridad) as max_prioridad,
                   max(created_at) as ultimo
            FROM om_senales_agentes
            WHERE tenant_id='authentic_pilates'
                AND created_at > now() - interval '48 hours'
            GROUP BY tipo ORDER BY total DESC
        """)

        # Bus: señales de alta prioridad no procesadas
        urgentes = await conn.fetch("""
            SELECT tipo, origen, prioridad,
                   payload->>'descripcion' as descripcion,
                   created_at
            FROM om_senales_agentes
            WHERE tenant_id='authentic_pilates'
                AND estado='pendiente' AND prioridad <= 3
            ORDER BY prioridad, created_at DESC LIMIT 10
        """)

        # Propiocepción: último snapshot
        propio = await conn.fetchrow("""
            SELECT periodo, senales_emitidas, senales_procesadas, senales_pendientes,
                   actividad_agentes, agentes_silenciosos,
                   acd_estado, acd_lentes, acd_delta_lentes,
                   fixes_fontaneria, mejoras_arquitecturales, created_at
            FROM om_telemetria_sistema
            WHERE tenant_id='authentic_pilates'
            ORDER BY created_at DESC LIMIT 1
        """)

        # Actividad de agentes: quién emitió señales en los últimos 7 días
        agentes_activos = await conn.fetch("""
            SELECT origen, count(*) as señales, max(created_at) as ultimo
            FROM om_senales_agentes
            WHERE tenant_id='authentic_pilates'
                AND created_at > now() - interval '7 days'
            GROUP BY origen ORDER BY señales DESC
        """)

        # Feed organismo: últimas 10 noticias del sistema
        feed_org = await conn.fetch("""
            SELECT tipo, icono, titulo, detalle, severidad, created_at
            FROM om_feed_estudio
            WHERE tenant_id='authentic_pilates'
                AND tipo LIKE 'organismo_%'
            ORDER BY created_at DESC LIMIT 10
        """)

    def _safe(row):
        if not row:
            return None
        d = dict(row)
        for k, v in d.items():
            if hasattr(v, 'isoformat'):
                d[k] = v.isoformat()
            elif isinstance(v, (dict, list)):
                pass
            elif isinstance(v, str):
                try:
                    d[k] = json.loads(v)
                except (json.JSONDecodeError, TypeError):
                    pass
        return d

    return {
        "diagnostico_acd": _safe(diag),
        "diagnostico_cognitivo_g4": _safe(g4),
        "configs_agentes": [_safe(c) for c in configs],
        "bus": {
            "resumen_48h": [_safe(r) for r in bus_resumen],
            "urgentes": [_safe(u) for u in urgentes],
        },
        "agentes_activos_7d": [_safe(a) for a in agentes_activos],
        "propiocepcion": _safe(propio),
        "feed_organismo": [_safe(f) for f in feed_org],
        "gomas": {
            "G1_datos_senales": True,
            "G2_senales_diagnostico": True,
            "G3_diagnostico_busqueda": True,
            "G4_busqueda_prescripcion": True,
            "G5_prescripcion_accion": True,
            "G6_accion_aprendizaje": True,
            "META_rotura_reparacion": True,
        },
    }


@router.get("/organismo/bus")
async def organismo_bus(horas: int = 48, limit: int = 50):
    """Señales del bus en las últimas N horas."""
    from src.db.client import get_pool
    pool = await get_pool()
    async with pool.acquire() as conn:
        señales = await conn.fetch(f"""
            SELECT id, tipo, origen, estado, prioridad,
                   payload, created_at
            FROM om_senales_agentes
            WHERE tenant_id='authentic_pilates'
                AND created_at > now() - interval '{min(horas, 168)} hours'
            ORDER BY created_at DESC LIMIT {min(limit, 200)}
        """)
    return [{
        "id": str(s["id"]),
        "tipo": s["tipo"],
        "origen": s["origen"],
        "estado": s["estado"],
        "prioridad": s["prioridad"],
        "payload": s["payload"] if isinstance(s["payload"], dict) else json.loads(s["payload"]) if s["payload"] else {},
        "created_at": s["created_at"].isoformat(),
    } for s in señales]


@router.get("/organismo/diagnostico-cognitivo")
async def organismo_diagnostico_cognitivo():
    """Último diagnóstico G4 completo: perfil INT×P×R + disfunciones + prescripción."""
    from src.db.client import get_pool
    pool = await get_pool()
    async with pool.acquire() as conn:
        g4 = await conn.fetchrow("""
            SELECT estado_acd_base, resultado_lentes, resultado_funciones,
                   resultado_clusters, señales_emitidas, tiempo_total_s, created_at
            FROM om_enjambre_diagnosticos
            ORDER BY created_at DESC LIMIT 1
        """)
        if not g4:
            return {"status": "sin_diagnostico", "mensaje": "Aún no se ha ejecutado el enjambre cognitivo."}

        # Lentes contiene repertorio + disfunciones
        lentes = g4["resultado_lentes"]
        if isinstance(lentes, str):
            lentes = json.loads(lentes)

        # Funciones contiene mecanismo causal o prescripción
        funciones = g4["resultado_funciones"]
        if isinstance(funciones, str):
            funciones = json.loads(funciones)

        # Clusters
        clusters = g4["resultado_clusters"]
        if isinstance(clusters, str):
            clusters = json.loads(clusters)

    return {
        "perfil": g4["estado_acd_base"],
        "repertorio_y_disfunciones": lentes,
        "mecanismo_causal_o_prescripcion": funciones,
        "clusters": clusters,
        "señales_emitidas": g4["señales_emitidas"],
        "tiempo_s": float(g4["tiempo_total_s"]) if g4["tiempo_total_s"] else 0,
        "fecha": g4["created_at"].isoformat(),
    }


@router.get("/organismo/pizarra")
async def organismo_pizarra():
    """Pizarra compartida del ciclo actual."""
    from src.pilates.pizarra import leer_todo, resumen_narrativo, _ciclo_actual
    return {
        "ciclo": _ciclo_actual(),
        "entradas": await leer_todo(),
        "resumen": await resumen_narrativo(),
    }


@router.get("/organismo/config-agentes")
async def organismo_config_agentes():
    """Configuración INT×P×R actual de cada agente (recompilador)."""
    from src.db.client import get_pool
    pool = await get_pool()
    async with pool.acquire() as conn:
        configs = await conn.fetch("""
            SELECT agente, config, version, aprobada_por, created_at
            FROM om_config_agentes
            WHERE tenant_id='authentic_pilates' AND activa=TRUE
            ORDER BY agente
        """)
    return [{
        "agente": c["agente"],
        "config": c["config"] if isinstance(c["config"], dict) else json.loads(c["config"]),
        "version": c["version"],
        "aprobada_por": c["aprobada_por"],
        "fecha": c["created_at"].isoformat(),
    } for c in configs]


@router.get("/organismo/director")
async def organismo_director():
    """Última ejecución del Director Opus."""
    from src.db.client import get_pool
    pool = await get_pool()
    async with pool.acquire() as conn:
        señal = await conn.fetchrow("""
            SELECT payload, created_at FROM om_senales_agentes
            WHERE tenant_id='authentic_pilates' AND origen='DIRECTOR_OPUS'
            ORDER BY created_at DESC LIMIT 1
        """)
    if not señal:
        return {"estado_sistema": None, "estrategia_global": None, "configs": []}
    payload = señal["payload"] if isinstance(señal["payload"], dict) else json.loads(señal["payload"])
    return {**payload, "fecha": str(señal["created_at"])}


@router.get("/organismo/evaluacion")
async def organismo_evaluacion():
    """Última evaluación de prescripción."""
    from src.db.client import get_pool
    pool = await get_pool()
    async with pool.acquire() as conn:
        señal = await conn.fetchrow("""
            SELECT payload, created_at FROM om_senales_agentes
            WHERE tenant_id='authentic_pilates' AND origen='EVALUADOR'
            ORDER BY created_at DESC LIMIT 1
        """)
    if not señal:
        return {"evaluacion_global": None, "delta_lentes": None}
    payload = señal["payload"] if isinstance(señal["payload"], dict) else json.loads(señal["payload"])
    return {**payload, "fecha": str(señal["created_at"])}


@router.get("/organismo/pizarra-cognitiva")
async def get_pizarra_cognitiva():
    """Recetas del Director para cada función — lo que piensa el organismo."""
    from src.pilates.pizarras import leer_recetas_ciclo
    from zoneinfo import ZoneInfo
    ahora = datetime.now(ZoneInfo("Europe/Madrid"))
    ciclo = f"W{ahora.isocalendar()[1]:02d}-{ahora.isocalendar()[0]}"
    recetas = await leer_recetas_ciclo("authentic_pilates", ciclo)
    return {"ciclo": ciclo, "recetas": recetas, "total": len(recetas)}


@router.get("/organismo/plan-temporal")
async def get_plan_temporal():
    """Plan de ejecución del ciclo — qué componentes corren y en qué orden."""
    from src.pilates.pizarras import leer_plan_ciclo
    from zoneinfo import ZoneInfo
    ahora = datetime.now(ZoneInfo("Europe/Madrid"))
    ciclo = f"W{ahora.isocalendar()[1]:02d}-{ahora.isocalendar()[0]}"
    plan = await leer_plan_ciclo("authentic_pilates", ciclo)
    return {"ciclo": ciclo, "plan": plan, "total": len(plan)}


@router.get("/organismo/patrones")
async def get_patrones():
    """Patrones aprendidos por el sistema — pizarra evolución."""
    from src.pilates.pizarras import leer_patrones
    patrones = await leer_patrones("authentic_pilates", min_confianza=0.3)
    return {"patrones": patrones, "total": len(patrones)}


@router.get("/organismo/mediaciones")
async def get_mediaciones_recientes():
    """Conflictos cross-AF resueltos por el Mediador."""
    from src.db.client import get_pool
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT * FROM om_mediaciones
            WHERE tenant_id = 'authentic_pilates'
            ORDER BY created_at DESC LIMIT 10
        """)
    return [dict(r) for r in rows]


@router.get("/organismo/motor-resumen")
async def get_motor_resumen():
    """Resumen del motor: gasto, caché hits, presupuesto."""
    from src.motor.pensar import presupuesto_restante, _presupuesto_ciclo
    from src.db.client import get_pool
    pool = await get_pool()
    async with pool.acquire() as conn:
        semana = await conn.fetch("""
            SELECT modelo, count(*) as calls, SUM(coste_usd) as coste,
                   SUM(CASE WHEN cache_hit THEN 1 ELSE 0 END) as cache_hits
            FROM om_motor_telemetria
            WHERE tenant_id='authentic_pilates' AND created_at >= date_trunc('week', now())
            GROUP BY modelo ORDER BY coste DESC
        """)
    return {
        "presupuesto_restante": round(presupuesto_restante(), 2),
        "gastado_ciclo": round(_presupuesto_ciclo, 4),
        "por_modelo": [dict(r) for r in semana],
    }


@router.get("/comunicaciones")
async def get_comunicaciones(estado: Optional[str] = None, limit: int = 50):
    """Lee pizarra de comunicaciones — tracking WA."""
    from src.db.client import get_pool
    pool = await get_pool()
    async with pool.acquire() as conn:
        query = """
            SELECT * FROM om_pizarra_comunicacion
            WHERE tenant_id = 'authentic_pilates'
        """
        params = []
        if estado:
            query += " AND estado = $1"
            params.append(estado)
        query += " ORDER BY created_at DESC LIMIT $" + str(len(params) + 1)
        params.append(limit)
        rows = await conn.fetch(query, *params)
    return [dict(r) for r in rows]


@router.get("/mediaciones")
async def get_mediaciones(ciclo: Optional[str] = None):
    """Historial de mediaciones cross-AF."""
    from src.db.client import get_pool
    pool = await get_pool()
    async with pool.acquire() as conn:
        if ciclo:
            rows = await conn.fetch(
                "SELECT * FROM om_mediaciones WHERE tenant_id=$1 AND ciclo=$2 ORDER BY created_at DESC",
                TENANT, ciclo)
        else:
            rows = await conn.fetch(
                "SELECT * FROM om_mediaciones WHERE tenant_id=$1 ORDER BY created_at DESC LIMIT 50",
                TENANT)
    return [dict(r) for r in rows]


@router.get("/motor/telemetria")
async def motor_telemetria(ciclo: Optional[str] = None):
    """Telemetría del motor unificado: coste, tokens, cache hits por ciclo."""
    from src.db.client import get_pool
    from src.motor.pensar import presupuesto_restante, PRESUPUESTO_MAX_SEMANAL
    pool = await get_pool()
    async with pool.acquire() as conn:
        if ciclo:
            rows = await conn.fetch("""
                SELECT funcion, modelo, count(*) as llamadas,
                       sum(tokens_input) as tokens_in, sum(tokens_output) as tokens_out,
                       sum(coste_usd) as coste_total, sum(case when cache_hit then 1 else 0 end) as cache_hits,
                       avg(tiempo_ms) as avg_ms
                FROM om_motor_telemetria WHERE tenant_id=$1 AND ciclo=$2
                GROUP BY funcion, modelo ORDER BY coste_total DESC
            """, TENANT, ciclo)
        else:
            rows = await conn.fetch("""
                SELECT funcion, modelo, count(*) as llamadas,
                       sum(tokens_input) as tokens_in, sum(tokens_output) as tokens_out,
                       sum(coste_usd) as coste_total, sum(case when cache_hit then 1 else 0 end) as cache_hits,
                       avg(tiempo_ms) as avg_ms
                FROM om_motor_telemetria WHERE tenant_id=$1
                  AND created_at >= now() - interval '7 days'
                GROUP BY funcion, modelo ORDER BY coste_total DESC
            """, TENANT)
        cache_stats = await conn.fetchrow("""
            SELECT count(*) as entradas, sum(hits) as total_hits
            FROM om_pizarra_cache_llm WHERE tenant_id=$1 AND expires_at > now()
        """, TENANT)
    return {
        "presupuesto_restante": presupuesto_restante(),
        "presupuesto_max_semanal": PRESUPUESTO_MAX_SEMANAL,
        "cache": {"entradas_activas": cache_stats["entradas"], "total_hits": cache_stats["total_hits"] or 0},
        "detalle": [{
            "funcion": r["funcion"], "modelo": r["modelo"],
            "llamadas": r["llamadas"], "tokens_in": r["tokens_in"],
            "tokens_out": r["tokens_out"], "coste_usd": round(float(r["coste_total"] or 0), 4),
            "cache_hits": r["cache_hits"], "avg_ms": round(float(r["avg_ms"] or 0)),
        } for r in rows],
    }


@router.get("/pizarra/dominio")
async def get_pizarra_dominio():
    """Lee la pizarra dominio del tenant."""
    from src.pilates.pizarras import leer_dominio
    return await leer_dominio()


@router.get("/pizarra/interfaz")
async def get_pizarra_interfaz():
    """Lee la pizarra interfaz para el ciclo actual."""
    from src.pilates.pizarras import leer_layout_ciclo
    from datetime import datetime
    from zoneinfo import ZoneInfo
    ahora = datetime.now(ZoneInfo("Europe/Madrid"))
    ciclo = f"W{ahora.isocalendar()[1]:02d}-{ahora.isocalendar()[0]}"
    layout = await leer_layout_ciclo("authentic_pilates", ciclo)

    if not layout:
        return {"source": "default", "capas": {
            "operativo":  {"label": "Operativo",  "icon": "zap", "modulos": ["agenda", "calendario", "buscar", "grupos", "wa"]},
            "financiero": {"label": "Financiero", "icon": "coins", "modulos": ["pagos_pendientes", "resumen_mes", "facturas"]},
            "cognitivo":  {"label": "Cognitivo",  "icon": "brain", "modulos": ["pizarra", "estrategia", "evaluacion", "feed_cognitivo", "bus"]},
            "voz":        {"label": "Voz",        "icon": "megaphone", "modulos": ["voz_proactiva", "voz"]},
            "identidad":  {"label": "Identidad",  "icon": "dna", "modulos": ["adn", "depuracion", "readiness", "engagement"]},
        }}

    return {"source": "pizarra", "ciclo": ciclo, "layout": layout}


@router.get("/sse/pizarra")
async def sse_pizarra():
    """SSE: retransmite cambios de pizarra en tiempo real."""
    import asyncio as _asyncio
    from fastapi.responses import StreamingResponse

    async def event_generator():
        from src.db.client import get_pool
        pool = await get_pool()
        conn = await pool.acquire()

        queue = _asyncio.Queue()

        def on_notify(conn_ref, pid, channel, payload):
            queue.put_nowait(payload)

        await conn.add_listener("pizarra_actualizada", on_notify)
        yield f"data: {json.dumps({'type': 'connected'})}\n\n"

        try:
            while True:
                try:
                    payload = await _asyncio.wait_for(queue.get(), timeout=30)
                    yield f"data: {payload}\n\n"
                except _asyncio.TimeoutError:
                    yield ": keepalive\n\n"
        finally:
            await conn.remove_listener("pizarra_actualizada", on_notify)
            await pool.release(conn)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


# ============================================================
# DIAGNÓSTICO DEL SISTEMA
# ============================================================

@router.get("/sistema/diagnostico")
async def diagnostico_sistema():
    """Diagnóstico completo del sistema — para Jesús en Modo Profundo."""
    from src.db.client import get_pool
    from src.motor.pensar import presupuesto_restante, _presupuesto_ciclo

    pool = await get_pool()
    checks = {}

    async with pool.acquire() as conn:
        # Tablas
        checks["tablas_om"] = await conn.fetchval(
            "SELECT count(*) FROM pg_tables WHERE tablename LIKE 'om_%'")

        # Tamaño DB
        checks["db_size_mb"] = await conn.fetchval(
            "SELECT pg_database_size(current_database()) / 1024 / 1024")

        # Cron state
        cron_rows = await conn.fetch(
            "SELECT tarea, ultima_ejecucion, resultado FROM om_cron_state ORDER BY ultima_ejecucion DESC")
        checks["cron"] = [dict(r) for r in cron_rows]

        # Motor LLM
        checks["motor"] = {
            "presupuesto_restante": presupuesto_restante(),
            "gastado_ciclo": _presupuesto_ciclo,
        }

        # Caché
        try:
            cache = await conn.fetchrow("""
                SELECT count(*) as entradas, SUM(hits) as total_hits
                FROM om_pizarra_cache_llm WHERE tenant_id='authentic_pilates'
            """)
            checks["cache_llm"] = dict(cache) if cache else {}
        except Exception:
            checks["cache_llm"] = "tabla_no_existe"

        # Pizarras
        for tabla in ["om_pizarra_dominio", "om_pizarra_cognitiva", "om_pizarra_temporal",
                      "om_pizarra_modelos", "om_pizarra_evolucion", "om_pizarra_interfaz"]:
            try:
                count = await conn.fetchval(f"SELECT count(*) FROM {tabla}")
                checks[f"pizarra_{tabla[13:]}"] = count
            except Exception:
                checks[f"pizarra_{tabla[13:]}"] = "no_existe"

        # Señales bus
        try:
            checks["bus_pendientes"] = await conn.fetchval(
                "SELECT count(*) FROM om_senales_agentes WHERE procesada=false AND tenant_id='authentic_pilates'")
        except Exception:
            checks["bus_pendientes"] = "tabla_no_existe"

    return {"timestamp": str(datetime.now()), "checks": checks}


# ============================================================
# IDENTIDAD + CONTENIDO (F7)
# ============================================================

@router.get("/identidad")
async def get_identidad():
    """Lee la pizarra identidad del tenant."""
    from src.pilates.filtro_identidad import leer_identidad
    return await leer_identidad()


@router.patch("/identidad")
async def actualizar_identidad(request: Request):
    """Actualiza campos de la pizarra identidad (CR1 Jesús)."""
    body = await request.json()
    from src.db.client import get_pool
    pool = await get_pool()
    campos_permitidos = ["esencia", "narrativa", "valores", "anti_identidad",
                         "depuraciones_deliberadas", "tono", "angulo_diferencial"]
    sets = []
    params = ["authentic_pilates"]
    for campo in campos_permitidos:
        if campo in body:
            params.append(body[campo])
            sets.append(f"{campo} = ${len(params)}")
    if not sets:
        raise HTTPException(400, "Sin campos válidos")
    sets.append("updated_at = now()")
    query = f"UPDATE om_pizarra_identidad SET {', '.join(sets)} WHERE tenant_id = $1"
    async with pool.acquire() as conn:
        await conn.execute(query, *params)
    return {"status": "ok"}


@router.get("/contenido")
async def get_contenido(ciclo: str = None, estado: str = None, limit: int = 20):
    """Lista contenido generado."""
    from src.db.client import get_pool
    pool = await get_pool()
    query = "SELECT * FROM om_contenido WHERE tenant_id = 'authentic_pilates'"
    params = []
    if ciclo:
        params.append(ciclo)
        query += f" AND ciclo = ${len(params)}"
    if estado:
        params.append(estado)
        query += f" AND estado = ${len(params)}"
    query += f" ORDER BY created_at DESC LIMIT ${len(params) + 1}"
    params.append(limit)
    async with pool.acquire() as conn:
        rows = await conn.fetch(query, *params)
    return [dict(r) for r in rows]


@router.post("/contenido/{contenido_id}/aprobar")
async def aprobar(contenido_id):
    """CR1: Jesús aprueba contenido para publicación."""
    from uuid import UUID
    from src.pilates.contenido import aprobar_contenido
    return await aprobar_contenido(UUID(contenido_id))


@router.post("/contenido/{contenido_id}/programar")
async def programar(contenido_id, request: Request):
    """Programa contenido aprobado."""
    from uuid import UUID
    from src.pilates.contenido import programar_publicacion
    body = await request.json()
    return await programar_publicacion(UUID(contenido_id))


@router.post("/contenido/filtrar")
async def filtrar_contenido_manual(request: Request):
    """Filtra texto contra identidad (para preview)."""
    body = await request.json()
    from src.pilates.filtro_identidad import filtrar_por_identidad
    return await filtrar_por_identidad(body.get("texto", ""), body.get("canal", "instagram"))


@router.get("/competencia")
async def get_competencia():
    """Lista competidores monitorizados."""
    from src.db.client import get_pool
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM om_competencia WHERE tenant_id = 'authentic_pilates'")
    return [dict(r) for r in rows]
