"""Buscador Inteligente — G3 upgrade: búsqueda dirigida por ACD dual.

Motor Gap: busca soluciones a carencias actuales (estado ACD)
Motor Gradiente: busca camino hacia estado deseado (prescripción ACD)

Las queries las genera un LLM (gpt-4o) que entiende el contexto del negocio,
no templates estáticos.

Modelo: BRAIN_MODEL (gpt-4o) para generar queries
Fuente: Perplexity API para ejecutar búsquedas
Filtro: ACD triple lente antes de persistir
"""
from __future__ import annotations

import json
import os
import structlog
import httpx
from datetime import date

from src.db.client import get_pool

log = structlog.get_logger()

TENANT = "authentic_pilates"
ORIGEN = "BUSCADOR"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
BRAIN_MODEL = os.getenv("BRAIN_MODEL", "openai/gpt-4o")
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "")


# ============================================================
# 1. RECOPILAR ESTADO ACD + CONTEXTO
# ============================================================

async def _obtener_estado_acd() -> dict | None:
    """Obtiene último diagnóstico ACD con datos duales."""
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

    vector_f = row["vector_pre"]
    if isinstance(vector_f, str):
        vector_f = json.loads(vector_f)
    lentes = row["lentes_pre"]
    if isinstance(lentes, str):
        lentes = json.loads(lentes)
    metricas = row["metricas"]
    if isinstance(metricas, str):
        metricas = json.loads(metricas)

    return {
        "id": str(row["id"]),
        "estado": row["estado_pre"],
        "vector_f": vector_f,
        "lentes": lentes,
        "metricas": metricas,
    }


async def _obtener_señales_recientes() -> list[dict]:
    """Señales del bus para contexto semántico (AF1-AF7 con cerebro)."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT origen, tipo, payload, created_at
            FROM om_senales_agentes
            WHERE tenant_id = $1 AND tipo IN ('PRESCRIPCION', 'ALERTA')
            ORDER BY created_at DESC LIMIT 15
        """, TENANT)
    return [{"origen": r["origen"], "tipo": r["tipo"],
             "payload": r["payload"] if isinstance(r["payload"], dict) else json.loads(r["payload"]),
             "fecha": str(r["created_at"])} for r in rows]


# ============================================================
# 2. GENERADOR DE QUERIES INTELIGENTE (gpt-4o)
# ============================================================

SYSTEM_QUERY_GENERATOR = """Eres el Generador de Queries del organismo cognitivo de OMNI-MIND.

Tu trabajo: traducir un diagnóstico ACD (numérico + semántico) en QUERIES DE BÚSQUEDA concretas y específicas que resolverán los gaps del negocio.

REGLAS:
1. Cada query debe estar vinculada a un gap (función con score bajo) o a un gradiente (dirección de mejora).
2. NO generes queries genéricas ("cómo mejorar mi negocio"). Sé ESPECÍFICO al sector y al problema concreto.
3. Usa el contexto semántico de las señales del bus para generar queries que ataquen la RAÍZ del problema, no el síntoma.
4. Clasifica cada query por tipo de buscador: sectorial, regulatorio, financiero, mercado_local, tecnologico, consumo.
5. Genera entre 6 y 12 queries priorizadas por urgencia del gap.

FRAMEWORK ACD:
- 3 Lentes: Salud (S=funciona), Sentido (Se=tiene propósito), Continuidad (C=puede transferirse)
- 7 Funciones: F1 Conservación, F2 Captación, F3 Depuración, F4 Distribución, F5 Identidad, F6 Adaptación, F7 Replicación
- Motor Gap: buscar soluciones a lo que falla HOY
- Motor Gradiente: buscar cómo llegar al estado deseado

Responde SOLO en JSON:
{
    "motor_gap": [
        {
            "funcion": "F3",
            "score_actual": 0.25,
            "razon_semantica": "15/16 grupos infrautilizados...",
            "query": "cómo fusionar grupos pilates baja ocupación sin perder clientes",
            "tipo_buscador": "sectorial",
            "urgencia": 1-5
        }
    ],
    "motor_gradiente": [
        {
            "desde_estado": "E3",
            "hacia_estado": "E2",
            "lente_a_subir": "Se",
            "query": "diferenciación estudio pilates terapéutico vs fitness España 2026",
            "tipo_buscador": "sectorial",
            "urgencia": 1-5
        }
    ]
}"""


