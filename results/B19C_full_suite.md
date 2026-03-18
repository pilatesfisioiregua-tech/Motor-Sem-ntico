# Test Validación Modelos — Post BRIEFING_06

Fecha: 2026-03-18T16:19:40
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
| T1 Quick (read+report) | ✅ PASS | 6 | 7.1s | 1 | Tools: ['read_file', 'list_dir', 'search_files', 'read_file', 'read_file'] / Sum |
| T2 Análisis (listar métodos) | ❌ FAIL | 5 | 3.7s | 1 | Métodos encontrados: 0/6 |
| T3 Execute (crear endpoint) | ❌ FAIL | 28 | 44.4s | 1 | Edit calls: 0 / Total tools: 28 / Tools: ['mochila', 'http_request', 'http_reque |
| T4 Deep (diagnóstico) | ✅ PASS | 12 | 20.6s | 0 | HTTP calls: 7 / Keywords diagnóstico: 2/6 / Tools: ['mochila', 'http_request', ' |

**Total: 2/4 passed**

## Diagnóstico

**❌ T1-T2 fallaron** → el cerebro no sirve ni para tareas básicas → CAMBIAR MODELO

## Detalle por test

### T1 Quick (read+report)
- Resultado: PASS
- Iteraciones: 6
- Tiempo: 7.1s
- Errores: 1
- Notas: Tools: ['read_file', 'list_dir', 'search_files', 'read_file', 'read_file'] | Summary: Completado en 8 pasos, resultado: La función get_gestor() está en la línea 1276 del archivo @project

### T2 Análisis (listar métodos)
- Resultado: FAIL
- Iteraciones: 5
- Tiempo: 3.7s
- Errores: 1
- Notas: Métodos encontrados: 0/6

### T3 Execute (crear endpoint)
- Resultado: FAIL
- Iteraciones: 28
- Tiempo: 44.4s
- Errores: 1
- Notas: Edit calls: 0 | Total tools: 28 | Tools: ['mochila', 'http_request', 'http_request', 'http_request', 'list_dir', 'list_dir', 'read_file', 'list_dir', 'list_dir', 'read_file']

### T4 Deep (diagnóstico)
- Resultado: PASS
- Iteraciones: 12
- Tiempo: 20.6s
- Errores: 0
- Notas: HTTP calls: 7 | Keywords diagnóstico: 2/6 | Tools: ['mochila', 'http_request', 'http_request', 'run_command', 'run_command', 'run_command', 'run_command', 'http_request', 'http_request', 'http_request', 'http_request', 'http_request']

