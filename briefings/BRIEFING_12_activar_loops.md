# BRIEFING_12: Activar Loops — El sistema aprende solo

Fecha: 2026-03-18
Prioridad: 2 (depende de Prioridad 1 completada ✅)
Objetivo: Que los 3 loops automáticos funcionen: Autopoiesis, Tool Telemetry, Señales

---

## CONTEXTO

El sistema tiene todo el código para auto-mejorarse pero los loops están desconectados.
Resultado: 0 señales, 0 tool_telemetry, ciclo autopoiético reportando roto.

3 problemas independientes, 3 fixes.

---

## FIX 1: Tool telemetry — el buffer nunca se vacía

### Problema
`tool_telemetry` tiene 0 rows aunque `chat.py` (línea ~912) llama a:
```python
get_tool_evolution().log_invocation(...)
```

El código en `core/tool_evolution.py` buferea invocaciones en `self._queue` y hace flush cuando:
- `len(self._queue) >= self._queue_max` (10 entries)
- `time.time() - self._last_flush >= self._flush_interval` (5 segundos)

**Causa probable**: El auto-flush solo se chequea DENTRO de `log_invocation()`. Si una sesión de chat usa 8 tools y termina, esos 8 entries quedan en el buffer y se pierden cuando el proceso recicla. `flush()` existe pero nadie lo llama al final de la sesión.

### Solución
En `chat.py`, buscar el bloque de Flywheel feedback al final de `_process_chat()` (alrededor de línea 933-948). Justo DESPUÉS de ese bloque (después del `except Exception: pass` del flywheel), añadir:

```python
        # Flush tool evolution telemetry buffer
        try:
            from core.tool_evolution import get_tool_evolution
            get_tool_evolution().flush()
        except Exception:
            pass
```

También hacer lo mismo al final de `_process_design()` y `_process_execute()` — buscar los bloques `yield {"type": "status", ...}` al final de cada método y añadir el flush justo antes.

### Verificación
Después del fix, hacer una sesión de chat que use al menos 1 tool (ej: `remember("test")`), y luego:
```sql
SELECT count(*) FROM tool_telemetry;
-- Debe ser > 0
SELECT tool_name, count(*) FROM tool_telemetry GROUP BY tool_name ORDER BY count DESC LIMIT 5;
```

---

## FIX 2: Señales — evaluar_reglas() nunca se llama automáticamente

### Problema
`señales` tiene 0 rows. `crear_señal()` existe en `telemetria.py` y funciona. `evaluar_reglas()` también existe y evalúa las 6 reglas de detección activas en `reglas_deteccion`. PERO `evaluar_reglas()` solo se ejecuta cuando alguien llama al endpoint `POST /evaluar-reglas` manualmente. No hay nada que lo llame periódicamente.

### Solución
Conectar `evaluar_reglas()` al ciclo del Gestor Scheduler. En `core/gestor_scheduler.py`, dentro del método `ejecutar_ciclo()`, buscar la línea:

```python
        resultado = gestor.ejecutar_loop()
```

Justo DESPUÉS de esa línea, añadir:

```python
        # Evaluar reglas de detección (genera señales si hay umbrales cruzados)
        try:
            from .telemetria import evaluar_reglas
            señales_generadas = evaluar_reglas()
            if señales_generadas:
                logger.info(f"Reglas evaluadas: {len(señales_generadas)} señales generadas")
        except Exception as e:
            logger.warning(f"evaluar_reglas failed: {e}")
```

### Verificación
Disparar un ciclo del gestor manualmente:
```bash
curl -X POST https://chief-os-omni.fly.dev/gestor/ciclo
```
(O el endpoint equivalente que dispara `ejecutar_ciclo()`)

Luego:
```sql
SELECT count(*) FROM señales;
-- Puede ser 0 si no se cruzan umbrales, pero la tabla debe ser consultable sin error

-- Verificar que evaluar_reglas se ejecutó:
SELECT * FROM metricas WHERE componente = 'registrador' ORDER BY created_at DESC LIMIT 5;
```

---

## FIX 3: Verificar y activar el Gestor Scheduler en el boot

### Problema
`gestor_scheduler.py` tiene `loop_infinito()` que ejecuta ciclos adaptativos (24h default). Pero necesitamos verificar que SE INICIA cuando la app arranca.

### Investigación necesaria
Buscar en `api.py` (raíz del agent, 3272 líneas) dónde se inicia el scheduler:

```
grep -n "scheduler\|gestor_scheduler\|loop_infinito\|get_scheduler" api.py
```

