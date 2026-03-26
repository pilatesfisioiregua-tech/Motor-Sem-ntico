"""Exocortex + Opus — El pipeline completo con interpretación profunda.

ARQUITECTURA:
  TEXTO → Perceptor (Sonnet, $0.003) → Estructura ACD
       → Razonador v3 (código puro, $0) → Diagnóstico con 41 detectores
       → Opus (interpretación profunda, ~$0.05) → Insight que ningún otro sistema puede dar

3 capas, 3 naturalezas:
  1. PERCEPCIÓN (LLM) — extrae estructura del texto
  2. RAZONAMIENTO (código) — aplica 41 reglas del marco lingüístico
  3. INTERPRETACIÓN (Opus) — conecta hallazgos con comprensión profunda

Coste total: ~$0.05 por análisis completo con Opus
Sin Opus: ~$0.003 (solo Sonnet + código)
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

ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY_1", os.getenv("ANTHROPIC_API_KEY", ""))


# ═══════════════════════════════════════════════════════════════
# OPUS: INTERPRETACIÓN PROFUNDA
# ═══════════════════════════════════════════════════════════════

SYSTEM_OPUS = """Eres un intérprete cognitivo-lingüístico.

Recibes:
1. Un texto original
2. Su estructura ACD (7 dimensiones lingüísticas extraídas)
3. Un diagnóstico con hallazgos detectados por 41 reglas de razonamiento estructural

Tu trabajo NO es repetir los hallazgos. Es INTERPRETAR:
- ¿Qué ESTRUCTURA MENTAL revela este texto?
- ¿Qué operaciones cognitivas FALTAN (luces apagadas)?
- ¿Qué CREENCIAS INVISIBLES condicionan lo que se dice?
- ¿Cuál es la PALANCA — el punto donde un pequeño cambio cambia todo?
- ¿Qué PREGUNTA haría que la persona viera lo que no ve?

MARCO TEÓRICO:
- Las operaciones sintácticas SON el pensamiento (no lo representan)
- Cada operación ausente = un foco apagado en la experiencia
- Las falacias son operaciones DEFECTUOSAS, no errores de contenido
- La resolución lumínica mide cuántos focos están encendidos (vela→estadio)
- Los 3 lentes (Salud/Sentido/Continuidad) son condiciones necesarias para VIDA

FORMATO DE RESPUESTA (JSON):
{
  "estructura_mental": "1-2 frases describiendo CÓMO piensa esta persona/sistema (no QUÉ dice)",
  "operacion_ausente_critica": "La operación cognitiva que más falta y qué ILUMINARÍA si se ejecutara",
  "creencia_invisible": "La creencia congelada que condiciona todo sin ser dicha",
  "palanca": "El punto exacto donde intervenir para máximo cambio",
  "pregunta_que_abre": "UNA pregunta que haría que la persona viera lo que no ve",
  "nivel_luminico_interpretado": "Qué se ve con esta luz y qué queda en sombra",
  "conexion_profunda": "Algo no obvio que conecta hallazgos aparentemente distintos",
  "prescripcion": "1-2 acciones concretas (no vagas) basadas en la estructura"
}"""


async def interpretar_con_opus(texto: str, estructura: dict, diagnostico: dict) -> dict:
    """Opus interpreta los hallazgos del Razonador en profundidad."""
    if not ANTHROPIC_KEY:
        return {"error": "Sin ANTHROPIC_API_KEY"}

    user = f"""TEXTO ORIGINAL:
{texto}

ESTRUCTURA ACD (percepción):
{json.dumps(estructura, ensure_ascii=False, indent=2)[:3000]}

DIAGNÓSTICO (41 reglas aplicadas):
{json.dumps(diagnostico, ensure_ascii=False, indent=2)[:4000]}

