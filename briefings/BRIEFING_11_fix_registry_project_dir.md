# BRIEFING_11: Fix project_dir Not Passed to Registry + Revert B10

## Diagnóstico

**Root cause encontrada:** `run_agent_loop` recibe `project_dir` pero nunca lo
pasa a `create_default_registry`. Línea 149:

```python
# ANTES (BUG — project_dir no se pasa):
registry = create_default_registry(sandbox_dir)

# DESPUÉS (FIX — project_dir se pasa):
registry = create_default_registry(sandbox_dir, project_dir)
```

Esto significa que `_PROJECT_DIR=""` en filesystem.py y TODA resolución de
`@project/` falla con "No project directory configured".

T1 "pasó" en B09 por falso positivo — el agent se stuck en 3 iters y el test
lo contó como pass porque: done_event + ≤8 tools. No verificó output real.

## Cambios

### Paso 1: Fix project_dir en agent_loop.py

Archivo: `@project/core/agent_loop.py`

Buscar:
```python
    if registry is None:
        registry = create_default_registry(sandbox_dir)
```

Reemplazar con:
```python
    if registry is None:
        registry = create_default_registry(sandbox_dir, project_dir)
```

### Paso 2: Revertir tool filtering de B10

El tool filtering causó regresión sin beneficio. Eliminar:

```python
# ELIMINAR estas líneas (~37-54):
# Tools by mode — reduce 61 to ~10-15 per task
CORE_TOOLS = { ... }
TOOLS_BY_MODE = { ... }
```

Y revertir la sección de tool_schemas a:
```python
    # Get tool schemas
    tool_schemas = registry.get_schemas()
```

(Eliminar el bloque if/else de TOOLS_BY_MODE)

### Paso 3: Deploy

```bash
fly deploy -a chief-os-omni
```

### Paso 4: Verificar path resolution manualmente

```
POST /code-os/execute
{"input": "Lee @project/core/gestor.py y dime cuántas líneas tiene. Llama finish con el número."}
```

Si el modelo responde con un número de líneas → @project/ funciona.

### Paso 5: Re-ejecutar test completo

```bash
python3 briefings/test_validacion_modelos.py --output results/test_modelos_fix_registry_b11.md
```

CRITERIO: T1 debe pasar REALMENTE (el summary debe mencionar "get_gestor" o "línea").
Al menos 2/4 tests deben pasar con output verificable.

## Impacto esperado

Este fix desbloquea TODOS los tests. Sin `project_dir`, el modelo no puede:
- T1: leer archivos del proyecto
- T2: leer motor_vn.py para listar métodos
- T3: leer api.py para encontrar dónde añadir el endpoint, ni edit_file
- T4: leer código fuente para diagnóstico (HTTP calls sí funcionan porque no usan @project/)

Con el fix, los 4 tests tienen posibilidad real de pasar.

## Notas

- Si 3/4+ pasan → stack operativo (Devstral 2 + system prompt B09 + project_dir fix)
- Si 1-2/4 → mejorar test criteria (verificar output real, no solo done_event)
- Si 0/4 → problema en el modelo o en cómo el SSE streaming pierde texto
