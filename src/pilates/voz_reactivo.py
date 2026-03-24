"""Voz Reactivo — B2.9: Bloque Voz conectado al bus de señales.

Transforma el Bloque Voz de batch semanal a sub-circuito reactivo.

Funciones:
  1. procesar_mensaje_wa_reactivo(): WA entrante → clasificar → señal al bus
     - Lead nuevo → ALERTA prioridad 2 (respuesta <5min)
     - Feedback/queja → ALERTA prioridad 3
     - Consulta normal → DATO prioridad 6
  2. propagar_diagnostico_a_voz(): ACD cambió → recalcular estrategia de voz
  3. procesar_señales_voz(): Lee señales del bus dirigidas a AF5 y actúa
"""
from __future__ import annotations

import asyncio
import structlog
from datetime import datetime, timezone
from uuid import UUID

from src.db.client import get_pool

log = structlog.get_logger()

from src.pilates.tenant_context import get_tenant_id, DEFAULT_TENANT
TENANT = DEFAULT_TENANT  # Fallback para llamadas sin request
ORIGEN = "AF5"

# Intenciones que requieren respuesta rápida
INTENCIONES_URGENTES = {"consulta_precio", "reserva", "queja"}
INTENCIONES_LEAD = {"consulta_precio", "reserva"}


async def procesar_mensaje_wa_reactivo(
    telefono: str,
    mensaje_texto: str,
    mensaje_id: UUID | None = None,
    cliente_id: UUID | None = None,
    es_cliente_existente: bool = False,
    intencion: str = "otro",
) -> dict:
    """Procesa un mensaje WA entrante y emite señales al bus.

    Llamado desde el webhook de WA (router.py) después de guardar el mensaje.
    NO reemplaza el procesamiento actual — lo ENRIQUECE con señales.
    """
    from src.pilates.bus import emitir

    acciones = []

    # 1. Lead nuevo: teléfono desconocido preguntando precio/reserva
    if not es_cliente_existente and intencion in INTENCIONES_LEAD:
        await emitir(
            "ALERTA", ORIGEN,
            {
                "subtipo": "lead_nuevo",
                "telefono": telefono,
                "mensaje": mensaje_texto[:200],
                "intencion": intencion,
                "accion_sugerida": f"Lead nuevo desde WA ({telefono}). Responder <5min con precios + enlace onboarding.",
                "funcion": "F2",
            },
            prioridad=2,  # Alta — cada minuto cuenta
        )
        acciones.append("lead_señalizado")

        # Auto-responder si está configurado
        try:
            from src.pilates.whatsapp import respuesta_lead_automatico, is_configured
            if is_configured():
                nombre = ""  # No tenemos nombre aún
                result = await respuesta_lead_automatico(telefono, nombre)
                if result.get("status") == "sent":
                    acciones.append("auto_respondido")
        except Exception as e:
            log.warning("voz_reactivo_autorespuesta_error", error=str(e))

    # 2. Queja de cliente existente → ALERTA para atención inmediata
    elif es_cliente_existente and intencion == "queja":
        await emitir(
            "ALERTA", ORIGEN,
            {
                "subtipo": "queja_cliente",
                "cliente_id": str(cliente_id) if cliente_id else None,
                "telefono": telefono,
                "mensaje": mensaje_texto[:200],
                "accion_sugerida": "Queja recibida por WA. Revisar y responder con empatía <1h.",
                "funcion": "F1",  # Afecta conservación
            },
            prioridad=3,
        )
        acciones.append("queja_señalizada")

    # 3. Feedback positivo → DATO (para telemetría, sin urgencia)
    elif intencion == "feedback":
        await emitir(
            "DATO", ORIGEN,
            {
                "subtipo": "feedback_wa",
                "cliente_id": str(cliente_id) if cliente_id else None,
                "telefono": telefono,
                "sentimiento": "positivo",
                "funcion": "F5",
            },
            prioridad=7,
        )
        acciones.append("feedback_registrado")

    # 4. Cualquier otro mensaje → DATO genérico (bajo ruido)
    else:
        await emitir(
            "DATO", ORIGEN,
            {
                "subtipo": "wa_mensaje",
                "cliente_id": str(cliente_id) if cliente_id else None,
                "intencion": intencion,
                "es_cliente": es_cliente_existente,
                "funcion": "F5",
            },
            prioridad=8,
        )
        acciones.append("mensaje_registrado")

    log.info("voz_reactivo_wa",
        telefono=telefono[:6] + "***",
        intencion=intencion,
        es_cliente=es_cliente_existente,
        acciones=acciones)

    return {"acciones": acciones, "intencion": intencion}


