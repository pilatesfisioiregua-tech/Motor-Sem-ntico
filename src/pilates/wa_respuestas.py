"""Generador de respuestas WA basadas en datos reales.

Cada intención tiene una función que consulta la DB y genera
la respuesta con datos actuales (precios, plazas, horarios).

Fuente: Exocortex v2.1 S7.
"""
from __future__ import annotations

import structlog
from datetime import date, datetime
from typing import Optional
from uuid import UUID

log = structlog.get_logger()

TENANT = "authentic_pilates"


async def _get_pool():
    from src.db.client import get_pool
    return await get_pool()


async def generar_respuesta(intencion: str, cliente_id: Optional[UUID] = None,
                             contenido_original: str = "") -> dict:
    """Genera respuesta sugerida según intención.

    Returns:
        {"mensaje": str, "accion": str|None, "accion_datos": dict|None,
         "auto_enviar": bool}
    """
    generadores = {
        "consulta_precio": _respuesta_precios,
        "consulta_horario": _respuesta_horarios,
        "reserva": _respuesta_reserva,
        "cancelacion": _respuesta_cancelacion,
        "feedback": _respuesta_feedback,
        "queja": _respuesta_queja,
    }

    gen = generadores.get(intencion)
    if gen:
        return await gen(cliente_id, contenido_original)

    return {"mensaje": "", "accion": None, "accion_datos": None, "auto_enviar": False}


