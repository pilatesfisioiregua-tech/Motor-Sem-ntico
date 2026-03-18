# B21 — Tool enforcement + http_request fuera de execute

Fecha: 2026-03-18
Base URL: https://chief-os-omni.fly.dev
Version: 3.4.0

## Cambios aplicados

1. **Tool enforcement real** en agent_loop.py — tools no en active set se rechazan con error
2. **http_request eliminado de execute MODE_TOOLS** — execute solo tiene CORE_TOOLS + run_command
3. **detect_mode() con word-boundary matching** — `\bcreate\b` no matchea `created_at` (fix para T4 regression)
4. **translate_intent passthrough** — inputs con `@project/` pasan directo, no se reemplazan con templates genéricos

## Hallazgo crítico durante ejecución

**translate_intent() reemplazaba T3 completo**: El input "Añade un endpoint... @project/api.py" contiene `"status"` (en `{"status": "pong"}`), que matcheaba la categoría "estado" en BUSINESS_KEYWORDS. El goal original se perdía completamente, reemplazado por un template de diagnóstico que usa http_request. **El modelo nunca vio la instrucción de editar código.** Esto explica el comportamiento desde B13 — no era el modelo ni el prompt, era que el goal de T3 era incorrecto.

## DIAG confirmado

```
T3: exec_mode=execute | goal_start='Añade un endpoint GET /test/ping en @project/api.py' | tools_count=8
    tools=['read_file', 'write_file', 'edit_file', 'insert_at', 'list_dir', 'run_command', 'finish', 'mochila']

T4: exec_mode=standard | goal_start='PRIMERO consulta mochila...' | tools_count=11
    tools=[...includes http_request, db_query...]
```

## Resultados

| Test | Resultado | Iteraciones | Tiempo | Errores | Notas |
|------|-----------|-------------|--------|---------|-------|
| T1 Quick | **PASS** | 5 | 6.8s | 1 | read_file, list_dir, search_files |
| T2 Análisis | **PASS** | 8 | 16.0s | 2 | 6/6 métodos encontrados |
| T3 Execute | **FAIL** | 21 | 36.7s | 8 | **edit_file LLAMADO** por primera vez! |
| T4 Deep | **FAIL** | 16 | 25.3s | 1 | 7 HTTP calls, 0/6 keywords |

**Total: 2/4 passed**

## T3 Detalle — BREAKTHROUGH

Tools: `['read_file', 'list_dir', 'list_dir', 'read_file', 'edit_file', 'run_command' ×5]`

- **read_file: 2** (lee el código!)
- **list_dir: 2** (explora la estructura!)
- **edit_file: 1** (intenta editar!)
- **run_command: 5** (intenta verificar!)
- http_request: 0 (bloqueado correctamente)
- insert_at: 0 (no lo usó, pero está disponible)

**Primer flujo correcto**: read → explore → read → edit → verify. El modelo sigue el workflow esperado.

**8 errores**: probablemente edit_file failures (old_string no encontrado) + run_command failures. El modelo intenta pero no acierta el string match exacto.

## Comparación evolutiva T3

| Métrica | B18 | B19C | B20 | B21-v1 | B21-v2 | B21-final |
|---------|-----|------|-----|--------|--------|-----------|
| Goal correcto | NO* | NO* | NO* | NO* | NO** | **SI** |
| exec_mode | execute | execute | execute | execute | analyze | **execute** |
| http_request bloqueado | NO | NO | NO | SI | NO | SI |
| read_file usado | NO | SI | NO | SI | NO | **SI** |
| edit_file usado | NO | NO | NO | NO | NO | **SI** |
| insert_at usado | N/A | N/A | NO | NO | NO | NO |
| Resultado | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL |

*Goal reemplazado por translate_intent template "estado" (falso positivo por "status")
**Goal reemplazado pero exec_mode cambió a analyze por word-boundary fix

## T4 Detalle

Tools: mochila, http_request ×7, run_command ×5, db_query ×2
- HTTP calls restaurados (7) — no regresión vs B19C
- 0/6 keywords diagnóstico — modelo hace trabajo pero no formula la respuesta con los keywords esperados
- T4 FAIL es por contenido, no por tools

## Veredicto

- **B21 changes: MANTENER** — todos los fixes son correctos y complementarios
- **T3: mayor avance desde que empezamos** — el modelo lee, explora, intenta editar
- **Siguiente paso T3**: el modelo usa edit_file (old_string matching) que es frágil. Debería usar insert_at. Posible fix: hacer que MODE_HINTS["execute"] priorice insert_at sobre edit_file, o dar feedback cuando edit_file falla sugiriendo insert_at.
- **T4**: problema de contenido/keywords, no de tools
