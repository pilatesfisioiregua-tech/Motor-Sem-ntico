# BRIEFING_20 — insert_at + read_file con líneas numeradas

**Objetivo**: Desbloquear T3 añadiendo `insert_at(path, line, content)` como herramienta de edición por número de línea, y haciendo que `read_file` muestre números de línea para que el modelo pueda referenciarlos.

**Diagnóstico**: B19A-D probaron 2 modelos × 2 formatos de prompt. Ninguno usa `edit_file`. La causa raíz: `edit_file(old_string, new_string)` exige que el LLM copie strings exactas carácter por carácter — la tarea más frágil para cualquier modelo. `insert_at` por número de línea es cognitivamente trivial: el modelo ve "línea 47: @app.get('/health')" y dice `insert_at(path, 53, código_nuevo)`.

**Cambios**: 3 archivos, ~40 líneas nuevas.

---

## Paso 1: Añadir `tool_insert_at` y modificar `tool_read_file` en filesystem.py

**Archivo**: `motor_v1_validation/agent/tools/filesystem.py`

### 1a. Modificar `tool_read_file` para mostrar números de línea

**Antes**:
```python
def tool_read_file(path: str, offset: int = 0, limit: int = 0) -> str:
    """Read file with optional line offset/limit for large files."""
    abs_path = _resolve_path(path)
    if not os.path.isfile(abs_path):
        return f"ERROR: File not found: {path}"
    size = os.path.getsize(abs_path)
    if size > MAX_FILE_SIZE:
        return f"ERROR: File too large ({size} bytes, max {MAX_FILE_SIZE})"
    with open(abs_path, 'r', errors='replace') as f:
        if offset > 0 or limit > 0:
            lines = f.readlines()
            total_lines = len(lines)
            start = max(0, offset)
            end = start + limit if limit > 0 else total_lines
            selected = lines[start:end]
            header = f"[Lines {start+1}-{min(end, total_lines)} of {total_lines}]\n"
            content = header + "".join(selected)
        else:
            content = f.read()
    if len(content) > MAX_OUTPUT_LEN:
        total_len = len(content)
        content = content[:MAX_OUTPUT_LEN] + f"\n... [TRUNCATED at {MAX_OUTPUT_LEN} of {total_len} chars. Use offset/limit params to read sections: read_file(path, offset=LINE, limit=LINES)]"
    return content
```

**Después**:
```python
def tool_read_file(path: str, offset: int = 0, limit: int = 0) -> str:
    """Read file with line numbers. Use offset/limit for large files."""
    abs_path = _resolve_path(path)
    if not os.path.isfile(abs_path):
        return f"ERROR: File not found: {path}"
    size = os.path.getsize(abs_path)
    if size > MAX_FILE_SIZE:
        return f"ERROR: File too large ({size} bytes, max {MAX_FILE_SIZE})"
    with open(abs_path, 'r', errors='replace') as f:
        all_lines = f.readlines()
    total_lines = len(all_lines)
    if offset > 0 or limit > 0:
        start = max(0, offset)
        end = start + limit if limit > 0 else total_lines
        selected = all_lines[start:end]
        header = f"[Lines {start+1}-{min(end, total_lines)} of {total_lines}]\n"
    else:
        selected = all_lines
        header = f"[{total_lines} lines]\n"
        start = 0
    # Always show line numbers (like cat -n) so models can reference them for insert_at
    numbered = [f"{start + i + 1:4d}| {line}" for i, line in enumerate(selected)]
    content = header + "".join(numbered)
    if len(content) > MAX_OUTPUT_LEN:
        total_len = len(content)
        content = content[:MAX_OUTPUT_LEN] + f"\n... [TRUNCATED at {MAX_OUTPUT_LEN} of {total_len} chars. Use offset/limit params to read sections: read_file(path, offset=LINE, limit=LINES)]"
    return content
```

### 1b. Añadir función `tool_insert_at` (después de `tool_edit_file`)

**Insertar después de la función `tool_edit_file`** (después de la línea `return f"OK: Replaced in {path}..."`):

```python
def tool_insert_at(path: str, line: int, content: str) -> str:
    """Insert content at a specific line number. Existing lines shift down."""
    abs_path = _resolve_path(path)
    if not os.path.isfile(abs_path):
        return f"ERROR: File not found: {path}"
    with open(abs_path, 'r', errors='replace') as f:
        lines = f.readlines()
    total = len(lines)
    if line < 1 or line > total + 1:
        return f"ERROR: Line {line} out of range (file has {total} lines, valid: 1-{total+1})"
    # Ensure content ends with newline
    if content and not content.endswith('\n'):
        content += '\n'
    new_lines = content.splitlines(keepends=True)
    # Insert at position (1-based: line=1 inserts before first line, line=total+1 appends)
    lines[line-1:line-1] = new_lines
    with open(abs_path, 'w') as f:
        f.writelines(lines)
    return f"OK: Inserted {len(new_lines)} lines at line {line} in {path} (file now {len(lines)} lines)"
```

### 1c. Registrar `insert_at` en `register_tools` (después del registro de `edit_file`)

**Insertar después del bloque `registry.register("edit_file", ...)`**:

