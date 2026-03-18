# B19C — System prompt dinámico: HERRAMIENTAS = tools filtrados

Fecha: 2026-03-18
Base URL: https://chief-os-omni.fly.dev
Version: 3.4.0

## Cambio aplicado

CODE_OS_SYSTEM ahora genera la sección HERRAMIENTAS dinámicamente
a partir de los tools que pasan el filtro de modo.

En execute mode, el prompt dice:
```
HERRAMIENTAS DISPONIBLES (usa SOLO estas, ninguna más):
- read_file(path) — lee archivos. SIEMPRE @project/ para proyecto
- edit_file(path, old_string, new_string) — edita archivos existentes
- write_file(path, content) — crea archivos NUEVOS
- list_dir(path) — lista directorio
- run_command(command) — ejecuta shell
- finish(result) — TERMINAR con resultado
- mochila() — contexto del proyecto
- http_request(method, url) — llamadas HTTP
```

Nota: `db_query` NO aparece porque no está en MODE_TOOLS["execute"].

## Diagnóstico DIAG:B18

```
exec_mode=execute | tools_count=8 | safety_net=NO
tools=['read_file', 'write_file', 'edit_file', 'list_dir', 'run_command', 'finish', 'mochila', 'http_request']
```

## Resultado T3

| Test | Resultado | Iteraciones | Tiempo | Errores |
|------|-----------|-------------|--------|---------|
| T3 Execute (crear endpoint) | FAIL | 51 | 206.0s | 7 |

**Tools llamados** (primeros 10): `['mochila', 'http_request', 'http_request', 'http_request', 'list_dir', 'list_dir', 'read_file', 'list_dir', 'list_dir', 'list_dir']`

## Comparación B18 → B19B → B19C

| Métrica | B18 (estático) | B19B (hint D) | B19C (dinámico) |
|---------|----------------|---------------|-----------------|
| db_query alucinado | 2 | 3 | **0** |
| read_file usado | NO | NO | **SI** |
| list_dir usado | NO | NO | **SI** (5+) |
| edit_file usado | NO | NO | NO |
| Iteraciones | 6 | 7 | 51 |
| Resultado | FAIL | FAIL | FAIL |

## Análisis

### Lo que se arregló
- **db_query ya no se alucina.** La hipótesis del briefing era correcta: el modelo leía el texto del prompt y llamaba tools que veía mencionados, independientemente del schema. Fix correcto.
- **El modelo ahora usa filesystem tools** (read_file, list_dir). Antes ni los tocaba. El prompt dinámico que solo muestra tools disponibles enfoca al modelo.

### Lo que sigue fallando
- **edit_file nunca se llama.** El modelo explora (51 iteraciones leyendo y listando) pero no edita. Devstral 2 no completa el flujo read→edit→finish.
- El problema es de capacidad del modelo para tareas de edición, no de configuración del prompt.

### Veredicto
- **Fix B19C: MANTENER** — elimina alucinación, mejora uso de filesystem tools
- **T3: sigue FAIL** — requiere cambio de modelo (B19A)
- **No rollback** — el fix es correcto aunque T3 no pase
