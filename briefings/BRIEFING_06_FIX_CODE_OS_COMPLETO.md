# BRIEFING 06 — Fix Code OS: Infraestructura que sabotea a los modelos

> Prioridad: P0-P3
> Fecha: 2026-03-17
> Fuente: Audit completo del código (agent_loop, router, context, gestor, motor_vn, registrador, recovery, sandwich, budget, api, db_pool)
> Ejecutor: Claude Code
> Scope: motor_v1_validation/agent/
> NOTA: Este briefing REEMPLAZA BRIEFING_05. Incluye todo lo de BRIEFING_05 + problemas adicionales de código.

---

## CONTEXTO

Code OS falla en tareas medianamente complejas. Se asume que es culpa de los modelos OS, pero el audit revela que la infraestructura tiene bugs que harían fallar a CUALQUIER modelo — incluyendo Claude. Los problemas se agrupan en 4 categorías:

1. **DB rota** (queries que fallan, pool agotado) → el modelo opera sin datos
2. **Context amnesia** (compresión pierde info) → el modelo "olvida" qué estaba haciendo
3. **try/except silenciosos** (errores tragados) → el modelo cree que tuvo éxito cuando falló
4. **Ruido en conversación** (recovery, escalation, finish nudge) → confunden al modelo con mensajes contradictorios

**Base de código:** `motor_v1_validation/agent/`
**DB:** `omni_mind` en fly.io Postgres (Amsterdam)
**Deploy:** `chief-os-omni` en fly.io (París)

---

## FASE 1 — P0: DB funcional (~2.5h)

Estos problemas causan que el Gestor, Motor, y otros componentes operen sin datos reales.

### TAREA 1.1: Añadir `created_at` a `preguntas_matriz`

**Problema:** Pasos 8 y 10 del Gestor GAMC fallan: `column "created_at" does not exist`.

**Acción:**
```sql
ALTER TABLE preguntas_matriz ADD COLUMN created_at timestamptz DEFAULT now();
UPDATE preguntas_matriz SET created_at = '2026-03-14T00:00:00Z' WHERE created_at IS NULL;
```

**Verificación:** `GET /gestor/obsoletas` y `GET /gestor/expiradas` → JSON sin error SQL.

---

### TAREA 1.2: Verificar columna `calibrado` en `datapoints_efectividad`

**Problema:** El registrador INSERT con `calibrado = true` y TODOS los queries del Gestor filtran por `WHERE calibrado = true`. Si la columna no existe, TODO el Gestor es un no-op silencioso.

**Acción:**
1. Verificar si existe:
```sql
SELECT column_name FROM information_schema.columns
WHERE table_name = 'datapoints_efectividad' AND column_name = 'calibrado';
```
2. Si NO existe, crearla:
```sql
ALTER TABLE datapoints_efectividad ADD COLUMN calibrado boolean DEFAULT true;
UPDATE datapoints_efectividad SET calibrado = true;
```
3. Si existe pero los 162 rows tienen `calibrado = false` o NULL:
```sql
UPDATE datapoints_efectividad SET calibrado = true WHERE calibrado IS NULL OR calibrado = false;
```

**Verificación:** `SELECT COUNT(*) FROM datapoints_efectividad WHERE calibrado = true;` → debe ser > 0.

---

### TAREA 1.3: Verificar columna `tasa_cierre` en `datapoints_efectividad`

**Problema:** El registrador calcula `tasa_cierre` y lo usa en señales PID, pero el INSERT actual NO escribe `tasa_cierre` — solo escribe `gap_pre`, `gap_post`, `operacion`, `calibrado`. El campo `tasa_cierre` queda NULL.

**Acción:**
1. Verificar:
```sql
SELECT COUNT(*) FROM datapoints_efectividad WHERE tasa_cierre IS NULL;
```
2. Añadir tasa_cierre al INSERT del registrador. Editar `core/registrador.py`, función `registrar_ejecucion`, el INSERT de `datapoints_efectividad`:

Buscar:
```python
cur.execute("""
    INSERT INTO datapoints_efectividad
      (pregunta_id, modelo, caso_id, consumidor, celda_objetivo,
       gap_pre, gap_post, operacion, calibrado)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, true)
""", [pregunta_id, modelo, caso_id, consumidor, celda,
      gap_pre, gap_post, operacion])
```

