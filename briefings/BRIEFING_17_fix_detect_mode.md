# BRIEFING_17 — Fix detect_mode: T3 se clasifica como analyze en vez de execute

## Root Cause

`detect_mode()` en `router.py` tiene dos bugs:

1. **Prioridad invertida**: ANALYZE_KEYWORDS se evalúa ANTES que EXECUTE_KEYWORDS. El prompt de T3 contiene "verifica" (analyze) Y "añade" (execute). Como analyze va primero, T3 se clasifica como "analyze" — usa V3.2 sin execute hint.

2. **Keyword incompleto**: EXECUTE_KEYWORDS tiene "añadir" (infinitivo) pero no "añade" (conjugado). `"añadir" in "añade"` → False. Incluso si se arreglara la prioridad, "añade" no matchea.

**Impacto**: B14, B15 y B16 NUNCA probaron Devstral 2 + execute hint para T3. Las tres veces fue V3.2 en modo analyze.

## Qué hacer

### Paso 1 — Fix detect_mode en router.py

Archivo: `motor_v1_validation/agent/core/router.py`

**ANTES:**
```python
EXECUTE_KEYWORDS = [
    "crear", "modificar", "implementar", "fix", "deploy", "añadir",
    "create", "modify", "implement", "build", "write",
]
```

**DESPUÉS:**
```python
EXECUTE_KEYWORDS = [
    "crear", "crea", "modificar", "modifica", "implementar", "implementa",
    "fix", "deploy", "añadir", "añade", "agrega",
    "create", "modify", "implement", "build", "write", "add",
]
```

**ANTES (en detect_mode):**
```python
    if any(kw in goal_lower for kw in ANALYZE_KEYWORDS):
        return "analyze"
    if any(kw in goal_lower for kw in EXECUTE_KEYWORDS):
        return "execute"
```

**DESPUÉS:**
```python
    # Execute tiene prioridad sobre analyze — la acción principal importa más que la verificación
    if any(kw in goal_lower for kw in EXECUTE_KEYWORDS):
        return "execute"
    if any(kw in goal_lower for kw in ANALYZE_KEYWORDS):
        return "analyze"
```

### Paso 2 — Añadir execute/analyze al MODE_TOOLS dict

Actualmente `MODE_TOOLS` no tiene "execute" ni "analyze" → caen al default. Hacerlo explícito:

**ANTES (en agent_loop.py):**
```python
    MODE_TOOLS = {
        "quick": CORE_TOOLS,
        "standard": CORE_TOOLS | {"http_request", "db_query", "search_files"},
        "deep": CORE_TOOLS | {"http_request", "db_query", "search_files",
                               "remember_search", "plan"},
    }
```

**DESPUÉS:**
```python
    MODE_TOOLS = {
        "quick": CORE_TOOLS,
        "execute": CORE_TOOLS | {"http_request", "run_command"},
        "analyze": CORE_TOOLS | {"http_request", "db_query", "search_files"},
        "standard": CORE_TOOLS | {"http_request", "db_query", "search_files"},
        "deep": CORE_TOOLS | {"http_request", "db_query", "search_files",
                               "remember_search", "plan"},
    }
```

### Paso 3 — Logging de modo en test_validacion_modelos.py

Añadir print del modo detectado para verificar que T3 ahora es "execute". En cada test, después de construir el input, hacer:

Al inicio del test script (después de health check), añadir una función de diagnóstico:

```python
def check_mode_detection():
    """Verificar qué modo se asigna a cada test."""
    goals = {
        "T1": "En el archivo @project/core/gestor.py, busca la función get_gestor()...",
        "T3": "Añade un endpoint GET /test/ping en @project/api.py...",
        "T4": "Diagnostica por qué GET /gestor/consistencia reporta consistente=false...",
    }
    for name, goal in goals.items():
        # Call /code-os/detect-mode if it exists, otherwise infer from keywords
        print(f"  {name}: goal starts with '{goal[:40]}...'")
```

(Opcional — lo importante es el fix de detect_mode.)

### Paso 4 — Deploy y test

```bash
cd /Users/jesusfernandezdominguez/omni-mind-cerebro
fly deploy --config motor-semantico/motor_v1_validation/agent/fly.toml \
           --dockerfile motor-semantico/motor_v1_validation/agent/Dockerfile

python3 motor-semantico/briefings/test_validacion_modelos.py \
    --output motor-semantico/results/test_modelos_fix_detect_mode_b17.md
```

## Criterio de éxito

| Test | B16 (bug) | Target B17 |
|------|-----------|------------|
| T1 | ✅ CACHE | ✅ (no regresión) |
| T2 | ✅ CACHE | ✅ (no regresión) |
| T3 | ❌ 0 edit_file (V3.2 en analyze!) | ✅ ≥1 edit_file (Devstral 2 en execute + hint) |
| T4 | ✅ 5/6 kw (V3.2 en analyze) | ✅ (no regresión) |

**4/4 → Code OS operativo. Stack final confirmado.**
**T3 sigue ❌ → Devstral 2 con execute hint de verdad no escribe. Probar Cogito-671b.**

## Notas

- Este bug explica por qué T3 tenía resultados IDÉNTICOS en B14-B16: siempre fue V3.2 en analyze.
- La prioridad execute > analyze es correcta semánticamente: si una tarea dice "crea X y verifica", la acción principal es crear.
- Los keywords conjugados (añade, crea, modifica, implementa, agrega) son necesarios porque `detect_mode` usa `in` substring matching, no stemming.
- Si 4/4 pasa, documentar como lección: siempre verificar que la clasificación de modo es correcta antes de evaluar modelos.