async def _respuesta_precios(cliente_id: Optional[UUID], contenido: str) -> dict:
    """Respuesta con precios reales del sistema."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        grupos_con_plaza = await conn.fetchval("""
            SELECT count(*) FROM om_grupos g
            WHERE g.tenant_id = $1 AND g.estado = 'activo'
              AND (SELECT count(*) FROM om_contratos c
                   WHERE c.grupo_id = g.id AND c.estado = 'activo') < g.capacidad_max
        """, TENANT)

    mensaje = (
        "¡Hola! Estos son nuestros servicios:\n\n"
        "🔹 Grupo Reformer (máx 4): 105€/mes (2x/semana)\n"
        "🔹 Grupo Mat (máx 6): 55€/mes (2x/semana)\n"
        "🔹 Grupo 1x/semana: 60€/mes\n"
        "🔹 Individual 1x/sem: 35€/sesión\n"
        "🔹 Individual 2x/sem: 30€/sesión\n\n"
        f"Ahora mismo hay plazas en {grupos_con_plaza} grupos. "
        "¿Te gustaría probar una clase?"
    )
    return {"mensaje": mensaje, "accion": None, "accion_datos": None, "auto_enviar": False}


async def _respuesta_horarios(cliente_id: Optional[UUID], contenido: str) -> dict:
    """Respuesta con horarios y disponibilidad real."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        grupos = await conn.fetch("""
            SELECT g.nombre, g.tipo, g.capacidad_max, g.dias_semana, g.precio_mensual,
                   (SELECT count(*) FROM om_contratos c
                    WHERE c.grupo_id = g.id AND c.estado = 'activo') as ocupadas
            FROM om_grupos g
            WHERE g.tenant_id = $1 AND g.estado = 'activo'
            ORDER BY g.nombre
        """, TENANT)

    lineas = ["¡Hola! Estos son nuestros horarios con plazas disponibles:\n"]
    for g in grupos:
        libres = g["capacidad_max"] - g["ocupadas"]
        if libres > 0:
            lineas.append(f"✅ {g['nombre']} — {libres} plaza{'s' if libres > 1 else ''} · {float(g['precio_mensual']):.0f}€/mes")
        else:
            lineas.append(f"❌ {g['nombre']} — COMPLETO")

    lineas.append("\n¿Algún horario te viene bien?")
    mensaje = "\n".join(lineas)

    return {"mensaje": mensaje, "accion": None, "accion_datos": None, "auto_enviar": False}


async def _respuesta_reserva(cliente_id: Optional[UUID], contenido: str) -> dict:
    """Respuesta para solicitud de reserva."""
    if cliente_id:
        return {
            "mensaje": "¡Genial! Te apunto. ¿Para qué día y hora?",
            "accion": "crear_sesion",
            "accion_datos": {"cliente_id": str(cliente_id)},
            "auto_enviar": False,
        }
    else:
        return {
            "mensaje": "",
            "accion": "enviar_onboarding",
            "accion_datos": {},
            "auto_enviar": False,
        }


async def _respuesta_cancelacion(cliente_id: Optional[UUID], contenido: str) -> dict:
    """Respuesta para cancelación. Busca próxima sesión del cliente."""
    if not cliente_id:
        return {
            "mensaje": "¿Podrías indicarme tu nombre para localizar tu sesión?",
            "accion": None, "accion_datos": None, "auto_enviar": False,
        }

    pool = await _get_pool()
    async with pool.acquire() as conn:
        proxima = await conn.fetchrow("""
            SELECT s.id as sesion_id, s.fecha, s.hora_inicio,
                   g.nombre as grupo_nombre, a.id as asistencia_id
            FROM om_asistencias a
            JOIN om_sesiones s ON s.id = a.sesion_id
            LEFT JOIN om_grupos g ON g.id = s.grupo_id
            WHERE a.cliente_id = $1 AND a.tenant_id = $2
                AND s.fecha >= CURRENT_DATE
                AND a.estado = 'confirmada'
            ORDER BY s.fecha, s.hora_inicio
            LIMIT 1
        """, cliente_id, TENANT)

    if not proxima:
        return {
            "mensaje": "No encuentro ninguna sesión próxima programada. ¿Cuál querías cancelar?",
            "accion": None, "accion_datos": None, "auto_enviar": False,
        }

    hora = str(proxima["hora_inicio"])[:5]
    sesion_dt = datetime.combine(proxima["fecha"], proxima["hora_inicio"])
    horas_antes = (sesion_dt - datetime.now()).total_seconds() / 3600

    if horas_antes >= 12:
        cargo_texto = "Sin cargo (más de 12h de antelación)."
    else:
        cargo_texto = "⚠️ Cancelación tardía — se aplicará cargo."

    mensaje = (
        f"Tu próxima sesión es el {proxima['fecha'].strftime('%A %d/%m')} a las {hora}"
        f"{' (' + proxima['grupo_nombre'] + ')' if proxima['grupo_nombre'] else ''}.\n\n"
        f"{cargo_texto}\n\n"
        "¿Confirmas la cancelación?"
    )

    return {
        "mensaje": mensaje,
        "accion": "cancelar_sesion",
        "accion_datos": {
            "sesion_id": str(proxima["sesion_id"]),
            "asistencia_id": str(proxima["asistencia_id"]),
            "cliente_id": str(cliente_id),
            "cargo": horas_antes < 12,
        },
        "auto_enviar": False,
    }


async def _respuesta_feedback(cliente_id: Optional[UUID], contenido: str) -> dict:
    return {
        "mensaje": "¡Muchas gracias! Me alegra mucho que te haya gustado 😊",
        "accion": None, "accion_datos": None, "auto_enviar": False,
    }


async def _respuesta_queja(cliente_id: Optional[UUID], contenido: str) -> dict:
    return {
        "mensaje": "",  # Las quejas NUNCA se auto-responden
        "accion": "alerta_urgente",
        "accion_datos": {"cliente_id": str(cliente_id) if cliente_id else None},
        "auto_enviar": False,
    }


# ============================================================
# PROCESAR RESPUESTA A BOTONES (confirmación pre-sesión)
# ============================================================

async def procesar_respuesta_boton(cliente_id: UUID, boton_id: str) -> dict:
    """Procesa respuesta a botón interactivo (confirmación pre-sesión).

    Si "no_puedo" → cancela asistencia de mañana (>=12h, sin cargo).
    Si "si_voy" → no hace nada (ya estaba confirmado).
    """
    from datetime import timedelta
    manana = date.today() + timedelta(days=1)

    if boton_id == "si_voy":
        return {"status": "ok", "accion": "ninguna", "mensaje": "Confirmado, te esperamos!"}

    if boton_id == "no_puedo":
        pool = await _get_pool()
        async with pool.acquire() as conn:
            asistencia = await conn.fetchrow("""
                SELECT a.id, s.id as sesion_id, s.hora_inicio, g.nombre as grupo_nombre
                FROM om_asistencias a
                JOIN om_sesiones s ON s.id = a.sesion_id
                LEFT JOIN om_grupos g ON g.id = s.grupo_id
                WHERE a.cliente_id = $1 AND s.fecha = $2
                    AND a.estado = 'confirmada' AND a.tenant_id = $3
                LIMIT 1
            """, cliente_id, manana, TENANT)

            if asistencia:
                await conn.execute("""
                    UPDATE om_asistencias SET estado = 'cancelada',
                        hora_cancelacion = now()
                    WHERE id = $1
                """, asistencia["id"])

                log.info("wa_cancelacion_automatica",
                         cliente=str(cliente_id),
                         sesion=str(asistencia["sesion_id"]))

                return {
                    "status": "ok",
                    "accion": "cancelacion_automatica",
                    "mensaje": "Vale, cancelo tu sesión de mañana. ¡Sin cargo!",
                    "sesion_id": str(asistencia["sesion_id"]),
                }

        return {"status": "ok", "accion": "ninguna",
                "mensaje": "No encuentro sesión para mañana. ¿Cuál querías cancelar?"}

    return {"status": "ok", "accion": "desconocido", "mensaje": ""}
