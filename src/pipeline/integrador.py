"""Capa 6: Síntesis final (Sonnet)."""
from __future__ import annotations

import structlog

from src.config.settings import MODEL_INTEGRATOR
from src.utils.llm_client import llm
from src.pipeline.ejecutor import ExecutionPlan, try_parse_json
from src.pipeline.compositor import Algoritmo

log = structlog.get_logger()


INTEGRADOR_SYSTEM = """Eres el integrador del Motor Semántico OMNI-MIND.
Tu trabajo es sintetizar los análisis de múltiples inteligencias en un output coherente y accionable para el usuario.

REGLAS:
1. No repitas lo que cada inteligencia dijo — sintetiza.
2. Prioriza HALLAZGOS EMERGENTES (lo que solo aparece al cruzar inteligencias).
3. Identifica CONTRADICCIONES entre inteligencias — son señales, no errores.
4. La síntesis debe ser ACCIONABLE — termina con acciones concretas.
5. Identifica PUNTOS CIEGOS — lo que NINGUNA inteligencia pudo ver.
6. Máximo 800 palabras. Densidad > extensión."""

INTEGRADOR_USER = """CASO ORIGINAL:
{input}

{contexto_extra}

ANÁLISIS POR INTELIGENCIA:
{analisis_formateados}

ALGORITMO USADO:
- Inteligencias: {inteligencias}
- Operaciones: {operaciones}
- Pasadas: {loops}

Produce una síntesis final con esta estructura exacta:

1. DIAGNÓSTICO (3-5 líneas): ¿Qué pasa realmente aquí?
2. HALLAZGOS CLAVE (3-5 bullets): Lo más importante que emerge del cruce de inteligencias.
3. CONTRADICCIONES: ¿Dónde las inteligencias se contradicen? ¿Qué señala eso?
4. FIRMA COMBINADA (1-2 frases): La firma única de este análisis multi-inteligencia.
5. PUNTOS CIEGOS (2-3 bullets): Lo que este análisis NO puede ver.
6. ACCIONES (3-5, ordenadas por prioridad): Qué hacer, en qué orden, con qué coste/riesgo.

Responde TAMBIÉN con un JSON al final:
{{
  "narrativa": "la síntesis en prosa",
  "hallazgos": ["hallazgo 1", ...],
  "firma_combinada": "firma del análisis",
  "puntos_ciegos": ["punto ciego 1", ...],
  "acciones": [{{"accion": "...", "prioridad": 1, "coste": "...", "riesgo": "..."}}],
  "contradicciones": ["contradicción 1", ...]
}}"""


async def integrar(
    plan: ExecutionPlan,
    input_text: str,
    contexto: str | None,
    algoritmo: Algoritmo,
) -> dict:
    """Síntesis final con Sonnet."""
    # Formatear outputs
    analisis = []
    for key, result in plan.results.items():
        analisis.append(
            f"### {result.intel_id} ({result.operacion_tipo}, pasada {result.pasada})\n"
            f"{result.output_raw[:2000]}"
        )

    prompt = INTEGRADOR_USER.format(
        input=input_text,
        contexto_extra=f"CONTEXTO: {contexto}" if contexto else "",
        analisis_formateados="\n\n".join(analisis),
        inteligencias=", ".join(algoritmo.inteligencias),
        operaciones=", ".join(
            f"{o.tipo}({','.join(o.inteligencias)})" for o in algoritmo.operaciones
        ),
        loops=str(algoritmo.loops),
    )

    response = await llm.complete(
        model=MODEL_INTEGRATOR,
        system=INTEGRADOR_SYSTEM,
        user_message=prompt,
        max_tokens=4096,
        temperature=0.3,
    )

    parsed = try_parse_json(response)

    return {
        "narrativa": parsed.get("narrativa", response) if parsed else response,
        "hallazgos": parsed.get("hallazgos", []) if parsed else [],
        "firma_combinada": parsed.get("firma_combinada", "") if parsed else "",
        "puntos_ciegos": parsed.get("puntos_ciegos", []) if parsed else [],
        "acciones": parsed.get("acciones", []) if parsed else [],
        "contradicciones": parsed.get("contradicciones", []) if parsed else [],
    }
