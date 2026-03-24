"""Sub-router: WhatsApp webhook, mensajes, envío."""
from __future__ import annotations

import asyncio
import json
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request

from src.pilates.router import (
    TENANT, log, _get_pool, _row_to_dict,
)

router = APIRouter(tags=["whatsapp"])


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
    import hashlib, hmac, os as _os
    app_secret = _os.getenv("WHATSAPP_APP_SECRET", "")
    if app_secret:
        signature = request.headers.get("X-Hub-Signature-256", "")
        raw_body = await request.body()
        expected = "sha256=" + hmac.new(
            app_secret.encode(), raw_body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            log.warning("wa_webhook_firma_invalida")
            raise HTTPException(403, "Firma inválida")
        body = json.loads(raw_body)
    else:
        body = await request.json()
    from src.pilates.whatsapp import procesar_webhook
    result = await procesar_webhook(body)

    # B2.9 Reactivo: emitir señales al bus tras procesar el mensaje
    if result.get("mensaje_guardado"):
        asyncio.create_task(_wa_reactivo(result))

    return {"status": "ok", **result}


async def _wa_reactivo(result: dict):
    """Fire-and-forget: WA webhook -> señales al bus."""
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
