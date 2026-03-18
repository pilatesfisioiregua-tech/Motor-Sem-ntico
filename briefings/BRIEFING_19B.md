# BRIEFING_19B — Formato D (pipeline como código) en execute hint

**Objetivo**: Reformatear el execute hint de prosa a formato D (P35: código para QUÉ HACER, natural para QUÉ PENSAR) y verificar si T3 pasa con Devstral 2.

**Contexto**: EXP-11 demostró que D_híbrido (91% cobertura, 100% adherencia) supera a todos los demás formatos. El execute hint actual es prosa libre. Reformatearlo como pipeline-código podría hacer que Devstral 2 (que es modelo de coding) siga las instrucciones de edición.

**Hipótesis**: Devstral 2 entiende código mejor que prosa. Si le damos las instrucciones en formato de código (plan como array de steps con tool names explícitos), es más probable que invoque edit_file.

## Paso 1: Cambiar MODE_HINTS["execute"] en agent_loop.py

**Archivo**: `motor_v1_validation/agent/core/agent_loop.py`

**Antes**:
```python
    MODE_HINTS = {
        "execute": (
            "\n\nPROTOCOLO EXECUTE: Esta tarea requiere MODIFICAR CÓDIGO. "
            "Flujo obligatorio: "
            "1) read_file(@project/archivo) para ver el código actual, "
            "2) edit_file(@project/archivo, old_string, new_string) para hacer cambios, "
            "3) run_command() o finish() para verificar/completar."
        ),
```

**Después**:
```python
    MODE_HINTS = {
        "execute": (
            "\n\n```python\n"
            "# PROTOCOLO EXECUTE — sigue este pipeline exacto:\n"
            "pipeline = [\n"
            "    {'step': 1, 'tool': 'read_file',  'args': {'path': '@project/<archivo_objetivo>'}},\n"
            "    {'step': 2, 'tool': 'edit_file',  'args': {'path': '@project/<archivo_objetivo>', 'old_string': '<código_actual>', 'new_string': '<código_nuevo>'}},\n"
            "    {'step': 3, 'tool': 'finish',     'args': {'result': '<resumen de cambios realizados>'}},\n"
            "]\n"
            "# IMPORTANTE: edit_file es OBLIGATORIO. Sin edit_file = tarea fallida.\n"
            "# old_string debe ser una copia EXACTA del código actual (usa read_file primero).\n"
            "```"
        ),
```

**Criterio**: `grep -c "pipeline = " motor_v1_validation/agent/core/agent_loop.py` devuelve 1.

## Paso 2: Desplegar a fly.io

```bash
fly deploy --app chief-os-omni
```

**Criterio**: Health check OK.

## Paso 3: Ejecutar T3

```bash
cd briefings && python3 test_validacion_modelos.py
```

**Criterio de éxito T3**: Al menos 1 `edit_file` en `api.py` y test PASS.

## Paso 4: Guardar resultado

Guardar output en `results/B19B_formato_d_hint.md` con:
- Confirmar que exec_mode=execute en logs DIAG
- Confirmar que el hint formato D llegó al modelo
- Número de iteraciones
- Tools llamados (¿apareció edit_file?)
- PASS/FAIL
- Si FAIL: qué hizo el modelo — ¿mismo patrón (db_query alucinado) o diferente?

## Rollback (si falla)

Revertir MODE_HINTS["execute"] al valor anterior (prosa) y redesplegar.

## Nota sobre paralelismo

Este briefing es INDEPENDIENTE de B19A. NO cambiar el modelo cerebro_execute — mantener Devstral 2. Solo cambiar el hint. Si se ejecuta en paralelo con B19A, cada uno en su propia sesión de Claude Code.
