"""WhatsApp Business Cloud API — Integración bidireccional.

Recibe mensajes via webhook, envía via API.
Clasifica intención de mensajes entrantes.
Almacena todo en om_mensajes_wa.

Fuente: Exocortex v2.1 S7.
"""
from __future__ import annotations

import os
import httpx
import structlog
from datetime import datetime
from typing import Optional
from uuid import UUID

log = structlog.get_logger()

TENANT = "authentic_pilates"

# Config desde env (fly.io secrets)
WA_TOKEN = os.getenv("WHATSAPP_TOKEN")
WA_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID")
WA_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "omni_mind_verify_2026")
WA_API_BASE = "https://graph.facebook.com/v19.0"


def is_configured() -> bool:
    return bool(WA_TOKEN and WA_PHONE_ID)


# ============================================================
# ENVIAR MENSAJES
# ============================================================

async def enviar_texto(telefono: str, mensaje: str, cliente_id: Optional[UUID] = None) -> dict:
    """Envía mensaje de texto por WhatsApp."""
    if not is_configured():
        return {"status": "error", "detail": "WhatsApp no configurado"}

    # Normalizar teléfono: quitar + y espacios
    telefono = telefono.replace("+", "").replace(" ", "").replace("-", "")
    if not telefono.startswith("34"):
        telefono = f"34{telefono}"

    url = f"{WA_API_BASE}/{WA_PHONE_ID}/messages"
    headers = {"Authorization": f"Bearer {WA_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "to": telefono,
        "type": "text",
        "text": {"body": mensaje},
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            wa_message_id = data.get("messages", [{}])[0].get("id")

            await _registrar_mensaje(
                direccion="saliente",
                remitente=WA_PHONE_ID,
                destinatario=telefono,
                cliente_id=cliente_id,
                tipo_contenido="texto",
                contenido=mensaje,
                wa_message_id=wa_message_id,
            )

            log.info("wa_enviado", telefono=telefono[-4:], chars=len(mensaje))
            return {"status": "sent", "wa_message_id": wa_message_id}

    except httpx.HTTPStatusError as e:
        log.error("wa_envio_error", status=e.response.status_code, detail=str(e))
        return {"status": "error", "detail": str(e)}
    except Exception as e:
        log.error("wa_envio_exception", error=str(e))
        return {"status": "error", "detail": str(e)}


async def enviar_botones(telefono: str, mensaje: str, botones: list[dict],
                          cliente_id: Optional[UUID] = None) -> dict:
    """Envía mensaje con botones interactivos (máx 3)."""
    if not is_configured():
        return {"status": "error", "detail": "WhatsApp no configurado"}

    telefono = telefono.replace("+", "").replace(" ", "").replace("-", "")
    if not telefono.startswith("34"):
        telefono = f"34{telefono}"

    url = f"{WA_API_BASE}/{WA_PHONE_ID}/messages"
    headers = {"Authorization": f"Bearer {WA_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "to": telefono,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": mensaje},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": b["id"], "title": b["titulo"][:20]}}
                    for b in botones[:3]
                ],
            },
        },
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            wa_message_id = data.get("messages", [{}])[0].get("id")

            await _registrar_mensaje(
                direccion="saliente", remitente=WA_PHONE_ID, destinatario=telefono,
                cliente_id=cliente_id, tipo_contenido="texto",
                contenido=f"{mensaje} [botones: {', '.join(b['titulo'] for b in botones)}]",
                wa_message_id=wa_message_id,
            )
            return {"status": "sent", "wa_message_id": wa_message_id}

    except Exception as e:
        log.error("wa_botones_error", error=str(e))
        return {"status": "error", "detail": str(e)}


# ============================================================
# PROCESAR WEBHOOK (mensajes entrantes)
# ============================================================

async def procesar_webhook(body: dict) -> dict:
    """Procesa webhook de WhatsApp Cloud API."""
    procesados = 0
    entry = body.get("entry", [])

    for e in entry:
        changes = e.get("changes", [])
        for change in changes:
            value = change.get("value", {})
            messages = value.get("messages", [])

            for msg in messages:
                await _procesar_mensaje_entrante(msg, value)
                procesados += 1

    return {"procesados": procesados}


