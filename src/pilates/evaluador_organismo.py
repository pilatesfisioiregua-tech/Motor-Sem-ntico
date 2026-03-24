"""Evaluador del Organismo — Cierra el loop de aprendizaje.

Compara la prescripción de la semana N con el diagnóstico de la semana N+1.
¿Se movieron las lentes? ¿Las INTs prescritas se activaron? ¿Los P/R se enraizaron?

La parte NUMÉRICA es código puro ($0): comparar scores, calcular deltas.
La parte INTERPRETATIVA es 1 call Sonnet: ¿POR QUÉ funcionó o no?

Se ejecuta ANTES del Compositor — le alimenta con evidencia de qué funcionó.
"""
from __future__ import annotations

import json
import structlog
from datetime import datetime, timezone, timedelta

from src.db.client import get_pool
from src.pilates.json_utils import extraer_json

log = structlog.get_logger()

TENANT = "authentic_pilates"


# ============================================================
# 1. COMPARACIÓN NUMÉRICA (código puro, $0)
# ============================================================

async def _comparar_diagnosticos() -> dict | None:
    """Compara los 2 últimos diagnósticos para medir cambio."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT estado_pre, lentes_pre, vector_pre, metricas, created_at
            FROM diagnosticos
            WHERE caso_input LIKE 'Diagnóstico autónomo%'
            ORDER BY created_at DESC LIMIT 2
        """)

    if len(rows) < 2:
        return None

    actual = rows[0]
    anterior = rows[1]

    def _parse(val):
        return val if isinstance(val, dict) else json.loads(val) if val else {}

    lentes_actual = _parse(actual["lentes_pre"])
    lentes_anterior = _parse(anterior["lentes_pre"])
    vector_actual = _parse(actual["vector_pre"])
    vector_anterior = _parse(anterior["vector_pre"])
    metricas_actual = _parse(actual["metricas"])
    metricas_anterior = _parse(anterior["metricas"])

    # Deltas de lentes
    delta_lentes = {}
    for lente in ["salud", "sentido", "continuidad"]:
        val_act = lentes_actual.get(lente, 0)
        val_ant = lentes_anterior.get(lente, 0)
        delta = round(val_act - val_ant, 3)
        delta_lentes[lente] = {
            "anterior": val_ant,
            "actual": val_act,
            "delta": delta,
            "direccion": "subió" if delta > 0.02 else "bajó" if delta < -0.02 else "estable",
        }

    # Deltas de funciones
    delta_funciones = {}
    for fi in ["F1", "F2", "F3", "F4", "F5", "F6", "F7"]:
        val_act = vector_actual.get(fi, 0)
        val_ant = vector_anterior.get(fi, 0)
        delta = round(val_act - val_ant, 3)
        delta_funciones[fi] = {
            "anterior": val_ant,
            "actual": val_act,
            "delta": delta,
            "direccion": "subió" if delta > 0.02 else "bajó" if delta < -0.02 else "estable",
        }

    # Cambio de estado
    cambio_estado = actual["estado_pre"] != anterior["estado_pre"]

    # Repertorio (si disponible en métricas)
    rep_actual = metricas_actual.get("repertorio", {})
    rep_anterior = metricas_anterior.get("repertorio", {})

    return {
        "periodo": {
            "desde": anterior["created_at"].isoformat() if hasattr(anterior["created_at"], 'isoformat') else str(anterior["created_at"]),
            "hasta": actual["created_at"].isoformat() if hasattr(actual["created_at"], 'isoformat') else str(actual["created_at"]),
        },
        "estado": {
            "anterior": anterior["estado_pre"],
            "actual": actual["estado_pre"],
            "cambio": cambio_estado,
        },
        "delta_lentes": delta_lentes,
        "delta_funciones": delta_funciones,
        "repertorio_anterior": rep_anterior,
        "repertorio_actual": rep_actual,
    }


