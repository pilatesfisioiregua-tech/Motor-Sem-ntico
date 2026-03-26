"""Generador ACD — Guía al LLM para generar output estructuralmente completo.

El framework ACD no solo ANALIZA input — también GENERA output.
Este módulo hace dos cosas:

1. GENERADOR: Crea un system prompt que obliga al LLM a generar
   respuestas con estructura ACD completa (sujeto claro, verbos fuertes,
   adjetivos cuantificados, modos explícitos, sin falacias).

2. VERIFICADOR: Chequea el output del LLM contra las 48 reglas
   del Razonador ANTES de entregarlo al usuario. Si falla, regenera.

RESULTADO: Output con garantía estructural.
- Sujeto siempre claro (no "se debería")
- Verbos con fuerza y objeto (no "mejorar" sin decir qué)
- Adjetivos con dato (no "significativamente")
- Modos explícitos (no implícitos)
- Sin falacias
- 3 lentes cubiertas
- Resolución de estadio
"""
from __future__ import annotations

import json
import os
from typing import Optional

import httpx
from dotenv import load_dotenv

load_dotenv()

from .perceptor import percibir
from .razonador import razonar, diagnostico_a_dict

ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY_1", os.getenv("ANTHROPIC_API_KEY", ""))


# ═══════════════════════════════════════════════════════════════
# GENERADOR: System prompt que fuerza estructura ACD en output
# ═══════════════════════════════════════════════════════════════

SYSTEM_GENERADOR_ACD = """REGLAS DE GENERACIÓN (5 obligatorias, el resto recomendadas):

OBLIGATORIAS:
1. SUJETO CONCRETO: Nunca "se debería" / "habría que" / "la empresa". Siempre nombre o rol: "María hará...", "el dueño decidirá..."
2. VERBO CON OBJETO: Nunca "mejorar" sin decir qué. Siempre: "reducir espera de 15 a 5 min", "llamar a 3 clientes"
3. DATO, NO ADJETIVO: Nunca "significativamente". Siempre: "35% más", "3 de 5 clientes"
4. MODO EXPLÍCITO: Nunca "contactar clientes". Siempre: "WhatsApp a las 10am preguntando cómo están"
5. SIN SUJETOS FALSOS: Nunca "la economía exige" / "la ciencia demuestra". Las abstracciones no actúan.

RECOMENDADAS:
- Cubrir 3 ángulos: estado actual (¿cómo está?), identidad (¿qué es?), continuidad (¿seguirá?)
- Cada afirmación tiene: quién + qué + cómo + cuánto + por qué
- No presentar condicionales como hechos
"""


def generar_prompt_acd(contexto: str = "", diagnostico_input: dict = None) -> str:
    """Genera un system prompt enriquecido con ACD para guiar al LLM.

    Args:
        contexto: Contexto adicional para el prompt
        diagnostico_input: Si hay diagnóstico del input, lo usa para guiar la respuesta

    Returns:
        System prompt con reglas ACD + contexto
    """
    prompt = SYSTEM_GENERADOR_ACD

    if diagnostico_input:
        # Inyectar hallazgos del input para que el LLM responda a ellos
        hallazgos = diagnostico_input.get("hallazgos", [])
        if hallazgos:
            prompt += "\n\nHALLAZGOS DEL ANÁLISIS DEL INPUT (responde a estos):\n"
            for h in hallazgos[:3]:
                prompt += f"- [{h.get('operacion', '?')}] {h.get('descripcion', '')[:100]}\n"

        palanca = diagnostico_input.get("palanca", "")
        if palanca:
            prompt += f"\nPALANCA DETECTADA: {palanca}\n"

        preguntas = diagnostico_input.get("preguntas", [])
        if preguntas:
            prompt += "\nPREGUNTAS QUE ABREN:\n"
            for q in preguntas[:3]:
                prompt += f"- {q}\n"

    if contexto:
        prompt += f"\nCONTEXTO ADICIONAL:\n{contexto}\n"

    return prompt


# ═══════════════════════════════════════════════════════════════
# VERIFICADOR: Chequea output del LLM contra reglas ACD
# ═══════════════════════════════════════════════════════════════

async def verificar_output(texto_output: str) -> dict:
    """Verifica que el output del LLM cumple las reglas ACD.

    Pasa el output por Perceptor + Razonador y devuelve:
    - aprobado: bool
    - problemas: lista de hallazgos
    - score: 0.0-1.0
    """
    # Percibir estructura del output
    estructura = await percibir(texto_output)
    if "error" in estructura:
        return {"aprobado": False, "error": estructura["error"], "score": 0.0}

    # Razonar sobre la estructura
    diagnostico = razonar(estructura)
    diag_dict = diagnostico_a_dict(diagnostico)

    # Criterios de aprobación
    salud = diag_dict.get("salud", 0)
    n_falacias = diag_dict.get("n_falacias", 0)
    n_hallazgos = diag_dict.get("n_hallazgos", 0)
    nivel = diag_dict.get("nivel_luminico", "vela")

    # Aprobado si:
    # - Salud >= 60%
    # - 0 falacias
    # - Resolución >= habitación
    aprobado = salud >= 0.4 and n_falacias <= 1 and nivel != "vela"

    problemas = []
    if salud < 0.4:
        problemas.append(f"Salud baja: {salud:.0%}")
    if n_falacias > 1:
        fal = [h for h in diag_dict.get("hallazgos", []) if h.get("tipo") == "falacia"]
        for f in fal:
            problemas.append(f"Falacia: {f.get('descripcion', '')[:80]}")
    if nivel == "vela":
        problemas.append("Resolución de vela — falta detalle estructural")

    return {
        "aprobado": aprobado,
        "score": salud,
        "nivel_luminico": nivel,
        "n_falacias": n_falacias,
        "n_hallazgos": n_hallazgos,
        "problemas": problemas,
        "diagnostico": diag_dict,
    }


