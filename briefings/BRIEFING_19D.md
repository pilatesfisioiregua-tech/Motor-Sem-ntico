# BRIEFING_19D — Cogito-671b + prompt dinámico (re-test limpio)

**Objetivo**: Re-probar Cogito-671b como cerebro_execute AHORA que el system prompt dinámico (B19C) está aplicado.

**Por qué**: B19A fue inválido — Cogito corrió contra el prompt viejo que listaba db_query como tool disponible. Cogito alucinó db_query x4, exactamente como Devstral. B19C eliminó esa alucinación (db_query 3→0 en Devstral). Cogito merece un test limpio.

**Hipótesis**: Cogito-671b con prompt dinámico leerá el archivo (como ya hace Devstral post-B19C) Y completará edit_file (que Devstral no hace). Si esto ocurre, T3 pasa y Cogito se convierte en cerebro_execute definitivo.

## Paso 1: Cambiar modelo en api.py

**Archivo**: `motor_v1_validation/agent/core/api.py`

**Antes**:
```python
        "cerebro_execute": "mistralai/devstral-2512",         # B16: Devstral 2 para execute (V3.2 no usa filesystem)
```

**Después**:
```python
        "cerebro_execute": "deepcogito/cogito-v2.1-671b",    # B19D: Cogito re-test con prompt dinámico (B19C)
```

**Criterio**: `grep -c "cogito-v2.1-671b" motor_v1_validation/agent/core/api.py` devuelve 1.

## Paso 2: Desplegar a fly.io

```bash
fly deploy --app chief-os-omni
```

**Criterio**: `curl -s https://chief-os-omni.fly.dev/health | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['status'])"` devuelve "ok".

## Paso 3: Ejecutar SOLO T3

```bash
cd briefings && python3 test_validacion_modelos.py
```

Observar específicamente:
- `[DIAG:B18]` line → confirmar exec_mode=execute, tools incluyen edit_file, NO incluyen db_query
- ¿Cogito llama read_file? (esperado: SÍ, como Devstral post-B19C)
- ¿Cogito llama edit_file? (esto es lo que falta)
- ¿Cogito alucina alguna tool? (no debería con prompt dinámico)

**Criterio de éxito T3**: Al menos 1 `edit_file` en `api.py` y test PASS.

## Paso 4: Guardar resultado

Guardar output completo en `results/B19D_cogito_prompt_dinamico.md` con:
- Modelo confirmado (Cogito en logs)
- Tools DIAG line (confirmar prompt dinámico activo)
- db_query alucinados: esperar 0
- edit_file llamados: esperar ≥1
- Secuencia de tools completa
- PASS/FAIL
- Si FAIL: descripción exacta de qué hizo el modelo después de read_file

## Paso 5: Decisión post-resultado

- **Si PASS**: Mantener Cogito como cerebro_execute. Commit con mensaje "B19D: Cogito-671b as cerebro_execute — T3 PASS".
- **Si FAIL con edit_file=0 pero read_file>0**: El modelo lee pero no edita. Revertir a Devstral 2. El problema es más profundo que el modelo — puede ser el execute hint o la estructura del goal.
- **Si FAIL con tools alucinadas**: Bug en prompt dinámico. Revertir y reportar.

## Rollback (si falla)

```python
        "cerebro_execute": "mistralai/devstral-2512",         # B16: Devstral 2 para execute (V3.2 no usa filesystem)
```
Y redesplegar.
