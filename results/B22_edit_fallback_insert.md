# B22 — edit_file fallback a insert_at

Fecha: 2026-03-18
Base URL: https://chief-os-omni.fly.dev
Version: 3.4.0

## Cambio aplicado

edit_file error message ahora incluye TIP sugiriendo insert_at como alternativa.

## Resultados

| Test | Resultado | Iteraciones | Tiempo | Errores |
|------|-----------|-------------|--------|---------|
| T1 Quick | **PASS** | 5 | 6.5s | 1 |
| T2 Análisis | **PASS** | 8 | 10.8s | 2 |
| T3 Execute | **FAIL** | 10 | 11.0s | 2 |
| T4 Deep | **FAIL** | 16 | 27.0s | 1 |

**Total: 2/4 passed**

## T3 Detalle

Tools: `['read_file', 'list_dir', 'list_dir', 'read_file', 'edit_file', 'run_command' ×5]`

- read_file: 2
- list_dir: 2
- **edit_file: 1** (falló — old_string no encontrado)
- run_command: 5
- **insert_at: 0** (no siguió el TIP del error)

### Secuencia

1. read_file → lee el código con líneas numeradas
2. list_dir ×2 → explora estructura
3. read_file → lee de nuevo (probablemente otro archivo)
4. edit_file → **FALLA** (old_string mismatch) → error incluye TIP sobre insert_at
5. run_command ×5 → el modelo intenta por otra vía (probablemente echo/sed/python)

### Análisis

El modelo no siguió el TIP del error. En vez de probar insert_at, cambió a run_command. Posibles razones:
- Devstral 2 no sigue hints en mensajes de error
- El modelo ya tenía un plan alternativo (run_command)
- Variabilidad del modelo

## Comparación B21 vs B22

| Métrica | B21 | B22 |
|---------|-----|-----|
| Workflow correcto | SI | SI |
| edit_file llamado | SI | SI |
| edit_file falló | SI (8 errores) | SI (2 errores) |
| insert_at después de error | NO | NO |
| run_command fallback | SI | SI |
| Resultado | FAIL | FAIL |

## Veredicto

- **Cambio B22: MANTENER** — el TIP es correcto y puede funcionar en futuras ejecuciones
- El workflow read → edit → fallback está consolidado (reproducible en 2 runs consecutivos)
- T3 sigue FAIL pero por razón distinta a antes: ahora el modelo SÍ intenta editar
- El modelo no usa insert_at — podría necesitar un hint más fuerte en MODE_HINTS o en el system prompt