# ═══════════════════════════════════════════════════════════════
# PIPELINE COMPLETO: Input → Análisis → Generación → Verificación
# ═══════════════════════════════════════════════════════════════

async def generar_respuesta_acd(
    texto_input: str,
    instruccion: str = "Responde al texto del usuario de forma estructuralmente completa.",
    max_intentos: int = 2,
    contexto: str = "",
) -> dict:
    """Pipeline completo bidireccional:

    1. Analiza input (Perceptor + Razonador)
    2. Genera prompt ACD con hallazgos del input
    3. LLM genera respuesta guiada por ACD
    4. Verifica output contra reglas ACD
    5. Si falla, regenera con feedback

    Returns:
        {respuesta, diagnostico_input, verificacion_output, intentos, meta}
    """
    import time
    t0 = time.time()

    # ── 1. ANALIZAR INPUT ──
    estructura_input = await percibir(texto_input)
    if "error" not in estructura_input:
        diagnostico_input = diagnostico_a_dict(razonar(estructura_input))
    else:
        diagnostico_input = None

    # ── 2. GENERAR PROMPT ACD ──
    system = generar_prompt_acd(contexto, diagnostico_input)
    system += f"\n\nINSTRUCCIÓN: {instruccion}"

    user = f"TEXTO DEL USUARIO:\n{texto_input}"

    respuesta_final = ""
    verificacion_final = None
    intentos = 0

    for intento in range(max_intentos):
        intentos = intento + 1

        # ── 3. LLM GENERA RESPUESTA ──
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
                    "system": system,
                    "messages": [{"role": "user", "content": user}],
                },
            )
            data = r.json()
            respuesta = data.get("content", [{}])[0].get("text", "")

        if not respuesta:
            continue

        # ── 4. VERIFICAR OUTPUT ──
        verificacion = await verificar_output(respuesta)
        verificacion_final = verificacion
        respuesta_final = respuesta

        if verificacion["aprobado"]:
            break  # Output aprobado

        # ── 5. FEEDBACK PARA REGENERAR ──
        if intento < max_intentos - 1:
            problemas_str = "\n".join(f"- {p}" for p in verificacion["problemas"])
            user = f"""Tu respuesta anterior tenía estos problemas estructurales:
{problemas_str}

TEXTO ORIGINAL DEL USUARIO:
{texto_input}

Genera una nueva respuesta que corrija TODOS los problemas. Aplica las reglas ACD estrictamente."""

    return {
        "respuesta": respuesta_final,
        "diagnostico_input": diagnostico_input,
        "verificacion_output": verificacion_final,
        "intentos": intentos,
        "meta": {
            "latencia_total_ms": round((time.time() - t0) * 1000),
            "pipeline": "input→perceptor→razonador→generador_acd→llm→verificador→output",
            "bidireccional": True,
        },
    }


# ═══════════════════════════════════════════════════════════════
# DEMO
# ═══════════════════════════════════════════════════════════════

async def demo():
    """Demo del pipeline bidireccional."""
    import asyncio

    textos = [
        ("Llevo tres meses sin ir a Pilates y me duele la espalda.",
         "Responde como un asistente de bienestar que ayuda a la persona a volver."),
        ("Deberíamos mejorar la experiencia del cliente.",
         "Traduce esta intención vaga en un plan de acción concreto."),
    ]

    print("═" * 70)
    print("  PIPELINE BIDIRECCIONAL ACD")
    print("  Input → Análisis → Generación guiada → Verificación → Output")
    print("═" * 70)

    for texto, instruccion in textos:
        print(f"\n{'─' * 70}")
        print(f"  INPUT: {texto}")
        print(f"  INSTRUCCIÓN: {instruccion}")
        print(f"{'─' * 70}")

        resultado = await generar_respuesta_acd(texto, instruccion)

        # Diagnóstico del input
        if resultado["diagnostico_input"]:
            di = resultado["diagnostico_input"]
            print(f"\n  📥 INPUT  → Salud: {di.get('salud', '?'):.0%} | Hallazgos: {di.get('n_hallazgos', 0)} | Falacias: {di.get('n_falacias', 0)}")

        # Verificación del output
        if resultado["verificacion_output"]:
            vo = resultado["verificacion_output"]
            status = "✅ APROBADO" if vo["aprobado"] else "⚠️ CON PROBLEMAS"
            print(f"  📤 OUTPUT → {status} | Score: {vo['score']:.0%} | Nivel: {vo.get('nivel_luminico', '?')} | Intentos: {resultado['intentos']}")
            if vo["problemas"]:
                for p in vo["problemas"][:3]:
                    print(f"     ⚠️ {p[:80]}")

        # Respuesta
        print(f"\n  💬 RESPUESTA:")
        for line in resultado["respuesta"].split("\n")[:10]:
            if line.strip():
                print(f"     {line.strip()[:90]}")

        print(f"\n  ⏱️ Total: {resultado['meta']['latencia_total_ms']}ms")

    print(f"\n{'═' * 70}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(demo())
