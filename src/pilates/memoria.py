"""Memoria — Detecta patrones cross-ciclo y escribe en Pizarra Evolución.

Mensual. Lee snapshots de múltiples ciclos + evaluaciones.
Detecta: estacionalidad, eficacia prescripciones, patrones recurrentes.

Ejemplo: "Cada marzo bajan las asistencias un 20% (Semana Santa)."
→ Director lee esto en pizarra evolución y prescribe AF1 preventivo en febrero.
"""
from __future__ import annotations

import json
import structlog
from datetime import datetime
from zoneinfo import ZoneInfo

from src.db.client import get_pool
from src.motor.pensar import pensar, ConfigPensamiento
from src.pilates.json_utils import extraer_json

log = structlog.get_logger()

TENANT = "authentic_pilates"

SYSTEM_MEMORIA = """Eres el agente Memoria del organismo cognitivo.
Tu trabajo: detectar PATRONES que emergen de múltiples ciclos semanales.

Recibes snapshots de varias semanas. Busca:
1. ESTACIONALIDAD: ¿Hay meses donde siempre pasa X? (ej: vacaciones, fiestas)
2. EFICACIA: ¿Las prescripciones del Director funcionaron? ¿Qué INTs dan resultados?
3. RECURRENCIA: ¿Hay clientes que repiten el mismo patrón? (ej: cancelan, vuelven, cancelan)
4. TENDENCIAS: ¿Mejora o empeora algo semana tras semana?

Formato JSON:
{
  "patrones": [
    {
      "tipo": "estacionalidad|eficacia|recurrencia|tendencia",
      "descripcion": "Descripción del patrón en lenguaje claro",
      "confianza": 0.0-1.0,
      "evidencia_ciclos": N,
      "accion_sugerida": "Lo que el Director debería hacer"
    }
  ]
}"""


async def detectar_patrones_cross_ciclo() -> dict:
    """Lee snapshots de los últimos 8 ciclos y detecta patrones."""
    pool = await get_pool()

    async with pool.acquire() as conn:
        # Últimos 8 snapshots de estado
        snapshots = await conn.fetch("""
            SELECT ciclo, tipo_pizarra, contenido, created_at
            FROM om_pizarra_snapshot
            WHERE tenant_id = $1
            ORDER BY created_at DESC
            LIMIT 80
        """, TENANT)

        # Últimas 8 evaluaciones
        evaluaciones = await conn.fetch("""
            SELECT estado_pre, lentes_pre, metricas, created_at
            FROM diagnosticos
            WHERE caso_input LIKE 'Diagnóstico autónomo%'
            ORDER BY created_at DESC
            LIMIT 8
        """)

    if len(snapshots) < 8:
        log.info("memoria_skip", razon="<8 snapshots", actual=len(snapshots))
        return {"status": "skip", "razon": "datos_insuficientes"}

    # Construir resumen para el LLM
    resumen_ciclos = []
    ciclos_vistos = set()
    for s in snapshots:
        if s["ciclo"] not in ciclos_vistos and s["tipo_pizarra"] == "estado":
            ciclos_vistos.add(s["ciclo"])
            contenido = s["contenido"] if isinstance(s["contenido"], dict) else json.loads(s["contenido"])
            resumen_ciclos.append(f"Ciclo {s['ciclo']}: {json.dumps(contenido, default=str)[:500]}")

    resumen_evaluaciones = []
    for e in evaluaciones:
        resumen_evaluaciones.append(
            f"  Estado: {e['estado_pre']}, Lentes: {e['lentes_pre']}, "
            f"Métricas: {str(e['metricas'])[:200]}")

    user_msg = (
        f"SNAPSHOTS DE {len(ciclos_vistos)} CICLOS:\n"
        + "\n".join(resumen_ciclos[:8])
        + f"\n\nEVALUACIONES ({len(resumen_evaluaciones)}):\n"
        + "\n".join(resumen_evaluaciones)
    )

    config = ConfigPensamiento(
        funcion="*", complejidad="media",
        usar_cache=True, ttl_cache_horas=720,  # 30 días
    )
    resultado = await pensar(system=SYSTEM_MEMORIA, user=user_msg, config=config)
    parsed = extraer_json(resultado.texto, fallback={"patrones": []})

    # Escribir patrones en Pizarra Evolución
    patrones = parsed.get("patrones", [])
    async with pool.acquire() as conn:
        for p in patrones[:10]:
            await conn.execute("""
                INSERT INTO om_pizarra_evolucion
                    (tenant_id, tipo, descripcion, datos, confianza, evidencia_ciclos)
                VALUES ($1, $2, $3, $4::jsonb, $5, $6)
            """, TENANT, p.get("tipo", "patron"),
                p.get("descripcion", "")[:500],
                json.dumps(p, default=str),
                p.get("confianza", 0.5),
                p.get("evidencia_ciclos", 1))

    log.info("memoria_ok", patrones=len(patrones), coste=resultado.coste_usd)
    return {"status": "ok", "patrones": len(patrones), "coste": resultado.coste_usd}
