# BRIEFING_19C — System prompt dinámico: HERRAMIENTAS = tools filtrados

**Objetivo**: Eliminar la contradicción entre el system prompt (lista ALL tools) y el tool schema filtrado (solo mode-specific tools). Verificar si T3 pasa.

**Root cause descubierto**: `CODE_OS_SYSTEM` lista db_query, http_request, etc. en texto fijo. El tool filtering (B13) filtra el schema correctamente, pero el modelo lee el TEXTO del prompt y llama tools que ve ahí, aunque no estén en el schema. Dos modelos diferentes (Devstral 2 y Cogito-671b) alucinan exactamente el mismo tool (db_query) — porque ambos leen el mismo prompt.

**Hipótesis**: Si el texto del system prompt SOLO menciona los tools que existen en el schema, el modelo dejará de alucinar db_query y usará edit_file.

## Paso 1: Hacer HERRAMIENTAS dinámico en agent_loop.py

**Archivo**: `motor_v1_validation/agent/core/agent_loop.py`

### 1a. Reemplazar el bloque HERRAMIENTAS estático por un placeholder

**Antes** (en CODE_OS_SYSTEM, líneas ~37-48):
```python
CODE_OS_SYSTEM = """Eres Code OS — agente técnico de OMNI-MIND. SIEMPRE en ESPAÑOL.

HERRAMIENTAS:
- read_file(path) — lee archivos. SIEMPRE @project/ para proyecto
- edit_file(path, old_string, new_string) — edita archivos existentes
- write_file(path, content) — crea archivos NUEVOS
- list_dir(path) — lista directorio
- run_command(command) — ejecuta shell
- db_query(sql) — consulta DB (solo SELECT)
- http_request(method, url) — llamadas HTTP
- finish(result) — TERMINAR con resultado. PON TU RESPUESTA AQUÍ.
```

**Después**:
```python
CODE_OS_SYSTEM = """Eres Code OS — agente técnico de OMNI-MIND. SIEMPRE en ESPAÑOL.

HERRAMIENTAS DISPONIBLES (usa SOLO estas, ninguna más):
{tools_section}
```

### 1b. Crear diccionario de descripciones de tools

Añadir ANTES de CODE_OS_SYSTEM:
```python
TOOL_DESCRIPTIONS = {
    "read_file": "read_file(path) — lee archivos. SIEMPRE @project/ para proyecto",
    "edit_file": "edit_file(path, old_string, new_string) — edita archivos existentes",
    "write_file": "write_file(path, content) — crea archivos NUEVOS",
    "list_dir": "list_dir(path) — lista directorio",
    "run_command": "run_command(command) — ejecuta shell",
    "db_query": "db_query(sql) — consulta DB (solo SELECT)",
    "http_request": "http_request(method, url) — llamadas HTTP",
    "search_files": "search_files(pattern) — busca archivos por patrón",
    "finish": "finish(result) — TERMINAR con resultado. PON TU RESPUESTA AQUÍ.",
    "mochila": "mochila() — contexto del proyecto (máx 3 llamadas)",
}
```

### 1c. Generar tools_section dinámicamente antes de construir history

En `run_agent_loop`, DESPUÉS de calcular `active_tools` y `tool_schemas`, ANTES de construir `system`:

**Antes**:
```python
    # Build system prompt
    system = CODE_OS_SYSTEM.format(
        context_section=f"PROJECT CONTEXT:\n{context_prompt}" if context_prompt else ""
    )
```

**Después**:
```python
    # Build dynamic tools section — ONLY list tools that are in the filtered schema
    _schema_names = {s["function"]["name"] for s in tool_schemas}
    _tools_lines = []
    for tname in ["read_file", "edit_file", "write_file", "list_dir", "run_command",
                   "db_query", "http_request", "search_files", "finish", "mochila"]:
        if tname in _schema_names and tname in TOOL_DESCRIPTIONS:
            _tools_lines.append(f"- {TOOL_DESCRIPTIONS[tname]}")
    _tools_section = "\n".join(_tools_lines) if _tools_lines else "- finish(result)"

    # Build system prompt
    system = CODE_OS_SYSTEM.format(
        tools_section=_tools_section,
        context_section=f"PROJECT CONTEXT:\n{context_prompt}" if context_prompt else ""
    )
```

**Criterio paso 1**: 
- `grep -c "tools_section" motor_v1_validation/agent/core/agent_loop.py` devuelve >= 3
- `grep -c "db_query.*consulta DB" motor_v1_validation/agent/core/agent_loop.py` devuelve 1 (solo en TOOL_DESCRIPTIONS, NO en CODE_OS_SYSTEM)

## Paso 2: Desplegar a fly.io

```bash
fly deploy --app chief-os-omni
```

**Criterio**: Health check OK.

## Paso 3: Ejecutar T3

```bash
cd briefings && python3 test_validacion_modelos.py
```

**Criterio de éxito T3**: 
- DIAG log muestra que db_query NO aparece en tools_count
- 0 llamadas a db_query alucinadas
- Al menos 1 edit_file en api.py
- Test PASS

## Paso 4: Guardar resultado

Guardar en `results/B19C_dynamic_prompt.md` con:
- Confirmar que el DIAG log muestra solo tools execute (sin db_query)
- Comparar con B18/B19A/B19B: ¿desapareció la alucinación de db_query?
- Tools llamados
- PASS/FAIL

## Paso 5: Si pasa, correr los 4 tests

```bash
cd briefings && python3 test_validacion_modelos.py
```

Confirmar que T1, T2, T4 siguen pasando (no regresión).

## Rollback (si falla por razón diferente a db_query)

Si el modelo ya NO alucina db_query pero sigue sin usar edit_file por otra razón → no revertir, el fix es correcto. Documentar el nuevo patrón de fallo.

Si el cambio rompe T1/T2/T4 → revertir a CODE_OS_SYSTEM estático y redesplegar.
