# BRIEFING_07: Cambio de Cerebro — Devstral 2 reemplaza Qwen3-Coder

## Contexto

Test de validación post-B06 con Qwen3-Coder como cerebro: **0/4 passed**.
- T1 (read+report): STUCK, monologue loop 3x, 13 iters, 7 errores
- T2 (análisis): 0/6 métodos encontrados, 7 iters
- T3 (execute, usa MiniMax worker): 0 edits en 17 tool calls
- T4 (diagnóstico): 6 HTTP calls, 0 keywords diagnóstico

Causa raíz: Qwen3-Coder no maneja el patrón agentic (61 tools + system prompt complejo).
MiniMax M2.5 como worker tampoco completa en execute mode.

Devstral 2 (`mistralai/devstral-2512`) fue validado previamente al 100% en tareas complejas.

## Cambios

### Paso 1: Actualizar config de modelos en api.py

Archivo: `@project/core/api.py`

En la función `get_tier_config()`, cambiar el bloque de fallback:

```python
# ANTES (Qwen3-Coder — 0/4 en test validación):
return {
    "cerebro":       "qwen/qwen3-coder",
    "worker":        "minimax/minimax-m2.5",
    "worker_budget": "deepseek/deepseek-v3.2",
    "evaluador":     "z-ai/glm-5",
    "swarm":         "deepseek/deepseek-v3.2",
    "orchestrator":  "qwen/qwen3-coder",
    "synthesis":     "z-ai/glm-5",
}

# DESPUÉS (Devstral 2 — validado 100% previamente):
return {
    "cerebro":       "mistralai/devstral-2512",          # 123B dense, agentic coding, validado 100%
    "worker":        "mistralai/devstral-2512",          # mismo modelo (unified) — evita split que falló
    "worker_budget": "deepseek/deepseek-v3.2",           # fallback barato
    "evaluador":     "z-ai/glm-5",                      # evaluación (#1 Arena) — sin cambio
    "swarm":         "deepseek/deepseek-v3.2",           # volumen — sin cambio
    "orchestrator":  "mistralai/devstral-2512",
    "synthesis":     "z-ai/glm-5",
}
```

**Decisión clave: cerebro = worker = Devstral 2 (unified).**
Razón: el split cerebro/worker falló porque MiniMax como worker no completa tareas.
Un modelo unificado que sabe hacer agentic coding cubre ambos roles.
Si queremos split después, lo hacemos con datos empíricos.

### Paso 2: Actualizar pricing en api.py

En `get_model_pricing`, añadir/actualizar:
```python
"mistralai/devstral-2512": 2.00,  # $0.40 input / $2.00 output
```

### Paso 3: Actualizar comentarios del router

Archivo: `@project/core/router.py`

Actualizar el docstring del módulo y del DualModelRouter para reflejar:
- CEREBRO: Devstral 2 (123B dense, agentic coding, $0.40/$2.00)
- WORKER: Devstral 2 (unified — mismo modelo)
- EVALUADOR: GLM-5 (sin cambio)

### Paso 4: Deploy

```bash
fly deploy -a chief-os-omni
```

### Paso 5: Re-ejecutar test de validación

```bash
python3 briefings/test_validacion_modelos.py --base-url https://chief-os-omni.fly.dev
```

CRITERIO: Al menos 2/4 tests deben pasar (T1 y T2 como mínimo).

## Notas

- Si Devstral 2 pasa 3/4 o 4/4 → stack validado, cerrar decisión
- Si Devstral 2 pasa 2/4 → stack parcial, evaluar Devstral Medium o MiniMax como worker
- Si Devstral 2 pasa 0-1/4 → problema sistémico en el system prompt o las 61 tools, no en el modelo
- Guardar resultados en `results/test_modelos_devstral2_b07.md`
