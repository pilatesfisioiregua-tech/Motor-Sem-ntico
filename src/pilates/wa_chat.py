"""WhatsApp Conversacional — Motor LLM sobre mensajes WA.

Reutiliza el motor de portal_chat.py pero adaptado a WhatsApp:
- Sin historial visual (cada mensaje es standalone o con contexto corto)
- Respuestas más cortas (WA no es para párrafos)
- Acciones destructivas: el bot pide confirmación por WA
- Si no es cliente: redirige al portal público

Fuente: Exocortex v2.1 B-PIL-18 Fase H.
"""
from __future__ import annotations
import json, os, structlog
from datetime import date
from uuid import UUID
from typing import Optional

log = structlog.get_logger()
TENANT = "authentic_pilates"


async def _get_pool():
    from src.db.client import get_pool
    return await get_pool()


# Cache de conversaciones WA en memoria (últimos 5 mensajes por teléfono)
# En producción usar Redis, pero para MVP dict en memoria vale
_wa_historial: dict[str, list] = {}


async def procesar_mensaje_wa(telefono: str, mensaje: str,
                                cliente_id: Optional[UUID] = None) -> dict:
    """Procesa mensaje WA entrante con el motor conversacional.

    Si es cliente → usa portal_chat.py con sus herramientas
    Si NO es cliente → respuesta de captación (portal público)

    Returns:
        {"respuesta": str, "auto_enviar": bool}
    """
    # Identificar si es cliente
    if not cliente_id:
        pool = await _get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT c.id FROM om_clientes c
                JOIN om_cliente_tenant ct ON ct.cliente_id=c.id
                WHERE ct.tenant_id=$1 AND c.telefono LIKE '%' || $2
                    AND ct.estado='activo'
            """, TENANT, telefono[-9:])
            if row:
                cliente_id = row["id"]

    if cliente_id:
        return await _procesar_cliente(telefono, mensaje, cliente_id)
    else:
        return await _procesar_lead(telefono, mensaje)


async def _procesar_cliente(telefono: str, mensaje: str, cliente_id: UUID) -> dict:
    """Procesa mensaje de cliente conocido — usa motor portal_chat."""

    # Obtener token del portal para reutilizar portal_chat.chat()
    pool = await _get_pool()
    async with pool.acquire() as conn:
        token = await conn.fetchval("""
            SELECT token FROM om_onboarding_links
            WHERE cliente_id=$1 AND tenant_id=$2 AND es_portal=true
        """, cliente_id, TENANT)

    if not token:
        return {
            "respuesta": "Oye, no te tengo localizado en el sistema. "
                         "¿Me dices tu nombre completo?",
            "auto_enviar": True
        }

    # Recuperar historial WA (últimos mensajes)
    historial = _wa_historial.get(telefono, [])

    # Usar el motor de portal_chat
    from src.pilates.portal_chat import chat
    result = await chat(token, mensaje, historial)

    # Guardar historial (máx 10 mensajes)
    historial.append({"role": "user", "content": mensaje})
    historial.append({"role": "assistant", "content": result["respuesta"]})
    _wa_historial[telefono] = historial[-10:]

    # Registrar evento
    from src.pilates.engagement import registrar_evento
    await registrar_evento(cliente_id, "wa_chat_entrante", {
        "mensaje": mensaje[:200],
        "tools": result.get("tools_usadas", [])
    })

    # Adaptar respuesta para WA (más corta)
    respuesta = result["respuesta"]
    # Truncar si es muy largo para WA
    if len(respuesta) > 1000:
        respuesta = respuesta[:950] + "\n\n(Más detalles en tu portal)"

    return {"respuesta": respuesta, "auto_enviar": True}


async def _procesar_lead(telefono: str, mensaje: str) -> dict:
    """Procesa mensaje de persona NO cliente — captación.

    Usa el motor del portal público (Fase I).
    """
    from src.pilates.portal_publico import chat_captacion
    result = await chat_captacion(mensaje, telefono)

    return {
        "respuesta": result["respuesta"],
        "auto_enviar": True
    }
