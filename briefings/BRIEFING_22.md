# BRIEFING_22 — edit_file fallback a insert_at

**Objetivo**: Cuando edit_file falla por string matching, el error debe sugerir insert_at como alternativa. Esto completa el flujo que B21 desbloqueó (read → edit_file FAIL → insert_at → PASS).

**Contexto**: B21 logró que el modelo siga el workflow correcto por primera vez: read_file → list_dir → read_file → edit_file → run_command. Pero edit_file falla porque el modelo no copia el old_string exacto. insert_at existe y funciona, pero el modelo no sabe que puede usarlo como alternativa.

**Cambio**: 1 línea en filesystem.py.

---

## Paso 1: Cambiar mensaje de error de edit_file

**Archivo**: `motor_v1_validation/agent/tools/filesystem.py`

**Antes**:
```python
        return f"ERROR: old_string not found in {path}. Read the file first to get exact content."
```

**Después**:
```python
        return f"ERROR: old_string not found in {path}. TIP: usa insert_at(path, línea, contenido) para insertar código en una línea específica — más fiable que edit_file. Usa los números de línea de read_file."
```

**Criterio**: `grep -c "insert_at" motor_v1_validation/agent/tools/filesystem.py` devuelve al menos 4 (función + registro + lambda + error message).

## Paso 2: Deploy y test

```bash
fly deploy --app chief-os-omni
```

Ejecutar solo T3 (o todos si es más rápido):
```bash
cd briefings && python3 test_validacion_modelos.py
```

**Criterio T3 PASS**: Secuencia esperada: read_file → edit_file(FAIL) → insert_at(OK) → finish. Al menos 1 insert_at exitoso en api.py.

## Paso 3: Guardar resultado

`results/B22_edit_fallback_insert.md` con:
- ¿edit_file falló? (esperado: sí)
- ¿El modelo usó insert_at después del error? (esto es lo que importa)
- PASS/FAIL
- Si T3 PASS → commit "B22: T3 PASS — edit_file fallback to insert_at"