Reemplazar con:
```python
cur.execute("""
    INSERT INTO datapoints_efectividad
      (pregunta_id, modelo, caso_id, consumidor, celda_objetivo,
       gap_pre, gap_post, gap_cerrado, tasa_cierre, operacion, calibrado)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, true)
""", [pregunta_id, modelo, caso_id, consumidor, celda,
      gap_pre, gap_post, gap_cerrado, tasa_cierre, operacion])
```

3. Backfill los existentes:
```sql
UPDATE datapoints_efectividad
SET gap_cerrado = GREATEST(0, gap_pre - gap_post),
    tasa_cierre = CASE WHEN gap_pre > 0 THEN GREATEST(0, gap_pre - gap_post) / gap_pre ELSE 0 END
WHERE tasa_cierre IS NULL AND gap_pre IS NOT NULL;
```

**Verificación:** `SELECT COUNT(*) FROM datapoints_efectividad WHERE tasa_cierre IS NOT NULL;` → debe ser 162.

---

### TAREA 1.4: Unificar conexiones DB en pool compartido

**Problema:** 11+ endpoints devuelven `"error": "no_db"`. Componentes crean conexiones propias.

**Acción:**
1. Buscar TODOS los archivos en `core/` que importan `asyncpg` o crean conexiones directas SIN usar `db_pool`:
```bash
grep -rn "asyncpg\|psycopg2.connect\|_get_conn" core/ --include="*.py" | grep -v db_pool.py | grep -v __pycache__
```

2. Para cada caso encontrado, reemplazar por uso de `from .db_pool import get_conn, put_conn` o `from .db_pool import pooled_conn`.

3. Verificar que `db_pool.py` tiene `maxconn=20` (ya lo tiene según el código leído).

**Verificación:** Los 11 endpoints "no_db" devuelven datos reales:
- `/models/report`, `/tools/stats`, `/tools/rankings`, `/tools/evolution-report`
- `/criticality/temperatura`, `/criticality/avalanchas`
- `/info/redundancia`, `/metacognitive/kalman`
- `/predictive/trayectoria`, `/predictive/plan`

---

### TAREA 1.5: Fix `/models/discover` (500 error)

**Acción:** Leer `core/model_observatory.py`, identificar el método que maneja `/models/discover`, leer el traceback, arreglar.

**Verificación:** `GET /models/discover` → 200 con datos.

---

## FASE 2 — P1: Eliminar try/except silenciosos (~3h)

Este es el problema MÁS dañino del codebase. Cada try/except vacío es un error que no sabes que ocurrió. El modelo puede hacer su trabajo correctamente, pero si la persistencia falla silenciosamente, parece que no hizo nada.

### TAREA 2.1: Añadir logging a TODOS los try/except vacíos

**Acción:**

1. Encontrar todos los bloques `except Exception: pass` y `except Exception: ...` vacíos:
```bash
grep -n "except.*:" core/*.py tools/*.py *.py | grep -E "pass$|pass\s+#" | head -60
```

2. Para CADA uno, reemplazar `pass` con un `print()` que identifique el componente y el error:

Patrón antes:
```python
except Exception:
    pass
```

Patrón después:
```python
except Exception as _e:
    print(f"[WARN:{COMPONENTE}] {type(_e).__name__}: {_e}")
```

Donde COMPONENTE es el nombre del archivo/función (ej: `motor_vn._persistir_programa`, `agent_loop.flywheel`, etc.)

3. PRIORIZAR estos archivos (los que más errores silenciosos tienen):
   - `core/motor_vn.py` — ~15 bloques try/except con pass
   - `core/agent_loop.py` — ~12 bloques try/except con pass
   - `core/gestor.py` — ~8 bloques try/except con pass
   - `core/registrador.py` — ~5 bloques

4. NO cambiar la lógica. Solo añadir print(). El sistema debe seguir sin romperse por errores — pero ahora SABREMOS qué falla.

**Verificación:** Ejecutar una tarea de prueba y revisar logs. Debe haber líneas `[WARN:...]` visibles si algo falla.

---

