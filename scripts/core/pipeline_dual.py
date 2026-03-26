"""Pipeline Dual — Dos cerebros, un sistema.

PIPELINE A (APERTURA): Genera inteligencia via preguntas
  → Detecta huecos en el pensamiento
  → Formula preguntas que ABREN razonamiento
  → Opera sobre operaciones cognitivas (Cálculo 3)
  → Efecto: +25% acción, +22% persuasión (datos corpus N=1377)

PIPELINE B (ESTRUCTURA): Optimiza comunicación via análisis
  → Detecta fallos en la estructura
  → Aplica recetas ACD (Cálculos 1+2)
  → Genera texto estructuralmente óptimo
  → Efecto: r=0.82 precisión→credibilidad

COMBINADOS: El Pipeline A abre el pensamiento,
             el Pipeline B estructura la respuesta.

Uso:
  python3 -m scripts.core.pipeline_dual "texto"
  python3 -m scripts.core.pipeline_dual --benchmark
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.core.perceptor import percibir
from scripts.core.razonador import razonar, diagnostico_a_dict

ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY_1", os.getenv("ANTHROPIC_API_KEY", ""))


async def _llamar_llm(system: str, user: str, model: str = "claude-sonnet-4-20250514",
                      max_tokens: int = 2048) -> str:
    """Llamada a Claude."""
    OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")
    GOOGLE_KEY = os.getenv("GOOGLE_API_KEY", "")

    async with httpx.AsyncClient(timeout=90) as client:
        if OPENAI_KEY:
            r = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {OPENAI_KEY}", "Content-Type": "application/json"},
                json={
                    "model": "gpt-4o-mini",
                    "max_tokens": max_tokens,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                },
            )
            data = r.json()
            return data.get("choices", [{}])[0].get("message", {}).get("content", "")
        elif GOOGLE_KEY:
            r = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GOOGLE_KEY}",
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{"parts": [{"text": f"{system}\n\n{user}"}]}],
                    "generationConfig": {"maxOutputTokens": max_tokens},
                },
            )
            data = r.json()
            candidates = data.get("candidates", [{}])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [{}])
                return parts[0].get("text", "") if parts else ""
            return ""
        else:
            return "[Sin API keys disponibles]"


# ============================================================
# PIPELINE A: APERTURA — Genera inteligencia via preguntas
# ============================================================

SYSTEM_PIPELINE_A = """Eres un generador de PREGUNTAS que abren pensamiento.
Tu trabajo NO es responder — es formular las preguntas que el receptor
necesita para CONSTRUIR su propio razonamiento.

REGLAS:
1. Cada pregunta debe ser IMPOSIBLE de responder con sí/no
2. Cada pregunta debe ABRIR un espacio de pensamiento nuevo
3. Las preguntas siguen una secuencia: apertura → profundización → confrontación → síntesis
4. Usa cuantificación en las preguntas ("¿cuántos?", "¿qué porcentaje?", "¿desde cuándo?")
5. Máximo 5 preguntas — cada una debe ser cirugía, no metralleta

TIPOS DE PREGUNTA (por operación cognitiva):
- INTERROGACIÓN SOCRÁTICA: "¿Qué pasaría si X fuera falso?"
- CUANTIFICACIÓN: "¿Cuántas veces ha ocurrido esto exactamente?"
- REFORMULACIÓN: "¿Cómo lo diría alguien que piensa lo contrario?"
- CONFRONTACIÓN: "¿Qué evidencia tienes de que X es verdad?"
- SUBORDINACIÓN: "¿Es X causa de Y, o Y causa de X?"

