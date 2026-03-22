"""Buscador por gaps — Agente G3: gaps ACD → queries → Perplexity → corpus.

Ejecuta semanalmente (lunes) en cron, después del Diagnosticador.
Lee último diagnóstico → identifica F con menor score → genera queries → Perplexity → persiste.
"""
from __future__ import annotations

import json
import structlog

from src.db.client import get_pool

log = structlog.get_logger()

TENANT = "authentic_pilates"
ORIGEN = "BUSCADOR"

QUERY_TEMPLATES = {
    "F1": [
        "estrategias retención clientes estudio pilates pequeño",
        "cómo reducir bajas en negocio fitness boutique",
    ],
    "F2": [
        "captación clientes pilates marketing local bajo presupuesto",
        "cómo conseguir nuevos alumnos pilates pueblo pequeño",
    ],
    "F3": [
        "optimizar horarios estudio pilates ocupación baja",
        "cuándo cerrar clases poco rentables negocio fitness",
    ],
    "F4": [
        "distribución óptima horarios clases grupales pilates",
        "equilibrar carga semanal estudio pilates individual y grupo",
    ],
    "F5": [
        "diferenciación estudio pilates marca personal propuesta valor",
        "identidad digital pilates estudio independiente",
    ],
    "F6": [
        "adaptación negocio pilates tendencias sector fitness España",
        "cambios regulatorios autónomos fitness España 2026",
    ],
    "F7": [
        "documentar procesos estudio pilates para escalar",
        "sistematizar operaciones negocio pilates unipersonal",
    ],
}


async def _obtener_ultimo_diagnostico() -> dict | None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT id, vector_pre, lentes_pre, estado_pre, flags_pre, metricas
            FROM diagnosticos
            WHERE caso_input LIKE 'Diagnóstico autónomo%'
            ORDER BY created_at DESC LIMIT 1
        """)
    if not row:
        return None
    return dict(row)


def _identificar_gaps(vector_f: dict, n_gaps: int = 2) -> list[str]:
    sorted_f = sorted(vector_f.items(), key=lambda x: x[1])
    return [f for f, _ in sorted_f[:n_gaps]]


def _generar_queries(gaps: list[str]) -> list[dict]:
    queries = []
    for gap in gaps:
        for t in QUERY_TEMPLATES.get(gap, []):
            queries.append({"funcion": gap, "query": t})
    return queries


async def _buscar_perplexity(query: str) -> dict | None:
    import os
    api_key = os.environ.get("PERPLEXITY_API_KEY")
    if not api_key:
        log.warning("buscador_sin_perplexity_key")
        return None

    try:
        import httpx
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "llama-3.1-sonar-small-128k-online",
                    "messages": [
                        {"role": "system", "content": "Eres un asistente de investigación para un estudio de Pilates en La Rioja, España. Responde con datos concretos, tendencias y recomendaciones accionables. Máximo 300 palabras."},
                        {"role": "user", "content": query},
                    ],
                    "max_tokens": 500,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return {"query": query, "respuesta": data["choices"][0]["message"]["content"]}
    except Exception as e:
        log.warning("buscador_perplexity_error", query=query[:50], error=str(e))
        return None


async def _persistir_resultado(funcion: str, query: str, respuesta: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        exists = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'om_voz_capa_a')")
        if not exists:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS om_voz_capa_a (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    created_at TIMESTAMPTZ DEFAULT now(),
                    tenant_id TEXT NOT NULL DEFAULT 'authentic_pilates',
                    funcion TEXT NOT NULL,
                    query TEXT NOT NULL,
                    respuesta TEXT NOT NULL,
                    fuente TEXT DEFAULT 'perplexity',
                    metadata JSONB DEFAULT '{}'
                )
            """)
        await conn.execute(
            "INSERT INTO om_voz_capa_a (tenant_id, funcion, query, respuesta, fuente) VALUES ($1, $2, $3, $4, 'perplexity')",
            TENANT, funcion, query, respuesta)


async def buscar_por_gaps() -> dict:
    """Ejecuta búsqueda dirigida por gaps ACD."""
    # 1. Obtener último diagnóstico
    diag = await _obtener_ultimo_diagnostico()
    if not diag:
        return {"error": "No hay diagnóstico previo. Ejecutar diagnosticar_tenant primero."}

    vector_f = diag["vector_pre"]
    if isinstance(vector_f, str):
        vector_f = json.loads(vector_f)

    # 2. Identificar gaps
    gaps = _identificar_gaps(vector_f, n_gaps=2)
    log.info("buscador_gaps", gaps=gaps, vector=vector_f)

    # 3. Generar queries
    queries = _generar_queries(gaps)

    # 4. Ejecutar en Perplexity
    resultados = []
    for q in queries:
        result = await _buscar_perplexity(q["query"])
        if result:
            await _persistir_resultado(q["funcion"], q["query"], result["respuesta"])
            resultados.append({**q, "respuesta_preview": result["respuesta"][:200]})

    # 5. Emitir señal OPORTUNIDAD
    if resultados:
        try:
            from src.pilates.bus import emitir
            await emitir(
                "OPORTUNIDAD", ORIGEN,
                {
                    "gaps": gaps,
                    "queries_ejecutadas": len(resultados),
                    "funciones_buscadas": list(set(r["funcion"] for r in resultados)),
                    "diagnostico_id": str(diag["id"]),
                },
                prioridad=6,
            )
        except Exception as e:
            log.warning("buscador_bus_error", error=str(e))

    log.info("buscador_completo", gaps=gaps, resultados=len(resultados))
    return {
        "gaps_identificados": gaps,
        "vector_f": vector_f,
        "queries_generadas": len(queries),
        "resultados_perplexity": len(resultados),
        "detalle": resultados,
    }
