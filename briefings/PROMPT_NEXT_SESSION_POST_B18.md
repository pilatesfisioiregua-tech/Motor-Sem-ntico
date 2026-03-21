# Prompt para siguiente sesión — Post B18 + EXP-11/11.1

## Resumen de esta sesión (18-Mar-2026, sesión 2)

### Code OS: 3/4 tests (B07→B18)

| Test | Estado | Modelo | Modo |
|------|--------|--------|------|
| T1 read+report | ✅ CACHE HIT | — | — |
| T2 listar métodos | ✅ CACHE HIT | — | — |
| T3 crear endpoint | ❌ 0 edit_file | Devstral 2 | execute (confirmado B18) |
| T4 diagnóstico HTTP | ✅ 5/6 kw, 9 iters | V3.2 | analyze |

**B18 diagnóstico confirmó**: exec_mode=execute, 8 tools filtrados, safety_net=NO. Infraestructura perfecta. El modelo (Devstral 2) no sigue instrucciones de editar código — alucina tool calls fuera del schema (db_query). Es problema de capacidad del modelo, no de stack.

**Stack actual desplegado:**
- Cerebro quick/standard: Devstral 2
- Cerebro execute: Devstral 2 (con execute hint)
- Cerebro analyze: V3.2
- Evaluador: GLM-5
- Worker budget: V3.2

### EXP-11 + 11.1: Formato de prompt (COMPLETADO)

**Resultado**: D_híbrido = formato canónico. Pipeline como código + preguntas en natural.

| Formato | Cobertura | Depth | Adherencia |
|---------|-----------|-------|------------|
| D_hibrido | 91% | 21% | 100% |
| G_metafora | 70% | 32% | 100% |
| B_json | 74% | — | 100% |
| A_natural | 61% | — | 100% |
| E_program | 57% | — | 17% |

**Principio 35 (CR0)**: Código para QUÉ HACER, natural para QUÉ PENSAR.
**Documento canónico**: `docs/L0/FORMATO_CANONICO_PROMPT.md`

### Documentos creados/actualizados esta sesión

- `briefings/BRIEFING_13` a `BRIEFING_18` — Tool filter, cerebro dual, execute hint, devstral execute, fix detect_mode, diagnóstico runtime
- `docs/sistema/EXP11_FORMATO_PROMPT_DISENO.md` — Diseño + resultados EXP-11 y 11.1
- `docs/L0/FORMATO_CANONICO_PROMPT.md` — **NUEVO**: Formato canónico del Generador con templates, anti-patrones, composición
- `briefings/exp11_formato_prompt_piloto.py` — Script EXP-11
- `briefings/exp11_1_ambiguedad_estructurada.py` — Script EXP-11.1
- `results/exp11_piloto.md` + `.json` — Resultados EXP-11
- `results/exp11_1_ambiguedad.md` + `.json` — Resultados EXP-11.1
- Ambos `INDICE_VIVO.md` actualizados

## Siguiente paso: T3

T3 es el último test pendiente. Opciones no probadas (en orden de ROI):

1. **Cogito-671b como cerebro_execute** ($5/M). Mejor razonamiento, puede que siga instrucciones de editar código. Cambio: 1 línea en `api.py`.

2. **Formato D aplicado al execute hint**. Actualmente el hint es prosa. Reformatearlo como pipeline código:
```python
plan = [
    {"step": 1, "tool": "read_file", "args": "@project/api.py"},
    {"step": 2, "tool": "edit_file", "target": "@project/api.py"},
    {"step": 3, "tool": "finish"},
]
```
Esto aplica P35 al problema de T3.

3. **Ambos en paralelo** — Cogito + formato D hint.

## Archivos clave

- Agent loop: `motor_v1_validation/agent/core/agent_loop.py`
- Router: `motor_v1_validation/agent/core/router.py` (detect_mode ya fixeado)
- API config: `motor_v1_validation/agent/core/api.py` (tier_config)
- Filesystem tools: `motor_v1_validation/agent/tools/filesystem.py`
- Test: `briefings/test_validacion_modelos.py`
- Formato canónico: `docs/L0/FORMATO_CANONICO_PROMPT.md`

## Progresión completa B07→B18

| B# | Fix | Score |
|----|-----|-------|
| B07 | Modelo Qwen3→Devstral 2 | 0/4 |
| B08 | Fix paths @project/ | 0/4 |
| B09 | Fix mochila loop | 1/4 |
| B10 | Tool filtering (roto por B11 bug) | 0/4 |
| B11 | Fix project_dir en registry | 1/4 |
| B12 | Nudges semánticos + AUTO_FINISH | 2/4 |
| B13 | Tool surface filter (61→7-11) | 2/4 |
| B14 | Cerebro dual V3.2 analyze | 3/4 (T4 resuelto) |
| B15 | Execute hint (prosa) | 3/4 (T3 sin cambio — V3.2) |
| B16 | Devstral 2 execute | 3/4 (T3 sin cambio — detect_mode bug) |
| B17 | Fix detect_mode | 3/4 (T3 sin cambio — confirmado execute) |
| B18 | Diagnóstico runtime | 3/4 (infra OK, modelo incapaz) |
