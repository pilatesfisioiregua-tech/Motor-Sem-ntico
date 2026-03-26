"""Exocortex — Pipeline completo: Percepción → Razonamiento → Acción.

Esta es la capa de razonamiento ENCIMA del LLM.

ARQUITECTURA:
  TEXTO → Perceptor (1 Haiku, $0.001) → Estructura ACD
       → Razonador (código puro, $0) → Diagnóstico
       → Acciones (agentes, $0) → Resultado

Coste total: ~$0.001 por análisis completo
Latencia: ~2-3 segundos

Vs el motor anterior:
  Coste: ~$0.20 (112 llamadas Haiku)
  Latencia: ~15-30 segundos
"""
from __future__ import annotations

import asyncio
import json
import time
from typing import Optional

from .perceptor import percibir
from .razonador import razonar, diagnostico_a_dict


async def analizar(texto: str, verbose: bool = False) -> dict:
    """Análisis completo de un texto usando Percepción + Razonamiento.

    1 llamada LLM (percepción) + código puro (razonamiento).
    Coste: ~$0.001. Latencia: ~2-3s.

    Args:
        texto: El texto a analizar
        verbose: Si True, incluye la estructura ACD completa

    Returns:
        {diagnostico, estructura?, meta}
    """
    t0 = time.time()

    # ── PASO 1: PERCIBIR (LLM, ~$0.001) ──
    t_percepcion = time.time()
    estructura = await percibir(texto)
    latencia_percepcion = round((time.time() - t_percepcion) * 1000)

    if "error" in estructura:
        return {
            "error": estructura["error"],
            "meta": {"latencia_ms": latencia_percepcion},
        }

    # ── PASO 2: RAZONAR (código puro, $0) ──
    t_razonamiento = time.time()
    diagnostico = razonar(estructura)
    latencia_razonamiento = round((time.time() - t_razonamiento) * 1000)

    # ── RESULTADO ──
    resultado = {
        "diagnostico": diagnostico_a_dict(diagnostico),
        "meta": {
            "latencia_percepcion_ms": latencia_percepcion,
            "latencia_razonamiento_ms": latencia_razonamiento,
            "latencia_total_ms": round((time.time() - t0) * 1000),
            "coste_usd": 0.001,
            "modelo": "haiku",
            "reglas_aplicadas": 12,
        },
    }

    if verbose:
        resultado["estructura_acd"] = estructura

    return resultado


async def analizar_batch(textos: list[str]) -> list[dict]:
    """Analiza múltiples textos en paralelo."""
    tareas = [analizar(texto) for texto in textos]
    return await asyncio.gather(*tareas)


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

async def demo():
    """Demo del Exocortex."""
    textos = [
        "Llevo tres meses sin ir a Pilates y la verdad es que noto que me duele más la espalda. Quiero volver pero me da pereza llamar al estudio.",
        "Deberíamos mejorar significativamente la experiencia del cliente para posicionarnos mejor en el mercado.",
        "Ana no ha venido en 2 semanas, le cobré 3 clases y le envié un WhatsApp. Mañana la llamo.",
    ]

    print("═" * 60)
    print("  EXOCORTEX — Percepción + Razonamiento ACD")
    print("═" * 60)

    for i, texto in enumerate(textos, 1):
        print(f"\n{'─' * 60}")
        print(f"  TEXTO {i}: {texto[:70]}...")
        print(f"{'─' * 60}")

        resultado = await analizar(texto, verbose=True)

        if "error" in resultado:
            print(f"  ❌ {resultado['error']}")
            continue

        diag = resultado["diagnostico"]
        meta = resultado["meta"]

        print(f"\n  🏥 Salud: {diag['salud']:.0%}")
        print(f"  📋 {diag['resumen']}")

        if diag["palanca"]:
            print(f"  🎯 Palanca: {diag['palanca']}")

        if diag["hallazgos"]:
            print(f"\n  Hallazgos ({len(diag['hallazgos'])}):")
            for h in diag["hallazgos"]:
                emoji = {"contradiccion": "⚡", "colapso": "🔄", "punto_ciego": "👁️",
                         "tension": "⚠️", "patron": "🔍", "oportunidad": "💡"}.get(h["tipo"], "•")
                print(f"    {emoji} [{h.get('operacion', h.get('regla', '?'))}] {h['descripcion'][:80]}")

        if diag["preguntas"]:
            print(f"\n  Preguntas:")
            for q in diag["preguntas"]:
                print(f"    ❓ {q}")

        print(f"\n  ⏱️ Percepción: {meta['latencia_percepcion_ms']}ms | Razonamiento: {meta['latencia_razonamiento_ms']}ms | Total: {meta['latencia_total_ms']}ms")
        print(f"  💰 Coste: ${meta['coste_usd']}")

    print(f"\n{'═' * 60}")
    print(f"  COSTE TOTAL: ${0.001 * len(textos):.3f}")
    print(f"  (vs ~${0.20 * len(textos):.2f} con motor anterior)")
    print(f"{'═' * 60}")


if __name__ == "__main__":
    asyncio.run(demo())
