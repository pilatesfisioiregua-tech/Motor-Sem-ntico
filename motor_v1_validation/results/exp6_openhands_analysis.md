# EXP 6 — Fase 1: Análisis de OpenHands

Fecha: 2026-03-11
Fuente: github.com/All-Hands-AI/OpenHands (commit más reciente)

## 1. Loop principal: observe→think→act

**Archivo:** `openhands/controller/agent_controller.py` (líneas 863-1039)

OpenHands usa un loop event-driven:
- **observe**: `_on_event()` procesa eventos del EventStream (Actions y Observations)
- **think**: `agent.step(state)` llama al LLM para generar la siguiente acción
- **act**: La acción se añade al EventStream, triggering observers

**Max iteraciones: 500** (configurable via `OpenHandsConfig.max_iterations`)

**Condiciones de parada:**
```python
# Control flags check
self.state_tracker.run_control_flags()  # Throws si límites alcanzados

# Stuck detection
if self.agent.config.enable_stuck_detection and self._is_stuck():
    raise AgentStuckInLoopError('Agent got stuck in a loop')

# Budget check
if self.current_value >= self.max_value:
    raise RuntimeError('Agent reached maximum budget.')
```

**Patrón clave:** El agente NO ejecuta directamente — emite Actions al EventStream, y el Runtime las ejecuta y devuelve Observations.

## 2. Sandbox: Docker isolation

**Archivo:** `openhands/runtime/impl/docker/docker_runtime.py`

- Cada agente corre en un **contenedor Docker** aislado
- Runtime: servidor HTTP dentro del contenedor (puertos 30000-39999)
- Volúmenes configurados via Docker API (`Mount` types)
- Contenedor creado al inicio, destruido al final
- Fallback: CLI runtime para ejecución local/test sin Docker

```python
self.docker_client = self._init_docker_client()
self.container = None  # Se crea/destruye automáticamente
```

## 3. Timeouts

**Archivos:** `action_execution_client.py:283-349`, `sandbox_config.py:68`

- **Per-command timeout: 120s** (default, configurable por acción)
- Buffer de 5s extra para captura de errores client-side
- Si timeout → `AgentRuntimeTimeoutError` → se convierte en `ErrorObservation` visible al agente
- Blocking commands sin timeout → RuntimeError inmediato

```python
if action.timeout is None:
    if isinstance(action, CmdRunAction) and action.blocking:
        raise RuntimeError('Blocking command with no timeout set')
    action.set_hard_timeout(self.config.sandbox.timeout, blocking=False)
```

## 4. Loops infinitos: 5 escenarios de detección

**Archivo:** `openhands/controller/stuck.py`

| Escenario | Condición | Umbral |
|-----------|-----------|--------|
| Acción+Observación repetida | Mismo par exacto | 4x consecutivas |
| Acción+Error repetido | Mismo error | 3x consecutivas |
| Monólogo | Habla sin acciones | Detectado |
| Patrón cíclico largo | Ciclo en historial | 6+ pasos |
| Context window error | Repetido ContextWindowExceeded | 10+ pasos |

**Respuesta:** `AgentStuckInLoopError` → estado ERROR, ejecución parada.

## 5. Comandos peligrosos: modelo de riesgo (NO blacklist)

**Archivos:** `security/invariant/analyzer.py`, `tools/security_utils.py`

OpenHands **NO usa blacklist**. Usa un modelo basado en riesgo:
- Risk levels: LOW, MEDIUM, HIGH
- HIGH o UNKNOWN → requiere confirmación del usuario
- Sin analyzer configurado → TODO es UNKNOWN → pide confirmación
- Seguridad delegada a: contenedor Docker + confirmación + auto-evaluación del LLM

**Insight para nuestro agente:** Sin Docker necesitamos blacklist explícita.

## 6. Gestión de contexto: Condenser plugin

**Archivos:** `controller/state/state_tracker.py`, `codeact_agent.py:200-216`

