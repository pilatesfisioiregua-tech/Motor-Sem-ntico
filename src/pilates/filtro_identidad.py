"""Filtro Identidad — F3 como guardián de coherencia (P67).

Todo contenido externo pasa por aquí ANTES de publicarse.
Compatible → pasa. Incompatible → om_depuracion + señal F3.

Reglas claras → código puro ($0).
Ambiguo → motor.pensar() con INT-15 (estética) + INT-17 (existencial).
"""
from __future__ import annotations

import json
import structlog
from typing import Optional

from src.db.client import get_pool

log = structlog.get_logger()

TENANT = "authentic_pilates"


async def leer_identidad(tenant_id: str = TENANT) -> dict:
    """Lee pizarra identidad del tenant."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM om_pizarra_identidad WHERE tenant_id = $1", tenant_id)
        if row:
            return dict(row)
    return {}


async def filtrar_por_identidad(
    contenido: str,
    canal: str = "instagram",
    tenant_id: str = TENANT,
) -> dict:
    """Filtra contenido contra la identidad del tenant.

    Returns:
        {"compatible": bool, "score": 0-1, "motivo": str, "metodo": "reglas"|"llm"}
    """
    identidad = await leer_identidad(tenant_id)
    if not identidad:
        return {"compatible": True, "score": 0.5, "motivo": "Sin identidad configurada", "metodo": "default"}

    # FASE 1: Reglas claras ($0)
    anti = identidad.get("anti_identidad") or []
    depuraciones = identidad.get("depuraciones_deliberadas") or []
    texto_lower = contenido.lower()

    # Check anti-identidad
    for anti_item in anti:
        keywords = anti_item.lower().split()
        if all(kw in texto_lower for kw in keywords if len(kw) > 3):
            return {
                "compatible": False,
                "score": 0.1,
                "motivo": f"Anti-identidad detectada: '{anti_item}'",
                "metodo": "reglas",
            }

    # Check depuraciones deliberadas
    for dep in depuraciones:
        dep_keywords = [w for w in dep.lower().split() if len(w) > 3]
        if dep_keywords and sum(1 for kw in dep_keywords if kw in texto_lower) >= len(dep_keywords) * 0.6:
            return {
                "compatible": False,
                "score": 0.15,
                "motivo": f"Depuración deliberada: '{dep}'",
                "metodo": "reglas",
            }

    # Check tono incompatible
    tonos_prohibidos = ["compra ya", "últimas plazas", "oferta limitada",
                        "transforma tu cuerpo", "resultados garantizados",
                        "pierde peso", "sin esfuerzo"]
    for tono in tonos_prohibidos:
        if tono in texto_lower:
            return {
                "compatible": False,
                "score": 0.2,
                "motivo": f"Tono incompatible: '{tono}'",
                "metodo": "reglas",
            }

    # FASE 2: Si no es claramente incompatible, ¿es claramente compatible?
    valores = identidad.get("valores") or []
    score_compatible = 0.5  # base
    for valor in valores:
        if valor.lower().replace("_", " ") in texto_lower:
            score_compatible += 0.1

    if score_compatible >= 0.7:
        return {
            "compatible": True,
            "score": min(1.0, score_compatible),
            "motivo": "Coherente con valores",
            "metodo": "reglas",
        }

    # FASE 3: Ambiguo → LLM (motor.pensar)
    try:
        from src.motor.pensar import pensar, ConfigPensamiento

        system = f"""Eres el filtro de identidad de {identidad.get('esencia', 'un estudio de Pilates')}.
Valores: {', '.join(valores)}
Anti-identidad: {', '.join(anti)}
Tono: {identidad.get('tono', 'cercano y profesional')}
Ángulo: {identidad.get('angulo_diferencial', '')}

Evalúa si el siguiente contenido es COHERENTE con esta identidad.
Responde SOLO JSON: {{"compatible": true/false, "score": 0-1, "motivo": "explicación breve"}}"""

        config = ConfigPensamiento(
            funcion="F3", lente="sentido", complejidad="baja",
            usar_cache=True, ttl_cache_horas=168,
        )
        resultado = await pensar(system=system, user=f"Contenido a evaluar:\n{contenido}", config=config)
        from src.pilates.json_utils import extraer_json
        parsed = extraer_json(resultado.texto, fallback={"compatible": True, "score": 0.5})
        parsed["metodo"] = "llm"
        return parsed

    except Exception as e:
        log.warning("filtro_identidad_llm_error", error=str(e)[:80])
        return {"compatible": True, "score": 0.5, "motivo": "LLM error, permitir por defecto", "metodo": "error"}


async def filtrar_contenido_db(contenido_id, tenant_id: str = TENANT) -> dict:
    """Filtra un contenido de om_contenido y actualiza su estado."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM om_contenido WHERE id = $1 AND tenant_id = $2",
            contenido_id, tenant_id)
        if not row:
            return {"error": "Contenido no encontrado"}

        resultado = await filtrar_por_identidad(row["cuerpo"], row["canal"], tenant_id)

        await conn.execute("""
            UPDATE om_contenido
            SET filtro_identidad = $2, filtro_motivo = $3, updated_at = now()
            WHERE id = $1
        """, contenido_id,
            "compatible" if resultado["compatible"] else "incompatible",
            resultado.get("motivo", ""))

        # Si incompatible → registrar en om_depuracion + señal F3
        if not resultado["compatible"]:
            try:
                from src.pilates.bus import emitir
                await emitir("ALERTA", "F3_FILTRO",
                    {"tipo": "contenido_incompatible", "contenido_id": str(contenido_id),
                     "motivo": resultado["motivo"], "score": resultado["score"]},
                    destino="AF3", prioridad=3)
            except Exception:
                pass

    return resultado