async def _generar_queries(estado_acd: dict, señales: list[dict]) -> dict:
    """Genera queries inteligentes basadas en el estado ACD + contexto semántico."""
    if not OPENROUTER_API_KEY:
        # Fallback: queries template como antes
        return _queries_template_fallback(estado_acd)

    user_prompt = f"""DIAGNÓSTICO ACD ACTUAL:
Estado: {estado_acd['estado']}
Lentes: {json.dumps(estado_acd['lentes'])}
Vector funcional: {json.dumps(estado_acd['vector_f'])}

SEÑALES RECIENTES DEL ORGANISMO (contexto semántico):
{json.dumps(señales[:10], ensure_ascii=False, indent=2, default=str)}

NEGOCIO: Authentic Pilates, estudio de Pilates en Albelda de Iregua (La Rioja), ~90 clientes, pueblo de 4.000 hab.

Genera queries de búsqueda dirigidas por los gaps y gradientes de este diagnóstico."""

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}",
                         "HTTP-Referer": "https://motor-semantico-omni.fly.dev"},
                json={
                    "model": BRAIN_MODEL,
                    "messages": [
                        {"role": "system", "content": SYSTEM_QUERY_GENERATOR},
                        {"role": "user", "content": user_prompt},
                    ],
                    "max_tokens": 2000,
                    "temperature": 0.5,
                },
            )
            resp.raise_for_status()
            raw = resp.json()["choices"][0]["message"]["content"]

        clean = raw.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1] if "\n" in clean else clean[3:]
        if clean.endswith("```"):
            clean = clean[:-3]
        return json.loads(clean.strip())

    except Exception as e:
        log.warning("buscador_query_gen_error", error=str(e))
        return _queries_template_fallback(estado_acd)


def _queries_template_fallback(estado_acd: dict) -> dict:
    """Fallback a queries template si no hay LLM disponible."""
    TEMPLATES = {
        "F1": "estrategias retención clientes estudio pilates pequeño",
        "F2": "captación clientes pilates marketing local pueblo pequeño",
        "F3": "cuándo cerrar clases poco rentables negocio fitness",
        "F4": "distribución óptima horarios clases pilates",
        "F5": "diferenciación estudio pilates marca personal",
        "F6": "tendencias sector fitness España 2026",
        "F7": "documentar procesos estudio pilates escalar",
    }
    gaps = sorted(estado_acd["vector_f"].items(), key=lambda x: x[1])[:3]
    return {
        "motor_gap": [
            {"funcion": f, "score_actual": s, "query": TEMPLATES.get(f, f"mejoras {f}"),
             "tipo_buscador": "sectorial", "urgencia": 2}
            for f, s in gaps
        ],
        "motor_gradiente": [],
    }


# ============================================================
# 3. EJECUTAR BÚSQUEDAS (Perplexity)
# ============================================================

