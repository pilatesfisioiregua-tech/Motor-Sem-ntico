"""Anti-dilución — Detecta drift de identidad en contenido publicado (P67).

Si el contenido publicado diverge de la pizarra identidad durante 4+ ciclos,
emite señal F3 para que el Director recalibre.

Se ejecuta mensualmente (en _tarea_mensual).
"""
from __future__ import annotations

import structlog
from src.db.client import get_pool
from src.pilates.filtro_identidad import leer_identidad, filtrar_por_identidad

log = structlog.get_logger()

TENANT = "authentic_pilates"
CICLOS_DRIFT_UMBRAL = 4


async def detectar_drift_identidad() -> dict:
    """Analiza contenido publicado de los últimos 4 ciclos.

    Si >30% del contenido publicado tiene coherencia_score < 0.5,
    hay drift → señal F3.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        publicados = await conn.fetch("""
            SELECT id, cuerpo, canal, coherencia_score, ciclo
            FROM om_contenido
            WHERE tenant_id = $1 AND estado = 'publicado'
            ORDER BY publicado_at DESC
            LIMIT 20
        """, TENANT)

    if len(publicados) < 4:
        return {"status": "skip", "razon": "datos_insuficientes"}

    # Re-evaluar coherencia de cada pieza
    incoherentes = 0
    total = len(publicados)

    for p in publicados:
        if p["coherencia_score"] is not None and p["coherencia_score"] < 0.5:
            incoherentes += 1
        elif p["coherencia_score"] is None:
            resultado = await filtrar_por_identidad(p["cuerpo"], p["canal"], TENANT)
            if not resultado.get("compatible", True) or resultado.get("score", 1) < 0.5:
                incoherentes += 1
            async with pool.acquire() as conn:
                await conn.execute("""
                    UPDATE om_contenido SET coherencia_score = $2 WHERE id = $1
                """, p["id"], resultado.get("score", 0.5))

    ratio_incoherente = incoherentes / max(total, 1)

    if ratio_incoherente > 0.3:
        # DRIFT detectado
        try:
            from src.pilates.bus import emitir
            await emitir("ALERTA", "ANTI_DILUCION",
                {"tipo": "drift_identidad",
                 "ratio_incoherente": round(ratio_incoherente, 2),
                 "total_evaluados": total,
                 "incoherentes": incoherentes,
                 "accion": "Director debe recalibrar contenido"},
                destino="DIRECTOR", prioridad=2)
            log.warning("anti_dilucion_drift", ratio=ratio_incoherente, incoherentes=incoherentes)
        except Exception:
            pass

        return {"status": "drift", "ratio": ratio_incoherente, "incoherentes": incoherentes}

    log.info("anti_dilucion_ok", ratio=ratio_incoherente)
    return {"status": "ok", "ratio": ratio_incoherente, "incoherentes": incoherentes}