```python
    registry.register("insert_at", {
        "name": "insert_at",
        "description": "Insert new lines at a specific line number. Use read_file first to see line numbers. Line 1 = before first line, line N+1 = append at end. Existing lines shift down.",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string", "description": "Path. Use @project/... for project files."},
            "line": {"type": "integer", "description": "Line number where content will be inserted (1-based). Use line numbers from read_file output."},
            "content": {"type": "string", "description": "Code/text to insert. Can be multiple lines."}
        }, "required": ["path", "line", "content"]}
    }, lambda a: tool_insert_at(a["path"], a["line"], a["content"]), category="filesystem")
```

**Criterio paso 1**: `grep -c "insert_at" motor_v1_validation/agent/tools/filesystem.py` devuelve al menos 3 (función + registro + lambda).

---

## Paso 2: Actualizar agent_loop.py — TOOL_DESCRIPTIONS, MODE_TOOLS, CÓMO TRABAJAR

**Archivo**: `motor_v1_validation/agent/core/agent_loop.py`

### 2a. Añadir a TOOL_DESCRIPTIONS

**Antes** (en el dict `TOOL_DESCRIPTIONS`):
```python
    "edit_file": "edit_file(path, old_string, new_string) — edita archivos existentes",
```

**Después** (añadir línea DESPUÉS de edit_file):
```python
    "edit_file": "edit_file(path, old_string, new_string) — edita archivos existentes",
    "insert_at": "insert_at(path, line, content) — inserta código en línea N (usa read_file para ver números)",
```

### 2b. Añadir `insert_at` a CORE_TOOLS y MODE_TOOLS

**Antes**:
```python
    CORE_TOOLS = {
        "read_file", "edit_file", "write_file", "list_dir",
        "run_command", "finish", "mochila",
    }
```

**Después**:
```python
    CORE_TOOLS = {
        "read_file", "edit_file", "insert_at", "write_file", "list_dir",
        "run_command", "finish", "mochila",
    }
```

### 2c. Actualizar "CÓMO TRABAJAR" en CODE_OS_SYSTEM para mencionar insert_at

**Antes**:
```
CÓMO TRABAJAR:
1. ¿Qué necesito saber? → usa las herramientas de lectura disponibles
2. ¿Necesito cambiar algo? → edit_file, write_file, run_command
3. ¿Ya tengo la respuesta? → finish(result='mi respuesta completa')
```

**Después**:
```
CÓMO TRABAJAR:
1. ¿Qué necesito saber? → read_file (muestra números de línea)
2. ¿Necesito añadir código? → insert_at(path, línea, código_nuevo)
3. ¿Necesito cambiar código existente? → edit_file(path, texto_viejo, texto_nuevo)
4. ¿Ya tengo la respuesta? → finish(result='mi respuesta completa')
```

**Criterio paso 2**: `grep -c "insert_at" motor_v1_validation/agent/core/agent_loop.py` devuelve al menos 3.

---

## Paso 3: Añadir `insert_at` a WORKER_TOOLS en router.py

**Archivo**: `motor_v1_validation/agent/core/router.py`

**Antes**:
```python
WORKER_TOOLS = {
    "write_file", "edit_file",
```

**Después**:
```python
WORKER_TOOLS = {
    "write_file", "edit_file", "insert_at",
```

**Criterio paso 3**: `grep -c "insert_at" motor_v1_validation/agent/core/router.py` devuelve 1.

---

## Paso 4: Añadir insert_at al drift_guard file check

**Archivo**: `motor_v1_validation/agent/core/agent_loop.py`

Buscar esta línea en el loop principal:
```python
            if tool_name in ("write_file", "edit_file", "create_tool"):
```

**Cambiar a**:
```python
            if tool_name in ("write_file", "edit_file", "insert_at", "create_tool"):
```

Y buscar la segunda ocurrencia (tracking de files_changed):
```python
            if tool_name in ("write_file", "edit_file") and not is_error:
```

**Cambiar a**:
```python
            if tool_name in ("write_file", "edit_file", "insert_at") and not is_error:
```

---

## Paso 4b: Añadir insert_at a la validación de código en agent_loop.py

Buscar esta línea (sandwich pre-validation para code):
```python
                if tool_name in ("write_file", "edit_file"):
                    code_ok, code_err = validate_code_output(tool_name, tool_args)
```

**Cambiar a**:
```python
                if tool_name in ("write_file", "edit_file", "insert_at"):
                    code_ok, code_err = validate_code_output(tool_name, tool_args)
```

---

## Paso 5: Desplegar y probar

```bash
fly deploy --app chief-os-omni
```

**Criterio health**: `curl -s https://chief-os-omni.fly.dev/health` devuelve status ok.

Luego ejecutar tests:
```bash
cd briefings && python3 test_validacion_modelos.py
```

**Criterio T3**: Al menos 1 `insert_at` O `edit_file` en api.py, y test PASS.
**Criterio T1/T2/T4**: Sin regresión (los que pasaban siguen pasando).

## Paso 6: Guardar resultado

Guardar output en `results/B20_insert_at.md` con:
- DIAG line (confirmar insert_at aparece en tools)
- read_file output (confirmar números de línea)
- Tools llamados
- ¿Usó insert_at? ¿O edit_file? ¿O ninguno?
- PASS/FAIL por test
- Tabla comparativa B19C vs B20

## Rollback

Si hay regresión en T1/T4: revertir los 3 archivos y redesplegar. Los cambios son aditivos (nueva tool + formato de read_file) así que el riesgo de regresión es bajo.
