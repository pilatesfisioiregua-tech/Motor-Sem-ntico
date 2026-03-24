"""Portal del Cliente — Autogestión.

Endpoints públicos (sin auth, acceso por token).
El cliente ve sus datos, sesiones, pagos, facturas.
Puede cancelar sesiones y solicitar recuperaciones.

Fuente: Exocortex v2.1 S16.4.
"""
from __future__ import annotations

import secrets
import structlog
from datetime import date, datetime, timedelta
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from uuid import UUID

log = structlog.get_logger()

router = APIRouter(prefix="/portal", tags=["portal"])

from src.pilates.tenant_context import get_tenant_id, DEFAULT_TENANT
TENANT = DEFAULT_TENANT  # Fallback para llamadas sin request


async def _get_pool():
    from src.db.client import get_pool
    return await get_pool()


def _row_to_dict(row) -> dict:
    d = dict(row)
    for k, v in d.items():
        if isinstance(v, UUID):
            d[k] = str(v)
    return d


async def _verificar_token(token: str) -> dict:
    """Verifica token de portal y devuelve datos del cliente."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        link = await conn.fetchrow("""
            SELECT l.*, c.nombre, c.apellidos, c.telefono, c.email
            FROM om_onboarding_links l
            JOIN om_clientes c ON c.id = l.cliente_id
            WHERE l.token = $1 AND l.tenant_id = $2
                AND l.estado = 'completado' AND l.es_portal = true
        """, token, TENANT)

        if not link:
            raise HTTPException(404, "Portal no encontrado. Contacta con el estudio.")

    return dict(link)


# ============================================================
# ACTIVAR PORTAL (interno — llamado tras completar onboarding)
# ============================================================

async def activar_portal(cliente_id: UUID) -> str:
    """Genera token de portal permanente para un cliente.

    Llamado automáticamente tras completar onboarding.
    Returns: token del portal.
    """
    pool = await _get_pool()
    token = secrets.token_urlsafe(32)

    async with pool.acquire() as conn:
        # Verificar si ya tiene portal
        existing = await conn.fetchval("""
            SELECT token FROM om_onboarding_links
            WHERE cliente_id = $1 AND tenant_id = $2 AND es_portal = true
        """, cliente_id, TENANT)
        if existing:
            return existing

        # Crear enlace portal (sin expiración)
        await conn.execute("""
            INSERT INTO om_onboarding_links (tenant_id, token, cliente_id,
                estado, es_portal, fecha_completado)
            VALUES ($1, $2, $3, 'completado', true, now())
        """, TENANT, token, cliente_id)

    log.info("portal_activado", cliente=str(cliente_id))
    return token


# ============================================================
# ENDPOINTS PÚBLICOS (acceso por token)
# ============================================================

@router.get("/{token}/data")
async def portal_home(token: str):
    """Datos del portal: cliente + contrato + próximas sesiones + saldo + asistencia mes."""
    link = await _verificar_token(token)
    cliente_id = link["cliente_id"]
    pool = await _get_pool()

    async with pool.acquire() as conn:
        # Contrato activo
        contrato = await conn.fetchrow("""
            SELECT co.*, g.nombre as grupo_nombre, g.dias_semana
            FROM om_contratos co
            LEFT JOIN om_grupos g ON g.id = co.grupo_id
            WHERE co.cliente_id = $1 AND co.tenant_id = $2 AND co.estado = 'activo'
            LIMIT 1
        """, cliente_id, TENANT)

        # Próximas sesiones (7 días)
        proximas = await conn.fetch("""
            SELECT s.id, s.fecha, s.hora_inicio, s.hora_fin, s.tipo,
                   g.nombre as grupo_nombre, a.estado as asistencia_estado, a.id as asistencia_id
            FROM om_asistencias a
            JOIN om_sesiones s ON s.id = a.sesion_id
            LEFT JOIN om_grupos g ON g.id = s.grupo_id
            WHERE a.cliente_id = $1 AND a.tenant_id = $2
                AND s.fecha >= CURRENT_DATE AND s.fecha <= CURRENT_DATE + 7
            ORDER BY s.fecha, s.hora_inicio
        """, cliente_id, TENANT)

        # Saldo pendiente
        saldo = await conn.fetchval("""
            SELECT COALESCE(SUM(total), 0) FROM om_cargos
            WHERE cliente_id = $1 AND tenant_id = $2 AND estado = 'pendiente'
        """, cliente_id, TENANT)

        # Asistencia este mes
        mes = date.today().replace(day=1)
        stats = await conn.fetchrow("""
            SELECT
                count(*) as total,
                count(*) FILTER (WHERE a.estado = 'asistio') as asistidas,
                count(*) FILTER (WHERE a.estado = 'no_vino') as faltas,
                count(*) FILTER (WHERE a.estado = 'cancelada') as canceladas
            FROM om_asistencias a
            JOIN om_sesiones s ON s.id = a.sesion_id
            WHERE a.cliente_id = $1 AND a.tenant_id = $2
                AND s.fecha >= $3 AND s.fecha < $3 + interval '1 month'
        """, cliente_id, TENANT, mes)

    return {
        "cliente": {
            "nombre": link["nombre"],
            "apellidos": link["apellidos"],
            "telefono": link["telefono"],
            "email": link["email"],
        },
        "contrato": _row_to_dict(contrato) if contrato else None,
        "proximas_sesiones": [_row_to_dict(s) for s in proximas],
        "saldo_pendiente": float(saldo),
        "asistencia_mes": {
            "total": stats["total"] if stats else 0,
            "asistidas": stats["asistidas"] if stats else 0,
            "faltas": stats["faltas"] if stats else 0,
            "canceladas": stats["canceladas"] if stats else 0,
        },
    }


@router.get("/{token}/sesiones")
async def portal_sesiones(token: str, mes: Optional[date] = None):
    """Historial de sesiones del mes."""
    link = await _verificar_token(token)
    cliente_id = link["cliente_id"]
    mes = mes or date.today().replace(day=1)
    pool = await _get_pool()

    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT s.fecha, s.hora_inicio, s.hora_fin, s.tipo,
                   g.nombre as grupo_nombre, a.estado, a.es_recuperacion,
                   a.notas_instructor
            FROM om_asistencias a
            JOIN om_sesiones s ON s.id = a.sesion_id
            LEFT JOIN om_grupos g ON g.id = s.grupo_id
            WHERE a.cliente_id = $1 AND a.tenant_id = $2
                AND s.fecha >= $3 AND s.fecha < $3 + interval '1 month'
            ORDER BY s.fecha DESC, s.hora_inicio DESC
        """, cliente_id, TENANT, mes)

    return {"mes": str(mes), "sesiones": [_row_to_dict(r) for r in rows]}