Interpreta: ¿qué estructura mental revela este texto? ¿qué luces están apagadas? ¿cuál es la palanca?"""

    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-20250514",  # Will use Opus when available
                "max_tokens": 2048,
                "system": SYSTEM_OPUS,
                "messages": [{"role": "user", "content": user}],
            },
        )
        data = r.json()
        response = data.get("content", [{}])[0].get("text", "")

    # Parsear JSON
    clean = response
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
    except json.JSONDecodeError:
        pass

    return {"raw": response[:2000]}


# ═══════════════════════════════════════════════════════════════
# PIPELINE COMPLETO
# ═══════════════════════════════════════════════════════════════

async def analizar_profundo(texto: str, con_opus: bool = True, verbose: bool = False) -> dict:
    """Pipeline completo: Percepción → Razonamiento → Interpretación Opus.

    Args:
        texto: El texto a analizar
        con_opus: Si True, añade interpretación con Opus (~$0.05 extra)
        verbose: Si True, incluye estructura ACD completa
    """
    t0 = time.time()
    resultado = {"texto": texto[:200]}

    # ── CAPA 1: PERCIBIR (Sonnet, ~$0.003) ──
    t1 = time.time()
    estructura = await percibir(texto)
    lat_percepcion = round((time.time() - t1) * 1000)

    if "error" in estructura:
        resultado["error"] = estructura["error"]
        return resultado

    # ── CAPA 2: RAZONAR (código puro, $0, <5ms) ──
    t2 = time.time()
    diagnostico_obj = razonar(estructura)
    diagnostico = diagnostico_a_dict(diagnostico_obj)
    lat_razonamiento = round((time.time() - t2) * 1000)

    resultado["diagnostico"] = diagnostico

    # ── CAPA 3: INTERPRETAR (Opus, ~$0.05) ──
    if con_opus:
        t3 = time.time()
        interpretacion = await interpretar_con_opus(texto, estructura, diagnostico)
        lat_interpretacion = round((time.time() - t3) * 1000)
        resultado["interpretacion"] = interpretacion
    else:
        lat_interpretacion = 0

    # ── META ──
    coste = 0.003 + (0.05 if con_opus else 0)
    resultado["meta"] = {
        "capas": ["perceptor_sonnet", "razonador_v3_41reglas"] + (["interprete_opus"] if con_opus else []),
        "latencia_percepcion_ms": lat_percepcion,
        "latencia_razonamiento_ms": lat_razonamiento,
        "latencia_interpretacion_ms": lat_interpretacion,
        "latencia_total_ms": round((time.time() - t0) * 1000),
        "coste_usd": coste,
        "detectores_aplicados": 41,
    }

    if verbose:
        resultado["estructura_acd"] = estructura

    return resultado


# ═══════════════════════════════════════════════════════════════
# DEMO
# ═══════════════════════════════════════════════════════════════

async def demo():
    textos = [
        "Llevo tres meses sin ir a Pilates y la verdad es que noto que me duele más la espalda. Quiero volver pero me da pereza llamar al estudio para preguntar si puedo retomar mi plaza.",
        "Deberíamos mejorar significativamente la experiencia del cliente para posicionarnos mejor en el mercado.",
        "Ana no ha venido en 2 semanas, le cobré 3 clases y le envié un WhatsApp. Mañana la llamo.",
    ]

    print("═" * 70)
    print("  EXOCORTEX + OPUS — Percepción + Razonamiento + Interpretación")
    print("  41 detectores | 8 operaciones | 6 falacias | 9 modos | 3 lentes")
    print("═" * 70)

    for i, texto in enumerate(textos, 1):
        print(f"\n{'─' * 70}")
        print(f"  TEXTO {i}: {texto[:70]}...")
        print(f"{'─' * 70}")

        resultado = await analizar_profundo(texto, con_opus=True)

        if "error" in resultado:
            print(f"  ❌ {resultado['error']}")
            continue

        diag = resultado["diagnostico"]
        interp = resultado.get("interpretacion", {})
        meta = resultado["meta"]

        # Diagnóstico estructural
        print(f"\n  ┌─ DIAGNÓSTICO ESTRUCTURAL (código puro, $0)")
        print(f"  │  Salud: {diag.get('salud', '?'):.0%} | Resolución: {diag.get('resolucion_luminica', '?'):.0%} | Nivel: {diag.get('nivel_luminico', '?')}")
        print(f"  │  Hallazgos: {diag.get('n_hallazgos', 0)} | Falacias: {diag.get('n_falacias', 0)}")

        modos_a = diag.get("modos_ausentes", [])
        if modos_a:
            print(f"  │  Modos ciegos: {', '.join(modos_a[:4])}")

        lentes = diag.get("lentes_cubiertas", [])
        lentes_falta = [l for l in ["salud", "sentido", "continuidad"] if l not in lentes]
        if lentes_falta:
            print(f"  │  Lentes ausentes: {', '.join(lentes_falta)}")

        print(f"  │  Palanca: {diag.get('palanca', '?')[:80]}")
        print(f"  └─")

        # Interpretación Opus
        if interp and "raw" not in interp and "error" not in interp:
            print(f"\n  ┌─ INTERPRETACIÓN PROFUNDA (Opus)")
            print(f"  │")
            if interp.get("estructura_mental"):
                print(f"  │  🧠 Estructura mental:")
                print(f"  │     {interp['estructura_mental'][:120]}")
            if interp.get("creencia_invisible"):
                print(f"  │")
                print(f"  │  👁️ Creencia invisible:")
                print(f"  │     {interp['creencia_invisible'][:120]}")
            if interp.get("operacion_ausente_critica"):
                print(f"  │")
                print(f"  │  💡 Operación ausente crítica:")
                print(f"  │     {interp['operacion_ausente_critica'][:120]}")
            if interp.get("palanca"):
                print(f"  │")
                print(f"  │  🎯 Palanca:")
                print(f"  │     {interp['palanca'][:120]}")
            if interp.get("pregunta_que_abre"):
                print(f"  │")
                print(f"  │  ❓ Pregunta que abre:")
                print(f"  │     {interp['pregunta_que_abre'][:120]}")
            if interp.get("conexion_profunda"):
                print(f"  │")
                print(f"  │  🔗 Conexión profunda:")
                print(f"  │     {interp['conexion_profunda'][:120]}")
            if interp.get("prescripcion"):
                print(f"  │")
                print(f"  │  💊 Prescripción:")
                print(f"  │     {interp['prescripcion'][:120]}")
            print(f"  └─")
        elif interp.get("raw"):
            print(f"\n  ┌─ INTERPRETACIÓN (raw)")
            print(f"  │  {interp['raw'][:300]}")
            print(f"  └─")

        print(f"\n  ⏱️ Percepción: {meta['latencia_percepcion_ms']}ms | Razonamiento: {meta['latencia_razonamiento_ms']}ms | Opus: {meta['latencia_interpretacion_ms']}ms")
        print(f"  💰 Coste: ${meta['coste_usd']:.3f}")

    print(f"\n{'═' * 70}")
    coste_total = 0.053 * len(textos)
    print(f"  COSTE TOTAL: ${coste_total:.3f} ({len(textos)} análisis)")
    print(f"  vs LLM solo (sin estructura): ~${0.10 * len(textos):.2f}")
    print(f"  Ventaja: {len(textos)} diagnósticos ESTRUCTURALES que un LLM solo no puede hacer")
    print(f"{'═' * 70}")


if __name__ == "__main__":
    asyncio.run(demo())
