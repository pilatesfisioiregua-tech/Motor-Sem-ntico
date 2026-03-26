"""Debate Multi-Modelo — Validación cruzada del framework ACD.

Envía el mismo texto a 2+ modelos LLM (Claude Sonnet + GPT-4o),
compara sus análisis ACD y mide convergencia.

Si modelos con arquitecturas COMPLETAMENTE DIFERENTES producen
análisis ACD similares → el framework captura estructura REAL.

Uso:
  python3 -m scripts.core.debate "texto a analizar"
  python3 -m scripts.core.debate --corpus 50    # 50 textos del corpus
  python3 -m scripts.core.debate --benchmark    # benchmark completo
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

from scripts.core.perceptor import SYSTEM_PERCEPTOR, TEMPLATE_RESPUESTA
from scripts.core.razonador import razonar, diagnostico_a_dict

ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY_1", os.getenv("ANTHROPIC_API_KEY", ""))
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")


# ============================================================
# LLAMADAS A MODELOS
# ============================================================

async def _llamar_claude(texto: str, model: str = "claude-sonnet-4-20250514") -> dict:
    """Percepción ACD via Claude."""
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": model,
                "max_tokens": 2048,
                "system": SYSTEM_PERCEPTOR,
                "messages": [
                    {"role": "user", "content": f"Texto a analizar:\n\n{texto}\n\nTemplate:\n{TEMPLATE_RESPUESTA}"},
                ],
            },
        )
        data = r.json()
        raw = data.get("content", [{}])[0].get("text", "")
        return _parsear_json(raw)


async def _llamar_openai(texto: str, model: str = "gpt-4o-mini") -> dict:
    """Percepción ACD via OpenAI."""
    if not OPENAI_KEY:
        return {"error": "Sin OPENAI_API_KEY"}

    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "max_tokens": 2048,
                "messages": [
                    {"role": "system", "content": SYSTEM_PERCEPTOR},
                    {"role": "user", "content": f"Texto a analizar:\n\n{texto}\n\nTemplate:\n{TEMPLATE_RESPUESTA}"},
                ],
            },
        )
        data = r.json()
        raw = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        return _parsear_json(raw)


def _parsear_json(raw: str) -> dict:
    """Parsea JSON de la respuesta de cualquier modelo."""
    clean = raw
    if "```json" in clean:
        clean = clean.split("```json", 1)[1].split("```", 1)[0]
    elif "```" in clean:
        parts = clean.split("```")
        if len(parts) >= 3:
            clean = parts[1]
    try:
        start = clean.find("{")
        end = clean.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(clean[start:end])
    except Exception:
        pass
    return {"error": f"No se pudo parsear: {raw[:200]}"}


# ============================================================
# COMPARAR ANÁLISIS
# ============================================================

def comparar_percepciones(p1: dict, p2: dict) -> dict:
    """Compara dos percepciones ACD y mide convergencia."""
    if "error" in p1 or "error" in p2:
        return {"convergencia": 0, "error": "Una percepción falló"}

    metricas_convergencia = {}

    # Comparar métricas numéricas
    pares_numericos = [
        ("sujeto_predicado", "agencia"),
        ("adjetivos", "precision"),
        ("adverbios", "explicitud"),
        ("verbo", "fuerza"),
    ]

    deltas = []
    for dim, campo in pares_numericos:
        v1 = p1.get(dim, {}).get(campo, 0)
        v2 = p2.get(dim, {}).get(campo, 0)
        try:
            v1 = float(v1)
            v2 = float(v2)
            delta = abs(v1 - v2)
            deltas.append(delta)
            metricas_convergencia[f"{dim}.{campo}"] = {
                "modelo_1": round(v1, 2),
                "modelo_2": round(v2, 2),
                "delta": round(delta, 2),
                "converge": delta < 0.3,
            }
        except (TypeError, ValueError):
            continue

    # Comparar booleanos
    v1_res = p1.get("verbo", {}).get("produce_resultado", False)
    v2_res = p2.get("verbo", {}).get("produce_resultado", False)
    metricas_convergencia["verbo.produce_resultado"] = {
        "modelo_1": v1_res,
        "modelo_2": v2_res,
        "converge": v1_res == v2_res,
    }

    # Comparar strings
    v1_nivel = p1.get("preposiciones", {}).get("nivel_logico", "")
    v2_nivel = p2.get("preposiciones", {}).get("nivel_logico", "")
    metricas_convergencia["preposiciones.nivel_logico"] = {
        "modelo_1": v1_nivel,
        "modelo_2": v2_nivel,
        "converge": v1_nivel.lower() == v2_nivel.lower() if v1_nivel and v2_nivel else False,
    }

    # Score de convergencia
    total = len(metricas_convergencia)
    convergentes = sum(1 for m in metricas_convergencia.values() if m.get("converge"))
    delta_promedio = sum(deltas) / len(deltas) if deltas else 1.0

    return {
        "convergencia": round(convergentes / total, 2) if total > 0 else 0,
        "delta_promedio": round(delta_promedio, 3),
        "convergentes": convergentes,
        "total": total,
        "detalle": metricas_convergencia,
    }


def comparar_diagnosticos(d1: dict, d2: dict) -> dict:
    """Compara dos diagnósticos ACD (post-Razonador)."""
    s1 = d1.get("salud", 0)
    s2 = d2.get("salud", 0)
    h1 = d1.get("n_hallazgos", 0)
    h2 = d2.get("n_hallazgos", 0)
    f1 = d1.get("n_falacias", 0)
    f2 = d2.get("n_falacias", 0)

    delta_salud = abs(s1 - s2)
    delta_hallazgos = abs(h1 - h2)

    return {
        "salud_modelo_1": s1,
        "salud_modelo_2": s2,
        "delta_salud": round(delta_salud, 2),
        "hallazgos_modelo_1": h1,
        "hallazgos_modelo_2": h2,
        "delta_hallazgos": delta_hallazgos,
        "falacias_modelo_1": f1,
        "falacias_modelo_2": f2,
        "convergencia_salud": delta_salud < 0.15,
        "convergencia_hallazgos": delta_hallazgos <= 5,
    }


# ============================================================
# DEBATE COMPLETO
# ============================================================

async def debatir(texto: str, modelo_1: str = "claude", modelo_2: str = "openai") -> dict:
    """Ejecuta debate: mismo texto → 2 modelos → comparar."""
    print(f"\n  📝 Texto: {texto[:80]}...")

    # 1. Percepción paralela
    print(f"  🤖 Modelo 1: {modelo_1}")
    print(f"  🤖 Modelo 2: {modelo_2}")

    tasks = []
    if modelo_1 == "claude":
        tasks.append(_llamar_claude(texto))
    if modelo_2 == "openai":
        tasks.append(_llamar_openai(texto))
    elif modelo_2 == "claude-haiku":
        tasks.append(_llamar_claude(texto, "claude-3-5-haiku-20241022"))

    # Si no hay OpenAI, usar Haiku como segundo modelo
    if not OPENAI_KEY and modelo_2 == "openai":
        print("  ⚠️ Sin OPENAI_API_KEY — usando Claude Haiku como modelo 2")
        modelo_2 = "claude-haiku"
        tasks = [
            _llamar_claude(texto, "claude-sonnet-4-20250514"),
            _llamar_claude(texto, "claude-3-5-haiku-20241022"),
        ]

    start = time.time()
    resultados = await asyncio.gather(*tasks, return_exceptions=True)
    latencia = round(time.time() - start, 1)

    p1 = resultados[0] if not isinstance(resultados[0], Exception) else {"error": str(resultados[0])}
    p2 = resultados[1] if len(resultados) > 1 and not isinstance(resultados[1], Exception) else {"error": "Modelo 2 falló"}

    # 2. Razonar con el mismo Razonador (código puro)
    d1 = diagnostico_a_dict(razonar(p1)) if "error" not in p1 else {"salud": 0, "n_hallazgos": 0, "n_falacias": 0}
    d2 = diagnostico_a_dict(razonar(p2)) if "error" not in p2 else {"salud": 0, "n_hallazgos": 0, "n_falacias": 0}

    # 3. Comparar
    comp_percepcion = comparar_percepciones(p1, p2)
    comp_diagnostico = comparar_diagnosticos(d1, d2)

    resultado = {
        "texto": texto[:200],
        "modelo_1": modelo_1,
        "modelo_2": modelo_2,
        "latencia_s": latencia,
        "percepcion": comp_percepcion,
        "diagnostico": comp_diagnostico,
        "percepcion_1": p1,
        "percepcion_2": p2,
    }

    # 4. Mostrar resultado
    conv = comp_percepcion["convergencia"] * 100
    delta = comp_percepcion["delta_promedio"]
    emoji = "✅" if conv >= 60 else "⚠️" if conv >= 40 else "❌"

    print(f"\n  {emoji} Convergencia percepción: {conv:.0f}% (delta promedio: {delta:.3f})")
    print(f"  📊 Salud M1: {d1.get('salud', 0):.0%} | Salud M2: {d2.get('salud', 0):.0%} | Delta: {comp_diagnostico['delta_salud']:.0%}")
    print(f"  🔍 Hallazgos M1: {d1.get('n_hallazgos', 0)} | M2: {d2.get('n_hallazgos', 0)}")
    print(f"  ⏱️ Latencia: {latencia}s")

    # Detalle de convergencia por métrica
    for nombre, det in comp_percepcion.get("detalle", {}).items():
        emoji_m = "✅" if det.get("converge") else "❌"
        print(f"    {emoji_m} {nombre}: M1={det.get('modelo_1')} | M2={det.get('modelo_2')}")

    return resultado


async def benchmark_debate(n: int = 20) -> dict:
    """Benchmark: N textos del corpus → debate → estadísticas."""
    from scripts.core.corpus import cargar_corpus
    import random

    corpus = cargar_corpus()
    if not corpus:
        print("  ❌ Corpus vacío")
        return {}

    muestra = random.sample(corpus, min(n, len(corpus)))

    print(f"\n{'=' * 70}")
    print(f"  BENCHMARK DEBATE MULTI-MODELO")
    print(f"  Textos: {len(muestra)}")
    print(f"{'=' * 70}")

    resultados = []
    for i, entrada in enumerate(muestra, 1):
        print(f"\n{'─' * 50}")
        print(f"  [{i}/{len(muestra)}]")
        texto = entrada.get("texto", "")
        if not texto:
            continue

        try:
            r = await debatir(texto)
            resultados.append(r)
        except Exception as e:
            print(f"  ❌ Error: {e}")

        # Rate limiting
        await asyncio.sleep(1.5)

    # Estadísticas agregadas
    if not resultados:
        return {"error": "Sin resultados"}

    convs = [r["percepcion"]["convergencia"] for r in resultados]
    deltas = [r["percepcion"]["delta_promedio"] for r in resultados]
    deltas_salud = [r["diagnostico"]["delta_salud"] for r in resultados]

    avg_conv = sum(convs) / len(convs)
    avg_delta = sum(deltas) / len(deltas)
    avg_delta_salud = sum(deltas_salud) / len(deltas_salud)

    print(f"\n{'=' * 70}")
    print(f"  RESULTADOS BENCHMARK DEBATE")
    print(f"{'=' * 70}")
    print(f"  Textos analizados: {len(resultados)}")
    print(f"  Convergencia promedio: {avg_conv:.0%}")
    print(f"  Delta numérico promedio: {avg_delta:.3f}")
    print(f"  Delta salud promedio: {avg_delta_salud:.2f}")
    print(f"\n  {'✅ VALIDADO' if avg_conv >= 0.5 else '❌ NO VALIDADO'}: ", end="")
    if avg_conv >= 0.5:
        print("Modelos diferentes CONVERGEN en análisis ACD → framework captura estructura REAL")
    else:
        print("Modelos divergen significativamente → revisar framework")
    print(f"{'=' * 70}")

    return {
        "n": len(resultados),
        "convergencia_promedio": round(avg_conv, 3),
        "delta_promedio": round(avg_delta, 3),
        "delta_salud_promedio": round(avg_delta_salud, 3),
        "validado": avg_conv >= 0.5,
    }


# ============================================================
# MAIN
# ============================================================

async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Debate Multi-Modelo ACD")
    parser.add_argument("texto", nargs="?", help="Texto a debatir")
    parser.add_argument("--corpus", type=int, help="N textos del corpus")
    parser.add_argument("--benchmark", action="store_true", help="Benchmark completo")
    args = parser.parse_args()

    if args.texto:
        await debatir(args.texto)
    elif args.corpus:
        await benchmark_debate(args.corpus)
    elif args.benchmark:
        await benchmark_debate(50)
    else:
        # Demo
        await debatir("Deberíamos mejorar significativamente la experiencia del cliente para aumentar la retención")


if __name__ == "__main__":
    asyncio.run(main())
