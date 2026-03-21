# BRIEFING_12: Nudges Semánticos + Protocol para tareas de lectura

## Diagnóstico

El modelo lee archivos y tiene la respuesta, pero no llama finish().
Produce monólogo → StuckDetector dispara → nudge imperativo → no funciona.

Root cause: el nudge actual es imperativo ("usa herramientas"), incompatible con
cómo los LLMs procesan información. La arquitectura OMNI-MIND ya demostró que
**las preguntas son el algoritmo** — la secuencia EXTRAER→CRUZAR→LENTES→INTEGRAR→
ABSTRAER→FRONTERA funciona porque crea un gradiente semántico hacia la respuesta.

**Aplicar el mismo principio al agent loop:**
En vez de comandar "llama finish()", preguntar al modelo qué ha encontrado.
La pregunta crea el gradiente; finish() emerge como respuesta natural.

## Fix 1: Nudges semánticos (preguntas que crean gradiente)

Archivo: `@project/core/agent_loop.py`

Buscar este bloque (dentro del `if not tool_calls:` section):

```python
            if stuck.no_tool_streak == 3:
                history.append({"role": "user", "content": "Recuerda usar herramientas para avanzar."})
            elif stuck.no_tool_streak >= 5:
                router.on_blowup()
                history.append({"role": "user", "content": "Sin progreso. Empieza con list_dir('@project/')."})
```

Reemplazar con:

```python
            if stuck.no_tool_streak == 2:
                # EXTRAER: pregunta que fuerza síntesis de lo encontrado
                history.append({"role": "user", "content": (
                    "¿Qué has encontrado hasta ahora? "
                    "¿Es suficiente para responder la tarea original? "
                    "Si sí → llama finish(result='tu conclusión'). "
                    "Si no → ¿qué dato te falta?"
                )})
            elif stuck.no_tool_streak == 3:
                # INTEGRAR: pregunta que empuja a formular conclusión
                history.append({"role": "user", "content": (
                    "Formula tu conclusión en UNA frase. "
                    "Luego llama finish(result='esa frase')."
                )})
            elif stuck.no_tool_streak >= 4:
                # FRONTERA: safety net mecánico — auto-finish con el texto del modelo
                last_text = content or ""
                if len(last_text) > 50:
                    stop_reason = "AUTO_FINISH"
                    final_result = last_text[:2000]
                    break
                else:
                    router.on_blowup()
                    history.append({"role": "user", "content": "Llama finish(result='...') ahora."})
```

**Lógica del gradiente semántico:**
- Streak 2 → EXTRAER: "¿Qué has encontrado?" — fuerza al modelo a inventariar lo que sabe
- Streak 3 → INTEGRAR: "Formula tu conclusión" — empuja a sintetizar en resultado
- Streak 4 → FRONTERA: AUTO_FINISH — el sistema cierra con lo que hay (safety net mecánico)

El modelo no recibe una orden ("llama finish"). Recibe una pregunta que lo guía
a razonar hacia finish() como conclusión natural.

## Fix 2: Protocol como preguntas-guía (no como pipeline lineal)

Archivo: `@project/core/agent_loop.py`

Reemplazar CODE_OS_SYSTEM:

```python
CODE_OS_SYSTEM = """Eres Code OS — agente técnico de OMNI-MIND. SIEMPRE en ESPAÑOL.

HERRAMIENTAS:
- read_file(path) — lee archivos. SIEMPRE @project/ para proyecto
- edit_file(path, old_string, new_string) — edita archivos existentes
- write_file(path, content) — crea archivos NUEVOS
- list_dir(path) — lista directorio
- run_command(command) — ejecuta shell
- db_query(sql) — consulta DB (solo SELECT)
- http_request(method, url) — llamadas HTTP
- finish(result) — TERMINAR con resultado. PON TU RESPUESTA AQUÍ.

RUTAS: @project/ = proyecto real. Sin prefijo = sandbox temporal.

CÓMO TRABAJAR:
1. ¿Qué necesito saber? → read_file, http_request, db_query
2. ¿Necesito cambiar algo? → edit_file, write_file, run_command
3. ¿Ya tengo la respuesta? → finish(result='mi respuesta completa')

REGLA: Tu análisis va DENTRO de finish(result='...'), no como texto suelto.
Si solo te piden leer/analizar: lee → finish(result='lo que encontré').

{context_section}
"""
```

**Cambio clave:** El protocol son 3 preguntas que el modelo se hace a sí mismo,
no 6 pasos secuenciales. Cada pregunta apunta a una herramienta. La tercera
pregunta ("¿Ya tengo la respuesta?") siempre termina en finish().

## Fix 3: Capturar auto-finish y texto en SSE

Archivo: `@project/api.py`

En `run_in_thread`, ANTES del push de tool calls, añadir:

```python
                    # Include model's final text as text event
                    final_text = result.get("result") or ""
                    if final_text and len(final_text) > 20:
                        evt_queue.put({"type": "text", "content": final_text[:2000]})
```

Y en la generación del `summary` del done event, enriquecer:

```python
                try:
                    reporter = Reporter()
                    summary = reporter.summarize_session(final_result) if isinstance(final_result, dict) and "stop_reason" in final_result else str(final_result)
                    # Append model's actual result for richer done event
                    if isinstance(final_result, dict):
                        model_result = final_result.get("result") or ""
                        if model_result and len(model_result) > 20:
                            summary += " | " + model_result[:500]
                except Exception:
                    ...
```

## Fix 4: Limpiar BRIEFING_EXECUTOR_PROMPT

Archivo: `@project/core/agent_loop.py`

Reemplazar BRIEFING_EXECUTOR_PROMPT:

```python
BRIEFING_EXECUTOR_PROMPT = """EJECUTA este briefing. Cada paso se EJECUTA, no se describe.

BRIEFING:
{briefing_content}

PROTOCOLO:
- SQL → db_insert(). Archivos → write_file(@project/...) o edit_file(@project/...).
- Tras cada paso → VERIFICAR (db_query, run_command).
- Al terminar → finish(result='resumen de lo ejecutado').
"""
```

## Paso 5: Deploy + Test

```bash
fly deploy -a chief-os-omni
python3 briefings/test_validacion_modelos.py --output results/test_modelos_nudge_semantico_b12.md
```

CRITERIO: Al menos 2/4 tests pasan.

## Por qué el enfoque semántico es mejor que el imperativo

| | Imperativo | Semántico (preguntas) |
|---|---|---|
| Streak 2 | "Llama finish()" | "¿Qué has encontrado? ¿Es suficiente?" |
| Streak 3 | "LLAMA FINISH AHORA" | "Formula tu conclusión en una frase" |
| Mecanismo | Obediencia | Razonamiento |
| Si no funciona | El modelo ignora | El modelo al menos intenta razonar |
| Alineado con OMNI-MIND | No | Sí — preguntas = algoritmo |

El imperativo tiene una sola oportunidad: el modelo obedece o no.
La pregunta abre un espacio de razonamiento: incluso si el modelo no llama finish(),
su respuesta a la pregunta contendrá la información útil que AUTO_FINISH captura.

## Notas

- AUTO_FINISH (streak 4) sigue siendo mecánico — es el safety net
- Pero con las preguntas en streaks 2-3, el modelo probablemente llame finish()
  antes de llegar al streak 4
- Este patrón (nudge semántico) puede generalizarse a otros momentos del loop:
  recovery, reflection, escalation
- Si funciona aquí, documentar como Principio 33 en el Maestro