async def _procesar_mensaje_entrante(msg: dict, value: dict) -> None:
    """Procesa un mensaje entrante individual."""
    telefono = msg.get("from", "")
    wa_message_id = msg.get("id")
    timestamp = msg.get("timestamp")
    msg_type = msg.get("type", "text")

    # Extraer contenido según tipo
    contenido = ""
    tipo_contenido = "texto"
    media_url = None

    if msg_type == "text":
        contenido = msg.get("text", {}).get("body", "")
    elif msg_type == "interactive":
        interactive = msg.get("interactive", {})
        if interactive.get("type") == "button_reply":
            contenido = interactive.get("button_reply", {}).get("id", "")
        elif interactive.get("type") == "list_reply":
            contenido = interactive.get("list_reply", {}).get("id", "")
    elif msg_type in ("image", "video", "audio", "document"):
        tipo_contenido = msg_type.replace("image", "imagen")
        media = msg.get(msg_type, {})
        media_url = media.get("id")
        contenido = media.get("caption", f"[{msg_type}]")
    else:
        tipo_contenido = msg_type
        contenido = f"[{msg_type}]"

    # Buscar cliente por teléfono
    cliente_id = await _buscar_cliente_por_telefono(telefono)

    # Clasificar intención
    intencion = _clasificar_intencion(contenido, telefono, cliente_id)

    # Generar acción sugerida
    accion = _generar_accion(intencion, contenido, cliente_id)

    # Registrar
    await _registrar_mensaje(
        direccion="entrante",
        remitente=telefono,
        destinatario=WA_PHONE_ID or "negocio",
        cliente_id=cliente_id,
        tipo_contenido=tipo_contenido,
        contenido=contenido,
        media_url=media_url,
        intencion=intencion,
        accion_generada=accion,
        wa_message_id=wa_message_id,
        wa_timestamp=datetime.fromtimestamp(int(timestamp)) if timestamp else None,
    )

    # Procesar respuestas a botones automáticamente
    if msg_type == "interactive" and cliente_id:
        from src.pilates.wa_respuestas import procesar_respuesta_boton
        result = await procesar_respuesta_boton(cliente_id, contenido)
        if result.get("mensaje"):
            await enviar_texto(telefono, result["mensaje"], cliente_id)
        accion = result.get("accion", accion)

    # Motor conversacional WA — procesar con LLM si es texto
    if msg_type == "text" and contenido:
        try:
            from src.pilates.wa_chat import procesar_mensaje_wa
            result = await procesar_mensaje_wa(telefono, contenido, cliente_id)
            if result.get("auto_enviar") and result.get("respuesta"):
                await enviar_texto(telefono, result["respuesta"], cliente_id)
                log.info("wa_chat_auto", telefono=telefono[-4:])
        except Exception as e:
            log.error("wa_chat_error", error=str(e))

    log.info("wa_recibido", telefono=telefono[-4:], tipo=msg_type,
             intencion=intencion, cliente_conocido=cliente_id is not None)


# ============================================================
# CLASIFICACIÓN DE INTENCIÓN
# ============================================================

def _clasificar_intencion(contenido: str, telefono: str, cliente_id: Optional[UUID]) -> str:
    """Clasifica intención del mensaje. Reglas heurísticas v0."""
    texto = contenido.lower().strip()

    # Respuestas a botones (confirmación pre-sesión)
    if texto in ("si_voy", "confirmar_asistencia"):
        return "reserva"
    if texto in ("no_puedo", "cancelar_sesion"):
        return "cancelacion"

    # Palabras clave
    if any(w in texto for w in ["precio", "cuanto", "cuesta", "tarifa", "coste"]):
        return "consulta_precio"
    if any(w in texto for w in ["horario", "hora", "cuando", "disponible", "hueco"]):
        return "consulta_horario"
    if any(w in texto for w in ["reserv", "apunt", "inscrib", "quiero ir", "puedo ir"]):
        return "reserva"
    if any(w in texto for w in ["cancel", "no puedo", "no voy", "anular"]):
        return "cancelacion"
    if any(w in texto for w in ["queja", "mal", "problema", "enfadad", "molest"]):
        return "queja"
    if any(w in texto for w in ["genial", "bien", "gracias", "encant", "gusto"]):
        return "feedback"

    # Si es cliente desconocido, probablemente es lead
    if cliente_id is None:
        return "otro"

    return "otro"


def _generar_accion(intencion: str, contenido: str, cliente_id: Optional[UUID]) -> str:
    """Genera acción sugerida para el panel WA del Modo Estudio."""
    acciones = {
        "consulta_precio": "responder_precios",
        "consulta_horario": "responder_horarios",
        "reserva": "crear_sesion" if cliente_id else "enviar_onboarding",
        "cancelacion": "cancelar_sesion",
        "feedback": "agradecer",
        "queja": "alerta_urgente",
        "otro": "responder_manual",
    }
    return acciones.get(intencion, "responder_manual")


# ============================================================
# HELPERS DB
# ============================================================

