"""AF Genérico — Ejecuta cualquier función leyendo Pizarra Cognitiva (P63).

Reemplaza la lógica hardcoded de af1_conservacion, af3_depuracion, etc.
Los sensores de cada AF se mantienen como funciones importadas.
La INTELIGENCIA viene de la pizarra (escrita por Director Opus).
"""
from __future__ import annotations

import json
import structlog
from typing import Optional

from src.motor.pensar import pensar, ConfigPensamiento
from src.motor.verificar import verificar

log = structlog.get_logger()

TENANT = "authentic_pilates"


async def ejecutar_af(
    funcion: str,
    datos_sensor: dict,
    ciclo: str = None,
    fallback_instruccion: str = None,
) -> dict:
    """Ejecuta un agente funcional genérico.

    1. Lee receta de Pizarra Cognitiva (escrita por Director)
    2. Si no hay receta, usa fallback_instruccion
    3. Llama a motor.pensar() con la receta
    4. Verifica output con motor.verificar()
    5. Emite señales al bus
    """
    from src.pilates.pizarras import leer_recetas_ciclo
    from datetime import datetime
    from zoneinfo import ZoneInfo

    if ciclo is None:
        ahora = datetime.now(ZoneInfo("Europe/Madrid"))
        ciclo = f"W{ahora.isocalendar()[1]:02d}-{ahora.isocalendar()[0]}"

    # 1. Leer receta de pizarra
    recetas = await leer_recetas_ciclo(TENANT, ciclo)
    receta = None
    for r in recetas:
        if r.get("funcion") == funcion:
            receta = r
            break
    if not receta:
        for r in recetas:
            if r.get("funcion") == "*":
                receta = r
                break

    # 2. Construir prompt
    if receta:
        system = _construir_system_desde_receta(funcion, receta)
        user = _construir_user_desde_datos(funcion, datos_sensor, receta)
        complejidad = "alta" if funcion in ("F3", "F5") else "media"
    elif fallback_instruccion:
        system = f"Eres el agente {funcion} del organismo cognitivo. {fallback_instruccion}"
        user = f"Datos del sensor:\n{_formatear_datos(datos_sensor)}\n\nAnaliza y propón acciones."
        complejidad = "media"
    else:
        log.warning("af_sin_receta_ni_fallback", funcion=funcion, ciclo=ciclo)
        return {"status": "skip", "razon": "Sin receta ni fallback"}

    # 3. Pensar
    config = ConfigPensamiento(
        funcion=funcion,
        lente=receta.get("lente") if receta else None,
        complejidad=complejidad,
        usar_cache=False,
    )
    resultado = await pensar(system=system, user=user, config=config)

    # 4. Verificar
    ints = receta.get("ints", []) if receta else []
    verif = verificar(resultado.texto, ints_usadas=ints, funcion=funcion)

    if not verif.ok:
        log.warning("af_verificacion_fallida",
                    funcion=funcion, errors=verif.errors, score=verif.score)

    # 5. Emitir señales al bus
    alertas_emitidas = 0
    try:
        from src.pilates.json_utils import extraer_json
        parsed = extraer_json(resultado.texto, fallback={"acciones": []})
        acciones = parsed.get("acciones", parsed.get("alertas", []))
        if acciones:
            alertas_emitidas = await _emitir_senales(funcion, acciones)
    except Exception as e:
        log.warning("af_senales_error", error=str(e)[:80])

    return {
        "status": "ok",
        "funcion": funcion,
        "modelo": resultado.modelo,
        "coste": resultado.coste_usd,
        "verificacion_score": verif.score,
        "verificacion_warnings": verif.warnings,
        "alertas_emitidas": alertas_emitidas,
    }


def _construir_system_desde_receta(funcion: str, receta: dict) -> str:
    """Construye system prompt desde receta del Director."""
    parts = [f"Eres el agente {funcion} del organismo cognitivo."]
    if receta.get("intencion"):
        parts.append(f"Intención: {receta['intencion']}")
    if receta.get("prompt_imperativo"):
        parts.append(f"INSTRUCCIÓN:\n{receta['prompt_imperativo']}")
    if receta.get("prompt_provocacion"):
        parts.append(f"PROVOCACIÓN:\n{receta['prompt_provocacion']}")
    parts.append("Responde en JSON con campos: analisis, acciones[], severidad.")
    return "\n\n".join(parts)


def _construir_user_desde_datos(funcion: str, datos: dict, receta: dict) -> str:
    """Construye user message con datos del sensor + preguntas del Director."""
    parts = [f"DATOS DEL SENSOR {funcion}:\n{_formatear_datos(datos)}"]
    if receta.get("prompt_preguntas"):
        parts.append(f"PREGUNTAS A RESPONDER:\n{receta['prompt_preguntas']}")
    if receta.get("prompt_razonamiento"):
        parts.append(f"RAZONAMIENTO REQUERIDO:\n{receta['prompt_razonamiento']}")
    return "\n\n".join(parts)


def _formatear_datos(datos: dict) -> str:
    """Formatea datos del sensor para el prompt."""
    return json.dumps(datos, indent=2, ensure_ascii=False, default=str)


async def _emitir_senales(funcion: str, acciones: list) -> int:
    """Emite señales al bus desde las acciones del AF."""
    from src.db.client import get_pool
    pool = await get_pool()
    emitidas = 0

    async with pool.acquire() as conn:
        for a in acciones[:10]:
            tipo = a.get("tipo", "ALERTA")
            prioridad = {"alta": 1, "media": 3, "baja": 5}.get(
                a.get("severidad", "media"), 3)
            try:
                await conn.execute("""
                    INSERT INTO om_senales_agentes
                        (tenant_id, origen, tipo_senal, prioridad, contenido, procesada)
                    VALUES ($1, $2, $3, $4, $5, false)
                """, TENANT, funcion, tipo, prioridad,
                    a.get("descripcion", str(a)[:500]))
                emitidas += 1
            except Exception:
                pass

    return emitidas