async def propagar_diagnostico_a_voz() -> dict:
    """Cuando el diagnóstico ACD cambia, recalcular estrategia de voz.

    Lee la última señal DIAGNOSTICO del bus y, si indica cambio,
    recalcula la estrategia de voz para alinear contenido con nuevo estado.
    """
    from src.pilates.bus import leer_pendientes, marcar_procesada

    # Buscar señales DIAGNOSTICO dirigidas a AF5 o broadcast
    señales = await leer_pendientes(destino="AF5", tipo="DIAGNOSTICO", limite=5)
    if not señales:
        return {"propagado": False, "razon": "Sin señales DIAGNOSTICO pendientes para AF5"}

    for señal in señales:
        payload = señal["payload"]
        if isinstance(payload, str):
            import json
            payload = json.loads(payload)

        cambio = payload.get("cambio", False)
        if cambio:
            try:
                from src.pilates.voz_estrategia import calcular_estrategia
                nueva_est = await calcular_estrategia()
                log.info("voz_reactivo_estrategia_recalculada",
                    estado_acd=payload.get("estado"),
                    foco=nueva_est.get("estrategia", {}).get("foco_principal"))

                await marcar_procesada(str(señal["id"]), ORIGEN)
                return {
                    "propagado": True,
                    "estado_acd": payload.get("estado"),
                    "estrategia_foco": nueva_est.get("estrategia", {}).get("foco_principal"),
                }
            except Exception as e:
                log.warning("voz_reactivo_estrategia_error", error=str(e))
                await marcar_procesada(str(señal["id"]), ORIGEN)
        else:
            # Sin cambio → marcar como procesada sin acción
            await marcar_procesada(str(señal["id"]), ORIGEN)

    return {"propagado": False, "razon": "Señales procesadas pero sin cambio de estado"}


async def emitir_señales_cross_af() -> dict:
    """AF5 emite señales que otros AF consumen.

    Analiza actividad reciente de voz y genera señales cross:
    - Canal sin ROI → AF3 (VETO para no invertir más)
    - Lead sin atender >1h → AF2 (alerta de oportunidad perdida)
    """
    pool = await get_pool()
    from src.pilates.bus import emitir

    señales_emitidas = 0

    async with pool.acquire() as conn:
        # Leads sin responder en >1 hora
        try:
            leads_sin_responder = await conn.fetch("""
                SELECT m.id, m.telefono_remitente, m.contenido, m.created_at
                FROM om_mensajes_wa m
                WHERE m.tenant_id = $1 AND m.direccion = 'entrante'
                AND m.intencion IN ('consulta_precio', 'reserva')
                AND m.respondido = false
                AND m.created_at < now() - interval '1 hour'
                AND m.created_at > now() - interval '24 hours'
            """, TENANT)

            for lead in leads_sin_responder:
                await emitir(
                    "ALERTA", ORIGEN,
                    {
                        "subtipo": "lead_sin_atender",
                        "telefono": lead["telefono_remitente"],
                        "horas_esperando": round((datetime.now(timezone.utc) - lead["created_at"]).total_seconds() / 3600, 1),
                        "accion_sugerida": f"Lead esperando respuesta >1h. Llamar o enviar WA ahora.",
                        "funcion": "F2",
                        "bloquea_af": [],
                    },
                    prioridad=2,
                )
                señales_emitidas += 1
        except Exception as e:
            log.warning("voz_reactivo_leads_error", error=str(e))

        # Canales con IRC < 0.30 → señal a AF3 para considerar abandonar
        try:
            canales_bajo_irc = await conn.fetch("""
                SELECT canal, irc_actual FROM om_voz_irc
                WHERE tenant_id = $1 AND irc_actual < 0.30
            """, TENANT)

            for canal in canales_bajo_irc:
                await emitir(
                    "ALERTA", ORIGEN,
                    {
                        "subtipo": "canal_bajo_irc",
                        "canal": canal["canal"],
                        "irc": float(canal["irc_actual"]),
                        "accion_sugerida": f"Canal '{canal['canal']}' con IRC={canal['irc_actual']:.2f} (<0.30). Considerar abandonar o reestructurar.",
                        "funcion": "F3",
                        "bloquea_af": ["AF2"],  # No captar por canal ineficiente
                    },
                    prioridad=5,
                )
                señales_emitidas += 1
        except Exception as e:
            log.warning("voz_reactivo_irc_error", error=str(e))

    log.info("voz_reactivo_cross_af", señales=señales_emitidas)
    return {"señales_cross_emitidas": señales_emitidas}
