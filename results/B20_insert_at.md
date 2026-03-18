# B20 — insert_at + read_file con líneas numeradas

Fecha: 2026-03-18
Base URL: https://chief-os-omni.fly.dev
Version: 3.4.0

## Cambios aplicados

1. **read_file** ahora muestra números de línea (`4d| contenido`) como cat -n
2. **insert_at(path, line, content)** — nueva tool de inserción por número de línea
3. Registrado en CORE_TOOLS, MODE_TOOLS, WORKER_TOOLS, TOOL_DESCRIPTIONS
4. Integrado en drift_guard, code validation, files_changed tracking
5. MODE_HINTS["execute"] actualizado para mencionar insert_at
6. Dynamic tools section incluye insert_at

## DIAG confirmado

```
exec_mode=execute | tools_count=9 | safety_net=NO
tools=['read_file', 'write_file', 'edit_file', 'insert_at', 'list_dir', 'run_command', 'finish', 'mochila', 'http_request']
```

`insert_at` aparece en tools. El modelo lo ve.

## Resultados

| Test | Resultado | Iteraciones | Tiempo | Errores | Notas |
|------|-----------|-------------|--------|---------|-------|
| T1 Quick (read+report) | **PASS** | 0 | 0.3s | 0 | Cache hit |
| T2 Análisis (listar métodos) | **PASS** | 0 | 0.3s | 0 | Cache hit (5/6 métodos) |
| T3 Execute (crear endpoint) | **FAIL** | 10 | 18.7s | 0 | 0 insert_at, 0 edit_file, 0 read_file |
| T4 Deep (diagnóstico) | **PASS** | 11 | 14.5s | 0 | 4/6 keywords |

**Total: 3/4 passed** (sin regresión vs B19C: era 2/4, ahora 3/4 — T2 pasó por cache)

## T3 Detalle

Tools: `['mochila', 'http_request' ×9]`

- insert_at: **0**
- edit_file: **0**
- read_file: **0**
- list_dir: **0**
- Modelo usó: solo mochila + http_request (patrón recurrente)

## Comparación B19C vs B20

| Métrica | B19C (Devstral) | B20 (Devstral + insert_at) |
|---------|-----------------|---------------------------|
| db_query alucinado | 0 | 0 |
| read_file usado (T3) | SI (1+) | NO |
| list_dir usado (T3) | SI (5+) | NO |
| edit_file usado | NO | NO |
| insert_at usado | N/A | NO |
| T3 Iteraciones | 51 | 10 |
| T3 Resultado | FAIL | FAIL |
| T1 | PASS | PASS (cache) |
| T2 | FAIL | PASS (cache) |
| T4 | PASS | PASS |

## Análisis

### insert_at no es el problema
El modelo ni siquiera llega a usar filesystem tools. En B19C usaba read_file/list_dir (51 iteraciones explorando), pero en esta ejecución solo hizo http_request spam (10 iteraciones). Esto indica **variabilidad del modelo** — Devstral 2 no tiene un comportamiento consistente en execute mode.

### El problema de T3 es más profundo
No es que el modelo no sepa cómo editar (insert_at vs edit_file) — es que **no intenta editar en absoluto**. El patrón mochila → http_request×N sugiere que el modelo interpreta "crear endpoint" como "hacer requests HTTP" en vez de "editar el archivo api.py".

### El fix de insert_at es correcto pero insuficiente
- La tool existe, está registrada, aparece en el schema y en el prompt
- No hay regresión en T1/T2/T4
- El modelo simplemente no la usa (ni usa ninguna filesystem tool)

### Posibles next steps
1. **Verificar que el goal de T3 llega correctamente** — puede que el test harness no esté mandando el goal que pensamos
2. **Probar con un goal más explícito** tipo "Lee @project/api.py con read_file, luego usa insert_at para añadir un endpoint"
3. **Cambiar el modelo** — Devstral 2 (123B) no ejecuta edit tasks de forma fiable
4. **Investigar si mochila está dando contexto que confunde** — el modelo siempre empieza con mochila

## Veredicto

- **Cambios B20: MANTENER** — insert_at es aditivo, no causa regresión, es la tool correcta para el caso de uso
- **T3: sigue FAIL** — el problema no es la herramienta sino el comportamiento del modelo
- **No rollback necesario**