### TAREA 2.2: Fix crítico en motor_vn._persistir_programa

**Problema:** Si `_persistir_programa()` retorna None (porque DB no conecta), `_actualizar_programa_post_ejecucion()` no actualiza nada. Todo el feedback loop se pierde silenciosamente. El motor ejecuta pero los programas siempre tienen n_ejecuciones=0.

**Acción:** En `core/motor_vn.py`, método `ejecutar()`, después de la llamada a `_persistir_programa`:

Buscar (aprox línea donde se persiste programa):
```python
programa_db_id = self._persistir_programa(programa_dict, gradientes, consumidor, modo)
```

Añadir después:
```python
if programa_db_id is None:
    print(f"[WARN:motor_vn] _persistir_programa retornó None — feedback loop desconectado para {consumidor}_{modo}")
```

Y en `_persistir_programa` mismo, el `except Exception: return None` cambiar a:
```python
except Exception as e:
    print(f"[ERROR:motor_vn._persistir_programa] {type(e).__name__}: {e}")
    return None
```

**Verificación:** Tras ejecutar el Motor, verificar:
```sql
SELECT id, consumidor, n_ejecuciones, tasa_cierre_media FROM programas_compilados WHERE activo = true;
```
Los contadores deben incrementarse.

---

## FASE 3 — P2: Mejorar estabilidad del agent loop (~3h)

Estos problemas causan que el modelo se confunda, entre en loops, o pierda contexto.

### TAREA 3.1: Mejorar context.py — no perder info crítica

**Problema:** Tras ~30 iteraciones, `_force_trim` (nuclear option) mantiene solo sistema + últimos 6 mensajes. El modelo pierde TODO el contexto de lo que hizo.

**Acción:** En `core/context.py`:

1. Subir `keep_last_n` de 6 a 12 (mantener más mensajes recientes):
```python
def __init__(self, max_tokens: int = 80000, compress_threshold: int = 60000,
             keep_last_n: int = 12):
```

2. En `_force_trim`, mantener también los mensajes con tool_calls exitosos (no solo los últimos N):
```python
def _force_trim(self, history: list) -> list:
    """Nuclear option — keep system + successful tool calls + last N."""
    protected = history[:2]  # system + task
    recent = history[-self.keep_last_n:]
    
    # Also keep successful tool results from older messages (max 5)
    older = history[2:-self.keep_last_n] if len(history) > self.keep_last_n + 2 else []
    important = []
    for msg in older:
        content = msg.get("content", "") or ""
        # Keep messages with successful write/edit results
        if msg.get("role") == "tool" and "OK" in content and "write_file" not in content:
            continue
        if msg.get("role") == "tool" and any(kw in content for kw in ["Successfully", "created", "updated", "OK"]):
            important.append(msg)
            if len(important) >= 5:
                break
    
    return protected + important + recent
```

3. En `_llm_compress`, subir el límite de input de 8000 a 15000 chars para comprimir mejor:
Cambiar:
```python
compressed_text += f"[{role}] {content[:300]}\n"
```
A:
```python
compressed_text += f"[{role}] {content[:500]}\n"
```
Y:
```python
"Summarize this conversation history:\n\n{compressed_text[:8000]}\n\n"
```
A:
```python
"Summarize this conversation history:\n\n{compressed_text[:15000]}\n\n"
```

**Verificación:** Ejecutar tarea de 30+ iteraciones. El modelo debe recordar qué archivos editó al principio.

---

### TAREA 3.2: Reducir ruido en mensajes de recovery

**Problema:** Los mensajes de recovery ("[RECOVERY] Decomposing into sub-goals", "[ESCALACIÓN] Modelo anterior falló") se inyectan en el historial y confunden al modelo. Piensa que hay instrucciones nuevas cuando son guías internas.

**Acción:** En `core/agent_loop.py`, buscar TODOS los mensajes de recovery inyectados y hacerlos más cortos y directos:

1. Buscar: `"[RECOVERY]"` en agent_loop.py — hay ~6 mensajes distintos.

2. Reemplazar mensajes largos por versiones cortas. Ejemplo:

Antes:
```python
history.append({"role": "user", "content":
    f"[RECOVERY] Decomposing into sub-goals:\n"
    ...
```

