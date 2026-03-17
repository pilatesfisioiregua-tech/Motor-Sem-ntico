# Test Validación Modelos — Post BRIEFING_06

Fecha: 2026-03-18T00:46:43
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
| T1 Quick (read+report) | ❌ FAIL | 15 | 50.4s | 7 | Tools: ['read_file', 'list_dir', 'list_dir', 'mochila', 'list_dir'] / Summary: C |
| T2 Análisis (listar métodos) | ❌ FAIL | 14 | 26.8s | 9 | Métodos encontrados: 0/6 |
| T3 Execute (crear endpoint) | ❌ FAIL | 14 | 27.7s | 1 | Edit calls: 0 / Total tools: 14 |
| T4 Deep (diagnóstico) | ❌ FAIL | 21 | 87.4s | 5 | HTTP calls: 6 / Keywords diagnóstico: 0/6 |

**Total: 0/4 passed**

## Diagnóstico

**❌ T1-T2 fallaron** → el cerebro no sirve ni para tareas básicas → CAMBIAR MODELO

## Detalle por test

### T1 Quick (read+report)
- Resultado: FAIL
- Iteraciones: 15
- Tiempo: 50.4s
- Errores: 7
- Notas: Tools: ['read_file', 'list_dir', 'list_dir', 'mochila', 'list_dir'] | Summary: Completado en 17 pasos, resultado: No se pudo localizar el archivo @project/core/gestor.py. El works

### T2 Análisis (listar métodos)
- Resultado: FAIL
- Iteraciones: 14
- Tiempo: 26.8s
- Errores: 9
- Notas: Métodos encontrados: 0/6

### T3 Execute (crear endpoint)
- Resultado: FAIL
- Iteraciones: 14
- Tiempo: 27.7s
- Errores: 1
- Notas: Edit calls: 0 | Total tools: 14

### T4 Deep (diagnóstico)
- Resultado: FAIL
- Iteraciones: 21
- Tiempo: 87.4s
- Errores: 5
- Notas: HTTP calls: 6 | Keywords diagnóstico: 0/6

