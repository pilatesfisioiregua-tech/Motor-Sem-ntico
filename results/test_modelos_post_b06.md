# Test Validación Modelos — Post BRIEFING_06

Fecha: 2026-03-18T00:05:05
Base URL: https://chief-os-omni.fly.dev

Version: 3.4.0
Tools: 61

## Modelos en uso

```json
{
  "version": "3.4.0",
  "briefings_implementados": [
    "SN-00: Schema verification",
    "SN-01: Seed matriz",
    "SN-02: Config models",
    "SN-03: Telemetria",
    "SN-04: Gestor basico",
    "SN-05: Mejora continua",
    "SN-06: Registrador PID",
    "SN-07: Gestor GAMC",
    "SN-08: Constraint Manifold (13 reglas)",
    "SN-09: Motor vN SFCE",
    "SN-10: Flywheel + Autopoiesis",
    "SN-11: Reactor vN",
    "SN-12: Gestor Pasos 8-10",
    "SN-13: Sinema",
    "SN-14: Propagacion",
   
```

## Resultados

| Test | Resultado | Iteraciones | Tiempo | Errores | Notas |
|------|-----------|-------------|--------|---------|-------|
| T1 Quick (read+report) | ✅ PASS | 0 | 7.3s | 0 | Tools: [] / Summary: No pude completar la tarea tras 0 pasos. Razon: API_FAILURE |
| T2 Análisis (listar métodos) | ❌ FAIL | 0 | 7.0s | 0 | Métodos encontrados: 0/6 |
| T3 Execute (crear endpoint) | ❌ FAIL | 0 | 6.8s | 0 | Edit calls: 0 / Total tools: 0 |
| T4 Deep (diagnóstico) | ❌ FAIL | 0 | 6.5s | 0 | HTTP calls: 0 / Keywords diagnóstico: 0/6 |

**Total: 1/4 passed**

## Diagnóstico

**❌ T1-T2 fallaron** → el cerebro no sirve ni para tareas básicas → CAMBIAR MODELO

## Detalle por test

### T1 Quick (read+report)
- Resultado: PASS
- Iteraciones: 0
- Tiempo: 7.3s
- Errores: 0
- Notas: Tools: [] | Summary: No pude completar la tarea tras 0 pasos. Razon: API_FAILURE: API failed after 3 tries: OpenRouter HT

### T2 Análisis (listar métodos)
- Resultado: FAIL
- Iteraciones: 0
- Tiempo: 7.0s
- Errores: 0
- Notas: Métodos encontrados: 0/6

### T3 Execute (crear endpoint)
- Resultado: FAIL
- Iteraciones: 0
- Tiempo: 6.8s
- Errores: 0
- Notas: Edit calls: 0 | Total tools: 0

### T4 Deep (diagnóstico)
- Resultado: FAIL
- Iteraciones: 0
- Tiempo: 6.5s
- Errores: 0
- Notas: HTTP calls: 0 | Keywords diagnóstico: 0/6