- **Sliding window** via plugin Condenser (configurable por agente)
- Cuando contexto excede ventana → `CondensationRequestAction`
- Sumariza eventos antiguos, preserva historial reciente
- No hay truncamiento automático a nivel framework — depende del Condenser

```python
match self.condenser.condensed_history(state):
    case View(events=events, forgotten_event_ids=forgotten_ids):
        condensed_history = events
    case Condensation(action=condensation_action):
        return condensation_action
```

## 7. Tool calling: function calling JSON

**Archivos:** `codeact_agent.py:116-157`, `function_calling.py:80-200+`

**9 herramientas:**
1. Bash (run shell commands)
2. IPython (run Python code)
3. File editor (str_replace_editor)
4. Browser (browse URLs)
5. Think (internal reasoning)
6. Finish (mark task complete)
7. Task tracker (manage tasks)
8. Condensation request (memory cleanup)
9. MCP tools (dynamic integrations)

**Formato: JSON function calling** (OpenAI-compatible via LiteLLM):
```json
{
  "tool_calls": [{
    "function": {
      "name": "bash",
      "arguments": "{\"command\": \"ls -la\", \"timeout\": 30}"
    },
    "id": "call_abc123"
  }]
}
```

## 8. Recuperación de errores

**Archivos:** `agent_controller.py:323-411, 916-976`, `retry_mixin.py`

**Patrón:** Error → ErrorObservation → el agente VE el error en su historial → decide siguiente acción.

**Errores capturados:**
- LLM: `LLMMalformedActionError`, `LLMNoActionError`, `LLMResponseError`
- Function: `FunctionCallValidationError`, `FunctionCallNotExistsError`
- Contexto: `ContextWindowExceededError` → trigger condensation
- API: `AuthenticationError`, `RateLimitError`, `ServiceUnavailableError`

**Retry:** Exponential backoff via Tenacity (`wait_exponential(multiplier=1, min=4, max=15)`)
- 3-5 intentos por defecto

## 9. Multi-modelo: LLMRegistry + LiteLLM

**Archivos:** `llm/llm_registry.py`, `llm/llm.py:64-115`, `llm/router/`

- **LLMRegistry** como factory de instancias LLM
- **LiteLLM** abstrae todos los providers (OpenAI, Claude, Gemini, Groq, local)
- **Router** opcional para dirigir diferentes prompts a diferentes modelos
- Cada LLM tiene `service_id` para tracking/métricas
- API key rotation y normalización de timeouts

## 10. Métricas

**Archivo:** `openhands/llm/metrics.py`

| Métrica | Tipo | Descripción |
|---------|------|-------------|
| `accumulated_cost` | float (USD) | Coste total acumulado |
| `prompt_tokens` | int | Tokens de entrada por llamada |
| `completion_tokens` | int | Tokens de salida por llamada |
| `cache_read/write_tokens` | int | Tokens de caché (Anthropic) |
| `response_latencies` | list[float] | Latencia por llamada |
| `max_budget_per_task` | float | Límite duro — para agente si excede |

**Budget enforcement:** Si coste acumulado > max_budget → RuntimeError.

## Patrones Clave para Nuestro Agente

1. **Event-driven > imperativo**: Separar acciones de observaciones permite retry limpio
2. **Error como input**: El error completo va al agente como Observation, no como excepción
3. **Stuck detection multi-escenario**: No basta con 1 check — necesitas 3-5 patrones
4. **Sin blacklist, con risk model**: Pero solo funciona con Docker. Sin Docker → blacklist
5. **Condenser > truncate**: Sumarizar es mejor que cortar, pero requiere LLM call extra
6. **Budget enforcement**: Imprescindible — los loops agenticos pueden costar mucho
7. **Function calling JSON**: Más robusto que parsing de texto libre
8. **5 herramientas son suficientes**: bash + file editor + finish cubren el 95% de los casos
