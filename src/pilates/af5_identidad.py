"""AF5 Identidad/Frontera — Agente funcional: definir qué es y qué no es el negocio.

F5 es la función META más importante (6 INTs dedicadas).
Orquesta los 7 archivos voz_* existentes como sensor,
añade cerebro con config dinámica del Director Opus,
y conecta al bus + pizarra.

Detecciones:
  1. Gap identidad declarada vs percibida: ¿lo que dice que es coincide con lo que hace?
  2. Canales sin coherencia: ¿el mensaje en WA = mensaje en Instagram = mensaje en clase?
  3. Diferenciación no articulada: ¿EEDAP está documentado como diferenciador o es implícito?
  4. Identidad amenazada: ¿algún cambio externo (competencia, regulación) cuestiona la identidad?
  5. Propuesta de valor no comunicada: ¿los clientes saben POR QUÉ este estudio y no otro?

Ejecuta semanalmente. Lee de voz_* como sensor. Razona con cerebro dinámico.
Emite al bus. Escribe en pizarra.
"""
from __future__ import annotations

import json
import structlog
from datetime import date, timedelta

from src.db.client import get_pool

log = structlog.get_logger()

TENANT = "authentic_pilates"
ORIGEN = "AF5"

INSTRUCCION_AF5 = """Analiza la IDENTIDAD del negocio: qué dice que es, qué hace realmente, y qué perciben los clientes.

Para gap identidad declarada vs real: ¿La propuesta de valor dice "Pilates terapéutico"
pero el 80% de las clases son fitness genérico? Eso es un gap F5.

Para coherencia de canales: ¿El tono en WhatsApp es profesional pero en Instagram es casual?
¿El briefing semanal habla de diferenciación pero las acciones son descuentos?

Para diferenciación no articulada: El método EEDAP puede ser un diferenciador POTENTE
pero si no está documentado ni comunicado, no existe para los clientes.

Para identidad amenazada: ¿Hay un nuevo estudio de Pilates en Logroño?
¿Una cadena de fitness ofrece Pilates a mitad de precio?

IMPORTANTE: F5 no es marketing. F5 es IDENTIDAD — saber qué eres y qué no eres.
La frontera entre lo que haces y lo que NO haces es tan importante como lo que haces.
Si no hay frontera clara, el negocio se diluye."""


