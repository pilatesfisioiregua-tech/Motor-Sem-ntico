# BRIEFING_24 — Path dinámico en execute hint

**Objetivo**: Extraer `@project/XXX` del goal e inyectarlo en MODE_HINTS para que el modelo tenga el path exacto en las instrucciones, no un genérico `@project/archivo`.

**Diagnóstico**: B23 confirmó que el modelo sigue el workflow correcto (read → insert_at → verify) pero no apunta a `@project/api.py`. El hint actual dice `insert_at(@project/archivo, ...)` — genérico. El modelo ignora el path del goal y usa otro archivo.

**Cambio**: ~5 líneas en agent_loop.py.

---

## Paso 1: Extraer target path del goal e inyectarlo en el hint

**Archivo**: `motor_v1_validation/agent/core/agent_loop.py`

Buscar este bloque:

```python
    # Mode-specific hints — guían al modelo sobre QUÉ herramientas usar
    MODE_HINTS = {
        "execute": (
            "\n\nPROTOCOLO EXECUTE — sigue EXACTAMENTE estos pasos:\n"
            "1. read_file(@project/archivo) → verás números de línea\n"
            "2. Identifica la línea DESPUÉS de la cual insertar\n"
            "3. insert_at(@project/archivo, NUMERO_LINEA, código_nuevo)\n"
            "4. finish(result='descripción del cambio')\n"
            "IMPORTANTE: Usa insert_at, NO edit_file. insert_at es más fiable."
        ),
```

**Reemplazar con**:

```python
    # Mode-specific hints — guían al modelo sobre QUÉ herramientas usar
    # Extract @project/ path from goal for targeted hints (B24)
    import re as _re_hint
    _target_match = _re_hint.search(r'@project/[\w./\-]+', goal)
    _target_path = _target_match.group(0) if _target_match else "@project/archivo"

    MODE_HINTS = {
        "execute": (
            f"\n\nPROTOCOLO EXECUTE — sigue EXACTAMENTE estos pasos:\n"
            f"1. read_file('{_target_path}') → verás números de línea\n"
            f"2. Identifica la línea DESPUÉS de la cual insertar\n"
            f"3. insert_at('{_target_path}', NUMERO_LINEA, código_nuevo)\n"
            f"4. finish(result='descripción del cambio')\n"
            f"IMPORTANTE: Usa insert_at sobre {_target_path}. NO edit_file. NO otros archivos."
        ),
```

**Criterio paso 1**: `grep -c "_target_path" motor_v1_validation/agent/core/agent_loop.py` devuelve al menos 3.

---

## Paso 2: Deploy y test

```bash
fly deploy --app chief-os-omni --remote-only
```

```bash
cd briefings && python3 test_validacion_modelos.py
```

**Criterio T3 PASS**: 
- DIAG log muestra hint con `@project/api.py` (no genérico)
- insert_at args contiene `api.py`
- done_evt no es None (el modelo llama finish)

## Paso 3: Guardar resultado

`results/B24_path_dinamico.md` con:
- Hint que llegó al modelo (confirmar @project/api.py en él)
- insert_at args (confirmar api.py en path)
- PASS/FAIL por test
- Si T3 PASS → commit "B24: T3 PASS — 4/4 tests, dynamic path in execute hint"

## Rollback

Revertir a la versión genérica del hint si hay regresión.
