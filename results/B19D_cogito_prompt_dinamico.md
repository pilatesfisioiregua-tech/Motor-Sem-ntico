# B19D — Cogito-671b + prompt dinámico (re-test limpio)

Fecha: 2026-03-18
Base URL: https://chief-os-omni.fly.dev
Version: 3.4.0

## Cambio aplicado

`cerebro_execute` cambiado de `mistralai/devstral-2512` a `deepcogito/cogito-v2.1-671b` en `api.py`.

## DIAG confirmado

```
exec_mode=execute | tools_count=8 | safety_net=NO
tools=['read_file', 'write_file', 'edit_file', 'list_dir', 'run_command', 'finish', 'mochila', 'http_request']
```

Prompt dinámico (B19C) activo. `db_query` NO en tools.

## Resultado T3

| Test | Resultado | Iteraciones | Tiempo | Errores |
|------|-----------|-------------|--------|---------|
| T3 Execute (crear endpoint) | **FAIL** | 7 | 14.8s | 0 |

**Tools llamados**: `['mochila', 'http_request', 'http_request', 'http_request', 'http_request', 'http_request', 'http_request']`

- edit_file: **0** (criterio: >=1)
- read_file: **0**
- list_dir: **0**
- db_query alucinado: **0** (prompt dinámico funciona)

## Comparación Devstral post-B19C vs Cogito post-B19D

| Métrica | Devstral (B19C) | Cogito (B19D) |
|---------|-----------------|---------------|
| db_query alucinado | 0 | 0 |
| read_file usado | **SI** | NO |
| list_dir usado | **SI** (5+) | NO |
| edit_file usado | NO | NO |
| http_request spam | parcial (algunos) | **SI** (6/7 tools) |
| Iteraciones | 51 | 7 |
| Resultado | FAIL | FAIL |

## Análisis

### Cogito peor que Devstral post-B19C

Cogito con prompt dinámico:
- **No usa filesystem tools** — ni read_file ni list_dir. Regresión vs Devstral que sí los usa.
- **Spam de http_request** — 6 de 7 tool calls son http_request. El modelo no interpreta que debe usar filesystem tools para editar archivos locales.
- **Solo 7 iteraciones** — el modelo se detiene rápido sin completar la tarea.

### Hipótesis B19D refutada

La hipótesis era: "Cogito con prompt dinámico leerá el archivo Y completará edit_file".
Resultado: Cogito no lee ni edita. El modelo es peor que Devstral para tareas de edición de archivos en este contexto.

## Decisión

Per B19D paso 5: **FAIL con edit_file=0 y read_file=0** (peor que el caso contemplado de read_file>0).

**Acción: ROLLBACK a Devstral 2** — Cogito no es viable como cerebro_execute.

Devstral 2 sigue siendo el mejor modelo disponible para execute mode:
- Con prompt dinámico (B19C) usa filesystem tools correctamente
- No alucina tools
- No completa edit_file, pero al menos explora el código

El problema de T3 no es del modelo — requiere investigación más profunda del flujo execute.
