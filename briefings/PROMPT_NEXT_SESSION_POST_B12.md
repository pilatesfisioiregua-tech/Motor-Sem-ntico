# Prompt para siguiente sesión — Post B12 / Pre B13

## Situación

Code OS debugging: 7 capas de bugs resueltas (B07-B12). Score: 0/4 → 2/4.

| Test | B12 | Problema |
|------|-----|----------|
| T1 read+report | ✅ 3 iters, 12s | — |
| T2 listar métodos | ✅ 1 iter, 23s, 5/6 | — |
| T3 crear endpoint | ❌ 0 edit_file en 6 iters | Modelo no escribe código |
| T4 diagnóstico HTTP | ❌ 1/6 keywords, 50 iters, 7 err | Modelo no sintetiza |

## Hipótesis activa

El modelo (Devstral 2) recibe 61 tool schemas via API pero solo necesita 7-11. Se pierde en el ruido. El system prompt lista 8 tools, pero `registry.get_schemas()` envía las 61 completas.

Evidencia: B10 probó reducir tools pero con el bug de `project_dir` (B11) aún presente → resultado inválido.

## BRIEFING_13 listo para ejecutar

Archivo: `briefings/BRIEFING_13_tool_surface_filter.md`

Cambio: una sola edición en `agent_loop.py` — línea donde está `tool_schemas = registry.get_schemas()`. Usar `registry.get_schemas(names=active_tools)` con sets por modo (quick=7, standard=10, deep=12). `get_schemas()` ya acepta el parámetro `names`.

### Instrucciones para Claude Code

1. Leer `briefings/BRIEFING_13_tool_surface_filter.md`
2. Aplicar el cambio EXACTO descrito en Paso 1 a `motor_v1_validation/agent/core/agent_loop.py`
3. Deploy a fly.io (desde `omni-mind-cerebro/` con `--dockerfile motor-semantico/motor_v1_validation/agent/Dockerfile`)
4. Ejecutar `python3 motor-semantico/briefings/test_validacion_modelos.py --output motor-semantico/results/test_modelos_tool_filter_b13.md`
5. Guardar resultados

### Criterio de éxito

- T1+T2: ✅ (no regresión)
- T3: ≥1 llamada a edit_file en api.py
- T4: ≥2/6 keywords de diagnóstico
- **3/4+ → Code OS operativo. Documentar como Principio 33.**
- **2/4 sin cambio → Devstral 2 no puede escribir/sintetizar. Siguiente: cerebro dual.**

## Si B13 falla (plan B)

Cerebro dual: Devstral 2 para lectura/análisis, modelo pesado (Cogito-671b o V3.2) para escritura/síntesis. Implementar en `SmartRouter` — clasificar goal como "read" vs "write" y seleccionar cerebro según tipo.

## Segundo tema pendiente: Sesiones como red neuronal

Diseño listo en `docs/operativo/sesiones/DISENO_SESIONES_COMO_RED.md`. Implementar como primer task real de Code OS cuando pase ≥3/4 tests.

## Archivos clave

- **Briefing a ejecutar**: `briefings/BRIEFING_13_tool_surface_filter.md`
- **Archivo a editar**: `motor_v1_validation/agent/core/agent_loop.py` (buscar `tool_schemas = registry.get_schemas()`)
- **Registry**: `motor_v1_validation/agent/tools/__init__.py` — `get_schemas(names=set)` ya existe
- **Test**: `briefings/test_validacion_modelos.py`
- **Resultados previos**: `results/test_modelos_nudge_semantico_b12.md` (baseline)
- **Progresión completa**: B07→B12 en tabla arriba

## Stack

- Cerebro + Worker: `mistralai/devstral-2512`
- Evaluador: `z-ai/glm-5`
- Worker budget: `deepseek/deepseek-v3.2`
- Deploy: fly.io `chief-os-omni`
- `CODE_OS_PROJECT_DIR=/app`