@router.post("/{token}/cancelar/{sesion_id}")
async def portal_cancelar(token: str, sesion_id: UUID):
    """El cliente cancela una sesión futura. Política auto-aplicada."""
    link = await _verificar_token(token)
    cliente_id = link["cliente_id"]
    pool = await _get_pool()

    async with pool.acquire() as conn:
        # Verificar asistencia
        asistencia = await conn.fetchrow("""
            SELECT a.id, s.fecha, s.hora_inicio, s.tipo
            FROM om_asistencias a
            JOIN om_sesiones s ON s.id = a.sesion_id
            WHERE a.sesion_id = $1 AND a.cliente_id = $2 AND a.estado = 'confirmada'
        """, sesion_id, cliente_id)

        if not asistencia:
            raise HTTPException(404, "Sesión no encontrada o ya cancelada")

        if asistencia["fecha"] < date.today():
            raise HTTPException(400, "No se pueden cancelar sesiones pasadas")

        # Calcular si hay cargo
        sesion_dt = datetime.combine(asistencia["fecha"], asistencia["hora_inicio"])
        horas_antes = (sesion_dt - datetime.now()).total_seconds() / 3600
        hay_cargo = horas_antes < 12 and asistencia["tipo"] == "individual"

        async with conn.transaction():
            await conn.execute("""
                UPDATE om_asistencias SET estado = 'cancelada', hora_cancelacion = now()
                WHERE id = $1
            """, asistencia["id"])

            if hay_cargo:
                contrato = await conn.fetchrow("""
                    SELECT precio_sesion FROM om_contratos
                    WHERE cliente_id = $1 AND tenant_id = $2 AND tipo = 'individual' AND estado = 'activo'
                """, cliente_id, TENANT)
                precio = float(contrato["precio_sesion"]) if contrato and contrato["precio_sesion"] else 35.00
                await conn.execute("""
                    INSERT INTO om_cargos (tenant_id, cliente_id, tipo, descripcion,
                        base_imponible, sesion_id)
                    VALUES ($1, $2, 'cancelacion_tardia', $3, $4, $5)
                """, TENANT, cliente_id,
                    f"Cancelación tardía {asistencia['fecha']}", precio, sesion_id)

    log.info("portal_cancelacion", cliente=str(cliente_id), sesion=str(sesion_id),
             cargo=hay_cargo)
    return {
        "status": "cancelada",
        "cargo": hay_cargo,
        "mensaje": "Cancelación tardía — se aplicará cargo" if hay_cargo
                   else "Sesión cancelada sin cargo",
    }


