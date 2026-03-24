"""Reactivo — Responde a señales urgentes en tiempo real (P66).

No espera al lunes. Escucha LISTEN/NOTIFY de señales prioridad ≤ 2
y actúa inmediatamente:
  - Lead nuevo → respuesta <5 min
  - Pago recibido → confirmar por WA
  - Cancelación → ofrecer alternativa
  - Queja → escalar a Jesús
"""
from __future__ import annotations

import json
import structlog
from datetime import datetime
from zoneinfo import ZoneInfo

from src.db.client import get_pool

log = structlog.get_logger()

TENANT = "authentic_pilates"


async def procesar_senal_urgente(payload: dict) -> dict:
    """Procesa una señal urgente recibida via LISTEN/NOTIFY.

    Llamado desde el listener en cron.py cuando llega una señal p≤2.
    """
    tipo = payload.get("tipo", "")
    origen = payload.get("origen", "")
    senal_id = payload.get("id", "")

    log.info("reactivo_procesando", tipo=tipo, origen=origen, id=senal_id)

    pool = await get_pool()
    async with pool.acquire() as conn:
        # Leer señal completa
        senal = await conn.fetchrow(
            "SELECT * FROM om_senales_agentes WHERE id = $1", senal_id)
        if not senal:
            return {"status": "senal_no_encontrada"}

        senal_payload = senal["payload"] if isinstance(senal["payload"], dict) else json.loads(senal["payload"] or "{}")

    # Dispatch por tipo de señal
    if tipo == "ALERTA" and senal_payload.get("subtipo") == "lead_nuevo":
        return await _responder_lead(senal_payload)
    elif tipo == "ALERTA" and senal_payload.get("subtipo") == "pago_recibido":
        return await _confirmar_pago(senal_payload)
    elif tipo == "ALERTA" and senal_payload.get("subtipo") == "cancelacion":
        return await _ofrecer_alternativa(senal_payload)
    elif tipo == "ALERTA" and senal_payload.get("subtipo") == "queja":
        return await _escalar_queja(senal_payload)
    else:
        log.info("reactivo_skip", tipo=tipo, razon="no_handler")
        return {"status": "skip", "tipo": tipo}


