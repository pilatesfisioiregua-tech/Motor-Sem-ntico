# Test Validación Modelos — Post BRIEFING_06

Fecha: 2026-03-18T11:37:56
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
| T1 Quick (read+report) | ✅ PASS | 3 | 12.0s | 0 | Tools: ['read_file', 'read_file', 'read_file'] / Summary: Completado en 5 pasos, |
| T2 Análisis (listar métodos) | ✅ PASS | 1 | 23.4s | 0 | Métodos encontrados: 5/6 |
| T3 Execute (crear endpoint) | ❌ FAIL | 6 | 21.1s | 0 | Edit calls: 0 / Total tools: 6 |
| T4 Deep (diagnóstico) | ❌ FAIL | 50 | 428.5s | 7 | HTTP calls: 13 / Keywords diagnóstico: 1/6 |

**Total: 2/4 passed**

## Diagnóstico

**⚠️ T1-T2 pasan pero T3-T4 fallan** → capacidad parcial → EVALUAR cambio de cerebro

## Detalle por test

### T1 Quick (read+report)
- Resultado: PASS
- Iteraciones: 3
- Tiempo: 12.0s
- Errores: 0
- Notas: Tools: ['read_file', 'read_file', 'read_file'] | Summary: Completado en 5 pasos, resultado: La función get_gestor() está en la línea 1273 del archivo @project

### T2 Análisis (listar métodos)
- Resultado: PASS
- Iteraciones: 1
- Tiempo: 23.4s
- Errores: 0
- Notas: Métodos encontrados: 5/6

### T3 Execute (crear endpoint)
- Resultado: FAIL
- Iteraciones: 6
- Tiempo: 21.1s
- Errores: 0
- Notas: Edit calls: 0 | Total tools: 6

### T4 Deep (diagnóstico)
- Resultado: FAIL
- Iteraciones: 50
- Tiempo: 428.5s
- Errores: 7
- Notas: HTTP calls: 13 | Keywords diagnóstico: 1/6

