# BRIEFING_10: Reducir Tool Schemas por Modo (61 → ~15)

## Diagnóstico

Con 61 tool schemas, cada llamada a OpenRouter envía ~8000 tokens solo en definiciones
de herramientas. El modelo se confunde entre 61 opciones:

- T3 (execute): 6 iters, 17 tool calls, 0 edit_file — no encuentra edit_file entre 61
- T2 (analyze): lee el archivo pero no sintetiza — gasta presupuesto cognitivo en tools
- T4 (deep): 12 HTTP calls, 0 keywords — ejecuta pero no sintetiza

## Solución: Filtrar tools por exec_mode

`detect_mode()` ya clasifica cada tarea en quick/analyze/execute/standard/deep.
Usar esa clasificación para pasar SOLO los tools relevantes.

### Paso 1: Crear mapping de tools por modo

Archivo: `@project/core/agent_loop.py`

Añadir DESPUÉS de los imports y ANTES de CODE_OS_SYSTEM:

```python
# Tools by mode — reduce 61 to ~10-15 per task
CORE_TOOLS = {
    "read_file", "write_file", "edit_file", "list_dir",
    "grep_content", "glob_files",
    "run_command",
    "finish", "mochila",
}

TOOLS_BY_MODE = {
    "quick": CORE_TOOLS,
    "analyze": CORE_TOOLS | {"db_query", "http_request", "remember", "analyze_codebase"},
    "execute": CORE_TOOLS | {"db_query", "db_insert", "git_status", "git_add", "git_commit", "run_tests"},
    "standard": CORE_TOOLS | {"db_query", "db_insert", "http_request", "remember",
                               "git_status", "git_add", "git_commit", "run_tests",
                               "web_search", "web_fetch"},
    "deep": None,  # None = all tools (61)
}
```

### Paso 2: Filtrar schemas en run_agent_loop

Archivo: `@project/core/agent_loop.py`

Buscar la línea:
```python
    tool_schemas = registry.get_schemas()
```

Reemplazarla con:
```python
    # Filter tools by mode — 61 tools overwhelms the model
    allowed_tools = TOOLS_BY_MODE.get(exec_mode)
    if allowed_tools is not None:
        tool_schemas = registry.get_schemas(names=allowed_tools)
    else:
        tool_schemas = registry.get_schemas()
```

### Paso 3: Verificar que el modelo recibe menos tools

El log debería mostrar ~10 tools en quick, ~14 en analyze, ~15 en execute.
Verificar con el endpoint /health o inyectando un log print.

### Paso 4: Deploy

```bash
fly deploy -a chief-os-omni
```

### Paso 5: Re-ejecutar test de validación

```bash
python3 briefings/test_validacion_modelos.py --output results/test_modelos_reduced_tools_b10.md
```

CRITERIO: Al menos 2/4 tests pasan (T1 ya pasaba; T3 debería pasar con edit_file visible entre ~15 tools en vez de 61).

## Por qué esto funciona

- **T3 (execute)**: El modelo ve 15 tools en vez de 61. `edit_file` es 1 de 15, no 1 de 61. Probabilidad de selección sube 4x.
- **T2 (analyze)**: Menos tokens en tool schemas = más tokens disponibles para análisis. El modelo tiene más "espacio mental" para sintetizar.
- **T4 (deep)**: Mantiene 61 tools — las necesita para diagnóstico completo. Pero si T4 sigue fallando por síntesis, el siguiente paso sería mejorar el streaming SSE.

## Notas

- Si 3/4+ pasan → stack operativo, cerrar iteración de debugging
- Si T1+T3 pasan pero T2+T4 fallan → problema es síntesis/output, no tool selection
- Si 0-1/4 → investigar si el streaming SSE pierde el texto del modelo (text events vacíos)
- deep mode mantiene todos los tools porque tareas complejas pueden necesitar cualquiera