async def _detectar_gaps_identidad() -> dict:
    """Sensor de AF5: recopila datos de identidad de múltiples fuentes."""
    pool = await get_pool()
    detecciones = []

    async with pool.acquire() as conn:
        # 1. Identidad declarada (voz_identidad)
        identidad = await conn.fetchrow("""
            SELECT propuesta_valor, diferenciadores, tono, personalidad,
                   target_primario, principios_comunicacion, lo_que_nunca_decir
            FROM om_voz_identidad WHERE tenant_id=$1
        """, TENANT)

        tiene_identidad = identidad and identidad.get("propuesta_valor")
        if not tiene_identidad:
            detecciones.append({
                "tipo": "identidad_no_definida",
                "severidad": "alta",
                "detalle": "No hay propuesta de valor definida. El negocio no sabe (o no ha articulado) qué es.",
            })

        # 2. Estrategia de voz actual
        estrategia = await conn.fetchrow("""
            SELECT foco_principal, created_at
            FROM om_voz_estrategia WHERE tenant_id=$1
            ORDER BY created_at DESC LIMIT 1
        """, TENANT)

        if not estrategia:
            detecciones.append({
                "tipo": "sin_estrategia_comunicacion",
                "severidad": "media",
                "detalle": "No hay estrategia de comunicación activa. El negocio no comunica su identidad.",
            })

        # 3. Coherencia canales (IRC)
        try:
            canales = await conn.fetch("""
                SELECT canal, irc_score FROM om_voz_canales
                WHERE tenant_id=$1 ORDER BY irc_score DESC
            """, TENANT)
            if canales:
                scores = [c["irc_score"] for c in canales if c["irc_score"]]
                if scores and max(scores) - min(scores) > 0.4:
                    detecciones.append({
                        "tipo": "canales_desbalanceados",
                        "severidad": "media",
                        "detalle": f"Canales con IRC muy desigual: max={max(scores):.2f}, min={min(scores):.2f}. "
                                   "Puede indicar mensaje inconsistente entre canales.",
                        "canales": [dict(c) for c in canales],
                    })
        except Exception:
            pass

        # 4. ADN del negocio (diferenciación documentada)
        adn_count = await conn.fetchval(
            "SELECT count(*) FROM om_adn WHERE tenant_id=$1 AND activo=true",
            TENANT) or 0

        if adn_count == 0:
            detecciones.append({
                "tipo": "adn_no_documentado",
                "severidad": "alta",
                "detalle": "0 principios ADN documentados. El método EEDAP no está articulado como diferenciador.",
            })
        elif adn_count < 5:
            sin_contraejemplo = await conn.fetchval("""
                SELECT count(*) FROM om_adn
                WHERE tenant_id=$1 AND activo=true
                AND (contra_ejemplos IS NULL OR contra_ejemplos = '[]'::jsonb)
            """, TENANT) or 0
            if sin_contraejemplo > adn_count / 2:
                detecciones.append({
                    "tipo": "adn_sin_fronteras",
                    "severidad": "media",
                    "detalle": f"{sin_contraejemplo}/{adn_count} principios ADN sin contra-ejemplos. "
                               "Los principios sin límites no definen identidad — son declaraciones vacías.",
                })

        # 5. Tensiones que afectan identidad
        try:
            tensiones_identidad = await conn.fetch("""
                SELECT tipo, descripcion, severidad FROM om_voz_tensiones
                WHERE tenant_id=$1 AND resuelta=false
                AND (tipo ILIKE '%identidad%' OR tipo ILIKE '%posicion%'
                     OR tipo ILIKE '%compet%' OR tipo ILIKE '%diferenc%')
            """, TENANT)
            for t in tensiones_identidad:
                detecciones.append({
                    "tipo": "tension_identidad",
                    "severidad": t["severidad"] or "media",
                    "detalle": f"Tensión abierta: {t['tipo']} — {t['descripcion'][:100]}",
                })
        except Exception:
            pass

        # 6. Feedback de clientes sobre identidad (WA)
        try:
            hace_4sem = date.today() - timedelta(weeks=4)
            menciones_identidad = await conn.fetchval("""
                SELECT count(*) FROM om_mensajes_wa
                WHERE tenant_id=$1 AND direccion='entrante'
                AND created_at > $2
                AND (contenido ILIKE '%diferent%' OR contenido ILIKE '%especial%'
                     OR contenido ILIKE '%unic%' OR contenido ILIKE '%por que%'
                     OR contenido ILIKE '%otro sitio%')
            """, TENANT, hace_4sem) or 0

            if menciones_identidad == 0:
                detecciones.append({
                    "tipo": "clientes_no_mencionan_diferenciacion",
                    "severidad": "baja",
                    "detalle": "0 menciones de diferenciación en mensajes WA en 4 semanas. "
                               "Los clientes no perciben (o no articulan) qué hace diferente a este estudio.",
                })
        except Exception:
            pass

    return {
        "identidad_declarada": dict(identidad) if identidad else None,
        "tiene_identidad": tiene_identidad,
        "adn_count": adn_count,
        "tiene_estrategia": bool(estrategia),
        "detecciones": detecciones,
    }


