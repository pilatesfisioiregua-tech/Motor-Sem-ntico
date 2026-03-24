"""Traductor — Convierte acciones algebraicas → castellano para WA (P66).

Lee pizarra cognitiva + estado → 1 LLM call → intención programada lunes 07:00.

Antes: El briefing generaba JSON técnico que Jesús no leía.
Ahora: Un mensaje WA claro, accionable, en tono de socio inteligente.
"""
from __future__ import annotations

import json
import structlog
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from src.db.client import get_pool
from src.motor.pensar import pensar, ConfigPensamiento
from src.pilates.json_utils import extraer_json

log = structlog.get_logger()

from src.pilates.tenant_context import get_tenant_id, DEFAULT_TENANT
TENANT = DEFAULT_TENANT  # Fallback para llamadas sin request

SYSTEM_TRADUCTOR = """Eres el Traductor del organismo cognitivo de un estudio de Pilates
en un pueblo de La Rioja (~4.000 habitantes).

Tu trabajo: convertir las ACCIONES del sistema (técnicas, algebraicas) en un
MENSAJE WHATSAPP claro, concreto y accionable para Jesús, el dueño del estudio.

REGLAS:
- Castellano de pueblo. Nada de jerga técnica. Nada de "inteligencias" ni "lentes".
- Máximo 5 acciones, priorizadas por impacto.
- Cada acción: QUÉ hacer + POR QUÉ + CUÁNDO.
- Tono: socio inteligente que te cuenta qué pasa y qué hacer. No un robot.
- Empieza con 1-2 líneas de resumen ("Esta semana: todo tranquilo" o "Ojo, hay 3 cosas importantes").
- Si hay riesgo de baja, di el nombre del cliente y qué hacer.
- Si hay deuda, di cuánto y de quién.
- Acaba con algo motivador breve.

Formato: texto plano para WhatsApp (sin markdown, sin JSON).
Máximo 800 caracteres (límite WA cómodo)."""


async def traducir_acciones_semana(ciclo: str = None) -> dict:
    """Lee señales procesadas + mediaciones + briefing → genera WA para Jesús.

    Se ejecuta al FINAL del ciclo semanal, después de todo lo demás.
    Programa la intención en om_pizarra_comunicacion para lunes 07:00.
    """
    import os
    if ciclo is None:
        ahora = datetime.now(ZoneInfo("Europe/Madrid"))
        ciclo = f"W{ahora.isocalendar()[1]:02d}-{ahora.isocalendar()[0]}"

    pool = await get_pool()
    async with pool.acquire() as conn:
        # Señales procesadas esta semana
        senales = await conn.fetch("""
            SELECT origen, tipo_senal, contenido, prioridad
            FROM om_senales_agentes
            WHERE tenant_id = $1 AND procesada = true
                AND created_at >= date_trunc('week', now())
            ORDER BY prioridad ASC
            LIMIT 20
        """, TENANT)

        # Mediaciones
        mediaciones = await conn.fetch("""
            SELECT conflicto, resolucion FROM om_mediaciones
            WHERE tenant_id = $1 AND ciclo = $2
        """, TENANT, ciclo)

        # Briefing numérico
        from src.pilates.briefing import generar_briefing
        briefing = await generar_briefing()

    # Construir contexto para el Traductor
    resumen = []
    resumen.append(f"NÚMEROS SEMANA: {json.dumps(briefing.get('numeros', {}), default=str)[:300]}")

    if senales:
        resumen.append(f"SEÑALES ({len(senales)}):")
        for s in senales[:10]:
            resumen.append(f"  {s['origen']} [{s['tipo_senal']}] p{s['prioridad']}: {s['contenido'][:100]}")

    if mediaciones:
        resumen.append(f"MEDIACIONES ({len(mediaciones)}):")
        for m in mediaciones:
            res = m["resolucion"] if isinstance(m["resolucion"], dict) else json.loads(m["resolucion"])
            resumen.append(f"  {res.get('resolucion', '')[:150]}")

    alertas = briefing.get("alertas", {})
    if alertas:
        resumen.append(f"ALERTAS: {json.dumps(alertas, default=str)[:300]}")

    user_msg = "\n".join(resumen)

    config = ConfigPensamiento(
        funcion="*", complejidad="media",
        usar_cache=False,
    )
    resultado = await pensar(system=SYSTEM_TRADUCTOR, user=user_msg, config=config)

    # Programar envío para lunes 07:00
    ahora = datetime.now(ZoneInfo("Europe/Madrid"))
    proximo_lunes = ahora + timedelta(days=(7 - ahora.weekday()) % 7)
    lunes_7am = proximo_lunes.replace(hour=7, minute=0, second=0, microsecond=0)
    if lunes_7am <= ahora:
        lunes_7am += timedelta(weeks=1)

    telefono_jesus = os.getenv("JESUS_TELEFONO", "")
    if telefono_jesus and resultado.texto:
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO om_pizarra_comunicacion
                    (tenant_id, destinatario, canal, tipo, mensaje,
                     programado_para, estado, origen)
                VALUES ($1, $2, 'whatsapp', 'briefing_semanal', $3,
                        $4, 'pendiente', 'TRADUCTOR')
            """, TENANT, telefono_jesus, resultado.texto[:1500], lunes_7am)

    log.info("traductor_ok", ciclo=ciclo, chars=len(resultado.texto),
             programado=str(lunes_7am), coste=resultado.coste_usd)

    return {
        "status": "ok",
        "mensaje_preview": resultado.texto[:200],
        "programado_para": str(lunes_7am),
        "coste": resultado.coste_usd,
    }