async def _responder_lead(payload: dict) -> dict:
    """Lead nuevo detectado — programar respuesta en pizarra comunicación."""
    telefono = payload.get("telefono", "")
    nombre = payload.get("nombre", "")

    if not telefono:
        return {"status": "sin_telefono"}

    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO om_pizarra_comunicacion
                (tenant_id, destinatario, destinatario_nombre, canal, tipo, mensaje,
                 programado_para, estado, origen)
            VALUES ($1, $2, $3, 'whatsapp', 'respuesta_lead', $4, now(), 'pendiente', 'REACTIVO')
        """, TENANT, telefono, nombre,
            f"Hola{' ' + nombre if nombre else ''}! Gracias por escribir a Authentic Pilates. "
            f"Tenemos grupos reducidos (máx 4 personas) y sesiones individuales. "
            f"¿Te cuento más?")

    log.info("reactivo_lead_programado", telefono=telefono[-4:])
    return {"status": "programado", "tipo": "respuesta_lead"}


async def _confirmar_pago(payload: dict) -> dict:
    """Pago recibido — confirmar al cliente por WA."""
    cliente_id = payload.get("cliente_id")
    importe = payload.get("importe", 0)

    if not cliente_id:
        return {"status": "sin_cliente"}

    pool = await get_pool()
    async with pool.acquire() as conn:
        cliente = await conn.fetchrow(
            "SELECT nombre, telefono FROM om_clientes WHERE id = $1", cliente_id)
        if not cliente or not cliente["telefono"]:
            return {"status": "sin_telefono"}

        await conn.execute("""
            INSERT INTO om_pizarra_comunicacion
                (tenant_id, destinatario, destinatario_nombre, cliente_id,
                 canal, tipo, mensaje, programado_para, estado, origen)
            VALUES ($1, $2, $3, $4, 'whatsapp', 'confirmacion_pago', $5,
                    now(), 'pendiente', 'REACTIVO')
        """, TENANT, cliente["telefono"], cliente["nombre"], cliente_id,
            f"Hola {cliente['nombre']}! Hemos recibido tu pago de {importe:.2f}€. ¡Gracias!")

    return {"status": "programado", "tipo": "confirmacion_pago"}


async def _ofrecer_alternativa(payload: dict) -> dict:
    """Cancelación detectada — programar oferta de alternativa."""
    cliente_id = payload.get("cliente_id")
    if not cliente_id:
        return {"status": "sin_cliente"}

    pool = await get_pool()
    async with pool.acquire() as conn:
        cliente = await conn.fetchrow(
            "SELECT nombre, telefono FROM om_clientes WHERE id = $1", cliente_id)
        if not cliente or not cliente["telefono"]:
            return {"status": "sin_telefono"}

        await conn.execute("""
            INSERT INTO om_pizarra_comunicacion
                (tenant_id, destinatario, destinatario_nombre, cliente_id,
                 canal, tipo, mensaje, programado_para, estado, origen)
            VALUES ($1, $2, $3, $4, 'whatsapp', 'oferta_alternativa', $5,
                    now() + interval '1 hour', 'pendiente', 'REACTIVO')
        """, TENANT, cliente["telefono"], cliente["nombre"], cliente_id,
            f"Hola {cliente['nombre']}, hemos visto que has cancelado tu sesión. "
            f"¿Te viene mejor otro horario esta semana? Podemos buscar hueco.")

    return {"status": "programado", "tipo": "oferta_alternativa"}


async def _escalar_queja(payload: dict) -> dict:
    """Queja detectada — avisar a Jesús inmediatamente."""
    import os
    telefono_jesus = os.getenv("JESUS_TELEFONO", "")
    if not telefono_jesus:
        return {"status": "sin_telefono_jesus"}

    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO om_pizarra_comunicacion
                (tenant_id, destinatario, canal, tipo, mensaje,
                 programado_para, estado, origen, metadata)
            VALUES ($1, $2, 'whatsapp', 'escalacion_queja', $3,
                    now(), 'pendiente', 'REACTIVO', $4::jsonb)
        """, TENANT, telefono_jesus,
            f"Queja de cliente: {payload.get('contenido', 'sin detalle')[:200]}",
            json.dumps(payload))

    return {"status": "programado", "tipo": "escalacion_queja"}


# ============================================================
# DESPACHADOR DE COMUNICACIONES PENDIENTES
# ============================================================

async def despachar_comunicaciones() -> dict:
    """Lee om_pizarra_comunicacion pendientes y las envía.

    Se ejecuta cada 15 min (desde cron_loop vigía).
    """
    pool = await get_pool()
    enviados = 0
    errores = 0

    async with pool.acquire() as conn:
        pendientes = await conn.fetch("""
            SELECT * FROM om_pizarra_comunicacion
            WHERE tenant_id = $1 AND estado = 'pendiente'
                AND (programado_para IS NULL OR programado_para <= now())
            ORDER BY programado_para ASC NULLS FIRST
            LIMIT 20
        """, TENANT)

        for p in pendientes:
            if p["canal"] == "whatsapp":
                try:
                    from src.pilates.whatsapp import enviar_texto, is_configured
                    if not is_configured():
                        continue

                    result = await enviar_texto(
                        p["destinatario"], p["mensaje"], p["cliente_id"])

                    if result.get("status") == "sent":
                        await conn.execute("""
                            UPDATE om_pizarra_comunicacion
                            SET estado = 'enviado', wa_message_id = $2,
                                updated_at = now()
                            WHERE id = $1
                        """, p["id"], result.get("wa_message_id"))
                        enviados += 1
                    else:
                        await conn.execute("""
                            UPDATE om_pizarra_comunicacion
                            SET estado = 'error', error = $2, updated_at = now()
                            WHERE id = $1
                        """, p["id"], result.get("detail", "unknown")[:200])
                        errores += 1

                except Exception as e:
                    await conn.execute("""
                        UPDATE om_pizarra_comunicacion
                        SET estado = 'error', error = $2, updated_at = now()
                        WHERE id = $1
                    """, p["id"], str(e)[:200])
                    errores += 1

    if enviados > 0 or errores > 0:
        log.info("despachar_ok", enviados=enviados, errores=errores)
    return {"enviados": enviados, "errores": errores}