FORMATO DE RESPUESTA (JSON):
{
  "huecos_detectados": ["hueco 1 en el pensamiento", "hueco 2"],
  "preguntas": [
    {
      "pregunta": "la pregunta",
      "tipo": "interrogacion|cuantificacion|reformulacion|confrontacion|subordinacion",
      "hueco_que_abre": "qué espacio de pensamiento abre",
      "efecto_esperado": "qué debería pasar en la mente del receptor"
    }
  ],
  "secuencia": "apertura → profundización → confrontación → síntesis",
  "meta_pregunta": "la pregunta que el receptor no sabe que necesita"
}"""


async def pipeline_a_apertura(texto: str, diagnostico: dict = None) -> dict:
    """Pipeline A: Analiza huecos → genera preguntas que abren pensamiento."""
    # 1. Percibir estructura
    estructura = await percibir(texto[:2000])
    diag = diagnostico or diagnostico_a_dict(razonar(estructura)) if "error" not in estructura else {}

    # 2. Preparar contexto de huecos
    hallazgos_ctx = ""
    if diag:
        halls = diag.get("hallazgos_top", [])
        if halls:
            hallazgos_ctx = "\n\nHUECOS ESTRUCTURALES DETECTADOS:\n"
            for h in halls[:5]:
                hallazgos_ctx += f"- [{h.get('tipo', '?')}] {h.get('descripcion', '')[:100]}\n"

    # 3. Generar preguntas
    user = f"""TEXTO A ANALIZAR:
{texto}
{hallazgos_ctx}

Detecta los huecos en el pensamiento de este texto y genera 3-5 preguntas
que ABRAN razonamiento nuevo. JSON."""

    response = await _llamar_llm(SYSTEM_PIPELINE_A, user)

    # Parsear
    try:
        clean = response
        if "```json" in clean:
            clean = clean.split("```json", 1)[1].split("```", 1)[0]
        start = clean.find("{")
        end = clean.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(clean[start:end])
    except Exception:
        pass

    return {"preguntas": [], "raw": response[:500]}


# ============================================================
# PIPELINE B: ESTRUCTURA — Optimiza comunicación
# ============================================================

SYSTEM_PIPELINE_B = """Eres un optimizador de estructura lingüística.
Recibes un texto + su diagnóstico ACD y generas una versión MEJORADA
que maximice credibilidad, acción, persuasión y empatía.

RECETAS BASADAS EN CORPUS (N=1377, correlaciones reales):

CREDIBILIDAD (r=0.82): precisión_adjetivos=0.69, explicitud=0.67, produce_resultado=0.94
ACCIÓN (r=0.67): precisión_adj=0.66, fuerza_verbo=0.76, explicitud=0.64
PERSUASIÓN (r=0.66): precisión_adj=0.65, fuerza_verbo=0.75, agencia=0.74
EMPATÍA (r=0.61): explicitud=0.65, agencia=0.76, produce_resultado=0.92

REGLAS:
1. Cada adjetivo DEBE tener un dato ("35% más" no "significativamente")
2. Cada verbo DEBE tener objeto y resultado ("reducir espera de 15 a 5 min")
3. Cada sujeto DEBE ser concreto (nombre o rol, no "se debería")
4. Decir CÓMO se hace, no solo QUÉ
5. INCLUIR NÚMEROS siempre que sea posible (cuantificación r=0.74 para acción)

FORMATO (JSON):
{
  "texto_original": "...",
  "texto_mejorado": "...",
  "cambios": [
    {"de": "vago", "a": "preciso", "regla": "qué regla aplicaste"}
  ],
  "metricas_predichas": {
    "credibilidad": 0.0-1.0,
    "accion": 0.0-1.0,
    "persuasion": 0.0-1.0,
    "empatia": 0.0-1.0
  }
}"""


async def pipeline_b_estructura(texto: str, diagnostico: dict = None) -> dict:
    """Pipeline B: Analiza estructura → optimiza texto."""
    estructura = await percibir(texto[:2000])
    diag = diagnostico or diagnostico_a_dict(razonar(estructura)) if "error" not in estructura else {}

    hallazgos_ctx = ""
    if diag:
        halls = diag.get("hallazgos_top", [])
        if halls:
            hallazgos_ctx = "\n\nDIAGNÓSTICO ACD:\n"
            hallazgos_ctx += f"Salud: {diag.get('salud', 0):.0%}\n"
            hallazgos_ctx += f"Falacias: {diag.get('n_falacias', 0)}\n"
            for h in halls[:5]:
                hallazgos_ctx += f"- [{h.get('tipo', '?')}] {h.get('descripcion', '')[:100]}\n"

    user = f"""TEXTO A OPTIMIZAR:
{texto}
{hallazgos_ctx}

