# BRIEFING_19A — Cogito-671b como cerebro_execute

**Objetivo**: Cambiar el modelo de `cerebro_execute` de Devstral 2 a Cogito-671b y verificar si T3 pasa.

**Contexto**: B18 confirmó que la infraestructura está perfecta (exec_mode=execute, 8 tools filtrados, safety_net=NO). El problema es que Devstral 2 no sigue instrucciones de editar código — alucina tool calls fuera del schema (db_query). Cogito-671b ($5/M) tiene mejor razonamiento y podría seguir instrucciones de edición.

## Paso 1: Cambiar modelo en api.py

**Archivo**: `motor_v1_validation/agent/core/api.py`

**Antes**:
```python
        "cerebro_execute": "mistralai/devstral-2512",         # B16: Devstral 2 para execute (V3.2 no usa filesystem)
```

**Después**:
```python
        "cerebro_execute": "deepcogito/cogito-v2.1-671b",    # B19A: Cogito-671b — mejor razonamiento para follow instructions
```

**Criterio**: `grep -c "cogito-v2.1-671b" motor_v1_validation/agent/core/api.py` devuelve 1.

## Paso 2: Desplegar a fly.io

```bash
fly deploy --app chief-os-omni
```

**Criterio**: `curl -s https://chief-os-omni.fly.dev/health | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['status'])"` devuelve "ok".

## Paso 3: Ejecutar T3

```bash
cd briefings && python3 test_validacion_modelos.py --test 3
```

Si `--test` no existe como flag, ejecutar todo:
```bash
cd briefings && python3 test_validacion_modelos.py
```

**Criterio de éxito T3**: El log muestra al menos 1 `edit_file` en `api.py` y el test reporta PASS.

## Paso 4: Guardar resultado

Guardar output completo en `results/B19A_cogito_execute.md` con:
- Modelo usado (confirmar que es Cogito en los logs)
- Número de iteraciones
- Tools llamados
- PASS/FAIL
- Si FAIL: qué hizo el modelo en vez de edit_file

## Rollback (si falla)

Revertir api.py al valor anterior:
```python
        "cerebro_execute": "mistralai/devstral-2512",         # B16: Devstral 2 para execute (V3.2 no usa filesystem)
```
Y redesplegar.
