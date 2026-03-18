# BRIEFING_23 — insert_at como herramienta primaria + redirect activo

**Objetivo**: Deploy y test de los cambios ya aplicados en agent_loop.py.

**Cambios YA aplicados** (por Opus Chat directamente):

1. **MODE_HINTS["execute"]** ahora dice explícitamente "usa insert_at, NO edit_file":
```
PROTOCOLO EXECUTE — sigue EXACTAMENTE estos pasos:
1. read_file(@project/archivo) → verás números de línea
2. Identifica la línea DESPUÉS de la cual insertar
3. insert_at(@project/archivo, NUMERO_LINEA, código_nuevo)
4. finish(result='descripción del cambio')
IMPORTANTE: Usa insert_at, NO edit_file. insert_at es más fiable.
```

2. **EDIT_FILE REDIRECT** en el loop: cuando edit_file falla con "old_string not found", se inyecta un mensaje de usuario que fuerza insert_at con instrucciones explícitas.

## Paso 1: Verificar cambios

```bash
grep -c "insert_at, NO edit_file" motor_v1_validation/agent/core/agent_loop.py
# Esperado: 1

grep -c "EDIT_FILE REDIRECT" motor_v1_validation/agent/core/agent_loop.py
# Esperado: 1
```

## Paso 2: Deploy

```bash
fly deploy --app chief-os-omni --remote-only
```

Verificar health.

## Paso 3: Ejecutar tests

```bash
cd briefings && python3 test_validacion_modelos.py
```

**Criterio T3 PASS**: Al menos 1 `insert_at` exitoso en api.py.

Flujo esperado:
- Modelo lee MODE_HINTS → intenta insert_at directamente (sin pasar por edit_file)
- O: intenta edit_file → falla → redirect lo envía a insert_at
- Cualquiera de las dos rutas → insert_at exitoso → T3 PASS

## Paso 4: Guardar resultado

`results/B23_insert_at_primary.md` con:
- ¿El modelo usó insert_at directamente? ¿O pasó por edit_file primero?
- Secuencia completa de tools
- PASS/FAIL por test
- Si T3 PASS → commit "B23: T3 PASS — 4/4 tests, insert_at as primary edit tool"
