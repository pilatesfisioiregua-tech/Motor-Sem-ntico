"""Capa 7: Registrador — Persiste datapoints de efectividad.

Cada ejecución del pipeline genera datapoints que alimentan al Gestor.
Sin esto, el sistema no aprende.

Fuente: Maestro §5.1 Paso 7, §6.5
"""
from __future__ import annotations

import structlog
from dataclasses import dataclass

log = structlog.get_logger()


@dataclass
class Datapoint:
    inteligencia: str
    modelo: str
    operacion: str          # 'individual', 'composicion', 'fusion', 'loop'
    score_calidad: float | None
    # Campos TCF (pueden ser None si no hay vector)
    funcion: str | None
    lente: str | None
    gap_pre: float | None
    gap_post: float | None


async def registrar_ejecucion(
    ejecucion_id: str,
    plan,                    # ExecutionPlan
    evaluation,              # EvaluationResult
    tcf_pre: dict | None,    # estado campo pre-ejecución (de detector)
    tcf_post: dict | None,   # estado campo post-ejecución (del evaluador, si existe)
) -> list[Datapoint]:
    """Registra datapoints de efectividad para cada operación ejecutada."""
    datapoints = []

    for key, result in plan.results.items():
        dp = Datapoint(
            inteligencia=result.intel_id,
            modelo=result.modelo_usado,
            operacion=result.operacion_tipo,
            score_calidad=evaluation.score if evaluation else None,
            funcion=None,
            lente=None,
            gap_pre=None,
            gap_post=None,
        )

        # Si hay info TCF, enriquecer con coordenadas del campo
        if tcf_pre and "receta" in tcf_pre:
            receta = tcf_pre.get("receta", {})
            if receta.get("secuencia"):
                dp.lente = receta.get("lente")

        datapoints.append(dp)

    # Persistir en DB (fire and forget)
    try:
        await _persist_datapoints(ejecucion_id, datapoints)
        if tcf_pre:
            await _persist_gradientes(ejecucion_id, tcf_pre, "pre")
        if tcf_post:
            await _persist_gradientes(ejecucion_id, tcf_post, "post")
        log.info("registrador_ok", n_datapoints=len(datapoints))
    except Exception as e:
        log.error("registrador_error", error=str(e))

    return datapoints


async def _persist_datapoints(ejecucion_id: str, datapoints: list[Datapoint]):
    """Inserta datapoints en DB."""
    try:
        from src.db.client import get_pool
        pool = await get_pool()
        async with pool.acquire() as conn:
            for dp in datapoints:
                await conn.execute(
                    """INSERT INTO datapoints_efectividad
                       (ejecucion_id, inteligencia, modelo, operacion,
                        score_calidad, funcion, lente, gap_pre, gap_post)
                       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                       ON CONFLICT DO NOTHING""",
                    ejecucion_id, dp.inteligencia, dp.modelo, dp.operacion,
                    dp.score_calidad, dp.funcion, dp.lente, dp.gap_pre, dp.gap_post,
                )
    except Exception as e:
        log.warning("persist_datapoints_skip", error=str(e))


async def _persist_gradientes(ejecucion_id: str, tcf_data: dict, momento: str):
    """Inserta perfil de gradientes pre/post en DB."""
    try:
        from src.db.client import get_pool
        import json
        pool = await get_pool()

        campo = tcf_data.get("campo", {})
        scoring = tcf_data.get("scoring", {})

        async with pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO perfil_gradientes
                   (ejecucion_id, momento, vector_funcional, lentes,
                    arquetipo_primario, arquetipo_score, coalicion,
                    perfil_lente, eslabon_debil, toxicidad_total, estable)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                   ON CONFLICT DO NOTHING""",
                ejecucion_id, momento,
                json.dumps(campo.get("vector", {})),
                json.dumps(campo.get("lentes", {})),
                scoring.get("primario", {}).get("arquetipo"),
                scoring.get("primario", {}).get("score"),
                campo.get("coalicion"),
                campo.get("perfil_lente"),
                campo.get("eslabon_debil"),
                campo.get("toxicidad_total"),
                campo.get("estable"),
            )
    except Exception as e:
        log.warning("persist_gradientes_skip", error=str(e))