async def _obtener_prescripcion_anterior() -> dict | None:
    """Obtiene la prescripción que se aplicó en la semana anterior."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        configs = await conn.fetch("""
            SELECT agente, config, created_at FROM om_config_agentes
            WHERE tenant_id=$1 AND aprobada_por='opus'
            ORDER BY created_at DESC LIMIT 10
        """, TENANT)

        presc_bus = await conn.fetchrow("""
            SELECT payload FROM om_senales_agentes
            WHERE tenant_id=$1 AND tipo='DIAGNOSTICO' AND origen='DIAGNOSTICADOR'
            AND payload::text LIKE '%prescripcion%'
            ORDER BY created_at DESC
            OFFSET 1 LIMIT 1
        """, TENANT)

    resultado = {
        "configs_director": [],
        "prescripcion_tcf": None,
    }

    for c in configs:
        cfg = c["config"] if isinstance(c["config"], dict) else json.loads(c["config"])
        resultado["configs_director"].append({
            "agente": c["agente"],
            "ints_prescritas": [i.get("id", "") for i in cfg.get("INT_activas", [])],
            "ps_prescritos": [p.get("id", "") for p in cfg.get("P_activos", [])],
            "rs_prescritos": [r.get("id", "") for r in cfg.get("R_activos", [])],
            "fecha": c["created_at"].isoformat() if hasattr(c["created_at"], 'isoformat') else str(c["created_at"]),
        })

    if presc_bus:
        payload = presc_bus["payload"] if isinstance(presc_bus["payload"], dict) else json.loads(presc_bus["payload"])
        resultado["prescripcion_tcf"] = payload.get("prescripcion", {})

    return resultado


async def _obtener_pizarras_semana() -> list[dict]:
    """Obtiene las entradas de pizarra de la última semana para ver qué hicieron los AF."""
    pool = await get_pool()
    desde = datetime.now(timezone.utc) - timedelta(days=8)

    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT agente, detectando, interpretacion, accion_propuesta,
                   confianza, datos, updated_at
            FROM om_pizarra WHERE tenant_id=$1 AND updated_at > $2
            ORDER BY updated_at DESC
        """, TENANT, desde)

    result = []
    for r in rows:
        d = dict(r)
        for k, v in d.items():
            if hasattr(v, 'isoformat'):
                d[k] = v.isoformat()
        result.append(d)
    return result


# ============================================================
# 2. INTERPRETACIÓN NARRATIVA (1 call Sonnet)
# ============================================================

SYSTEM_EVALUADOR = """Eres el EVALUADOR del organismo OMNI-MIND.

Tu trabajo: comparar la prescripción de la semana anterior con los resultados de esta semana.
¿FUNCIONÓ? ¿Se movieron las lentes en la dirección prescrita?

Recibes:
1. DELTAS: cómo cambiaron las lentes y funciones (numérico)
2. PRESCRIPCIÓN ANTERIOR: qué INTs/Ps/Rs se prescribieron y para qué agentes
3. PIZARRA: qué hicieron los agentes esta semana (evidencia de ejecución)

EVALÚA:
1. ¿Las lentes se movieron en la dirección correcta?
   - Si prescripción decía "subir Se" y Se subió → FUNCIONÓ
   - Si Se bajó → NO FUNCIONÓ o CONTRAPRODUCENTE
   - Si Se no se movió → SIN EFECTO (prescripción ignorada o insuficiente)

2. ¿Las INTs prescritas se ACTIVARON?
   - Evidencia en pizarra: ¿los AF hicieron preguntas de las INTs prescritas?

3. ¿Los P/R prescritos se ENRAIZARON?
   - Si P05 (primeros principios) estaba prescrito pero AF3 sigue cerrando por
     números sin cuestionar premisas → P05 no se enraizó

4. ¿Qué cambiar para la próxima semana?

Responde en JSON:
{
    "evaluacion_global": {
        "prescripcion_funciono": "si|parcialmente|no|sin_datos",
        "lente_objetivo": "Se",
        "lente_movimiento": "subió 0.04 | bajó 0.02 | estable",
        "conclusion": "2 frases sobre qué pasó y por qué"
    },
    "evaluacion_por_agente": [
        {
            "agente": "AF3",
            "ints_prescritas": ["INT-18", "INT-09"],
            "ints_activadas": ["INT-18"],
            "ints_no_activadas": ["INT-09"],
            "evidencia": "descripción",
            "ps_enraizados": ["P05"],
            "ps_no_enraizados": ["P03"],
            "efecto_en_lentes": "F3.Se subió 0.03"
        }
    ],
    "recomendaciones_director": [
        "Para AF3: reforzar INT-09 con preguntas más concretas"
    ],
    "patrones_entre_semanas": [
        "Se sube lento pero consistente"
    ]
}"""


