# BRIEFING_08: Fix @project/ Path Resolution

## Diagnóstico

Dos modelos diferentes (Qwen3-Coder y Devstral 2) fallan con el mismo patrón:
no encuentran archivos en `@project/core/`. Causa raíz identificada:

- `CODE_OS_PROJECT_DIR=/repo` en fly.toml y Dockerfile
- `/repo` = raíz del monorepo completo (omni-mind-cerebro/)
- `/app` = código del agente (motor_v1_validation/agent/) — donde están `core/`, `tools/`, `api.py`
- `@project/core/gestor.py` → resuelve a `/repo/core/gestor.py` → **NO EXISTE**
- El archivo real está en `/app/core/gestor.py`

## Fix

### Paso 1: Cambiar CODE_OS_PROJECT_DIR en fly.toml

Archivo: `motor_v1_validation/agent/fly.toml`

```
# ANTES:
CODE_OS_PROJECT_DIR = "/repo"

# DESPUÉS:
CODE_OS_PROJECT_DIR = "/app"
```

### Paso 2: Cambiar CODE_OS_PROJECT_DIR en Dockerfile

Archivo: `motor_v1_validation/agent/Dockerfile`

```
# ANTES:
ENV CODE_OS_PROJECT_DIR=/repo

# DESPUÉS:
ENV CODE_OS_PROJECT_DIR=/app
```

### Paso 3: Deploy

```bash
cd motor-semantico
fly deploy -a chief-os-omni
```

### Paso 4: Verificar que @project/ resuelve correctamente

Llamar al endpoint con un test mínimo:
```
POST /code-os/execute
{"input": "Lee @project/core/gestor.py y dime cuántas líneas tiene. Llama finish con el número."}
```

### Paso 5: Re-ejecutar test de validación completo

```bash
python3 briefings/test_validacion_modelos.py --output results/test_modelos_fix_paths_b08.md
```

CRITERIO: Al menos 3/4 tests deben pasar ahora que los paths resuelven correctamente.

## Notas

- NO tocar el Dockerfile más allá del ENV. La copia a `/repo` sigue siendo útil como referencia.
- Si 3/4+ pasan → bug era infraestructura, cerrar debate de modelos.
- Si 0-1/4 pasan → problema adicional en el agente (system prompt, 61 tools, etc.)
- El modelo anterior (Devstral 2) es el que queda como cerebro — no revertir a Qwen3-Coder.
