"""Benchmark ACD — Demuestra que el pipeline mejora el razonamiento del LLM.

Compara:
  A) LLM SOLO: Sonnet responde directamente
  B) LLM + ACD: Sonnet responde guiado por el pipeline ACD

Métricas (todas medidas por el Razonador, código puro):
  - Salud estructural (0-100%)
  - Falacias detectadas
  - Resolución lumínica (vela/habitación/estadio)
  - Lentes cubiertas (0-3)
  - Modos de percepción presentes (0-9)
  - Invariantes L0 violados (0-7)
  - Especificidad (sujetos concretos vs difusos)

Si ACD > SOLO consistentemente → tenemos algo gordo.
"""
from __future__ import annotations

import asyncio
import json
import os
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv()

from .perceptor import percibir
from .razonador import razonar, diagnostico_a_dict
from .generador import generar_respuesta_acd

ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY_1", os.getenv("ANTHROPIC_API_KEY", ""))
RESULTADOS_DIR = Path(__file__).parent.parent.parent / "benchmark_results"


# ═══════════════════════════════════════════════════════════════
# TEXTOS DE PRUEBA — Variados en dominio y complejidad
# ═══════════════════════════════════════════════════════════════

BENCHMARK_CASES = [
    {
        "id": "B1_vago_corporativo",
        "input": "Deberíamos mejorar significativamente la experiencia del cliente para posicionarnos mejor en el mercado.",
        "instruccion": "Convierte esto en un plan de acción concreto.",
        "dificultad": "alta",
    },
    {
        "id": "B2_cliente_pilates",
        "input": "Llevo tres meses sin ir a Pilates y la verdad es que noto que me duele más la espalda. Quiero volver pero me da pereza llamar.",
        "instruccion": "Responde como asistente de bienestar que ayuda a esta persona a volver.",
        "dificultad": "media",
    },
    {
        "id": "B3_decision_negocio",
        "input": "No sé si subir los precios o mantenerlos. Si los subo pierdo clientes, si no los subo no llego a fin de mes.",
        "instruccion": "Ayuda a esta persona a tomar una decisión bien fundamentada.",
        "dificultad": "alta",
    },
    {
        "id": "B4_conflicto_equipo",
        "input": "El equipo no funciona. Hay mal ambiente y la gente no se compromete. Hemos probado de todo.",
        "instruccion": "Diagnostica la situación y propón acciones específicas.",
        "dificultad": "alta",
    },
    {
        "id": "B5_oportunidad",
        "input": "Un amigo me ha ofrecido asociarnos para abrir otro estudio de Pilates en la zona norte. Suena bien pero no estoy seguro.",
        "instruccion": "Ayuda a evaluar esta oportunidad con rigor.",
        "dificultad": "media",
    },
]


async def generar_sin_acd(texto: str, instruccion: str) -> str:
    """Genera respuesta SIN pipeline ACD — LLM solo."""
    async with httpx.AsyncClient(timeout=90) as client:
        r = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 2048,
                "system": instruccion,
                "messages": [{"role": "user", "content": texto}],
            },
        )
        data = r.json()
        return data.get("content", [{}])[0].get("text", "")


async def analizar_respuesta(texto: str) -> dict:
    """Analiza una respuesta con Perceptor + Razonador."""
    estructura = await percibir(texto)
    if "error" in estructura:
        return {"error": estructura["error"], "salud": 0, "n_hallazgos": 99}

    diagnostico = razonar(estructura)
    return diagnostico_a_dict(diagnostico)


async def ejecutar_caso(caso: dict) -> dict:
    """Ejecuta un caso de benchmark: LLM solo vs LLM+ACD."""
    print(f"\n  {'─' * 60}")
    print(f"  {caso['id']}: {caso['input'][:60]}...")

    # ── A) LLM SOLO ──
    t1 = time.time()
    respuesta_solo = await generar_sin_acd(caso["input"], caso["instruccion"])
    lat_solo = round(time.time() - t1, 1)

    # Analizar output del LLM solo
    analisis_solo = await analizar_respuesta(respuesta_solo)

    # ── B) LLM + ACD ──
    t2 = time.time()
    resultado_acd = await generar_respuesta_acd(
        caso["input"], caso["instruccion"], max_intentos=2
    )
    lat_acd = round(time.time() - t2, 1)

    respuesta_acd = resultado_acd["respuesta"]
    # Analizar output del LLM+ACD
    analisis_acd = await analizar_respuesta(respuesta_acd)

    # ── COMPARAR ──
    def extraer_metricas(analisis):
        return {
            "salud": analisis.get("salud", 0),
            "n_hallazgos": analisis.get("n_hallazgos", 0),
            "n_falacias": analisis.get("n_falacias", 0),
            "resolucion": analisis.get("resolucion_luminica", 0),
            "nivel": analisis.get("nivel_luminico", "?"),
            "n_lentes": analisis.get("n_lentes_cubiertas", 0),
            "n_modos": analisis.get("n_modos_presentes", 0),
            "n_invariantes_violados": analisis.get("n_invariantes_violados", 0),
        }

    m_solo = extraer_metricas(analisis_solo)
    m_acd = extraer_metricas(analisis_acd)

    # Calcular mejora
    mejora_salud = m_acd["salud"] - m_solo["salud"]
    mejora_falacias = m_solo["n_falacias"] - m_acd["n_falacias"]
    mejora_lentes = m_acd["n_lentes"] - m_solo["n_lentes"]
    mejora_relativa = (m_acd["salud"] - m_solo["salud"]) / max(m_solo["salud"], 0.01) * 100

    # Mostrar resultados
    print(f"\n  {'':>20} {'LLM SOLO':>12} {'LLM+ACD':>12} {'MEJORA':>12}")
    print(f"  {'Salud':>20} {m_solo['salud']:>11.0%} {m_acd['salud']:>11.0%} {mejora_salud:>+11.0%}")
    print(f"  {'Hallazgos':>20} {m_solo['n_hallazgos']:>12} {m_acd['n_hallazgos']:>12} {m_acd['n_hallazgos'] - m_solo['n_hallazgos']:>+12}")
    print(f"  {'Falacias':>20} {m_solo['n_falacias']:>12} {m_acd['n_falacias']:>12} {-mejora_falacias:>+12}")
    print(f"  {'Resolución':>20} {m_solo['resolucion']:>11.0%} {m_acd['resolucion']:>11.0%}")
    print(f"  {'Nivel':>20} {m_solo['nivel']:>12} {m_acd['nivel']:>12}")
    print(f"  {'Lentes (0-3)':>20} {m_solo['n_lentes']:>12} {m_acd['n_lentes']:>12} {mejora_lentes:>+12}")
    print(f"  {'Modos (0-9)':>20} {m_solo['n_modos']:>12} {m_acd['n_modos']:>12}")
    print(f"  {'Inv. violados':>20} {m_solo['n_invariantes_violados']:>12} {m_acd['n_invariantes_violados']:>12}")
    print(f"  {'Latencia (s)':>20} {lat_solo:>12} {lat_acd:>12}")

    ganador = "ACD" if m_acd["salud"] > m_solo["salud"] else ("EMPATE" if m_acd["salud"] == m_solo["salud"] else "SOLO")
    print(f"  {'Mejora relativa':>20} {'':>12} {'':>12} {mejora_relativa:>+11.0f}%")
    print(f"\n  🏆 Ganador: {ganador}")

    return {
        "caso": caso["id"],
        "dificultad": caso["dificultad"],
        "metricas_solo": m_solo,
        "metricas_acd": m_acd,
        "mejora_salud": mejora_salud,
        "mejora_relativa": mejora_relativa,
        "mejora_falacias": mejora_falacias,
        "ganador": ganador,
        "respuesta_solo": respuesta_solo[:500],
        "respuesta_acd": respuesta_acd[:500],
        "latencia_solo": lat_solo,
        "latencia_acd": lat_acd,
    }