async def _buscar_cliente_por_telefono(telefono: str) -> Optional[UUID]:
    """Busca cliente por teléfono. Normaliza formato."""
    from src.db.client import get_pool
    pool = await get_pool()

    tel_limpio = telefono.replace("+", "").replace(" ", "")
    variantes = [tel_limpio]
    if tel_limpio.startswith("34"):
        variantes.append(tel_limpio[2:])
    else:
        variantes.append(f"34{tel_limpio}")

    async with pool.acquire() as conn:
        for tel in variantes:
            row = await conn.fetchrow("""
                SELECT c.id FROM om_clientes c
                JOIN om_cliente_tenant ct ON ct.cliente_id = c.id AND ct.tenant_id = $1
                WHERE c.telefono LIKE $2
            """, TENANT, f"%{tel[-9:]}")
            if row:
                return row["id"]
    return None


async def _registrar_mensaje(
    direccion: str, remitente: str, destinatario: str,
    cliente_id: Optional[UUID] = None, tipo_contenido: str = "texto",
    contenido: str = "", media_url: str = None,
    intencion: str = None, accion_generada: str = None,
    wa_message_id: str = None, wa_timestamp=None,
) -> UUID:
    """Registra mensaje en om_mensajes_wa."""
    from src.db.client import get_pool
    pool = await get_pool()

    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO om_mensajes_wa (tenant_id, direccion, remitente, destinatario,
                cliente_id, tipo_contenido, contenido, media_url,
                intencion, accion_generada, wa_message_id, wa_timestamp)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)
            RETURNING id
        """, TENANT, direccion, remitente, destinatario,
            cliente_id, tipo_contenido, contenido, media_url,
            intencion, accion_generada, wa_message_id, wa_timestamp)
    return row["id"]


# ============================================================
# CONFIRMACIÓN PRE-SESIÓN (24h antes)
# ============================================================

async def enviar_confirmaciones_manana() -> dict:
    """Envía confirmación pre-sesión a todos los alumnos con sesión mañana."""
    from datetime import date, timedelta
    from src.db.client import get_pool

    manana = date.today() + timedelta(days=1)
    pool = await get_pool()
    enviados = 0
    errores = 0

    async with pool.acquire() as conn:
        asistencias = await conn.fetch("""
            SELECT a.id as asistencia_id, a.cliente_id,
                   c.nombre, c.telefono,
                   s.hora_inicio, s.tipo,
                   g.nombre as grupo_nombre
            FROM om_asistencias a
            JOIN om_clientes c ON c.id = a.cliente_id
            JOIN om_sesiones s ON s.id = a.sesion_id
            LEFT JOIN om_grupos g ON g.id = s.grupo_id
            WHERE s.tenant_id = $1 AND s.fecha = $2
                AND a.estado = 'confirmada'
                AND c.telefono IS NOT NULL
        """, TENANT, manana)

        for a in asistencias:
            if not a["telefono"]:
                continue

            hora = str(a["hora_inicio"])[:5]
            tipo = a["grupo_nombre"] or "sesión individual"
            mensaje = f"Hola {a['nombre']}! Mañana tienes Pilates a las {hora} ({tipo}). ¿Vienes?"

            result = await enviar_botones(
                telefono=a["telefono"],
                mensaje=mensaje,
                botones=[
                    {"id": "si_voy", "titulo": "Sí, voy"},
                    {"id": "no_puedo", "titulo": "No puedo"},
                ],
                cliente_id=a["cliente_id"],
            )

            if result["status"] == "sent":
                enviados += 1
            else:
                errores += 1

    log.info("confirmaciones_enviadas", fecha=str(manana), enviados=enviados, errores=errores)
    return {"fecha": str(manana), "enviados": enviados, "errores": errores}


# ============================================================
# LEAD AUTOMÁTICO (primer contacto)
# ============================================================

async def respuesta_lead_automatico(telefono: str, nombre_contacto: str = "") -> dict:
    """Genera respuesta automática para primer contacto WA."""
    import secrets
    from src.db.client import get_pool
    pool = await get_pool()

    # Generar enlace onboarding
    token = secrets.token_urlsafe(32)
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO om_onboarding_links (tenant_id, token, nombre_provisional, telefono,
                fecha_expiracion)
            VALUES ($1, $2, $3, $4, now() + interval '7 days')
        """, TENANT, token, nombre_contacto or "Nuevo contacto", telefono)

    base_url = "https://motor-semantico-omni.fly.dev"
    enlace = f"{base_url}/onboarding/{token}"

    mensaje = (
        f"¡Hola{' ' + nombre_contacto if nombre_contacto else ''}! "
        f"Bienvenido/a a Authentic Pilates.\n\n"
        f"Tenemos sesiones individuales desde 30€ y grupos reducidos "
        f"(máx 4 personas) a 105€/mes.\n\n"
        f"Si te interesa, rellena esta ficha y te proponemos una clase de prueba:\n"
        f"{enlace}"
    )

    result = await enviar_texto(telefono, mensaje)
    return {**result, "enlace_onboarding": enlace}
