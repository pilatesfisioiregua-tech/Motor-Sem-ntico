"""Perceptor — Capa de percepción (LLM barato, 1 sola llamada).

Extrae TODA la estructura ACD de un texto en UNA llamada a Haiku.
Coste: ~$0.001 por texto.

Antes: 7 primitivas × 16 calls = 112 llamadas Haiku (~$0.20)
Ahora: 1 llamada Haiku (~$0.001)

El LLM NO razona. Solo PERCIBE y estructura.
"""
from __future__ import annotations

import json
import os
from typing import Optional

import httpx
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY_1", os.getenv("ANTHROPIC_API_KEY", ""))

# ═══════════════════════════════════════════════════════════════
# PROMPT DE PERCEPCIÓN — Extrae estructura ACD en 1 llamada
# ═══════════════════════════════════════════════════════════════

SYSTEM_PERCEPTOR = """Eres un perceptor lingüístico-cognitivo. Extraes la estructura de un texto.
NO interpretes. NO opines. Solo PERCIBE y estructura en JSON.

REGLAS CRÍTICAS:
- "perdido" = lista de CONCEPTOS/IDEAS perdidos al comprimir (frases cortas, NO caracteres sueltos)
- "modos_ocultos" = lista de MODOS DE OPERAR implícitos (frases cortas, NO caracteres)
- "colapsos" y "conexiones_rotas" = FRASES que describen el problema
- "cualidades" y "vacios" = PALABRAS completas del texto, no caracteres
- Todos los arrays contienen strings legibles de 3+ palabras (NUNCA caracteres sueltos como "m", "é", "t")

7 DIMENSIONES A EXTRAER:

1. SUSTANTIVOS: capsulas={palabra: compresión máxima en 1-3 palabras, frase: en 1 oración, parrafo: en 2-3 oraciones}, perdido=[conceptos importantes que se pierden al comprimir]

2. SUJETO-PREDICADO: sujeto=quién actúa (nombre concreto), predicado=qué hace, agencia=0.0-1.0 (0=pasivo/difuso, 1=claro/activo), responsabilidad=quién responde

3. ADJETIVOS: cualidades=[adjetivos usados en el texto], precision=0.0-1.0 (0=vagos, 1=medibles), vacios=[adjetivos sin dato que los sostenga]

4. ADVERBIOS: modo_explicito=cómo dice que opera, modos_ocultos=[modos implícitos de operar], explicitud=0.0-1.0

5. PREPOSICIONES: relaciones=[conexiones entre ideas], nivel_logico=conducta/capacidad/creencia/identidad/meta, conexiones_rotas=[relaciones sin justificar], colapsos=[mezclas entre niveles]

6. CONJUNCIONES: tipo_conexion=adición/oposición/causalidad/condición/temporal/ausencia, falsas_dicotomias=[si hay], causalidades_circulares=[si hay], piezas_sueltas=[ideas sin conexión]

7. VERBO: verbo_nuclear=acción central, fuerza=0.0-1.0, verbo_vida=mantener/distinguir/repartir/responder/copiar/sacar/meter, produce_resultado=true/false

RESPONDE SOLO EN JSON. Sin explicaciones. Sin markdown."""

TEMPLATE_RESPUESTA = """{
  "sustantivos": {"capsulas": {"palabra": "", "frase": "", "parrafo": ""}, "perdido": []},
  "sujeto_predicado": {"sujeto": "", "predicado": "", "agencia": 0.0, "responsabilidad": ""},
  "adjetivos": {"cualidades": [], "precision": 0.0, "vacios": []},
  "adverbios": {"modo_explicito": "", "modos_ocultos": [], "explicitud": 0.0},
  "preposiciones": {"relaciones": [], "nivel_logico": "", "conexiones_rotas": [], "colapsos": []},
  "conjunciones": {"tipo_conexion": "", "falsas_dicotomias": [], "causalidades_circulares": [], "piezas_sueltas": []},
  "verbo": {"verbo_nuclear": "", "fuerza": 0.0, "verbo_vida": "", "produce_resultado": false}
}"""


async def percibir(texto: str) -> dict:
    """Percibe la estructura ACD de un texto. 1 llamada LLM. ~$0.001.

    Args:
        texto: El texto a analizar

    Returns:
        Estructura ACD con 7 dimensiones extraídas
    """
    if not ANTHROPIC_KEY:
        return {"error": "Sin ANTHROPIC_API_KEY"}

    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 1024,
                "system": SYSTEM_PERCEPTOR,
                "messages": [{"role": "user", "content": f"TEXTO:\n{texto}\n\nEstructura (JSON):"}],
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
            estructura = json.loads(clean[start:end])
            estructura["_meta"] = {
                "modelo": "haiku",
                "coste_estimado": 0.001,
                "texto_len": len(texto),
            }
            return estructura
    except json.JSONDecodeError:
        pass

    return {"error": "No se pudo parsear la percepción", "raw": response[:500]}
