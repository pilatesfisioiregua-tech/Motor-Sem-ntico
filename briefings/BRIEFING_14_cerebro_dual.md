# BRIEFING_14 — Cerebro Dual: V3.2 para Execute/Analyze

## Contexto

B13 confirmó: tool overload no es el problema. Devstral 2 lee y analiza (T1/T2 ✅) pero no escribe código ni sintetiza diagnósticos (T3/T4 ❌). Es su techo como agente.

El router (`DualModelRouter`) YA distingue 5 modos: quick, execute, analyze, standard, deep. El modo se detecta automáticamente:
- T3 ("Añade un endpoint...") → `execute` (contiene "Añade")
- T4 ("Diagnostica por qué...") → `analyze` (contiene "Diagnostica")

Pero **todos los modos usan el mismo modelo** (Devstral 2). La infraestructura de routing está lista — solo falta asignar modelos distintos por modo.

## Hipótesis

Deepseek V3.2 (`deepseek/deepseek-v3.2`, $0.14/$0.38) es un modelo general fuerte con soporte de function calling via OpenRouter. Ya está en el stack como `worker_budget`. A $0.38/M output es 5x más barato que Devstral 2. Si V3.2 puede llamar `edit_file` (T3) y sintetizar diagnósticos (T4), el cerebro dual funciona.

## Qué hacer

### Paso 1 — Añadir config para execute/analyze

Archivo: `motor_v1_validation/agent/core/api.py`

En `get_tier_config()`, añadir dos keys al dict de fallback:

**ANTES:**
```python
    return {
        "cerebro":       "mistralai/devstral-2512",
        "worker":        "mistralai/devstral-2512",
        "worker_budget": "deepseek/deepseek-v3.2",
        ...
    }
```

**DESPUÉS:**
```python
    return {
        "cerebro":       "mistralai/devstral-2512",
        "worker":        "mistralai/devstral-2512",
        "worker_budget": "deepseek/deepseek-v3.2",
        "cerebro_execute": "deepseek/deepseek-v3.2",     # NUEVO: para tareas de escritura
        "cerebro_analyze": "deepseek/deepseek-v3.2",     # NUEVO: para síntesis profunda
        ...
    }
```

### Paso 2 — Router usa modelos por modo

Archivo: `motor_v1_validation/agent/core/router.py`

En `DualModelRouter.__post_init__()`, añadir:

**ANTES:**
```python
    def __post_init__(self):
        super().__post_init__()
        tc = get_tier_config()
        self._cerebro_model = tc.get("cerebro", ...)
        self._worker_model = tc.get("worker", ...)
        self._worker_budget = tc.get("worker_budget", ...)
        self._evaluador_model = tc.get("evaluador", ...)
```

**DESPUÉS** (añadir 2 líneas):
```python
    def __post_init__(self):
        super().__post_init__()
        tc = get_tier_config()
        self._cerebro_model = tc.get("cerebro", ...)
        self._worker_model = tc.get("worker", ...)
        self._worker_budget = tc.get("worker_budget", ...)
        self._evaluador_model = tc.get("evaluador", ...)
        self._cerebro_execute = tc.get("cerebro_execute", self._cerebro_model)   # NUEVO
        self._cerebro_analyze = tc.get("cerebro_analyze", self._cerebro_model)   # NUEVO
```

En `DualModelRouter.select()`, cambiar execute y analyze:

**ANTES:**
```python
        # Execute mode: prefer worker (coding)
        if self._mode == "execute":
            model = self._worker_model
            if model in self._blowup_models:
                model = self._worker_budget
            self._worker_iters += 1
            return model

        # Analyze mode: prefer cerebro (reasoning)
        if self._mode == "analyze":
            model = self._cerebro_model
            if model in self._blowup_models:
                model = self._worker_budget
            self._cerebro_iters += 1
            return model
```

**DESPUÉS:**
```python
        # Execute mode: modelo capaz de escribir código via tools
        if self._mode == "execute":
            model = self._cerebro_execute
            if model in self._blowup_models:
                model = self._worker_budget
            self._worker_iters += 1
            return model

        # Analyze mode: modelo capaz de sintetizar diagnósticos
        if self._mode == "analyze":
            model = self._cerebro_analyze
            if model in self._blowup_models:
                model = self._worker_budget
            self._cerebro_iters += 1
            return model
```

### Paso 3 — Mejorar logging en test para T3

Archivo: `briefings/test_validacion_modelos.py`

En `test_3_execute()`, cambiar la generación de notas para ver QUÉ tools llama:

**ANTES:**
```python
    notes = f"Edit calls: {len(edit_calls)} | Total tools: {len(tool_calls)}"
```

**DESPUÉS:**
```python
    all_tools = [e.get("tool") for e in tool_calls]
    notes = f"Edit calls: {len(edit_calls)} | Total tools: {len(tool_calls)} | Tools: {all_tools[:10]}"
```

Hacer lo mismo en `test_4_deep()`:

**ANTES:**
```python
    notes = f"HTTP calls: {len(http_calls)} | Keywords diagnóstico: {found_keywords}/6"
```

**DESPUÉS:**
```python
    all_tools = [e.get("tool") for e in tool_calls]
    notes = f"HTTP calls: {len(http_calls)} | Keywords diagnóstico: {found_keywords}/6 | Tools: {all_tools[:15]}"
```

### Paso 4 — Deploy y test

```bash
cd /Users/jesusfernandezdominguez/omni-mind-cerebro
fly deploy --config motor-semantico/motor_v1_validation/agent/fly.toml \
           --dockerfile motor-semantico/motor_v1_validation/agent/Dockerfile

python3 motor-semantico/briefings/test_validacion_modelos.py \
    --output motor-semantico/results/test_modelos_cerebro_dual_b14.md
```

## Criterio de éxito

| Test | B12/B13 | Target B14 |
|------|---------|------------|
| T1 | ✅ PASS (cache) | ✅ PASS (no regresión) |
| T2 | ✅ PASS (cache) | ✅ PASS (no regresión) |
| T3 | ❌ 0 edit_file | ✅ ≥1 edit_file en api.py |
| T4 | ❌ 1/6 keywords | ✅ ≥2/6 keywords diagnóstico |

**Árbol de decisión:**
- **3/4+** → Code OS operativo. V3.2 como cerebro execute+analyze. Documentar cerebro dual como Principio 33.
- **T3 ✅, T4 ❌** → V3.2 escribe pero no sintetiza. Cambiar `cerebro_analyze` a `deepcogito/cogito-v2.1-671b` ($5/M, mejor sintetizador validado en Exp 7-9).
- **T3 ❌, T4 ✅** → V3.2 sintetiza pero no escribe via tools. Investigar si V3.2 soporta function calling en OpenRouter (puede que solo genere JSON sin usar el schema).
- **0 cambio** → V3.2 tiene el mismo techo que Devstral 2 para agentic tasks. Escalar a Cogito-671b para ambos o replantear la arquitectura del agent loop (el problema es el loop, no el modelo).

## Notas

- V3.2 a $0.38/M es MÁS BARATO que Devstral 2 a $2.00/M. Si funciona igual o mejor, reduce costes 5x para execute+analyze.
- El cache tier 0 protege T1/T2 de regresión — se resuelven sin tocar el modelo.
- Si T1/T2 regresionan (cache miss por diferente prompt hash), significa que el cache depende del goal text exacto — documentar.
- El logging mejorado de T3/T4 nos da diagnóstico independientemente del resultado.
