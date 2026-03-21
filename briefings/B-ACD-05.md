# B-ACD-05: Derivar vector funcional desde texto (LLM)

**Fecha:** 2026-03-20
**Ejecutor:** Claude Code
**Dependencia:** B-ACD-01 ✅, B-ACD-02 ✅, B-ACD-03 ✅
**Modelo:** DeepSeek V3.2 (`deepseek/deepseek-v3.2`) vía OpenRouter
**Por qué V3.2:** Rendimiento GPT-5 class en extracción estructurada, soporta `response_format: json_schema`, ya validado en el stack, ~4x más barato que Haiku para la misma calidad.

---

## CONTEXTO

GAP más crítico del pipeline ACD. `campo.py` asume VectorFuncional precompilado. Para end-to-end necesitamos derivar el vector desde texto libre.

**Flujo:** texto del caso → V3.2 (OpenRouter, json_schema forzado) → 21 scores (7F × 3L) → agregar → VectorFuncional (7 scores)

---

## PASO 0: Crear cliente OpenRouter para el motor

**Crear archivo:** `@project/src/utils/openrouter_client.py`

**Contenido EXACTO:**

```python
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
```

**Pass/fail paso 0:**
```bash
cd @project/ && python3 -c "
import os
assert os.getenv('OPENROUTER_API_KEY'), 'OPENROUTER_API_KEY no configurada'
from src.utils.openrouter_client import openrouter_complete, openrouter_json, MODEL_EXTRACTOR_OR
print(f'PASS: Cliente importa. Modelo extractor: {MODEL_EXTRACTOR_OR}')
"
```

---

## PASO 1: Crear evaluador_funcional.py

**Crear archivo:** `@project/src/tcf/evaluador_funcional.py`

**Contenido EXACTO:**

```python
"""Evaluador funcional — deriva VectorFuncional desde texto usando LLM.

Paso P1 del pipeline ACD: caso (texto) → 21 scores F×L → VectorFuncional.
Usa DeepSeek V3.2 vía OpenRouter con json_schema forzado.
"""
from __future__ import annotations

import structlog

from src.tcf.campo import VectorFuncional
from src.tcf.constantes import FUNCIONES, LENTES
from src.utils.openrouter_client import openrouter_json, MODEL_EXTRACTOR_OR

log = structlog.get_logger()


SYSTEM_PROMPT = """Eres un evaluador funcional de sistemas (empresas, proyectos, organizaciones).

Tu tarea: dado un caso descrito en texto, evaluar 7 funciones vitales desde 3 perspectivas (lentes).

## 7 FUNCIONES

F1 Conservar: Mantener lo que funciona. Proteger recursos, conocimiento, procesos estables.
F2 Captar: Adquirir del exterior. Clientes, talento, información, recursos, oportunidades.
F3 Depurar: Eliminar lo que sobra o daña. Filtrar, limpiar, descartar lo tóxico o ineficiente.
F4 Distribuir: Repartir internamente. Asignar recursos, información, responsabilidades donde se necesitan.
F5 Frontera: Definir identidad y límites. Saber qué es el sistema y qué no, qué entra y qué no.
F6 Adaptar: Cambiar ante el entorno. Flexibilidad, innovación, respuesta a nuevas condiciones.
F7 Replicar: Transmitir y escalar. Que el sistema pueda funcionar sin sus creadores originales.

## 3 LENTES

salud: ¿Funciona? Operativa, eficiencia, supervivencia día a día.
sentido: ¿Comprende por qué? Propósito, significado, cuestionamiento profundo.
continuidad: ¿Puede persistir y transmitirse? Escalabilidad, transferencia, legado.

## INSTRUCCIONES

Para CADA función (F1-F7), evalúa el grado en que el sistema la cumple desde CADA lente.

Escala: 0.0 (ausente) a 1.0 (excelente).
- 0.0-0.20: No existe o no funciona
- 0.20-0.40: Presente pero deficiente
- 0.40-0.60: Funcional pero mejorable
- 0.60-0.80: Bueno
- 0.80-1.0: Excelente"""


# JSON Schema para response_format (fuerza estructura exacta)
SCHEMA_VECTOR = {
    "type": "object",
    "properties": {
        fi: {
            "type": "object",
            "properties": {
                lente: {"type": "number"} for lente in ("salud", "sentido", "continuidad")
            },
            "required": ["salud", "sentido", "continuidad"],
            "additionalProperties": False,
        }
        for fi in ("F1", "F2", "F3", "F4", "F5", "F6", "F7")
    },
    "required": ["F1", "F2", "F3", "F4", "F5", "F6", "F7"],
    "additionalProperties": False,
}


async def evaluar_funcional(caso_texto: str) -> tuple[dict[str, dict[str, float]], VectorFuncional]:
    """Deriva VectorFuncional desde texto usando LLM.

    Args:
        caso_texto: Descripción del caso/sistema a evaluar.

    Returns:
        Tupla (scores_raw, vector):
          - scores_raw: dict 7F × 3L con los 21 scores originales del LLM
          - vector: VectorFuncional agregado (7 scores, uno por función)

    Raises:
        ValueError: Si los scores están fuera de rango.
    """
    log.info("evaluador_funcional.start", caso_len=len(caso_texto))

    scores_raw = await openrouter_json(
        model=MODEL_EXTRACTOR_OR,
        system=SYSTEM_PROMPT,
        user_message=f"CASO A EVALUAR:\n\n{caso_texto}",
        schema_name="vector_funcional",
        schema=SCHEMA_VECTOR,
        max_tokens=512,
        temperature=0.1,
    )

    # Validar rangos
    for fi in FUNCIONES:
        if fi not in scores_raw:
            raise ValueError(f"Falta función {fi} en respuesta LLM")
        for lente in LENTES:
            if lente not in scores_raw[fi]:
                raise ValueError(f"Falta lente {lente} en {fi}")
            val = float(scores_raw[fi][lente])
            if not (0.0 <= val <= 1.0):
                raise ValueError(f"{fi}.{lente}={val} fuera de rango [0,1]")
            scores_raw[fi][lente] = val

    # Agregar: promedio de las 3 lentes por función → grado funcional
    grados = {}
    for fi in FUNCIONES:
        grados[fi] = round(
            sum(scores_raw[fi][l] for l in LENTES) / len(LENTES),
            3,
        )

    vector = VectorFuncional.from_dict(grados)

    log.info(
        "evaluador_funcional.ok",
        vector=vector.to_dict(),
        eslabon_debil=vector.eslabon_debil(),
    )

    return scores_raw, vector
```