async def ejecutar_af5() -> dict:
    """Ejecuta AF5 Identidad: sensor + cerebro + bus + pizarra.

    Sigue el MISMO patrón que AF1-AF7.
    """
    log.info("af5_inicio")

    # 1. LEER PIZARRA — qué saben los demás
    from src.pilates.pizarra import leer_relevante, leer_conflictos
    pizarra = await leer_relevante("AF5")
    conflictos = await leer_conflictos("AF5")

    # Construir contexto de pizarra para el cerebro
    pizarra_str = ""
    if pizarra:
        pizarra_str = "\n\nLO QUE LOS DEMÁS AGENTES DETECTARON:\n"
        for entry in pizarra:
            pizarra_str += f"- {entry['agente']}: {entry.get('detectando', '')} → {entry.get('accion_propuesta', '')}\n"
    if conflictos:
        pizarra_str += "\n⚡ CONFLICTOS CONMIGO:\n"
        for c in conflictos:
            pizarra_str += f"- {c['agente']}: {c.get('accion_propuesta', '')}\n"

    # 2. SENSOR
    datos_sensor = await _detectar_gaps_identidad()

    # 3. CEREBRO (config dinámica del Director Opus)
    from src.pilates.cerebro_organismo import razonar
    razonamiento = await razonar(
        agente="AF5",
        funcion="F5 Identidad/Frontera",
        datos_detectados=datos_sensor,
        instruccion_especifica=INSTRUCCION_AF5 + pizarra_str,
        nivel=1,
    )

    # 4. EMITIR AL BUS
    from src.pilates.bus import emitir
    alertas_emitidas = 0

    for accion in razonamiento.get("acciones", []):
        try:
            await emitir("PRESCRIPCION", ORIGEN, {
                "funcion": "F5",
                "accion": accion.get("accion", ""),
                "prioridad": accion.get("prioridad", 4),
                "impacto": accion.get("impacto", ""),
                "esfuerzo": accion.get("esfuerzo", ""),
                "interpretacion": razonamiento["interpretacion"],
            }, prioridad=accion.get("prioridad", 4))
            alertas_emitidas += 1
        except Exception as e:
            log.warning("af5_bus_error", error=str(e))

    if razonamiento.get("alerta_critica"):
        try:
            await emitir("ALERTA", ORIGEN, {
                "funcion": "F5",
                "alerta_critica": razonamiento["alerta_critica"],
                "urgente": True,
            }, prioridad=1)
            alertas_emitidas += 1
        except Exception:
            pass

    # 5. ESCRIBIR EN PIZARRA
    from src.pilates.pizarra import escribir
    await escribir(
        agente="AF5",
        capa="ejecutiva",
        estado="completado",
        detectando=f"{len(datos_sensor['detecciones'])} gaps de identidad. "
                   f"ADN: {datos_sensor['adn_count']} principios. "
                   f"Identidad definida: {'sí' if datos_sensor['tiene_identidad'] else 'NO'}.",
        interpretacion=razonamiento.get("interpretacion", ""),
        accion_propuesta=razonamiento.get("acciones", [{}])[0].get("accion", "") if razonamiento.get("acciones") else "",
        necesita_de=["AF3"] if any(d["tipo"] == "adn_sin_fronteras" for d in datos_sensor["detecciones"]) else [],
        confianza=razonamiento.get("acciones", [{}])[0].get("prioridad", 5) / 10 if razonamiento.get("acciones") else 0.5,
        prioridad=3,
        datos={
            "detecciones": len(datos_sensor["detecciones"]),
            "tiene_identidad": datos_sensor["tiene_identidad"],
            "adn_count": datos_sensor["adn_count"],
        },
    )

    # 6. DISPARAR VOZ con contexto del organismo
    propuestas_voz = 0
    if razonamiento.get("acciones"):
        try:
            # Obtener config del Director para AF5 (si existe)
            config_director = {}
            pool = await get_pool()
            async with pool.acquire() as conn:
                cfg_row = await conn.fetchrow("""
                    SELECT config FROM om_config_agentes
                    WHERE tenant_id=$1 AND agente='AF5' AND activa=TRUE
                    ORDER BY version DESC LIMIT 1
                """, TENANT)
                if cfg_row:
                    cfg = cfg_row["config"]
                    config_director = cfg if isinstance(cfg, dict) else json.loads(cfg)

            from src.pilates.voz_ciclos import ejecutar_ciclo_completo
            voz_result = await ejecutar_ciclo_completo(
                contexto_organismo={
                    "partitura_af5": config_director,
                    "pizarra_resumen": pizarra_str,
                    "gaps_identidad": datos_sensor["detecciones"],
                },
            )
            propuestas_voz = voz_result.get("ciclos", {}).get("escuchar", {}).get("senales_creadas", 0)
        except Exception as e:
            log.warning("af5_voz_error", error=str(e))

    resultado = {
        "gaps_identidad": len(datos_sensor["detecciones"]),
        "tiene_identidad": datos_sensor["tiene_identidad"],
        "adn_count": datos_sensor["adn_count"],
        "tiene_estrategia": datos_sensor["tiene_estrategia"],
        "alertas_emitidas": alertas_emitidas,
        "propuestas_voz_generadas": propuestas_voz,
        "razonamiento": razonamiento,
        "detalle": datos_sensor["detecciones"][:10],
    }

    log.info("af5_completo", gaps=len(datos_sensor["detecciones"]),
             identidad=datos_sensor["tiene_identidad"], adn=datos_sensor["adn_count"],
             propuestas_voz=propuestas_voz)
    return resultado