async def main():
    print("═" * 70)
    print("  BENCHMARK: ¿EL PIPELINE ACD MEJORA EL RAZONAMIENTO DEL LLM?")
    print("  5 casos × 2 condiciones (LLM solo vs LLM+ACD)")
    print("  Métricas: 48 detectores del Razonador (código puro, objetivo)")
    print("═" * 70)

    resultados = []
    for caso in BENCHMARK_CASES:
        resultado = await ejecutar_caso(caso)
        resultados.append(resultado)

    # ── RESUMEN FINAL ──
    print(f"\n{'═' * 70}")
    print(f"  RESULTADOS AGREGADOS")
    print(f"{'═' * 70}")

    victorias_acd = sum(1 for r in resultados if r["ganador"] == "ACD")
    victorias_solo = sum(1 for r in resultados if r["ganador"] == "SOLO")
    empates = sum(1 for r in resultados if r["ganador"] == "EMPATE")

    avg_salud_solo = sum(r["metricas_solo"]["salud"] for r in resultados) / len(resultados)
    avg_salud_acd = sum(r["metricas_acd"]["salud"] for r in resultados) / len(resultados)
    avg_falacias_solo = sum(r["metricas_solo"]["n_falacias"] for r in resultados) / len(resultados)
    avg_falacias_acd = sum(r["metricas_acd"]["n_falacias"] for r in resultados) / len(resultados)

    avg_mejora_relativa = sum(r["mejora_relativa"] for r in resultados) / len(resultados)

    print(f"\n  Victorias:  ACD {victorias_acd} | SOLO {victorias_solo} | Empate {empates}")
    print(f"\n  {'':>25} {'LLM SOLO':>12} {'LLM+ACD':>12} {'MEJORA':>12}")
    print(f"  {'Salud promedio':>25} {avg_salud_solo:>11.0%} {avg_salud_acd:>11.0%} {avg_salud_acd - avg_salud_solo:>+11.0%}")
    print(f"  {'Falacias promedio':>25} {avg_falacias_solo:>12.1f} {avg_falacias_acd:>12.1f} {avg_falacias_acd - avg_falacias_solo:>+12.1f}")
    print(f"  {'Mejora relativa prom.':>25} {'':>12} {'':>12} {avg_mejora_relativa:>+11.0f}%")

    # Veredicto
    if victorias_acd > victorias_solo:
        print(f"\n  🎯 VEREDICTO: El pipeline ACD MEJORA el razonamiento del LLM")
        print(f"     en {victorias_acd}/{len(resultados)} casos ({victorias_acd/len(resultados):.0%})")
        if avg_salud_acd > avg_salud_solo:
            mejora_pct = ((avg_salud_acd / max(avg_salud_solo, 0.01)) - 1) * 100
            print(f"     Mejora promedio en salud estructural: +{mejora_pct:.0f}%")
    elif victorias_solo > victorias_acd:
        print(f"\n  ⚠️ VEREDICTO: El LLM solo es mejor en {victorias_solo}/{len(resultados)} casos")
        print(f"     El pipeline ACD necesita ajustes")
    else:
        print(f"\n  🤝 VEREDICTO: Empate — se necesitan más datos")

    print(f"\n{'═' * 70}")

    # Guardar resultados
    RESULTADOS_DIR.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    path = RESULTADOS_DIR / f"benchmark_{ts}.json"
    path.write_text(json.dumps(resultados, ensure_ascii=False, indent=2))
    print(f"  Resultados guardados: {path}")


if __name__ == "__main__":
    asyncio.run(main())