Después:
```python
history.append({"role": "user", "content":
    f"Error repetido. Simplifica: {sub_goals[0]}"})
```

3. El mensaje de escalación también. Antes:
```python
f"[ESCALACIÓN] Modelo anterior falló repetidamente. "
f"Último error: {self._escalation_reason}\n"
f"INSTRUCCIÓN: Revisa las acciones previas..."
```

Después:
```python
f"Error previo: {self._escalation_reason[:100]}. Prueba diferente enfoque."
```

**Verificación:** Ejecutar tarea que produce errores. Los mensajes en el historial deben ser cortos (<100 chars cada uno).

---

### TAREA 3.3: Suavizar finish gate nudge

**Problema:** El finish gate rechaza el PRIMER finish() si queda >20% de iteraciones. Si el modelo completó correctamente en pocas iteraciones, esto lo fuerza a seguir y potencialmente romper cosas.

**Acción:** En `core/agent_loop.py`, cambiar la condición de nudge:

Buscar:
```python
if finish_accepted and not _finish_nudged:
    remaining_ratio = (max_iterations - iteration) / max_iterations
    if remaining_ratio > 0.2:
```

Reemplazar con:
```python
if finish_accepted and not _finish_nudged:
    remaining_ratio = (max_iterations - iteration) / max_iterations
    # Solo nudge si quedan >80% de iteraciones Y se hicieron <5 acciones exitosas
    successful_actions = sum(1 for e in log if isinstance(e, dict) and not e.get("is_error"))
    if remaining_ratio > 0.8 and successful_actions < 5:
```

Y cambiar el mensaje de nudge:
```python
"content": "¿Terminaste? Si todo OK → finish() de nuevo."
```

**Verificación:** Tarea simple (rename, typo) debe completar en <5 iteraciones sin nudge.

---

### TAREA 3.4: Reducir gritos al modelo por monólogo

**Problema:** Cuando el modelo no usa tools por 2 iteraciones, se le grita "Use a tool NOW" y "CRITICAL: Call list_dir('.') NOW." Esto causa que llame tools aleatorios por pánico.

**Acción:** En `core/agent_loop.py`, buscar la sección de monólogo:

Cambiar:
```python
if stuck.no_tool_streak == 2:
    history.append({"role": "user", "content": "Use a tool NOW to make progress."})
elif stuck.no_tool_streak >= 3:
    router.on_blowup()
    history.append({"role": "user", "content": "CRITICAL: Call list_dir('.') NOW."})
```

A:
```python
if stuck.no_tool_streak == 3:
    history.append({"role": "user", "content": "Recuerda usar herramientas para avanzar."})
elif stuck.no_tool_streak >= 5:
    router.on_blowup()
    history.append({"role": "user", "content": "Sin progreso. Empieza con list_dir('@project/')."})
```

Razonamiento: dar 3 iteraciones de monólogo antes de intervenir (a veces el modelo razona varios pasos antes de actuar), y 5 antes de escalar.

**Verificación:** El modelo puede pensar 2-3 iteraciones sin que le griten.

---

## FASE 4 — P2: Limpieza DB y config (~1.5h)

### TAREA 4.1: Limpiar duplicados en config_enjambre y config_modelos

(Igual que BRIEFING_05 Tarea 3.2)

```sql
DELETE FROM config_enjambre WHERE id IN (
  SELECT id FROM (
    SELECT id, ROW_NUMBER() OVER (PARTITION BY tier ORDER BY id DESC) as rn
    FROM config_enjambre
  ) t WHERE rn > 1
);

DELETE FROM config_modelos WHERE id IN (
  SELECT id FROM (
    SELECT id, ROW_NUMBER() OVER (PARTITION BY rol, modelo ORDER BY id DESC) as rn
    FROM config_modelos
  ) t WHERE rn > 1
);
```

---

### TAREA 4.2: Separar scopes en knowledge_base

(Igual que BRIEFING_05 Tarea 3.1)

En `core/neural_db.py`, función `hybrid_search`, añadir filtro por defecto que excluya scopes `repo%`:
```python
# Añadir al WHERE: AND scope NOT LIKE 'repo%'
# O parámetro include_repo=False
```

