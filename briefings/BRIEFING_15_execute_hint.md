# BRIEFING_15 — Execute Mode Hint: conectar código con filesystem

## Contexto

B14: 3/4. V3.2 resolvió T4 (diagnóstico, 5/6 keywords en 9 iters). T3 sigue fallando.

T3 tools: `mochila → http_request ×3 → db_query ×2`. V3.2 interpreta "Añade un endpoint" como tarea de red. Nunca llama `read_file` ni `edit_file`.

El problema no es el modelo ni el tool set — es que el prompt no conecta "crear código" con "editar archivos". Ambos modelos (Devstral 2 y V3.2) tienen el mismo fallo: no asocian tareas de código con herramientas de filesystem.

## Solución: Execute mode hint

Cuando `exec_mode == "execute"`, inyectar un hint en el mensaje del usuario que explicite el flujo: leer archivo → editar → verificar.

## Qué hacer

### Paso 1 — Añadir hint por modo en agent_loop.py

Archivo: `motor_v1_validation/agent/core/agent_loop.py`

Buscar el bloque donde se construye `history` (después de construir `system`):

**ANTES:**
```python
    history = [
        {"role": "system", "content": system},
        {"role": "user", "content": (
            f"TASK:\n{goal}\n\n"
            f"Workspace: {sandbox_dir}\n"
            f"Runtimes: python3, pytest, deno, node.\n"
            f"Tools available: {registry.tool_count()}\n"
            f"Start by understanding the task, then plan and implement."
        )},
    ]
```

**DESPUÉS:**
```python
    # Mode-specific hints — guían al modelo sobre QUÉ herramientas usar
    MODE_HINTS = {
        "execute": (
            "\n\nPROTOCOLO EXECUTE: Esta tarea requiere MODIFICAR CÓDIGO. "
            "Flujo obligatorio: "
            "1) read_file(@project/archivo) para ver el código actual, "
            "2) edit_file(@project/archivo, old_string, new_string) para hacer cambios, "
            "3) run_command() o finish() para verificar/completar."
        ),
        "analyze": "",  # V3.2 ya maneja analyze bien (B14: 5/6 keywords)
        "quick": "",
        "standard": "",
        "deep": "",
    }
    mode_hint = MODE_HINTS.get(exec_mode, "")

    history = [
        {"role": "system", "content": system},
        {"role": "user", "content": (
            f"TASK:\n{goal}\n\n"
            f"Workspace: {sandbox_dir}\n"
            f"Runtimes: python3, pytest, deno, node.\n"
            f"Tools available: {len(tool_schemas)}"
            f"{mode_hint}\n"
            f"Start by understanding the task, then plan and implement."
        )},
    ]
```

### Paso 2 — Deploy y test

```bash
cd /Users/jesusfernandezdominguez/omni-mind-cerebro
fly deploy --config motor-semantico/motor_v1_validation/agent/fly.toml \
           --dockerfile motor-semantico/motor_v1_validation/agent/Dockerfile

python3 motor-semantico/briefings/test_validacion_modelos.py \
    --output motor-semantico/results/test_modelos_execute_hint_b15.md
```

## Criterio de éxito

| Test | B14 | Target B15 |
|------|-----|------------|
| T1 | ✅ CACHE | ✅ (no regresión) |
| T2 | ✅ CACHE | ✅ (no regresión) |
| T3 | ❌ 0 edit_file | ✅ ≥1 edit_file en api.py |
| T4 | ✅ 5/6 kw | ✅ (no regresión) |

**4/4 → Code OS operativo. Documentar:**
- Principio 33: Cerebro dual (V3.2 execute+analyze, Devstral 2 quick/standard)
- Principio 34: Mode hints (guiar modelo sobre QUÉ herramientas usar según tipo de tarea)

**T3 sigue fallando → el modelo no puede o no quiere usar edit_file. Opciones:**
- a) Probar Devstral 2 con hint (es modelo de coding, quizá con el hint sí lo hace)
- b) Probar Cogito-671b para execute (más caro pero mejor razonamiento)
- c) Cambiar el test T3 para usar write_file en vez de edit_file (quizá el modelo prefiere crear archivos nuevos)

## Notas

- El hint solo se añade para modo execute. No toca analyze (que ya funciona) ni quick (cache).
- El hint usa el flujo exacto del system prompt pero lo repite con énfasis en el user message.
- Esto es coherente con B12: las preguntas/instrucciones directas en el user message son más efectivas que descripciones genéricas en el system prompt.
- Si funciona, el patrón es generalizable: cada modo tiene su propio "protocol hint" que guía la selección de herramientas.
- El `registry.tool_count()` se cambió a `len(tool_schemas)` para reflejar el count real post-filtering (B13).
