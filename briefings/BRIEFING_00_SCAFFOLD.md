# BRIEFING_00 — SCAFFOLD DEL PROYECTO

**Objetivo:** Crear la estructura completa del proyecto, dependencias, Dockerfile y configuración fly.io.
**Pre-requisito:** Ninguno. Este es el primer briefing.
**Output:** Proyecto inicializado, listo para poblar con código.

---

## TAREA

1. Crear la estructura de directorios exacta de CLAUDE.md (incluye detector_huecos.py y marco_linguistico.json)
2. Crear todos los `__init__.py` vacíos
3. Crear `requirements.txt` con dependencias exactas
4. Crear `Dockerfile` para Python 3.12 + FastAPI
5. Crear `fly.toml` para deploy en fly.io
6. Crear `src/config/settings.py` con todas las variables de entorno
7. Crear `src/utils/llm_client.py` con rotación de 4 API keys
8. Crear `src/main.py` con FastAPI skeleton (health + ejecutar endpoints)

---

## ARCHIVOS A CREAR

### requirements.txt

```
fastapi==0.115.6
uvicorn[standard]==0.34.0
asyncpg==0.30.0
anthropic==0.43.0
networkx==3.4.2
structlog==24.4.0
pydantic==2.10.4
python-dotenv==1.0.1
httpx==0.28.1
pytest==8.3.4
pytest-asyncio==0.24.0
```

### Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### fly.toml

```toml
app = "motor-semantico-omni"
primary_region = "mad"

[build]
  dockerfile = "Dockerfile"

[env]
  PORT = "8080"
  PYTHONUNBUFFERED = "1"

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = "suspend"
  auto_start_machines = true
  min_machines_running = 0
  processes = ["app"]

  [http_service.concurrency]
    type = "requests"
    hard_limit = 10
    soft_limit = 5

[[vm]]
  memory = "1gb"
  cpu_kind = "shared"
  cpus = 1
```

### src/config/settings.py

```python
"""Configuración central — lee de env vars."""
import os
from dotenv import load_dotenv

load_dotenv()

# Anthropic API keys (rotación)
ANTHROPIC_API_KEYS: list[str] = [
    k for k in [
        os.getenv("ANTHROPIC_API_KEY_1"),
        os.getenv("ANTHROPIC_API_KEY_2"),
        os.getenv("ANTHROPIC_API_KEY_3"),
        os.getenv("ANTHROPIC_API_KEY_4"),
    ] if k
]

# Database
DATABASE_URL: str = os.getenv("DATABASE_URL", "")

# Modelos LLM
MODEL_ROUTER: str = "claude-sonnet-4-20250514"
MODEL_EXTRACTOR: str = "claude-haiku-4-5-20251001"
MODEL_INTEGRATOR: str = "claude-sonnet-4-20250514"

# Límites
MAX_COST_USD: float = 1.50
MAX_TIME_S: int = 150
DEFAULT_INTELLIGENCES: int = 5
MIN_INTELLIGENCES: int = 3
MAX_INTELLIGENCES: int = 6

# Scoring
MIN_QUALITY_SCORE: float = 6.0
```

### src/utils/llm_client.py

```python
"""Cliente Anthropic con rotación de API keys y retry."""
import asyncio
import itertools
import structlog
from anthropic import AsyncAnthropic
from src.config.settings import ANTHROPIC_API_KEYS

log = structlog.get_logger()

class LLMClient:
    """Wrapper Anthropic con rotación de keys y backoff."""

    def __init__(self):
        if not ANTHROPIC_API_KEYS:
            raise ValueError("No ANTHROPIC_API_KEY_* configuradas")
        self._key_cycle = itertools.cycle(ANTHROPIC_API_KEYS)
        self._clients: dict[str, AsyncAnthropic] = {
            key: AsyncAnthropic(api_key=key) for key in ANTHROPIC_API_KEYS
        }
        self._total_cost: float = 0.0

    def _next_client(self) -> AsyncAnthropic:
        key = next(self._key_cycle)
        return self._clients[key]

    async def complete(
        self,
        model: str,
        system: str,
        user_message: str,
        max_tokens: int = 4096,
        temperature: float = 0.3,
        retries: int = 3,
    ) -> str:
        """Envía mensaje y devuelve texto. Rota key en cada retry."""
        last_error = None
        for attempt in range(retries):
            client = self._next_client()
            try:
                response = await client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system,
                    messages=[{"role": "user", "content": user_message}],
                )
                # Track cost (approximate)
                input_tokens = response.usage.input_tokens
                output_tokens = response.usage.output_tokens
                cost = self._estimate_cost(model, input_tokens, output_tokens)
                self._total_cost += cost
                log.info("llm_complete", model=model, input_tokens=input_tokens,
                         output_tokens=output_tokens, cost=cost, attempt=attempt)
                return response.content[0].text
            except Exception as e:
                last_error = e
                log.warning("llm_retry", model=model, attempt=attempt, error=str(e))
                await asyncio.sleep(2 ** attempt)
        raise last_error

    @staticmethod
    def _estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
        """Estimación de coste por modelo (USD)."""
        rates = {
            "claude-sonnet-4-20250514": (0.003, 0.015),
            "claude-haiku-4-5-20251001": (0.001, 0.005),
            "claude-opus-4-20250514": (0.015, 0.075),
        }
        input_rate, output_rate = rates.get(model, (0.003, 0.015))
        return (input_tokens * input_rate + output_tokens * output_rate) / 1000

    @property
    def total_cost(self) -> float:
        return self._total_cost

    def reset_cost(self):
        self._total_cost = 0.0


# Singleton
llm = LLMClient()
```

### src/main.py

```python
"""Motor Semántico OMNI-MIND — API endpoint."""
import structlog
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.dev.ConsoleRenderer(),
    ]
)

app = FastAPI(title="Motor Semántico OMNI-MIND", version="0.1.0")
log = structlog.get_logger()


class MotorConfig(BaseModel):
    presupuesto_max: float = 1.50
    tiempo_max_s: int = 120
    profundidad: str = Field(default="normal", pattern="^(normal|profunda|maxima)$")
    modo: str = Field(default="analisis", pattern="^(analisis|generacion|conversacion|confrontacion)$")
    inteligencias_forzadas: list[str] = []
    inteligencias_excluidas: list[str] = []


class MotorRequest(BaseModel):
    input: str
    contexto: Optional[str] = None
    config: MotorConfig = MotorConfig()


class MotorResponse(BaseModel):
    algoritmo_usado: dict
    resultado: dict
    meta: dict


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}


@app.post("/motor/ejecutar", response_model=MotorResponse)
async def ejecutar(request: MotorRequest):
    """Ejecuta el pipeline completo del motor semántico."""
    log.info("motor_ejecutar", input_preview=request.input[:100], modo=request.config.modo)
    try:
        # TODO: import orchestrator and run pipeline
        from src.pipeline.orchestrator import run_pipeline
        result = await run_pipeline(request)
        return result
    except Exception as e:
        log.error("motor_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
```

---

## VERIFICACIÓN

Después de crear todo:
1. `python -c "from src.main import app; print('OK')"` debe pasar
2. `python -c "from src.config.settings import ANTHROPIC_API_KEYS; print(len(ANTHROPIC_API_KEYS))"` debe imprimir el número de keys configuradas
3. La estructura de directorios debe coincidir exactamente con CLAUDE.md
