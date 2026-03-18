# BRIEFING_26 — Post-insert_at finish force + disable finish gate

Fecha: 2026-03-18
Prerequisito: B25 (path auto-correction) deployed + committed

## Problema

T3 falla porque:
1. Modelo hace `insert_at` exitoso → loopea `read_file` × 40-49 → nunca llama `finish`
2. Incluso si llamara `finish` temprano, el **finish gate** lo rechazaría (`remaining_ratio > 0.8` y `successful_actions < 5`)

Dos problemas superpuestos = T3 imposible sin fix.

## Root cause

No hay ninguna señal post-insert_at que diga al modelo "ya terminaste, llama finish". El modelo interpreta el silencio como "sigue trabajando" y entra en loop de verificación (read_file).

## Fix (2 cambios en 1 bloque)

**Archivo**: `motor_v1_validation/agent/core/agent_loop.py`

Dentro del bloque `if tool_name in ("write_file", "edit_file", "insert_at") and not is_error:`, después de `recovery.record_write()`:

```python
# B26 — POST-INSERT_AT FINISH FORCE: after successful edit in execute mode,
# inject message forcing finish and disable finish gate
if exec_mode == "execute" and tool_name in ("insert_at", "edit_file", "write_file"):
    _finish_nudged = True  # Disable finish gate so model can finish immediately
    history.append({"role": "user", "content": (
        f"CÓDIGO INSERTADO CORRECTAMENTE en {fpath}. "
        f"Llama finish(result='Insertado código en {fpath}') AHORA. "
        f"NO leas más archivos. NO hagas más cambios. SOLO finish()."
    )})
```

### Mecánica

1. `_finish_nudged = True` → el finish gate (que rechaza finish si `remaining_ratio > 0.8` y `successful_actions < 5`) queda desactivado porque el gate solo actúa cuando `not _finish_nudged`
2. El mensaje inyectado fuerza al modelo a llamar `finish()` en la siguiente iteración en vez de loopear con `read_file`

### Impacto esperado

- T3 iterations: 40-49 → ~5-8 (read_file + insert_at + finish)
- T3 finish: NO → YES
- T3 edit_calls: 1 (ya logrado en B25 Run 3)
- T3 tool_calls <= 20: probable con iterations < 10

## Criterio de éxito

```
T3 PASS = done_evt is not None AND edit_calls > 0 AND len(tool_calls) <= 20
```

## Verificación

```bash
fly deploy --app chief-os-omni --remote-only
cd briefings && python3 test_validacion_modelos.py
```

Resultado → `results/B26_finish_force.md`

## Cadena causal B21→B26

| B# | Fix | T3 Estado |
|----|-----|-----------|
| B21 | translate_intent fix | Modelo usa edit_file por primera vez |
| B22 | TIP pasivo insert_at | Modelo ignora TIP |
| B23 | MODE_HINTS + redirect activo | insert_at usado por primera vez |
| B24 | Path dinámico en hint | Path incorrecto |
| B25 | Path auto-correction + SSE args fix | Edit calls: 1, pero no finish, 40+ iters |
| **B26** | **Finish force + disable gate** | **Pendiente** |