async def evaluar_semana() -> dict:
    """Evalúa si la prescripción de la semana anterior funcionó.

    Pipeline:
    1. Comparar diagnósticos (código puro, $0)
    2. Obtener prescripción anterior
    3. Obtener pizarras de la semana
    4. Interpretar con Sonnet (1 call, ~$0.05)
    5. Escribir en pizarra + bus + feed
    """
    # 1. Comparación numérica
    comparacion = await _comparar_diagnosticos()
    if not comparacion:
        return {"status": "sin_datos", "razon": "Menos de 2 diagnósticos disponibles"}

    # 2. Prescripción anterior
    prescripcion = await _obtener_prescripcion_anterior()

    # 3. Pizarras de la semana
    pizarras = await _obtener_pizarras_semana()

    # 4. Interpretación narrativa (Sonnet via motor.pensar)
    resultado_interpretacion = {}
    user_prompt = f"""DELTAS NUMÉRICOS (esta semana vs anterior):
{json.dumps(comparacion, ensure_ascii=False, indent=2, default=str)[:2500]}

PRESCRIPCIÓN QUE SE APLICÓ:
{json.dumps(prescripcion, ensure_ascii=False, indent=2, default=str)[:2000]}

PIZARRA (qué hicieron los agentes esta semana):
{json.dumps(pizarras, ensure_ascii=False, indent=2, default=str)[:2500]}

¿La prescripción funcionó? ¿Qué cambiar para la próxima semana?"""

    try:
        from src.motor.pensar import pensar, ConfigPensamiento
        config = ConfigPensamiento(
            funcion="*", complejidad="media",
            max_tokens=3000, temperature=0.2,
            usar_cache=False,
        )
        resultado_llm = await pensar(
            system=SYSTEM_EVALUADOR, user=user_prompt, config=config)
        resultado_interpretacion = extraer_json(resultado_llm.texto)

    except Exception as e:
        log.warning("evaluador_interpretacion_error", error=str(e))
        resultado_interpretacion = {"error": str(e)[:200]}

    # 5. Pizarra + bus + feed
    from src.pilates.pizarra import escribir
    eval_global = resultado_interpretacion.get("evaluacion_global", {})
    await escribir(
        agente="EVALUADOR",
        capa="cognitiva",
        estado="completado",
        detectando=f"Prescripción {eval_global.get('prescripcion_funciono', '?')}. "
                   f"Lente {eval_global.get('lente_objetivo', '?')}: {eval_global.get('lente_movimiento', '?')}",
        interpretacion=eval_global.get("conclusion", ""),
        accion_propuesta="; ".join(resultado_interpretacion.get("recomendaciones_director", [])[:3]),
        necesita_de=["COMPOSITOR", "ESTRATEGA"],
        confianza=0.75,
        prioridad=2,
        datos={
            "delta_lentes": comparacion["delta_lentes"],
            "estado_cambio": comparacion["estado"],
            "recomendaciones": resultado_interpretacion.get("recomendaciones_director", []),
        },
    )

    from src.pilates.bus import emitir
    await emitir("DIAGNOSTICO", "EVALUADOR", {
        "tipo": "evaluacion_prescripcion",
        "funciono": eval_global.get("prescripcion_funciono"),
        "delta_lentes": comparacion["delta_lentes"],
        "recomendaciones": resultado_interpretacion.get("recomendaciones_director", []),
    }, prioridad=3)

    try:
        from src.pilates.feed import publicar
        funciono = eval_global.get("prescripcion_funciono", "?")
        emoji = {"si": "V", "parcialmente": "~", "no": "X"}.get(funciono, "?")
        await publicar("organismo_evaluador", emoji,
                       f"Evaluador: prescripción {funciono}",
                       eval_global.get("conclusion", "")[:200],
                       severidad="info" if funciono == "si" else "warning")
    except Exception:
        pass

    log.info("evaluador_ok",
             funciono=eval_global.get("prescripcion_funciono"),
             delta_se=comparacion["delta_lentes"].get("sentido", {}).get("delta"))

    return {
        "status": "ok",
        "comparacion_numerica": comparacion,
        "prescripcion_evaluada": prescripcion,
        "interpretacion": resultado_interpretacion,
    }