Posibles escenarios:
1. **Ya se inicia en startup** — verificar que no hay error silencioso
2. **NO se inicia** — añadirlo al lifespan/startup de FastAPI

### Solución si NO se inicia
En `api.py`, buscar el event handler de startup de FastAPI. Puede ser un `@app.on_event("startup")` o un `lifespan` contextmanager. Añadir:

```python
@app.on_event("startup")
async def start_gestor_scheduler():
    """Start the adaptive Gestor loop (24h default cycle)."""
    from core.gestor_scheduler import get_scheduler
    scheduler = get_scheduler()
    # Start with 5 minute delay to let the app fully boot
    scheduler._task = asyncio.create_task(scheduler.loop_infinito(delay_inicial_s=300))
```

Si ya existe un startup handler, añadir las líneas del scheduler dentro del bloque existente.

### Solución si YA se inicia pero el ciclo está roto
El autopoiesis check_datapoints comparaba dp_recientes vs dp_anteriores en ventanas de 24h. Con solo 7 ejecuciones históricas (todas viejas), no hay datos en las ventanas recientes → check_datapoints devuelve NULL (indeterminado, no fallo). Verificar:

```sql
SELECT count(*) FROM datapoints_efectividad 
WHERE calibrado = true AND timestamp > NOW() - INTERVAL '7 days';
```

Si es 0, el autopoiesis no puede evaluarse. Esto se resuelve en Prioridad 3 (ejecutar Motor sobre pilotos reales).

### Verificación
```bash
# Ver logs del scheduler
curl https://chief-os-omni.fly.dev/gestor/estado
# Debe devolver running=true, ciclos_completados >= 0

curl https://chief-os-omni.fly.dev/gestor/autopoiesis
# Debe devolver checks con valores (no todo null/error)
```

---

## FIX 4 (bonus): Consumir las 7 alertas stale de autopoiesis

### Problema
Hay 7 marcas estigmérgicas de tipo "alerta" con contenido "autopoiesis_roto" sin consumir. Son residuo de cuando la fontanería estaba rota. Ahora que está arreglada, estas alertas ensucian el check_alertas del autopoiesis.

### Solución
```sql
UPDATE marcas_estigmergicas 
SET consumida = true 
WHERE consumida = false 
  AND tipo = 'alerta' 
  AND contenido->>'tipo' = 'autopoiesis_roto';
```

NOTA: `gestor_scheduler.py` ya tiene lógica para consumir alertas stale automáticamente (líneas ~200-220) cuando los data checks pasan pero hay alertas viejas. Pero esa lógica solo corre cuando se ejecuta un ciclo. Si el scheduler no está activo, las alertas quedan.

### Verificación
```sql
SELECT count(*) FROM marcas_estigmergicas WHERE consumida = false AND tipo = 'alerta';
-- Debe ser 0
```

---

## ORDEN DE EJECUCIÓN

```
PASO 1: Investigar estado actual
  - grep "scheduler\|gestor_scheduler\|loop_infinito" en api.py
  - curl /gestor/estado → ver si scheduler corre
  - SELECT count(*) FROM tool_telemetry (confirmar 0)
  - SELECT count(*) FROM señales (confirmar 0)

PASO 2: Aplicar FIX 1 (tool telemetry flush en chat.py)
  - Editar chat.py: añadir flush() al final de _process_chat, _process_design, _process_execute

PASO 3: Aplicar FIX 2 (evaluar_reglas en gestor_scheduler.py)
  - Editar gestor_scheduler.py: añadir evaluar_reglas() después de ejecutar_loop()

PASO 4: Aplicar FIX 3 (scheduler en startup)
  - Si no se inicia: añadir al startup de api.py
  - Si ya se inicia: verificar que no hay error silencioso

PASO 5: Aplicar FIX 4 (limpiar alertas stale)
  - SQL directo contra la DB

PASO 6: Deploy y verificar
  - Deploy a fly.io
  - Esperar 1 minuto
  - curl /gestor/estado → running=true
  - curl /gestor/autopoiesis → check_alertas=true (sin alertas stale)
  - Hacer una sesión de chat con 1 tool call → verificar tool_telemetry > 0
```

---

## CRITERIO DE ÉXITO

- [ ] `tool_telemetry` recibe datos después de cada sesión de chat (flush funciona)
- [ ] `evaluar_reglas()` se ejecuta en cada ciclo del Gestor
- [ ] Gestor Scheduler está activo (running=true en /gestor/estado)
- [ ] 0 alertas stale de autopoiesis
- [ ] /gestor/autopoiesis devuelve checks reales (no todo null/error)

## COSTE
$0 — solo ediciones de código y SQL
