"""Cliente OpenRouter async para el motor semántico.

Usa API compatible con OpenAI (chat/completions).
Soporta response_format json_schema para extracción estructurada.
Activa Response Healing automáticamente vía plugin.
"""
from __future__ import annotations

import os
import json
import asyncio
import httpx
import structlog
from dotenv import load_dotenv

load_dotenv()
log = structlog.get_logger()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

# Modelo por defecto para extracción estructurada
MODEL_EXTRACTOR_OR = os.getenv("MODEL_EXTRACTOR_OR", "deepseek/deepseek-v3.2")


async def openrouter_complete(
    model: str,
    system: str,
    user_message: str,
    json_schema: dict | None = None,
    max_tokens: int = 4096,
    temperature: float = 0.1,
    retries: int = 3,
) -> str:
    """Llama a OpenRouter y devuelve texto (o JSON si json_schema).

    Args:
        model: ID del modelo en OpenRouter (ej: deepseek/deepseek-v3.2)
        system: System prompt.
        user_message: Mensaje del usuario.
        json_schema: Si se pasa, activa response_format json_schema.
                     El modelo DEBE devolver JSON válido que cumpla el schema.
        max_tokens: Máximo tokens de respuesta.
        temperature: 0.0-1.0.
        retries: Reintentos con backoff.

    Returns:
        Texto de la respuesta del modelo.
    """
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY no configurada")

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "X-Title": "OMNI-MIND Motor Semantico",
    }

    body: dict = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_message},
        ],
        "plugins": [{"id": "response-healing"}],
    }

    if json_schema:
        body["response_format"] = {
            "type": "json_schema",
            "json_schema": json_schema,
        }

    last_error = None
    async with httpx.AsyncClient(timeout=60.0) as client:
        for attempt in range(retries):
            try:
                resp = await client.post(OPENROUTER_BASE_URL, headers=headers, json=body)
                resp.raise_for_status()
                data = resp.json()

                # Extraer texto de la respuesta
                choices = data.get("choices", [])
                if not choices:
                    raise ValueError(f"Sin choices en respuesta: {data}")

                content = choices[0].get("message", {}).get("content", "")

                # Log usage
                usage = data.get("usage", {})
                log.info(
                    "openrouter.ok",
                    model=model,
                    input_tokens=usage.get("prompt_tokens", 0),
                    output_tokens=usage.get("completion_tokens", 0),
                    attempt=attempt,
                )
                return content

            except Exception as e:
                last_error = e
                log.warning("openrouter.retry", model=model, attempt=attempt, error=str(e))
                await asyncio.sleep(2 ** attempt)

    raise last_error


async def openrouter_json(
    model: str,
    system: str,
    user_message: str,
    schema_name: str,
    schema: dict,
    max_tokens: int = 4096,
    temperature: float = 0.1,
) -> dict:
    """Wrapper que llama a OpenRouter con json_schema y parsea el resultado.

    Args:
        model: ID del modelo.
        system: System prompt.
        user_message: Mensaje.
        schema_name: Nombre del schema (ej: "vector_funcional").
        schema: JSON Schema dict.
        max_tokens: Máximo tokens.
        temperature: 0.0-1.0.

    Returns:
        Dict parseado del JSON devuelto por el modelo.
    """
    json_schema = {
        "name": schema_name,
        "strict": True,
        "schema": schema,
    }

    respuesta = await openrouter_complete(
        model=model,
        system=system,
        user_message=user_message,
        json_schema=json_schema,
        max_tokens=max_tokens,
        temperature=temperature,
    )

    # Limpiar posibles backticks (por si acaso, aunque json_schema debería evitarlos)
    texto = respuesta.strip()
    if texto.startswith("```"):
        texto = texto.split("\n", 1)[1] if "\n" in texto else texto[3:]
    if texto.endswith("```"):
        texto = texto[:-3]
    texto = texto.strip()

    return json.loads(texto)