@router.get("/{token}/recuperaciones")
async def portal_recuperaciones_disponibles(token: str):
    """Huecos disponibles para recuperar (grupos con plaza libre en los próximos 7 días)."""
    link = await _verificar_token(token)
    cliente_id = link["cliente_id"]
    pool = await _get_pool()

    async with pool.acquire() as conn:
        mes = date.today().replace(day=1)
        faltas = await conn.fetchval("""
            SELECT count(*) FROM om_asistencias a
            JOIN om_sesiones s ON s.id = a.sesion_id
            WHERE a.cliente_id = $1 AND a.tenant_id = $2
                AND a.estado = 'no_vino' AND s.fecha >= $3
        """, cliente_id, TENANT, mes)

        recuperaciones_hechas = await conn.fetchval("""
            SELECT count(*) FROM om_asistencias a
            JOIN om_sesiones s ON s.id = a.sesion_id
            WHERE a.cliente_id = $1 AND a.tenant_id = $2
                AND a.es_recuperacion = true AND a.estado = 'asistio'
                AND s.fecha >= $3
        """, cliente_id, TENANT, mes)

        if recuperaciones_hechas >= faltas:
            return {
                "puede_recuperar": False,
                "faltas": faltas,
                "recuperaciones": recuperaciones_hechas,
                "huecos": [],
                "mensaje": "No tienes faltas pendientes de recuperar",
            }

        # Buscar huecos: sesiones futuras de grupos con plaza libre
        hoy = date.today()
        huecos = await conn.fetch("""
            SELECT s.id as sesion_id, s.fecha, s.hora_inicio, s.hora_fin,
                   g.nombre as grupo_nombre, g.capacidad_max,
                   (SELECT count(*) FROM om_asistencias a2
                    WHERE a2.sesion_id = s.id AND a2.estado IN ('confirmada','asistio','recuperacion')) as ocupadas
            FROM om_sesiones s
            JOIN om_grupos g ON g.id = s.grupo_id
            WHERE s.tenant_id = $1 AND s.fecha > $2 AND s.fecha <= $2 + 7
                AND s.estado = 'programada'
            ORDER BY s.fecha, s.hora_inicio
        """, TENANT, hoy)

        huecos_libres = []
        for h in huecos:
            if h["ocupadas"] < h["capacidad_max"]:
                huecos_libres.append({
                    "sesion_id": str(h["sesion_id"]),
                    "fecha": str(h["fecha"]),
                    "hora": str(h["hora_inicio"])[:5],
                    "grupo": h["grupo_nombre"],
                    "plazas_libres": h["capacidad_max"] - h["ocupadas"],
                })

    return {
        "puede_recuperar": True,
        "faltas": faltas,
        "recuperaciones": recuperaciones_hechas,
        "huecos": huecos_libres,
    }


class SolicitudRecuperacion(BaseModel):
    sesion_id: UUID

@router.post("/{token}/recuperar")
async def portal_solicitar_recuperacion(token: str, data: SolicitudRecuperacion):
    """El cliente solicita recuperar en un hueco disponible."""
    link = await _verificar_token(token)
    cliente_id = link["cliente_id"]
    pool = await _get_pool()

    async with pool.acquire() as conn:
        sesion = await conn.fetchrow("""
            SELECT s.*, g.capacidad_max,
                   (SELECT count(*) FROM om_asistencias a
                    WHERE a.sesion_id = s.id AND a.estado IN ('confirmada','asistio','recuperacion')) as ocupadas
            FROM om_sesiones s
            JOIN om_grupos g ON g.id = s.grupo_id
            WHERE s.id = $1 AND s.tenant_id = $2
        """, data.sesion_id, TENANT)

        if not sesion:
            raise HTTPException(404, "Sesión no encontrada")
        if sesion["ocupadas"] >= sesion["capacidad_max"]:
            raise HTTPException(409, "Ya no hay plaza en este grupo")
        if sesion["fecha"] <= date.today():
            raise HTTPException(400, "Solo puedes recuperar en sesiones futuras")

        ya_inscrito = await conn.fetchval("""
            SELECT 1 FROM om_asistencias
            WHERE sesion_id = $1 AND cliente_id = $2
        """, data.sesion_id, cliente_id)
        if ya_inscrito:
            raise HTTPException(409, "Ya estás inscrito en esta sesión")

        await conn.execute("""
            INSERT INTO om_asistencias (tenant_id, sesion_id, cliente_id, estado, es_recuperacion)
            VALUES ($1, $2, $3, 'recuperacion', true)
        """, TENANT, data.sesion_id, cliente_id)

    log.info("portal_recuperacion_solicitada", cliente=str(cliente_id),
             sesion=str(data.sesion_id))
    return {
        "status": "solicitada",
        "mensaje": "Recuperación solicitada. Te confirmaremos por WhatsApp.",
    }