async def _buscar_perplexity(query: str, contexto: str = "") -> dict | None:
    """Ejecuta búsqueda en Perplexity con contexto del negocio."""
    if not PERPLEXITY_API_KEY:
        log.warning("buscador_sin_perplexity_key")
        return None

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers={"Authorization": f"Bearer {PERPLEXITY_API_KEY}",
                         "Content-Type": "application/json"},
                json={
                    "model": "llama-3.1-sonar-small-128k-online",
                    "messages": [
                        {"role": "system", "content":
                            "Eres un asistente de investigación para un estudio de Pilates "
                            "en La Rioja, España. Responde con datos concretos, tendencias "
                            "y recomendaciones accionables. Máximo 300 palabras. "
                            f"Contexto: {contexto[:200]}"},
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


# ============================================================
# 4. FILTRO ACD (triple lente)
# ============================================================

async def _filtrar_acd(resultado: dict, lentes: dict) -> dict:
    """Filtra resultado por relevancia a las 3 lentes ACD.

    Retorna resultado enriquecido con lentes que atraviesa y prioridad.
    """
    texto = resultado.get("respuesta", "")[:500].lower()

    # Heurística rápida de qué lentes toca
    lentes_tocadas = []
    keywords_salud = ["retención", "clientes", "asistencia", "eficiencia", "ocupación", "horario"]
    keywords_sentido = ["diferencia", "identidad", "marca", "propósito", "competencia", "posicionamiento"]
    keywords_continuidad = ["proceso", "documentar", "sistematizar", "replicar", "escalar", "transferir"]

    if any(k in texto for k in keywords_salud):
        lentes_tocadas.append("salud")
    if any(k in texto for k in keywords_sentido):
        lentes_tocadas.append("sentido")
    if any(k in texto for k in keywords_continuidad):
        lentes_tocadas.append("continuidad")

    prioridad = len(lentes_tocadas)  # 0=descarte, 1=baja, 2=media, 3=alta

    return {
        **resultado,
        "lentes_tocadas": lentes_tocadas,
        "prioridad_acd": prioridad,
        "descartado": prioridad == 0,
    }


# ============================================================
# 5. PERSISTIR EN CORPUS VIVO
# ============================================================

async def _persistir_resultado(funcion: str, query: str, respuesta: str,
                                motor: str, lentes_tocadas: list, prioridad: int):
    """Persiste resultado en om_voz_capa_a con metadatos ACD."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO om_voz_capa_a (tenant_id, funcion, query, respuesta, fuente, metadata)
            VALUES ($1, $2, $3, $4, 'perplexity', $5)
        """, TENANT, funcion, query, respuesta,
            json.dumps({
                "motor": motor,
                "lentes_tocadas": lentes_tocadas,
                "prioridad_acd": prioridad,
                "fecha": str(date.today()),
            }))


# ============================================================
# 6. ORQUESTADOR PRINCIPAL
# ============================================================

async def buscar_por_gaps() -> dict:
    """Ejecuta búsqueda inteligente dirigida por ACD dual.

    1. Obtener estado ACD + señales del bus (contexto semántico)
    2. Generar queries con LLM (Motor Gap + Motor Gradiente)
    3. Ejecutar en Perplexity
    4. Filtrar por ACD triple lente
    5. Persistir en corpus vivo
    6. Emitir señal OPORTUNIDAD al bus
    """
    # 1. Estado ACD
    estado = await _obtener_estado_acd()
    if not estado:
        return {"error": "No hay diagnóstico previo. Ejecutar diagnosticar_tenant primero."}

    señales = await _obtener_señales_recientes()

    # 2. Generar queries inteligentes
    queries_plan = await _generar_queries(estado, señales)
    log.info("buscador_queries_generadas",
             gap=len(queries_plan.get("motor_gap", [])),
             gradiente=len(queries_plan.get("motor_gradiente", [])))

    # 3+4+5. Ejecutar, filtrar, persistir
    resultados = []
    descartados = 0

    contexto_negocio = f"Estudio Pilates Albelda de Iregua, estado ACD: {estado['estado']}"

    for q in queries_plan.get("motor_gap", []):
        result = await _buscar_perplexity(q["query"], contexto_negocio)
        if result:
            filtrado = await _filtrar_acd(result, estado["lentes"])
            if not filtrado["descartado"]:
                await _persistir_resultado(
                    q.get("funcion", ""), q["query"], result["respuesta"],
                    "gap", filtrado["lentes_tocadas"], filtrado["prioridad_acd"])
                resultados.append({
                    **q, "motor": "gap",
                    "respuesta_preview": result["respuesta"][:200],
                    "lentes_tocadas": filtrado["lentes_tocadas"],
                })
            else:
                descartados += 1

    for q in queries_plan.get("motor_gradiente", []):
        result = await _buscar_perplexity(q["query"], contexto_negocio)
        if result:
            filtrado = await _filtrar_acd(result, estado["lentes"])
            if not filtrado["descartado"]:
                await _persistir_resultado(
                    q.get("lente_a_subir", ""), q["query"], result["respuesta"],
                    "gradiente", filtrado["lentes_tocadas"], filtrado["prioridad_acd"])
                resultados.append({
                    **q, "motor": "gradiente",
                    "respuesta_preview": result["respuesta"][:200],
                    "lentes_tocadas": filtrado["lentes_tocadas"],
                })
            else:
                descartados += 1

    # 6. Emitir señal OPORTUNIDAD
    if resultados:
        try:
            from src.pilates.bus import emitir
            await emitir(
                "OPORTUNIDAD", ORIGEN,
                {
                    "estado_acd": estado["estado"],
                    "queries_gap": len(queries_plan.get("motor_gap", [])),
                    "queries_gradiente": len(queries_plan.get("motor_gradiente", [])),
                    "resultados_utiles": len(resultados),
                    "descartados_filtro_acd": descartados,
                    "diagnostico_id": estado["id"],
                    "funciones_buscadas": list(set(
                        r.get("funcion", r.get("lente_a_subir", ""))
                        for r in resultados
                    )),
                },
                prioridad=6,
            )
        except Exception as e:
            log.warning("buscador_bus_error", error=str(e))

    log.info("buscador_completo",
             gap_queries=len(queries_plan.get("motor_gap", [])),
             gradiente_queries=len(queries_plan.get("motor_gradiente", [])),
             resultados=len(resultados), descartados=descartados)

    return {
        "estado_acd": estado["estado"],
        "lentes": estado["lentes"],
        "vector_f": estado["vector_f"],
        "queries_generadas": {
            "motor_gap": len(queries_plan.get("motor_gap", [])),
            "motor_gradiente": len(queries_plan.get("motor_gradiente", [])),
        },
        "resultados_utiles": len(resultados),
        "descartados_filtro_acd": descartados,
        "detalle": resultados,
    }
