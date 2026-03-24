"""Extracción robusta de JSON desde respuestas LLM."""
from __future__ import annotations

import json
import re
import structlog

log = structlog.get_logger()


def extraer_json(texto: str, fallback: dict = None) -> dict:
    """Extrae JSON de una respuesta LLM que puede contener markdown, texto extra, etc.

    Estrategia:
    1. Intenta parsear directo
    2. Busca bloque ```json ... ```
    3. Busca primer { ... último }
    4. Devuelve fallback
    """
    if not texto:
        return fallback or {}

    texto = texto.strip()

    # 1. Directo
    try:
        return json.loads(texto)
    except (json.JSONDecodeError, TypeError):
        pass  # expected

    # 2. Bloque markdown
    match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', texto, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except (json.JSONDecodeError, TypeError):
            pass  # expected

    # 3. Primer { ... último }
    start = texto.find('{')
    end = texto.rfind('}')
    if start != -1 and end > start:
        try:
            return json.loads(texto[start:end + 1])
        except (json.JSONDecodeError, TypeError):
            pass  # expected

    # 4. Array?
    start = texto.find('[')
    end = texto.rfind(']')
    if start != -1 and end > start:
        try:
            arr = json.loads(texto[start:end + 1])
            return {"items": arr}
        except (json.JSONDecodeError, TypeError):
            pass  # expected

    log.warning("json_extract_failed", preview=texto[:100])
    return fallback or {}


def extraer_json_lista(texto: str) -> list:
    """Extrae una lista JSON de una respuesta LLM."""
    result = extraer_json(texto, fallback={"items": []})
    if isinstance(result, list):
        return result
    return result.get("items", [])
