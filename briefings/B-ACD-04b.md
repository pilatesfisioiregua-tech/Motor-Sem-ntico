# B-ACD-04b: Cliente OpenRouter para pipeline ACD

**Fecha:** 2026-03-20
**Ejecutor:** Claude Code
**Dependencia:** Ninguna
**Pre-requisito de:** B-ACD-05, B-ACD-07

---

## CONTEXTO

El pipeline ACD necesita LLM para dos tareas:
- B-ACD-05: texto → 21 scores JSON (evaluador funcional)
- B-ACD-07: texto + vector → clasificación INT/P/R JSON (repertorio)

El cliente actual (`src/utils/llm_client.py`) solo habla Anthropic API. El modelo óptimo es DeepSeek V3.2 vía OpenRouter — rendimiento GPT-5-class, structured outputs nativos, ~4x más barato que Haiku.

OpenRouter soporta `response_format: { type: "json_schema" }` que **garantiza** JSON válido a nivel de infraestructura. Además ofrece Response Healing (gratis, <1ms) como safety net.

---

## PASO 1: Actualizar settings.py

**Archivo:** `@project/src/config/settings.py`

**Leer primero.** Luego AÑADIR al final (no modificar lo existente):

```python
# OpenRouter
OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

# Modelos ACD (vía OpenRouter)
MODEL_ACD_EVALUATOR: str = "deepseek/deepseek-v3.2"   # texto → 21 scores F×L
MODEL_ACD_REPERTORIO: str = "deepseek/deepseek-v3.2"  # texto → INT×P×R
```

**Pass/fail:** `from src.config.settings import OPENROUTER_API_KEY, MODEL_ACD_EVALUATOR` no crashea.

---

## PASO 2: Crear openrouter_client.py

**Crear archivo:** `@project/src/utils/openrouter_client.py`

**Contenido EXACTO:**

```python
"""Cliente OpenRouter mínimo para pipeline ACD.

Soporta:
  - response_format json_schema (structured outputs garantizados)
  - Response Healing plugin (repara JSON malformado, gratis, <1ms)
  - Retry con backoff exponencial
  - Tracking de coste

Usa DeepSeek V3.2 por defecto (GPT-5-class, $0.27/$1.10 per M tokens).
"""
from __future__ import annotations

import asyncio
import json
from typing import Any

import httpx
import structlog

from src.config.settings import OPENROUTER_API_KEY, OPENROUTER_BASE_URL

log = structlog.get_logger()


class OpenRouterClient:
    """Cliente async para OpenRouter API con structured outputs."""

    def __init__(self, api_key: str | None = None):
        self._api_key = api_key or OPENROUTER_API_KEY
        if not self._api_key:
            raise ValueError("OPENROUTER_API_KEY no configurada")
        self._total_cost: float = 0.0

    async def complete_json(
        self,
        model: str,
        system: str,
        user_message: str,
        json_schema: dict[str, Any] | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.1,
        retries: int = 3,
    ) -> dict:
        """Envía mensaje y devuelve JSON parseado.

        Args:
            model: ID del modelo en OpenRouter (ej: "deepseek/deepseek-v3.2")
            system: System prompt
            user_message: Mensaje del usuario
            json_schema: Schema JSON para structured outputs. Si None, usa json_object mode.
            max_tokens: Máximo tokens de output
            temperature: Temperature (0.1 para máximo determinismo)
            retries: Intentos con backoff exponencial

        Returns:
            dict parseado del JSON del modelo.

        Raises:
            ValueError: Si el modelo no devuelve JSON válido tras todos los reintentos.
        """
        # Construir response_format
        if json_schema:
            response_format = {
                "type": "json_schema",
                "json_schema": json_schema,
            }
        else:
            response_format = {"type": "json_object"}

        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "response_format": response_format,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user_message},
            ],
            "plugins": [{"id": "response-healing"}],
        }

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://omni-mind.ai",
            "X-Title": "OMNI-MIND Motor ACD",
        }

        last_error = None
        for attempt in range(retries):
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    resp = await client.post(
                        f"{OPENROUTER_BASE_URL}/chat/completions",
                        json=payload,
                        headers=headers,
                    )
                    resp.raise_for_status()
                    data = resp.json()

                # Extraer texto de la respuesta
                choices = data.get("choices", [])
                if not choices:
                    raise ValueError("OpenRouter devolvió 0 choices")

                text = choices[0].get("message", {}).get("content", "")

                # Parsear JSON
                result = json.loads(text)

                # Track cost
                usage = data.get("usage", {})
                input_tokens = usage.get("prompt_tokens", 0)
                output_tokens = usage.get("completion_tokens", 0)
                cost = self._estimate_cost(model, input_tokens, output_tokens)
                self._total_cost += cost

                log.info(
                    "openrouter.complete_json",
                    model=model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cost=cost,
                    attempt=attempt,
                )

                return result

            except (httpx.HTTPStatusError, json.JSONDecodeError, ValueError, KeyError) as e:
                last_error = e
                log.warning(
                    "openrouter.retry",
                    model=model,
                    attempt=attempt,
                    error=str(e),
                )
                await asyncio.sleep(2 ** attempt)

        raise ValueError(f"OpenRouter falló tras {retries} intentos: {last_error}")

    @staticmethod
    def _estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
        """Estimación de coste (USD). Precios OpenRouter marzo 2026."""
        rates = {
            # (input_per_M, output_per_M)
            "deepseek/deepseek-v3.2": (0.27, 1.10),
            "google/gemini-2.0-flash-001": (0.10, 0.40),
            "google/gemini-3-flash-preview": (0.15, 0.60),
            "qwen/qwen3-235b-a22b": (0.20, 0.80),
            "mistralai/mistral-small-3.1-24b-instruct": (0.10, 0.30),
        }
        input_rate, output_rate = rates.get(model, (0.50, 1.50))
        return (input_tokens * input_rate + output_tokens * output_rate) / 1_000_000

    @property
    def total_cost(self) -> float:
        return self._total_cost

    def reset_cost(self):
        self._total_cost = 0.0


# Singleton lazy
class _LazyOpenRouter:
    _instance: OpenRouterClient | None = None

    def _get(self) -> OpenRouterClient:
        if self._instance is None:
            self._instance = OpenRouterClient()
        return self._instance

    def __getattr__(self, name: str):
        return getattr(self._get(), name)


openrouter = _LazyOpenRouter()
```

