# B19B — Formato D (pipeline como código) en execute hint

Fecha: 2026-03-18T16:00:33
Base URL: https://chief-os-omni.fly.dev
Version: 3.4.0

## Cambio aplicado

MODE_HINTS["execute"] cambiado de prosa a formato D (pipeline como código Python):
```python
pipeline = [
    {'step': 1, 'tool': 'read_file',  'args': {'path': '@project/<archivo_objetivo>'}},
    {'step': 2, 'tool': 'edit_file',  'args': {'path': '@project/<archivo_objetivo>', ...}},
    {'step': 3, 'tool': 'finish',     'args': {'result': '<resumen>'}},
]
# IMPORTANTE: edit_file es OBLIGATORIO. Sin edit_file = tarea fallida.
```

## Diagnóstico DIAG:B18

```
exec_mode=execute | tools_count=8 | safety_net=NO
tools=['read_file', 'write_file', 'edit_file', 'list_dir', 'run_command', 'finish', 'mochila', 'http_request']
```

- exec_mode=execute: CORRECTO
- safety_net=NO: CORRECTO (8 tools bien filtrados)
- edit_file en los schemas: SI

## Resultado T3

| Test | Resultado | Iteraciones | Tiempo | Errores |
|------|-----------|-------------|--------|---------|
| T3 Execute (crear endpoint) | FAIL | 7 | 17.9s | 1 |

**Tools llamados**: `['mochila', 'http_request', 'http_request', 'http_request', 'db_query', 'db_query', 'db_query']`

- edit_file llamado: **NO** (0 veces)
- read_file llamado: **NO** (0 veces)
- db_query llamado: 3 veces (NO está en los 8 schemas — tool alucinado)

## Análisis

**Mismo patrón exacto que B18 sin el hint formato D.** El modelo (Devstral 2):
1. Ignora completamente el pipeline hint en formato código
2. No intenta read_file ni edit_file
3. Alucina tool calls fuera del schema (db_query)
4. Se limita a mochila + http_request + db_query

**Comparación B18 vs B19B:**

| Métrica | B18 (hint prosa) | B19B (hint formato D) |
|---------|------------------|-----------------------|
| edit_file | 0 | 0 |
| read_file | 0 | 0 |
| db_query (alucinado) | 2 | 3 |
| Iteraciones | 6 | 7 |
| Tiempo | 368.5s | 17.9s |
| Resultado | FAIL | FAIL |

El tiempo mucho menor (17.9s vs 368.5s) sugiere que el modelo respondió más rápido pero con el mismo patrón erróneo.

## Conclusión

**El formato D en el hint NO resuelve el problema.** La hipótesis de que Devstral 2 entendería mejor instrucciones en formato código era incorrecta. El modelo no está leyendo ni procesando el hint — su comportamiento es idéntico independientemente del formato.

**El problema es de capacidad del modelo**, no de formato del prompt. Devstral 2 no es capaz de:
- Seguir instrucciones de tool calling
- Respetar los schemas de tools ofrecidos
- Ejecutar un flujo read→edit→finish

**Próximo paso**: Cambiar el modelo cerebro para execute (B19A), no el formato del hint.

## Rollback

Revertir MODE_HINTS["execute"] al valor anterior (prosa) ya que el formato D no aporta mejora.
