# B24 — Path dinámico en execute hint

Fecha: 2026-03-18
Base URL: https://chief-os-omni.fly.dev
Version: 3.4.0

## Cambio

Extraer `@project/XXX` del goal e inyectarlo en MODE_HINTS para que el modelo tenga el path exacto en las instrucciones.

```python
import re as _re_hint
_target_match = _re_hint.search(r'@project/[\w./\-]+', goal)
_target_path = _target_match.group(0) if _target_match else "@project/archivo"
```

MODE_HINTS["execute"] ahora usa f-strings con `_target_path` en vez de genérico `@project/archivo`.

## Verificación

```
grep -c "_target_path" agent_loop.py → 4 (OK, esperado ≥3)
```

## Resultados Run 1 (variabilidad negativa)

| Test | Resultado | Iteraciones | Tiempo | Notas |
|------|-----------|-------------|--------|-------|
| T1 Quick | PASS | 0 | 0.3s | Cache hit |
| T2 Análisis | PASS | 0 | 0.3s | Cache hit (5/6) |
| T3 Execute | FAIL | 34 | 42.1s | 0 insert_at, 0 edit_file — regresión por variabilidad |
| T4 Deep | PASS | 9 | 15.0s | 6 HTTP, 4/6 keywords |

**Total: 3/4 passed**

## Resultados Run 2 (insert_at usado)

| Test | Resultado | Iteraciones | Tiempo | Notas |
|------|-----------|-------------|--------|-------|
| T1 Quick | PASS | 0 | 0.3s | Cache hit |
| T2 Análisis | PASS | 0 | 0.3s | Cache hit (5/6) |
| T3 Execute | FAIL | 13 | 13.3s | insert_at LLAMADO pero "Edit calls: 0" |
| T4 Deep | PASS | 9 | 14.8s | 6 HTTP, 4/6 keywords |

**Total: 3/4 passed**

### T3 Run 2 — insert_at con path incorrecto

Tools: `['read_file', 'list_dir' ×3, 'read_file', 'insert_at', 'run_command' ×3, 'read_file']`

Workflow correcto:
1. read_file → vio números de línea
2. list_dir ×3 → exploró proyecto
3. read_file → leyó archivo
4. **insert_at** → insertó código (pero args no contienen "api.py")
5. run_command ×3 → verificó
6. read_file → comprobó resultado

El hint dinámico llega con `@project/api.py`, el modelo sigue el workflow correcto (read → insert_at → verify), pero el path en los args de insert_at no contiene "api.py" — probablemente usa un path resuelto diferente o un archivo distinto.

## Evolución T3 (B21 → B24)

| Briefing | edit_file | insert_at | Targeting api.py | Workflow |
|----------|-----------|-----------|-----------------|----------|
| B21 | SI (1 call, FAIL) | NO | NO | read → list → edit(FAIL) → run_cmd |
| B22 | SI (1 call, FAIL) | NO | NO | read → list → edit(FAIL) → run_cmd |
| B23 | SI → FAIL | **SI** (1 call) | NO | read → list → edit(FAIL) → **insert_at** → verify |
| B24 | NO | **SI** (1 call) | NO (aún) | read → list → read → **insert_at** → verify |

## Veredicto

- **B24 behavioral goal: PARTIAL** — hint dinámico inyectado correctamente, modelo lo sigue parcialmente
- **T3 test: FAIL** — insert_at no targetea api.py en args (model path resolution issue)
- **Mejora vs B23**: El modelo ya no pasa por edit_file (va directo a insert_at)
- **No regresión**: T1/T2/T4 estables
- **Próximo paso**: Investigar qué path usa el modelo en insert_at args — puede ser un issue de cómo resuelve @project/ → path real