---

## PASO 3: Test de conectividad

**Pass/fail:**

```bash
cd @project/ && python3 -c "
import asyncio
from src.utils.openrouter_client import openrouter
from src.config.settings import MODEL_ACD_EVALUATOR, OPENROUTER_API_KEY

# Test 0: Config cargada
assert OPENROUTER_API_KEY, 'OPENROUTER_API_KEY no configurada'
print(f'PASS 0: API key presente ({len(OPENROUTER_API_KEY)} chars)')

# Test 1: complete_json con json_object mode (sin schema)
async def test():
    result = await openrouter.complete_json(
        model=MODEL_ACD_EVALUATOR,
        system='Responde SOLO con JSON válido. Formato: {\"test\": true, \"model\": \"nombre\"}',
        user_message='¿Qué modelo eres?',
        max_tokens=128,
        temperature=0.1,
    )
    assert isinstance(result, dict), f'Expected dict, got {type(result)}'
    print(f'PASS 1: complete_json retorna dict: {result}')

    # Test 2: complete_json con json_schema (structured outputs)
    schema = {
        'name': 'test_output',
        'strict': True,
        'schema': {
            'type': 'object',
            'properties': {
                'salud': {'type': 'number'},
                'sentido': {'type': 'number'},
                'continuidad': {'type': 'number'},
            },
            'required': ['salud', 'sentido', 'continuidad'],
            'additionalProperties': False,
        }
    }
    result2 = await openrouter.complete_json(
        model=MODEL_ACD_EVALUATOR,
        system='Evalúa las 3 lentes de un negocio. Valores 0.0 a 1.0.',
        user_message='Estudio de Pilates rentable pero dependiente de una instructora.',
        json_schema=schema,
        max_tokens=128,
        temperature=0.1,
    )
    assert 'salud' in result2, f'Missing salud: {result2}'
    assert 'sentido' in result2, f'Missing sentido: {result2}'
    assert 'continuidad' in result2, f'Missing continuidad: {result2}'
    print(f'PASS 2: json_schema retorna {result2}')
    print(f'Coste total: \${openrouter.total_cost:.6f}')

asyncio.run(test())
print('\\nTODOS LOS TESTS PASAN')
"
```

**CRITERIO PASS:**
1. API key presente
2. `complete_json` con json_object mode retorna dict válido
3. `complete_json` con json_schema retorna dict con campos exactos del schema

---

## ARCHIVOS QUE SE TOCAN

| Archivo | Acción |
|---------|--------|
| `src/config/settings.py` | EDITAR — añadir 4 líneas OpenRouter al final |
| `src/utils/openrouter_client.py` | CREAR (nuevo) |

## ARCHIVOS QUE NO SE TOCAN

llm_client.py (Anthropic) sigue existiendo para el pipeline original. No se modifica.

## NOTAS

- `httpx` debe estar en requirements.txt. Si no está, añadir: `httpx>=0.27.0`
- El plugin `response-healing` se activa en cada request (gratis, <1ms). Repara JSON malformado automáticamente.
- `json_schema` mode es más estricto que `json_object`: garantiza que el output matchea el schema exacto. Usar siempre que el schema sea conocido (B-ACD-05 y B-ACD-07 lo tienen).
- El singleton `openrouter` funciona igual que el `llm` de Anthropic — lazy init al primer uso.
