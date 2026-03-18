# B23 — insert_at como herramienta primaria + redirect activo

Fecha: 2026-03-18
Base URL: https://chief-os-omni.fly.dev
Version: 3.4.0

## Cambios verificados y desplegados

1. **MODE_HINTS["execute"]** prioriza insert_at sobre edit_file explícitamente
2. **EDIT_FILE REDIRECT** en agent_loop: cuando edit_file falla, inyecta mensaje forzando insert_at

## Resultados (run 1 — sin fix test harness)

| Test | Resultado | Iteraciones | Tiempo | Notas |
|------|-----------|-------------|--------|-------|
| T1 Quick | PASS | 5 | 8.2s | read_file, list_dir, search_files |
| T2 Análisis | FAIL | 5 | 4.2s | 0/6 métodos (variabilidad) |
| T3 Execute | FAIL | 26 | 35.5s | **insert_at LLAMADO POR PRIMERA VEZ** |
| T4 Deep | FAIL | 16 | 25.8s | 7 HTTP calls, 0/6 keywords |

### T3 Run 1 — insert_at usado!

Tools: `['read_file', 'list_dir', 'list_dir', 'read_file', 'insert_at', 'run_command' ×4, 'read_file']`

El modelo siguió el workflow del nuevo MODE_HINTS:
1. read_file → vio números de línea
2. list_dir ×2 → exploró
3. read_file → leyó archivo
4. **insert_at** → insertó código (primera vez!)
5. run_command ×4 → verificó
6. read_file → comprobó resultado

Test marcaba FAIL porque `insert_at` no estaba en la lista de edit_calls del test harness.

## Fix test harness

Añadido `"insert_at"` a la lista de edit tools en test_validacion_modelos.py (línea 219).

## Resultados (run 2 — con fix test harness)

| Test | Resultado | Iteraciones | Tiempo | Notas |
|------|-----------|-------------|--------|-------|
| T1 Quick | **PASS** | 0 | 0.3s | Cache hit |
| T2 Análisis | **PASS** | 0 | 0.3s | Cache hit (5/6) |
| T3 Execute | **FAIL** | 11 | 13.6s | edit_file + insert_at llamados, api.py no en args |
| T4 Deep | **PASS** | 9 | 15.5s | 6 HTTP calls, 4/6 keywords |

**Total: 3/4 passed**

### T3 Run 2

Tools: `['read_file', 'list_dir' ×3, 'read_file', 'edit_file', 'insert_at', 'run_command' ×3]`

Flujo completo B23:
1. read_file → lee código
2. list_dir ×3 → explora
3. read_file → lee de nuevo
4. edit_file → **FALLA** → redirect activa
5. **insert_at** → inserta código (redirect funcionó!)
6. run_command ×3 → verifica

"Edit calls: 0" porque ni edit_file ni insert_at contenían "api.py" en args (el modelo puede haber usado path diferente o sandbox).

## Evolución T3 (B18 → B23)

| Briefing | Goal correcto | Filesystem tools | edit_file | insert_at | Workflow |
|----------|--------------|------------------|-----------|-----------|----------|
| B18 | NO (translate_intent) | NO | NO | N/A | mochila → http_request ×N |
| B19C | NO | SI (read+list) | NO | N/A | mochila → read/list → stuck |
| B20 | NO | NO | NO | NO | mochila → http_request ×N |
| B21 | **SI** | **SI** | **SI** (1 call) | NO | read → list → edit(FAIL) → run_cmd |
| B22 | SI | SI | SI | NO | read → list → edit(FAIL) → run_cmd |
| B23 | SI | SI | SI → FAIL | **SI** (1 call) | read → list → edit(FAIL) → **insert_at** → verify |

## Veredicto

- **B23 behavioral goal: ACHIEVED** — el modelo usa insert_at, el redirect funciona
- **T3 test: FAIL** — insert_at no targetea api.py específicamente (model targeting issue)
- **Test harness: FIXED** — ahora cuenta insert_at como edit call
- **T4: PASS** (4/6 keywords) — no regresión
- **Próximo paso**: el modelo necesita targetear @project/api.py en insert_at. Podría ser un issue de cómo el modelo interpreta el goal "en @project/api.py" vs cómo resuelve el path.
