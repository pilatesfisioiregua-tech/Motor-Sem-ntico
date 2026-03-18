# BRIEFING_21 — Tool enforcement en ejecución + http_request fuera de execute

**Objetivo**: Hacer que el filtro de tools sea real (no solo cosmético) y eliminar http_request de execute mode.

**Diagnóstico**: El schema filtering de B13 solo controla qué tools VE el modelo en la lista de herramientas de la API. Pero `registry.execute()` acepta CUALQUIER tool independientemente del filtro. Mochila agrava el problema: su sección "herramientas" lista 63 tools con http_request prominente + ejemplos de URLs. El modelo lee mochila → ve http_request con ejemplos de endpoints → asocia "crear endpoint" con "hacer HTTP requests" → ignora filesystem tools.

**Evidencia**: B19C eliminó db_query del system prompt → 0 alucinaciones de db_query. Pero mochila reintroduce http_request (y otros) por la puerta de atrás. Y aunque el schema no incluya un tool, el registry lo ejecuta igual.

**Fix**: Dos cambios complementarios.

---

## Paso 1: Tool enforcement real en agent_loop.py

**Archivo**: `motor_v1_validation/agent/core/agent_loop.py`

Buscar este bloque en el loop de tool processing (dentro del `for tc in tool_calls:`):

**Antes**:
```python
            # Run pre_tool hooks
            if hooks:
                hooks.run("pre_tool", {"tool": tool_name, "args": tool_args})
```

**Insertar ANTES de ese bloque** (después de `tc_id = ...`):

```python
            # TOOL ENFORCEMENT — reject tools not in active set (B21)
            active_tool_names = {s["function"]["name"] for s in tool_schemas}
            if tool_name not in active_tool_names and tool_name != "finish":
                result_str = (
                    f"ERROR: '{tool_name}' no está disponible en modo {exec_mode}. "
                    f"Tools disponibles: {', '.join(sorted(active_tool_names))}. "
                    f"Usa SOLO estas herramientas."
                )
                history.append({"role": "tool", "tool_call_id": tc_id, "content": result_str})
                stuck.record_action(tool_name, tool_args, result_str, True)
                if verbose:
                    print(f" -> {tool_name} BLOCKED (not in {exec_mode} tools)")
                continue
```

**Criterio paso 1**: `grep -c "TOOL ENFORCEMENT" motor_v1_validation/agent/core/agent_loop.py` devuelve 1.

---

## Paso 2: Quitar http_request de execute MODE_TOOLS

**Archivo**: `motor_v1_validation/agent/core/agent_loop.py`

**Antes**:
```python
        "execute": CORE_TOOLS | {"http_request", "run_command"},
```

**Después**:
```python
        "execute": CORE_TOOLS | {"run_command"},
```

Nota: `run_command` se mantiene porque es útil para verificar compilación (`python3 -c "import api"`).

**Criterio paso 2**: `grep "execute.*CORE_TOOLS" motor_v1_validation/agent/core/agent_loop.py` NO contiene http_request.

---

## Paso 3: Desplegar y probar

```bash
fly deploy --app chief-os-omni
```

**Criterio health**: OK.

Ejecutar tests:
```bash
cd briefings && python3 test_validacion_modelos.py
```

**Observar en logs**:
- ¿El modelo intenta http_request? → Debe ver "ERROR: 'http_request' no está disponible en modo execute"
- ¿Después de ese error, cambia a filesystem tools (read_file, insert_at)?
- ¿Completa edit_file o insert_at en api.py?

**Criterio T3 PASS**: Al menos 1 `insert_at` o `edit_file` en api.py exitoso.
**Criterio no regresión**: T1, T4 siguen PASS. (T2 tiene variabilidad conocida.)

## Paso 4: Guardar resultado

Guardar en `results/B21_tool_enforcement.md` con:
- DIAG line (confirmar http_request NO en tools de execute)
- ¿Cuántas veces intentó http_request? (esperado: 0-2 antes de aprender)
- ¿Cuántas veces usó read_file, insert_at, edit_file?
- Secuencia completa de tools
- Tabla comparativa B20 vs B21
- PASS/FAIL por test

## Rollback

Si hay regresión en T1/T4:
- Revertir el bloque TOOL ENFORCEMENT (paso 1)
- Restaurar `"execute": CORE_TOOLS | {"http_request", "run_command"}`
- Redesplegar

Riesgo bajo: T1 usa mode=auto (→ quick/standard, NO execute), T4 usa mode=auto (→ analyze). Ninguno debería verse afectado por cambios en execute mode.

## Nota sobre mochila (NO arreglar ahora)

Mochila tiene contenido estático con 63 tools hardcodeados. El fix correcto a largo plazo es hacer mochila dinámica (como el system prompt post-B19C). Pero el enforcement de B21 hace eso innecesario para T3: aunque mochila mencione http_request, el enforcement lo bloquea. Mochila dinámica queda como tarea post-4/4.
