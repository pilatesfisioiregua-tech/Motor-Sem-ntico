# Prompt para siguiente sesión — Post B13 / Pre B14

## Situación

Code OS debugging: 8 capas de bugs resueltas (B07-B13). Score estable en 2/4.

| Test | B13 | Modelo usado | Problema |
|------|-----|-------------|----------|
| T1 read+report | ✅ CACHE HIT | — | — |
| T2 listar métodos | ✅ CACHE HIT | — | — |
| T3 crear endpoint | ❌ 0 edit_file, 6 iters | Devstral 2 | No escribe código |
| T4 diagnóstico HTTP | ❌ 1/6 kw, 24 iters, 7 err | Devstral 2 | No sintetiza |

B13 descartó tool overload (61→7-11 tools: mismo resultado). El problema es capacidad del modelo.

## Hipótesis B14

El router YA distingue modos (execute/analyze) pero todos apuntan a Devstral 2. V3.2 (`deepseek/deepseek-v3.2`) es más barato ($0.38 vs $2.00/M) y posiblemente mejor para tareas agentic generales. Probarlo como cerebro para execute+analyze.

## BRIEFING_14 listo para ejecutar

Archivo: `briefings/BRIEFING_14_cerebro_dual.md`

3 cambios:
1. `api.py` → añadir `cerebro_execute` y `cerebro_analyze` keys al tier_config (V3.2)
2. `router.py` → `select()` usa `_cerebro_execute` / `_cerebro_analyze` por modo
3. `test_validacion_modelos.py` → logging mejorado (qué tools llama T3/T4)

### Instrucciones para Claude Code

1. Leer `briefings/BRIEFING_14_cerebro_dual.md`
2. Aplicar los 3 cambios (api.py, router.py, test script)
3. Deploy + test completo
4. Guardar resultados en `results/test_modelos_cerebro_dual_b14.md`

### Criterio de éxito

- 3/4+ → Code OS operativo con cerebro dual
- T3 ✅ T4 ❌ → V3.2 escribe pero no sintetiza → probar Cogito para analyze
- T3 ❌ T4 ✅ → V3.2 sintetiza pero no escribe → investigar function calling
- 2/4 sin cambio → replantear: ¿el problema es el loop, no el modelo?

## Progresión completa

| B# | Fix | Score |
|----|-----|-------|
| B07 | Modelo Qwen3→Devstral 2 | 0/4 |
| B08 | Fix paths @project/ | 0/4 |
| B09 | Fix mochila loop | 1/4 |
| B10 | Tool filtering (roto por B11 bug) | 0/4 |
| B11 | Fix project_dir en registry | 1/4 |
| B12 | Nudges semánticos + AUTO_FINISH | 2/4 |
| B13 | Tool surface filter (61→7-11) | 2/4 (descarta tool overload) |
| B14 | Cerebro dual V3.2 execute+analyze | ⏳ |

## Stack actual

- Cerebro (quick/standard): `mistralai/devstral-2512`
- Cerebro execute+analyze (B14): `deepseek/deepseek-v3.2` (NUEVO)
- Evaluador: `z-ai/glm-5`
- Worker budget: `deepseek/deepseek-v3.2`
- Deploy: fly.io `chief-os-omni`

## Archivos clave

- **Briefing**: `briefings/BRIEFING_14_cerebro_dual.md`
- **Router**: `motor_v1_validation/agent/core/router.py`
- **API config**: `motor_v1_validation/agent/core/api.py`
- **Test**: `briefings/test_validacion_modelos.py`
- **Baseline**: `results/test_modelos_tool_filter_b13.md`
