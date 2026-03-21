# BRIEFING_13 — Tool Surface Filter por Modo de Ejecución

## Contexto

Post-B12: 2/4 tests pasan (T1 read, T2 analysis). T3 (execute) y T4 (deep) fallan.

Patrón: el modelo lee y analiza correctamente pero no escribe código (T3: 0 llamadas a `edit_file` en 6 iteraciones) y no sintetiza diagnósticos profundos (T4: 1/6 keywords en 50 iteraciones).

Hipótesis: el modelo recibe 61 tool schemas via `registry.get_schemas()` sin filtrar. El system prompt lista 8 tools pero la API envía 61. Devstral 2 se pierde en el ruido.

Evidencia: B10 probó tool filtering pero con el bug de `project_dir` (B11) aún presente → resultado inválido. B10 redujo a 15 tools de forma estática. Este briefing hace filtering dinámico por modo de ejecución.

## Infraestructura existente

`ToolRegistry.get_schemas()` ya acepta `names: Optional[set]` como filtro. Solo hay que usarlo.

`detect_mode(goal)` ya clasifica en "quick", "standard", "deep".

## Qué hacer

### Paso 1 — Definir tool sets por modo

Archivo: `motor_v1_validation/agent/core/agent_loop.py`

**ANTES** (línea ~aprox donde está `tool_schemas = registry.get_schemas()`):
```python
    # Get tool schemas
    tool_schemas = registry.get_schemas()
```

**DESPUÉS**:
```python
    # Get tool schemas — filtered by execution mode
    CORE_TOOLS = {
        "read_file", "edit_file", "write_file", "list_dir",
        "run_command", "finish", "mochila",
    }
    MODE_TOOLS = {
        "quick": CORE_TOOLS,
        "standard": CORE_TOOLS | {"http_request", "db_query", "search_files"},
        "deep": CORE_TOOLS | {"http_request", "db_query", "search_files",
                               "remember_search", "plan"},
    }
    active_tools = MODE_TOOLS.get(exec_mode, CORE_TOOLS | {"http_request", "db_query"})
    tool_schemas = registry.get_schemas(names=active_tools)

    # Fallback: si el filtro dejó <3 tools, usar todo (safety net)
    if len(tool_schemas) < 3:
        tool_schemas = registry.get_schemas()
```

### Paso 2 — Verificar que edit_file existe en el registry

Antes de ejecutar los tests, verificar:
```bash
curl -s https://chief-os-omni.fly.dev/health | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Tools: {d.get(\"tools\",\"?\")}')"
curl -s https://chief-os-omni.fly.dev/version | python3 -m json.tool
```

Y también verificar que `edit_file` está registrado consultando el endpoint de tools si existe, o leyendo `create_default_registry()`.

### Paso 3 — Deploy y test

```bash
# Deploy
cd /Users/jesusfernandezdominguez/omni-mind-cerebro
fly deploy --config motor-semantico/motor_v1_validation/agent/fly.toml \
           --dockerfile motor-semantico/motor_v1_validation/agent/Dockerfile

# Test solo T3 y T4 (T1/T2 ya pasan — verificar que no regresen)
python3 motor-semantico/briefings/test_validacion_modelos.py \
    --output motor-semantico/results/test_modelos_tool_filter_b13.md
```

## Criterio de éxito

| Test | Baseline B12 | Target B13 |
|------|-------------|------------|
| T1 | ✅ PASS | ✅ PASS (no regresión) |
| T2 | ✅ PASS | ✅ PASS (no regresión) |
| T3 | ❌ 0 edit_file | ✅ ≥1 edit_file en api.py |
| T4 | ❌ 1/6 keywords | ✅ ≥2/6 keywords diagnóstico |

**3/4+ → Code OS operativo básico. Documentar tool filtering como Principio 33.**
**2/4 sin cambio → El problema no es tool count sino capacidad de Devstral 2 para tareas de escritura/síntesis. Siguiente: cerebro dual.**

## Notas

- El safety net (`if len(tool_schemas) < 3`) previene la regresión tipo B10.
- `mochila` se incluye en CORE porque el modelo la usa en T1 exitosamente.
- No tocar el system prompt — B12 ya lo optimizó.
- Si T4 sigue fallando con tools filtradas, el problema es síntesis, no tool overload. Eso apuntaría a cerebro dual (Cogito-671b para T4).
- Si T3 pasa pero T4 no → confirma que el techo es razonamiento multi-paso, no tool selection.