---

### TAREA 4.3: Unificar version string

(Igual que BRIEFING_05 Tarea 3.3)

Fijar en 3.4.0 en todas las fuentes.

---

### TAREA 4.4: Setup pytest mínimo

(Igual que BRIEFING_05 Tarea 3.4)

Crear `pytest.ini` y verificar que tests existentes pasan.

---

## FASE 5 — P3: Cerrar ciclos rotos (~2h)

### TAREA 5.1: Implementar consumo de marcas estigmérgicas

(Igual que BRIEFING_05 Tarea 2.2)

7 alertas sin consumir. Implementar consumidor en el scheduler.

---

### TAREA 5.2: Añadir telemetría mínima de tools

**Problema:** `tool_telemetry` tiene 0 rows. No sabemos qué tools se usan realmente y cuáles fallan.

**Acción:** En `core/agent_loop.py`, el bloque que llama a `evo.log_invocation()` ya existe pero está en un try/except que traga errores.

1. Verificar que `tool_evolution.py` tiene la función `log_invocation` y que funciona
2. Si falla por "no_db", es porque tool_evolution usa su propia conexión → arreglado en Tarea 1.4
3. Verificar tras Tarea 1.4 que tool_telemetry empieza a llenarse

**Verificación:** Tras 1 sesión de Code OS, `SELECT COUNT(*) FROM tool_telemetry;` → > 0.

---

## ORDEN DE EJECUCIÓN

```
FASE 1 — DB funcional:
  1.1 ALTER TABLE created_at          → 15 min
  1.2 Verificar calibrado             → 15 min
  1.3 Fix tasa_cierre en registrador  → 30 min
  1.4 Unificar pool DB               → 1h
  1.5 Fix /models/discover           → 30 min
  --- DEPLOY + verificar endpoints ---

FASE 2 — try/except logging:
  2.1 Añadir logging a except pass    → 1.5h (muchos archivos)
  2.2 Fix motor_vn._persistir         → 30 min
  --- DEPLOY + ejecutar tarea de prueba + revisar logs ---

FASE 3 — Estabilidad agent loop:
  3.1 Mejorar context.py              → 45 min
  3.2 Reducir ruido recovery          → 30 min
  3.3 Suavizar finish gate            → 15 min
  3.4 Reducir gritos monólogo         → 15 min
  --- DEPLOY + ejecutar tarea de 30+ iteraciones ---

FASE 4 — Limpieza:
  4.1 Limpiar duplicados config       → 15 min
  4.2 Separar scopes knowledge_base   → 30 min
  4.3 Unificar version                → 15 min
  4.4 Setup pytest                    → 30 min
  --- DEPLOY ---

FASE 5 — Ciclos:
  5.1 Consumo marcas estigmérgicas    → 1h
  5.2 Verificar tool telemetry        → 30 min
  --- DEPLOY FINAL ---
```

## POST-EJECUCIÓN: TEST DE VALIDACIÓN DE MODELOS

Una vez completadas TODAS las fases, ejecutar este test para evaluar si los modelos actuales son capaces:

```
TEST 1 (Quick): "Renombra la función get_gestor a obtener_gestor en core/gestor.py"
  → Esperado: completar en <5 iteraciones, 0 errores

TEST 2 (Standard): "Lee core/motor_vn.py y lista todos los métodos que llaman a call_openrouter"
  → Esperado: completar en <10 iteraciones, resultado correcto

TEST 3 (Execute): "Añade un endpoint GET /test/ping que devuelva {status: 'pong', timestamp: now()}"
  → Esperado: completar en <15 iteraciones, endpoint funcional

TEST 4 (Deep): "Diagnostica por qué /gestor/autopoiesis reporta ciclo_roto=true y arréglalo"
  → Esperado: completar en <30 iteraciones, diagnóstico correcto + fix aplicado

Si TEST 1-2 fallan → el modelo cerebro no es capaz ni para tareas básicas → cambiar cerebro
Si TEST 1-2 pasan pero TEST 3-4 fallan → el modelo puede hacer análisis pero no ejecución → evaluar cambio
Si TEST 1-4 pasan → los modelos son capaces, el problema era la infraestructura
```
