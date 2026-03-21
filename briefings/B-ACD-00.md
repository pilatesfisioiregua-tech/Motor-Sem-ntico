# B-ACD-00: Rediseño loop agentic Code OS

**Fecha:** 2026-03-19
**Reemplaza:** B25
**Ejecutor:** Claude Code
**CR1:** Aceptado

---

## CONTEXTO

Code OS tiene bugs de diseño, no de modelos. El system prompt + mochila crean loops porque:
1. Las secciones de mochila se cross-referencian (herramientas menciona @project/, rutas menciona @project/, reglas menciona read_file...)
2. El modelo llama mochila repetidamente buscando contexto que debería estar inline
3. context.py no tiene hard limit de tokens por mensaje individual
4. No hay concepto de "paso atómico" — el modelo puede divagar indefinidamente

La mochila ya tiene rate limiter de 3 calls (bien). Pero las secciones siguen siendo enormes y redundantes.

---

## PASO 1: Eliminar cross-references de mochila

**Archivo:** `@project/core/mochila.py`

**Acción:** Reescribir SECTIONS para que cada sección sea AUTOCONTENIDA — ninguna sección referencia a otra.

**ANTES (ejemplo herramientas):**
```
"herramientas": """CATÁLOGO DE HERRAMIENTAS CODE OS v3 (63 tools)
FILESYSTEM: read_file(path), write_file(path, content), edit_file(path, old_string, new_string), list_dir(path)
  - SIEMPRE usa @project/ para archivos del proyecto
...
```

**DESPUÉS:** Cada sección máximo 500 chars. Sin mencionar contenido de otras secciones.

Reemplazar el dict SECTIONS completo por:

```python
SECTIONS = {
    "herramientas": (
        "CORE: read_file(path), edit_file(path, old, new), insert_at(path, line, code), "
        "write_file(path, content), list_dir(path), run_command(cmd), finish(result), mochila(seccion)\n"
        "EXTRA: db_query(sql), db_insert(sql), http_request(method, url), search_files(query)\n"
        "Rutas: @project/ = proyecto real. Sin prefijo = sandbox."
    ),
    "reglas": (
        "1. Usa tools, no adivines. 2. Lee antes de editar. 3. Verifica tras escribir. "
        "4. edit_file para cambios puntuales. 5. @project/ siempre para proyecto. "
        "6. finish(result) con respuesta completa. 7. Español siempre."
    ),
    "errores": (
        "old_string NOT FOUND: lee el archivo primero, copia string exacto. "
        "ARCHIVO NO ENCONTRADO: usa @project/ prefix. "
        "LOOP: para y cambia de enfoque. "
        "BLOWUP: simplifica la petición."
    ),
    "proyecto": (
        "Stack: Python 3.12 / FastAPI / fly.io Postgres+pgvector / NetworkX\n"
        "Deploy: fly deploy -a chief-os-omni --remote-only\n"
        "Estructura: motor_v1_validation/agent/ (api.py, core/, tools/)"
    ),
}
```

**Pass/fail:** `len(SECTIONS)` == 4. Ninguna sección > 600 chars. `grep -c "SIEMPRE usa @project" mochila.py` == 0 (la frase duplicada ya no existe).

---

## PASO 2: Inlinear info crítica en system prompt

**Archivo:** `@project/core/agent_loop.py`

**Acción:** Reemplazar CODE_OS_SYSTEM por versión que inline las 3 cosas que el modelo SIEMPRE necesita (tools, rutas, protocolo), eliminando la necesidad de llamar mochila al inicio.

**Reemplazar** la variable `CODE_OS_SYSTEM` por:

```python
CODE_OS_SYSTEM = """Eres Code OS — agente técnico de OMNI-MIND. ESPAÑOL siempre.

TOOLS:
{tools_section}

RUTAS: @project/ = proyecto real. Sin prefijo = sandbox temporal.

PROTOCOLO:
1. Lee (read_file) → 2. Edita (edit_file/insert_at) → 3. Verifica (run_command) → 4. finish(result='respuesta')
Tu respuesta va DENTRO de finish(result='...').

{context_section}
"""
```

