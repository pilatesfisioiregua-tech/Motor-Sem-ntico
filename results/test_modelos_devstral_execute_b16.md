# Test Validación Modelos — Post BRIEFING_06

Fecha: 2026-03-18T12:31:40
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
| T1 Quick (read+report) | ✅ PASS | 0 | 0.8s | 0 | Tools: [] / Summary: No pude completar la tarea tras 0 pasos. Razon: CACHE_HIT.  |
| T2 Análisis (listar métodos) | ✅ PASS | 0 | 0.3s | 0 | Métodos encontrados: 5/6 |
| T3 Execute (crear endpoint) | ❌ FAIL | 8 | 14.8s | 1 | Edit calls: 0 / Total tools: 8 / Tools: ['mochila', 'http_request', 'http_reques |
| T4 Deep (diagnóstico) | ✅ PASS | 9 | 22.5s | 0 | HTTP calls: 6 / Keywords diagnóstico: 3/6 / Tools: ['mochila', 'http_request', ' |

**Total: 3/4 passed**

## Diagnóstico

**⚠️ T1-T2 pasan pero T3-T4 fallan** → capacidad parcial → EVALUAR cambio de cerebro

## Detalle por test

### T1 Quick (read+report)
- Resultado: PASS
- Iteraciones: 0
- Tiempo: 0.8s
- Errores: 0
- Notas: Tools: [] | Summary: No pude completar la tarea tras 0 pasos. Razon: CACHE_HIT. | [CACHE HIT: cache_exact] La función get

### T2 Análisis (listar métodos)
- Resultado: PASS
- Iteraciones: 0
- Tiempo: 0.3s
- Errores: 0
- Notas: Métodos encontrados: 5/6

### T3 Execute (crear endpoint)
- Resultado: FAIL
- Iteraciones: 8
- Tiempo: 14.8s
- Errores: 1
- Notas: Edit calls: 0 | Total tools: 8 | Tools: ['mochila', 'http_request', 'http_request', 'http_request', 'http_request', 'db_query', 'db_query', 'db_query']

### T4 Deep (diagnóstico)
- Resultado: PASS
- Iteraciones: 9
- Tiempo: 22.5s
- Errores: 0
- Notas: HTTP calls: 6 | Keywords diagnóstico: 3/6 | Tools: ['mochila', 'http_request', 'http_request', 'http_request', 'http_request', 'http_request', 'http_request', 'db_query', 'db_query']

