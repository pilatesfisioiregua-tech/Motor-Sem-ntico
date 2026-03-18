# Test Validación Modelos — Post BRIEFING_06

Fecha: 2026-03-18T08:35:11
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
| T1 Quick (read+report) | ❌ FAIL | 11 | 151.9s | 6 | Tools: ['read_file', 'mochila', 'read_file', 'read_file', 'list_dir'] / Summary: |
| T2 Análisis (listar métodos) | ❌ FAIL | 7 | 37.2s | 4 | Métodos encontrados: 0/6 |
| T3 Execute (crear endpoint) | ❌ FAIL | 11 | 189.7s | 4 | Edit calls: 0 / Total tools: 11 |
| T4 Deep (diagnóstico) | ❌ FAIL | 22 | 594.7s | 5 | HTTP calls: 8 / Keywords diagnóstico: 0/6 |

**Total: 0/4 passed**

## Diagnóstico

**❌ T1-T2 fallaron** → el cerebro no sirve ni para tareas básicas → CAMBIAR MODELO

## Detalle por test

### T1 Quick (read+report)
- Resultado: FAIL
- Iteraciones: 11
- Tiempo: 151.9s
- Errores: 6
- Notas: Tools: ['read_file', 'mochila', 'read_file', 'read_file', 'list_dir'] | Summary: Completado en 11 pasos, resultado: No fue posible completar la tarea. El directorio del proyecto (@p

### T2 Análisis (listar métodos)
- Resultado: FAIL
- Iteraciones: 7
- Tiempo: 37.2s
- Errores: 4
- Notas: Métodos encontrados: 0/6

### T3 Execute (crear endpoint)
- Resultado: FAIL
- Iteraciones: 11
- Tiempo: 189.7s
- Errores: 4
- Notas: Edit calls: 0 | Total tools: 11

### T4 Deep (diagnóstico)
- Resultado: FAIL
- Iteraciones: 22
- Tiempo: 594.7s
- Errores: 5
- Notas: HTTP calls: 8 | Keywords diagnóstico: 0/6