---

## PASO 2: Test de validación

**Pass/fail:**

```bash
cd @project/ && python3 -c "
import asyncio
from src.tcf.evaluador_funcional import evaluar_funcional, SYSTEM_PROMPT, SCHEMA_VECTOR
from src.tcf.constantes import FUNCIONES, LENTES

# Verificar schema
assert len(SCHEMA_VECTOR['properties']) == 7, 'Schema debe tener 7 funciones'
for fi in FUNCIONES:
    assert fi in SCHEMA_VECTOR['properties'], f'Falta {fi} en schema'
print('PASS 1: Schema tiene 7F × 3L')

# Test LLM real con caso Pilates
async def test():
    caso = '''Estudio de Pilates con 8 años de operación. Rentable pero altamente dependiente de la instructora principal.
    Sin ella, las clases se cancelan. No hay manual de operaciones. Los clientes vienen por ella, no por la marca.
    Identidad clara (Pilates reformer premium), pero no hay plan de expansión ni sistema de formación de instructores.
    No se ha despedido a ningún proveedor ineficiente ni se han revisado procesos en años.'''

    scores_raw, vector = await evaluar_funcional(caso)

    # Verificar estructura
    assert len(scores_raw) == 7, f'Expected 7 functions, got {len(scores_raw)}'
    for fi in FUNCIONES:
        for lente in LENTES:
            val = scores_raw[fi][lente]
            assert 0.0 <= val <= 1.0, f'{fi}.{lente}={val} fuera de rango'
    print(f'PASS 2: 21 scores validos (7F × 3L)')

    # Verificar VectorFuncional
    d = vector.to_dict()
    assert len(d) == 7
    print(f'PASS 3: VectorFuncional valido: {d}')

    # Coherencia minima Pilates:
    assert d['F5'] > d['F7'], f'F5={d[\"F5\"]} deberia ser > F7={d[\"F7\"]}'
    assert d['F7'] < 0.45, f'F7={d[\"F7\"]} deberia ser < 0.45'
    print(f'PASS 4: Coherencia basica (F5 > F7, F7 baja)')

    print(f'\\nVector Pilates: {d}')
    print(f'Eslabon debil: {vector.eslabon_debil()}')

asyncio.run(test())
print('\\nTODOS LOS TESTS PASAN')
"
```

**CRITERIO PASS:**
1. Schema tiene 7F × 3L
2. V3.2 devuelve 21 scores válidos [0,1] (json_schema forzado)
3. VectorFuncional tiene 7 grados válidos
4. Para caso Pilates: F5 > F7 y F7 < 0.45

---

## ARCHIVOS QUE SE TOCAN

| Archivo | Acción |
|---------|--------|
| `src/utils/openrouter_client.py` | CREAR (nuevo) |
| `src/tcf/evaluador_funcional.py` | CREAR (nuevo) |

## ARCHIVOS QUE NO SE TOCAN

Todo lo demás. No se modifica campo.py, constantes.py, flags.py, settings.py ni llm_client.py.

## NOTAS

- MODEL_EXTRACTOR_OR = `deepseek/deepseek-v3.2` (env var, overridable)
- `response_format: json_schema` fuerza JSON válido a nivel de infraestructura OpenRouter
- Response Healing activado como plugin (gratis, <1ms)
- Los 21 scores raw se devuelven para uso futuro (análisis granular Se por función → flag monopolio_se)
- Coste estimado: ~$0.001/caso con V3.2 (vs ~$0.003 con Haiku)
- El cliente OpenRouter también lo usa B-ACD-07 (repertorio.py)