**Pass/fail:** `CODE_OS_SYSTEM` < 400 chars (sin contar placeholders). No menciona mochila en el system prompt.

---

## PASO 3: Añadir hard limit por mensaje en context.py

**Archivo:** `@project/core/context.py`

**Acción:** Añadir truncado de mensajes individuales en `maybe_compress()`. Ningún mensaje individual debe exceder 8000 chars.

**Añadir** al inicio de `maybe_compress()`, ANTES de la estimación de tokens:

```python
    def maybe_compress(self, history: list) -> list:
        """Compress history if it exceeds threshold. Returns new history."""
        # Hard limit: truncar mensajes individuales > 8000 chars
        for msg in history:
            content = msg.get("content", "")
            if isinstance(content, str) and len(content) > 8000:
                msg["content"] = content[:7500] + "\n...[TRUNCADO]..."
        
        total = estimate_history_tokens(history)
        # ... rest unchanged
```

**Pass/fail:** Añadir test inline:
```bash
python3 -c "
from core.context import ContextManager
cm = ContextManager()
history = [{'role': 'system', 'content': 'x'}, {'role': 'user', 'content': 'A' * 10000}]
result = cm.maybe_compress(history)
assert len(result[1]['content']) < 8100, f'Message too long: {len(result[1][\"content\"])}'
print('PASS: hard limit works')
"
```

---

## PASO 4: Mochila no llamable en system prompt

**Archivo:** `@project/core/agent_loop.py`

**Acción:** En `TOOL_DESCRIPTIONS`, cambiar la descripción de mochila para que NO invite a llamarla al inicio:

**Reemplazar:**
```python
    "mochila": "mochila() — contexto del proyecto (máx 3 llamadas)",
```

**Por:**
```python
    "mochila": "mochila(seccion) — referencia: herramientas|reglas|errores|proyecto. Solo si necesitas algo específico.",
```

**Pass/fail:** `grep "contexto del proyecto" agent_loop.py` == 0 hits.

---

## PASO 5: Verificación end-to-end

**Ejecutar:**
```bash
cd @project/
python3 -c "
from core.mochila import SECTIONS, consultar, reset_mochila
# Test 1: Secciones reducidas
for k, v in SECTIONS.items():
    assert len(v) <= 600, f'{k} demasiado larga: {len(v)} chars'
print(f'PASS: {len(SECTIONS)} secciones, todas <= 600 chars')

# Test 2: Sin cross-references
import re
for k, v in SECTIONS.items():
    other_keys = [ok for ok in SECTIONS if ok != k]
    for ok in other_keys:
        assert ok not in v.lower(), f'{k} referencia a {ok}'
print('PASS: sin cross-references')

# Test 3: Rate limiter
reset_mochila()
for i in range(4):
    r = consultar('herramientas')
assert 'LIMITE' in r
print('PASS: rate limiter funciona')

# Test 4: System prompt size
from core.agent_loop import CODE_OS_SYSTEM
base = CODE_OS_SYSTEM.replace('{tools_section}', '').replace('{context_section}', '')
assert len(base) < 400, f'System prompt demasiado largo: {len(base)}'
print(f'PASS: system prompt base = {len(base)} chars')
"
```

**Criterio final:** Los 4 tests pasan. 0 errores.

---

## PASO 6 (OPCIONAL si hay tiempo): Deploy y test en fly.io

```bash
cd @project/
fly deploy -a chief-os-omni --remote-only
# Esperar deploy
curl -s https://chief-os-omni.fly.dev/health | python3 -c "import json,sys; d=json.load(sys.stdin); print('HEALTH:', d.get('status'))"
```

---

## ARCHIVOS QUE SE TOCAN

| Archivo | Acción |
|---------|--------|
| `core/mochila.py` | Reescribir SECTIONS (4 secciones, <=600 chars cada una) |
| `core/agent_loop.py` | Reescribir CODE_OS_SYSTEM + cambiar descripción mochila |
| `core/context.py` | Añadir hard limit 8000 chars por mensaje |

## ARCHIVOS QUE NO SE TOCAN

Todo lo demás. Este briefing es quirúrgico — solo 3 archivos, solo las variables/funciones especificadas.