@router.get("/{token}/pagos")
async def portal_pagos(token: str, limit: int = 20):
    """Historial de pagos del cliente."""
    link = await _verificar_token(token)
    cliente_id = link["cliente_id"]
    pool = await _get_pool()

    async with pool.acquire() as conn:
        pagos = await conn.fetch("""
            SELECT p.id, p.metodo, p.monto, p.fecha_pago, p.notas
            FROM om_pagos p
            WHERE p.cliente_id = $1 AND p.tenant_id = $2
            ORDER BY p.fecha_pago DESC
            LIMIT $3
        """, cliente_id, TENANT, limit)

        saldo = await conn.fetchval("""
            SELECT COALESCE(SUM(total), 0) FROM om_cargos
            WHERE cliente_id = $1 AND tenant_id = $2 AND estado = 'pendiente'
        """, cliente_id, TENANT)

    return {
        "pagos": [_row_to_dict(p) for p in pagos],
        "saldo_pendiente": float(saldo),
    }


@router.get("/{token}/facturas")
async def portal_facturas(token: str):
    """Facturas del cliente con enlace a PDF."""
    link = await _verificar_token(token)
    cliente_id = link["cliente_id"]
    pool = await _get_pool()

    async with pool.acquire() as conn:
        facturas = await conn.fetch("""
            SELECT id, numero_factura, fecha_emision, base_imponible,
                   iva_monto, total, estado
            FROM om_facturas
            WHERE cliente_id = $1 AND tenant_id = $2 AND estado = 'emitida'
            ORDER BY fecha_emision DESC
        """, cliente_id, TENANT)

    return {
        "facturas": [{
            **_row_to_dict(f),
            "pdf_url": f"/pilates/facturas/{f['id']}/pdf",
        } for f in facturas],
    }


# ============================================================
# PORTAL CONVERSACIONAL
# ============================================================

class ChatRequest(BaseModel):
    mensaje: str
    historial: Optional[list] = None

@router.post("/{token}/chat")
async def portal_chat(token: str, data: ChatRequest):
    """Portal conversacional — el cliente habla en lenguaje natural."""
    from src.pilates.portal_chat import chat
    return await chat(token, data.mensaje, data.historial)


# ============================================================
# RGPD — Derechos del interesado
# ============================================================

@router.get("/{token}/mis-datos")
async def mis_datos(token: str):
    """RGPD: El cliente puede ver todos sus datos."""
    import json as _json
    link = await _verificar_token(token)
    cliente_id = link["cliente_id"]
    pool = await _get_pool()

    async with pool.acquire() as conn:
        cliente = await conn.fetchrow(
            "SELECT * FROM om_clientes WHERE id = $1", cliente_id)
        if not cliente:
            raise HTTPException(404, "Cliente no encontrado")

        datos = dict(cliente)
        for k, v in datos.items():
            if hasattr(v, 'isoformat'):
                datos[k] = v.isoformat()
            elif hasattr(v, 'hex'):
                datos[k] = str(v)

        contratos = await conn.fetch(
            "SELECT * FROM om_contratos WHERE cliente_id=$1", cliente_id)
        datos["contratos"] = [dict(c) for c in contratos]

        pagos = await conn.fetch(
            "SELECT * FROM om_pagos WHERE cliente_id=$1 ORDER BY fecha_pago DESC LIMIT 50",
            cliente_id)
        datos["pagos"] = [dict(p) for p in pagos]

        asistencias = await conn.fetch("""
            SELECT a.*, s.fecha, s.hora_inicio FROM om_asistencias a
            JOIN om_sesiones s ON s.id = a.sesion_id
            WHERE a.cliente_id=$1 ORDER BY s.fecha DESC LIMIT 100
        """, cliente_id)
        datos["asistencias"] = [dict(a) for a in asistencias]

    return _json.loads(_json.dumps(datos, default=str))


@router.post("/{token}/solicitar-baja")
async def solicitar_baja(token: str, motivo: str = ""):
    """RGPD: El cliente solicita eliminación de datos."""
    import os as _os
    link = await _verificar_token(token)
    cliente_id = link["cliente_id"]
    nombre = link.get("nombre", "")
    pool = await _get_pool()

    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO om_solicitudes_baja (tenant_id, cliente_id, motivo)
            VALUES ('authentic_pilates', $1, $2)
        """, cliente_id, motivo or "Sin motivo especificado")

    # Notificar a Jesús por WA
    try:
        from src.pilates.whatsapp import enviar_texto, is_configured
        telefono_jesus = _os.getenv("JESUS_TELEFONO", "")
        if is_configured() and telefono_jesus:
            await enviar_texto(
                telefono_jesus,
                f"⚠️ Solicitud de baja RGPD de {nombre}. Revisar en admin.",
            )
    except Exception as e:
        log.debug("silenced_exception", exc=str(e))

    return {"status": "ok", "mensaje": "Solicitud registrada. Te contactaremos en 48h."}
