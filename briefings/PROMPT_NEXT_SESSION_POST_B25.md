# Prompt para siguiente sesión — Post B25

## Estado actual: B25 pendiente de deploy + test

### Código YA aplicado (en repo, no desplegado)

**Archivo**: `motor_v1_validation/agent/core/agent_loop.py` — 3 cambios acumulados de esta sesión:

1. **B23 — MODE_HINTS insert_at-first** (~línea 219): El hint de execute mode dice explícitamente "usa insert_at, NO edit_file" con protocolo de 4 pasos.

2. **B23 — EDIT_FILE REDIRECT** (~línea 557): Cuando edit_file falla con "old_string not found", inyecta mensaje de usuario forzando insert_at con instrucciones explícitas.

3. **B24 — Path dinámico** (~línea 213): Extrae `@project/XXX` del goal con regex e inyecta el path exacto en el hint (ej: `insert_at('@project/api.py', ...)` en vez de genérico).

4. **B25 — Path auto-correction** (~línea 453): En execute mode, si insert_at/edit_file/write_file/read_file recibe path sin `@project/` prefix, se prepend automáticamente. Fix determinista.

### Acción inmediata

```bash
fly deploy --app chief-os-omni --remote-only
cd briefings && python3 test_validacion_modelos.py
```

Guardar resultado en `results/B25_path_autocorrect.md`. Si T3 PASS → commit "B25: T3 PASS — 4/4 tests".

---

## Contexto Code OS: Test Validation 3/4 → objetivo 4/4

### T3 es el único test que falta (crear endpoint GET /test/ping en api.py)

**Progresión B18→B25** (cadena causal completa):

| B# | Fix | Efecto en T3 |
|----|-----|-------------|
| B18 | Diagnóstico runtime | Infra OK, modelo incapaz (db_query spam) |
| B19A | Cogito-671b como cerebro | INVÁLIDO — prompt viejo contaminaba |
| B19B | Formato D en hint | INVÁLIDO — prompt viejo contaminaba |
| B19C | System prompt dinámico | db_query=0, read_file SÍ, edit_file=0 |
| B19D | Cogito + prompt dinámico | Peor que Devstral (http_request spam) |
| B20 | insert_at + read_file numerado | Herramientas listas, modelo no las usa |
| B21 | Tool enforcement + quitar http_request de execute + fix translate_intent | **BREAKTHROUGH**: modelo usa edit_file por primera vez |
| B22 | edit_file error sugiere insert_at (TIP pasivo) | Modelo ignora TIP, usa run_command |
| B23 | MODE_HINTS insert_at-first + redirect activo | **insert_at usado por primera vez** |
| B24 | Path dinámico en hint (@project/api.py) | Modelo va directo a insert_at, pero path incorrecto |
| B25 | Path auto-correction (prepend @project/) | **Pendiente de test** |

### Causa raíz descubierta en B21

`translate_intent()` reemplazaba el goal de T3 con un template de diagnóstico porque `"status"` en `{"status": "pong"}` matcheaba la categoría "estado". El modelo nunca vio la instrucción de editar código. Fix: passthrough para inputs con `@project/`.

### Stack actual desplegado

- Cerebro quick/standard/execute: `mistralai/devstral-2512`
- Cerebro analyze: `deepseek/deepseek-v3.2`
- Evaluador: `z-ai/glm-5`
- Worker budget: `deepseek/deepseek-v3.2`

---

## Si T3 pasa con B25

**Prioridad 4** (roadmap post-4/4):
- Reactor v4: generar preguntas desde telemetría operacional real
- Capa A Perplexity: búsquedas ad-hoc para F6 (Adaptación) y F5 (Identidad/Frontera)
- Swarm Tiers 4-5: Profundo ($1/45min) y Cartografía ($10/horas)
- Supabase → fly.io migration (Code OS's first real task — "eating its own food")

## Si T3 falla con B25

El path auto-correction es determinista — si el modelo dice `insert_at('api.py', N, code)`, se corrige a `@project/api.py`. Si aún falla, las posibilidades son:
1. El modelo no apunta a api.py en absoluto (usa otro archivo) → necesita log exacto de args
2. El modelo no llama finish → necesita investigar por qué no cierra
3. done_evt es None → puede ser timeout o error en SSE streaming

---

## Archivos clave

- Agent loop: `motor_v1_validation/agent/core/agent_loop.py` (~956 líneas)
- Router: `motor_v1_validation/agent/core/router.py`
- API config: `motor_v1_validation/agent/core/api.py`
- Filesystem tools: `motor_v1_validation/agent/tools/filesystem.py`
- Intent translator: `motor_v1_validation/agent/core/intent.py`
- Mochila: `motor_v1_validation/agent/core/mochila.py`
- Test: `briefings/test_validacion_modelos.py`
- Briefing pendiente: `briefings/BRIEFING_25.md`
- Resultados: `results/B19A_cogito_execute.md` → `results/B24_path_dinamico.md`

## Principio operativo descubierto esta sesión

**P36 (CR0)**: Cuando un LLM no usa una herramienta, la causa más probable NO es el modelo ni el formato del prompt — es que algo en el pipeline (translate_intent, mochila, system prompt estático, tool filtering cosmético) le está diciendo algo diferente de lo que tú crees. Verifica el goal que REALMENTE llega al modelo antes de cambiar modelos o prompts.
