# BRIEFING_25 — Path auto-correction en execute mode

**Cambio YA aplicado** por Opus Chat en `motor_v1_validation/agent/core/agent_loop.py`:

Path auto-correction: en execute mode, si insert_at/edit_file/write_file/read_file recibe un path sin `@project/` prefix (ej: `api.py` en vez de `@project/api.py`), se prepend automáticamente.

## Verificar

```bash
grep -c "PATH AUTO-CORRECTION" motor_v1_validation/agent/core/agent_loop.py
# Esperado: 1
```

## Deploy + test

```bash
fly deploy --app chief-os-omni --remote-only
cd briefings && python3 test_validacion_modelos.py
```

## Criterio T3 PASS

- insert_at args contiene `api.py` (con o sin @project/ prefix, el auto-correction lo arregla)
- done_evt no es None
- edit_calls > 0

Si T3 PASS → commit "B25: T3 PASS — path auto-correction in execute mode"

Guardar en `results/B25_path_autocorrect.md`.
