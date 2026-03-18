# B25 — Path auto-correction en execute mode

Fecha: 2026-03-18
Base URL: https://chief-os-omni.fly.dev
Version: 3.4.0

## Cambios

### 1. PATH AUTO-CORRECTION (ya aplicado por Opus Chat)
En execute mode, si insert_at/edit_file/write_file/read_file recibe un path sin `@project/` prefix, se prepend automáticamente.

```python
# PATH AUTO-CORRECTION — execute mode: prepend @project/ if missing (B25)
if exec_mode == "execute" and tool_name in ("insert_at", "edit_file", "write_file", "read_file"):
    _path = tool_args.get("path", "")
    if _path and not _path.startswith("@project/") and not _path.startswith("/"):
        tool_args["path"] = f"@project/{_path}"
```

### 2. FIX CRÍTICO: Args en SSE events (descubierto en B25)

**Root cause de "Edit calls: 0" en TODOS los briefings B21-B24**: el SSE event de `tool_call` enviaba `"args": {}` — args vacíos SIEMPRE. El test busca `"api.py" in str(args)` pero args era `{}` → nunca podía pasar.

**Fix en 2 archivos**:
- `agent_loop.py`: incluir `tool_args` (truncado a 200 chars) en el log
- `api.py`: reenviar `entry.get("args", {})` en vez de `{}` hardcodeado

## Verificación

```
grep -c "PATH AUTO-CORRECTION" agent_loop.py → 1 ✓
```

## Resultados

### Run 1 (fresh deploy — IncompleteRead)
| Test | Resultado | Notas |
|------|-----------|-------|
| T1 | PASS | Cache hit |
| T2 | PASS | Cache hit |
| T3 | FAIL | IncompleteRead — transient |
| T4 | FAIL | 0/6 keywords (cold start) |

### Run 2 (warm — insert_at con args!)
| Test | Resultado | Iters | Tiempo | Notas |
|------|-----------|-------|--------|-------|
| T1 | PASS | 0 | 0.2s | Cache hit |
| T2 | PASS | 0 | 0.2s | Cache hit |
| T3 | FAIL | 32 | 47.1s | insert_at llamado, Edit calls: 0 (pre-fix args) |
| T4 | PASS | 9 | 23.1s | 2/6 keywords |

### Run 3 (con fix args — **Edit calls: 1!**)
| Test | Resultado | Iters | Tiempo | Notas |
|------|-----------|-------|--------|-------|
| T1 | PASS | 0 | 0.7s | Cache hit |
| T2 | PASS | 0 | 0.3s | Cache hit |
| T3 | FAIL | 40 | 69.5s | **Edit calls: 1** — args ahora visibles, api.py detectado! |
| T4 | PASS | 9 | 14.0s | 3/6 keywords |

### Run 4 (variabilidad negativa)
| Test | Resultado | Iters | Tiempo | Notas |
|------|-----------|-------|--------|-------|
| T1 | PASS | 0 | 0.2s | Cache hit |
| T2 | PASS | 0 | 0.2s | Cache hit |
| T3 | FAIL | 49 | 75.2s | 0 insert_at — modelo en loop de read_file |
| T4 | PASS | 9 | 21.4s | **5/6 keywords** — mejor resultado T4 |

**Total mejor run: 3/4 passed**

## Hallazgos clave

### Edit calls: 1 — primera vez DETECTABLE
Run 3 es la primera vez que el test harness detecta un edit call targeting api.py. Los runs anteriores (B21-B24) probablemente también tenían insert_at en api.py, pero el bug de args vacíos impedía la detección.

### T3 criterios faltantes
Para T3 PASS necesita:
1. ✅ `edit_calls > 0` — logrado en Run 3
2. ❌ `done_evt is not None` — modelo no llama finish (loop infinito)
3. ❌ `len(tool_calls) <= 20` — 40-49 iterations

### Problema residual: modelo no llama finish
El modelo entra en loops de read_file (49 iterations en Run 4). El MODE_HINTS dice "finish(result='...')" pero el modelo no lo sigue consistentemente. Devstral 2 variability.

## Evolución T3 (B21 → B25)

| Briefing | edit_file | insert_at | Args visibles | api.py en args | finish |
|----------|-----------|-----------|---------------|----------------|--------|
| B21-B24 | variable | variable | **NO** (bug) | imposible saber | raro |
| B25 Run3 | NO | **SI** | **SI** (fix) | **SI** (1 call) | NO |
| B25 Run4 | NO | NO | SI | NO (no insert_at) | NO |

## Veredicto

- **B25 critical discovery: SSE args bug** — args nunca se enviaban, test nunca podía detectar targeting
- **PATH AUTO-CORRECTION: WORKING** — cuando el modelo llama insert_at, el path se corrige
- **T3: FAIL** — Edit calls: 1 logrado pero modelo no llama finish y usa 40+ iterations
- **T4: BEST EVER** — 5/6 keywords en Run 4
- **Próximo paso**: forzar finish en execute mode tras insert_at exitoso, o limitar iterations
