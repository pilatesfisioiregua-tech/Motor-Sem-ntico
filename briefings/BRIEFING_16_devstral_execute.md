# BRIEFING_16 — Devstral 2 + Execute Hint para T3

## Contexto

B14: V3.2 resolvió T4 (5/6 keywords). B15: execute hint no movió T3 porque V3.2 nunca toca filesystem — sesgo fijo hacia http/db.

Observación: **Devstral 2 + execute hint nunca se ha probado.** Devstral 2 ya usa `read_file` (T1/T2 ✅). Es modelo de coding. El hint le dice `read_file → edit_file → finish`. Combinación no testeada.

V3.2 para analyze funciona (B14). No tocar.

## Qué hacer

### Paso 1 — Cambiar cerebro_execute a Devstral 2

Archivo: `motor_v1_validation/agent/core/api.py`

En `get_tier_config()`:

**ANTES:**
```python
        "cerebro_execute": "deepseek/deepseek-v3.2",
```

**DESPUÉS:**
```python
        "cerebro_execute": "mistralai/devstral-2512",
```

Solo esa línea. `cerebro_analyze` queda como V3.2.

### Paso 2 — Deploy y test

```bash
cd /Users/jesusfernandezdominguez/omni-mind-cerebro
fly deploy --config motor-semantico/motor_v1_validation/agent/fly.toml \
           --dockerfile motor-semantico/motor_v1_validation/agent/Dockerfile

python3 motor-semantico/briefings/test_validacion_modelos.py \
    --output motor-semantico/results/test_modelos_devstral_execute_b16.md
```

## Criterio de éxito

| Test | B15 | Target B16 |
|------|-----|------------|
| T1 | ✅ CACHE | ✅ (no regresión) |
| T2 | ✅ CACHE | ✅ (no regresión) |
| T3 | ❌ 0 edit_file (V3.2) | ✅ ≥1 edit_file (Devstral 2 + hint) |
| T4 | ✅ 5/6 kw (V3.2) | ✅ (no regresión — V3.2 sigue en analyze) |

**4/4 → Code OS operativo. Stack final:**
- Quick/standard: Devstral 2 (cerebro default)
- Execute: Devstral 2 + execute hint
- Analyze: V3.2
- Evaluador: GLM-5

**T3 sigue ❌ → Devstral 2 tampoco escribe con hint. Opciones restantes:**
- Cogito-671b como cerebro_execute ($5/M — caro pero mejor razonamiento)
- Replantear: quizá el problema es cómo `edit_file` está registrado (schema, descripción, parámetros)
- Inspeccionar el schema de edit_file que recibe el modelo para verificar que es correcto