Optimiza este texto aplicando las recetas ACD para maximizar todos los efectos. JSON."""

    response = await _llamar_llm(SYSTEM_PIPELINE_B, user)

    try:
        clean = response
        if "```json" in clean:
            clean = clean.split("```json", 1)[1].split("```", 1)[0]
        start = clean.find("{")
        end = clean.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(clean[start:end])
    except Exception:
        pass

    return {"texto_mejorado": "", "raw": response[:500]}


# ============================================================
# PIPELINE DUAL COMPLETO
# ============================================================

async def pipeline_dual(texto: str) -> dict:
    """Ejecuta ambos pipelines en paralelo y fusiona resultados.

    Pipeline A: ¿Qué preguntas abren pensamiento?
    Pipeline B: ¿Cómo optimizar la estructura?

    Resultado: Texto mejorado + preguntas de profundización.
    """
    print(f"\n{'=' * 70}")
    print(f"  PIPELINE DUAL — Apertura + Estructura")
    print(f"{'=' * 70}")
    print(f"  📝 Input: {texto[:80]}...")

    start = time.time()

    # 1. Percepción compartida (1 sola llamada)
    print(f"\n  🔍 Percibiendo estructura...")
    estructura = await percibir(texto[:2000])
    if "error" in estructura:
        print(f"  ❌ Percepción falló: {estructura['error']}")
        return {"error": estructura["error"]}

    diag_dict = diagnostico_a_dict(razonar(estructura))
    print(f"  📊 Salud ACD: {diag_dict.get('salud', 0):.0%} | Hallazgos: {diag_dict.get('n_hallazgos', 0)}")

    # 2. Pipelines en paralelo
    print(f"\n  🧠 Pipeline A (Apertura) + Pipeline B (Estructura) en paralelo...")
    result_a, result_b = await asyncio.gather(
        pipeline_a_apertura(texto, diag_dict),
        pipeline_b_estructura(texto, diag_dict),
    )

    latencia = round(time.time() - start, 1)

    # 3. Mostrar resultados
    print(f"\n{'─' * 70}")
    print(f"  🧠 PIPELINE A — APERTURA (preguntas que abren pensamiento)")
    print(f"{'─' * 70}")
    preguntas = result_a.get("preguntas", [])
    huecos = result_a.get("huecos_detectados", [])
    if huecos:
        print(f"  Huecos detectados:")
        for h in huecos:
            print(f"    🕳️ {h}")
    for i, p in enumerate(preguntas, 1):
        pregunta = p if isinstance(p, str) else p.get("pregunta", str(p))
        tipo = p.get("tipo", "?") if isinstance(p, dict) else "?"
        print(f"    ❓ [{tipo}] {pregunta}")
    meta = result_a.get("meta_pregunta", "")
    if meta:
        print(f"\n    🔮 Meta-pregunta: {meta}")

    print(f"\n{'─' * 70}")
    print(f"  📐 PIPELINE B — ESTRUCTURA (texto optimizado)")
    print(f"{'─' * 70}")
    mejorado = result_b.get("texto_mejorado", "")
    if mejorado:
        print(f"  {mejorado[:300]}")
    cambios = result_b.get("cambios", [])
    if cambios:
        print(f"\n  Cambios aplicados:")
        for c in cambios[:5]:
            if isinstance(c, dict):
                print(f"    📝 \"{c.get('de', '')}\" → \"{c.get('a', '')}\" [{c.get('regla', '')}]")

    metricas = result_b.get("metricas_predichas", {})
    if metricas:
        print(f"\n  Efectos predichos:")
        for ef, val in metricas.items():
            try:
                bar = "█" * int(float(val) * 20) + "░" * (20 - int(float(val) * 20))
                print(f"    {ef:15s} {bar} {float(val):.0%}")
            except (ValueError, TypeError):
                pass

    print(f"\n  ⏱️ Latencia total: {latencia}s")
    print(f"{'=' * 70}")

    return {
        "texto_original": texto,
        "pipeline_a": result_a,
        "pipeline_b": result_b,
        "diagnostico": diag_dict,
        "latencia_s": latencia,
    }


# ============================================================
# MAIN
# ============================================================

async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Pipeline Dual ACD")
    parser.add_argument("texto", nargs="?", help="Texto a procesar")
    parser.add_argument("--benchmark", action="store_true")
    args = parser.parse_args()

    if args.texto:
        await pipeline_dual(args.texto)
    else:
        # Demo
        await pipeline_dual(
            "Deberíamos mejorar significativamente la experiencia del cliente "
            "para aumentar la retención y ser más competitivos en el mercado."
        )


if __name__ == "__main__":
    asyncio.run(main())
