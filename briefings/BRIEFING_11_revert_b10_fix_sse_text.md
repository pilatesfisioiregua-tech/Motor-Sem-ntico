# BRIEFING_11: Revert B10 + Fix SSE Text Streaming

## Diagnóstico

Dos problemas diferentes causan los 3 tests fallidos:

**Problema 1 (T2 + T4): Texto del modelo perdido en SSE**
El endpoint `/code-os/execute` emite tool_call/tool_result pero NUNCA emite el
texto de respuesta del modelo. El agent_loop acumula el texto en `history[]` pero
el SSE endpoint no lo extrae. El test busca method names (T2) y diagnostic keywords (T4)
en text events que nunca se emiten.

**Problema 2 (T3): Modelo no llama edit_file**
El modelo lee api.py pero no transiciona a editar. Esto es parcialmente un issue de
capacidad/prompt — el modelo interpreta "añade endpoint" como "lee y reporta" en vez de
"edita el archivo".

**Problema 3 (B10 regresión): Tool filtering rompió T1**
B10 causó regresión en T1. Revertir a B09 como baseline estable.

## Paso 1: Revert B10 — eliminar tool filtering

Archivo: `@project/core/agent_loop.py`

Buscar y ELIMINAR este bloque (añadido por B10):

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

Y revertir la línea de tool_schemas a:
```python
    tool_schemas = registry.get_schemas()
```

(Eliminar el bloque if/else de `TOOLS_BY_MODE.get(exec_mode)`)

## Paso 2: Capturar texto del modelo en agent_loop

Archivo: `@project/core/agent_loop.py`

2a. Añadir lista `text_outputs` al inicio del loop (después de `log = []`):

```python
    log = []
    text_outputs = []  # Collect model's text responses for SSE streaming
```

2b. En la sección donde se procesa content (después de extract_response), añadir:
Buscar la línea `content, tool_calls, is_blowup = extract_response(api_resp)` y
DESPUÉS de ella, añadir:

```python
        # Capture model text for SSE streaming
        if content and content.strip() and not is_blowup:
            text_outputs.append(content.strip())
```

2c. Incluir text_outputs en el return dict. Buscar el return final del loop y añadir
`"text_outputs"` al dict:

```python
    return {
        ...
        "log": log,
        "text_outputs": text_outputs,  # ADD THIS LINE
    }
```

## Paso 3: Emitir texto como SSE events

Archivo: `@project/api.py`

En la función `run_in_thread`, buscar el bloque que pushea tool calls del log
(~línea 248) y DESPUÉS de él, ANTES de `evt_queue.put({"__done__": ...})`, añadir:

```python
                    # Push model's text outputs as SSE text events
                    for text in result.get("text_outputs", []):
                        if text and len(text) > 10:  # Skip trivial outputs
                            evt_queue.put({"type": "text", "content": text[:2000]})
```

## Paso 4: Incluir texto en done summary

Archivo: `@project/api.py`

En la sección donde se genera el `summary` para el done event (~línea 281),
modificar el try/except para incluir texto del modelo:

```python
                try:
                    reporter = Reporter()
                    summary = reporter.summarize_session(final_result) if isinstance(final_result, dict) and "stop_reason" in final_result else str(final_result)
                    # Append model's last text output for richer summary
                    if isinstance(final_result, dict):
                        texts = final_result.get("text_outputs", [])
                        if texts:
                            last_text = texts[-1][:500]
                            summary += " | " + last_text
                except Exception:
                    ...
```

## Paso 5: Deploy + Test

```bash
fly deploy -a chief-os-omni
python3 briefings/test_validacion_modelos.py --output results/test_modelos_fix_sse_b11.md
```

CRITERIO: Al menos 3/4 tests pasan:
- T1: debería pasar (ya pasaba en B09)
- T2: debería pasar (texto con method names ahora llega al SSE)
- T3: posiblemente falle (problema de capacidad del modelo, no de streaming)
- T4: debería pasar (texto diagnóstico ahora llega al SSE)

## Notas

- Si T1+T2+T4 pasan (3/4) → Code OS operativo para lectura y diagnóstico
- T3 (execute/edit) requiere que el modelo decida llamar edit_file.
  Si sigue fallando, investigar:
  a) El modelo no sabe que DEBE editar (prompt issue)
  b) edit_file requiere old_string exacto y el modelo no lo tiene
  c) El archivo api.py es demasiado grande para leer + editar en el budget
- NO re-intentar B10 (tool filtering). La idea es correcta pero la implementación
  introduce complejidad sin beneficio probado. Revisitar solo si 61 tools sigue
  siendo un problema documentado con datos.
