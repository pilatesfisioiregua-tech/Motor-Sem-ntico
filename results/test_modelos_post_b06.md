# Test Validación Modelos — Post BRIEFING_06

Fecha: 2026-03-18T23:10:20
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
| T1 Quick (read+report) | ✅ PASS | 0 | 0.4s | 0 | Tools: [] / Summary: No pude completar la tarea tras 0 pasos. Razon: CACHE_HIT.  |
| T2 Análisis (listar métodos) | ✅ PASS | 0 | 0.3s | 0 | Métodos encontrados: 5/6 |
| T3 Execute (crear endpoint) | ✅ PASS | 8 | 12.8s | 0 | Edit calls: 2 / Total tools: 8 / Tools: ['read_file', 'read_file', 'read_file',  |
| T4 Deep (diagnóstico) | ✅ PASS | 9 | 19.4s | 0 | HTTP calls: 6 / Keywords diagnóstico: 5/6 / Tools: ['mochila', 'http_request', ' |

**Total: 4/4 passed**

## Diagnóstico

**✅ T1-T4 pasan** → los modelos son capaces, el problema era la infraestructura

## Detalle por test

### T1 Quick (read+report)
- Resultado: PASS
- Iteraciones: 0
- Tiempo: 0.4s
- Errores: 0
- Notas: Tools: [] | Summary: No pude completar la tarea tras 0 pasos. Razon: CACHE_HIT. | [CACHE HIT: cache_exact] La función get

### T2 Análisis (listar métodos)
- Resultado: PASS
- Iteraciones: 0
- Tiempo: 0.3s
- Errores: 0
- Notas: Métodos encontrados: 5/6

### T3 Execute (crear endpoint)
- Resultado: PASS
- Iteraciones: 8
- Tiempo: 12.8s
- Errores: 0
- Notas: Edit calls: 2 | Total tools: 8 | Tools: ['read_file', 'read_file', 'read_file', 'read_file', 'read_file', 'read_file', 'edit_file', 'insert_at']

### T4 Deep (diagnóstico)
- Resultado: PASS
- Iteraciones: 9
- Tiempo: 19.4s
- Errores: 0
- Notas: HTTP calls: 6 | Keywords diagnóstico: 5/6 | Tools: ['mochila', 'http_request', 'http_request', 'http_request', 'http_request', 'http_request', 'http_request', 'db_query', 'db_query']

