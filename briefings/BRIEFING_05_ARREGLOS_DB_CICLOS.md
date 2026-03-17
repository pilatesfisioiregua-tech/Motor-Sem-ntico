# BRIEFING 05 — Arreglos DB, Pool, Ciclos Rotos

> Prioridad: P0-P2
> Fecha: 2026-03-17
> Fuente: Audit de ESTADO_REAL_SISTEMA.md
> Ejecutor: Claude Code
> Scope: motor_v1_validation/agent/

---

## CONTEXTO

El audit del sistema revela 16 de 67 endpoints rotos (24%). La mayoría comparten causas raíz comunes: pool de DB agotado, columna faltante en tabla crítica, y wiring roto entre componentes. Este briefing contiene 9 arreglos ordenados por prioridad. Ejecutar secuencialmente.

**Base de código:** `motor_v1_validation/agent/`
**DB:** `omni_mind` en fly.io Postgres (Amsterdam)
**Deploy:** `chief-os-omni` en fly.io (París)

---

## FASE 1 — P0: Desbloqueo crítico (~2h total)

### TAREA 1.1: Añadir `created_at` a `preguntas_matriz`

**Problema:** Los pasos 8 (obsoletas) y 10 (expirar) del Gestor GAMC fallan con `column "created_at" does not exist`. Endpoints afectados: `/gestor/obsoletas`, `/gestor/expiradas`.

**Acción:**

1. Conectar a la DB y ejecutar:
```sql
ALTER TABLE preguntas_matriz ADD COLUMN created_at timestamptz DEFAULT now();

-- Backfill: asignar a las 617 preguntas existentes la fecha de la primera ejecución
UPDATE preguntas_matriz SET created_at = '2026-03-14T00:00:00Z' WHERE created_at IS NULL;
```

2. Verificar que los endpoints ya no dan error SQL:
   - `GET /gestor/obsoletas` → debe devolver lista (vacía o con datos), NO error SQL
   - `GET /gestor/expiradas` → idem

3. Si hay un archivo de schema SQL en el repo (`src/db/schema.sql` o migrations), actualizar la definición de `preguntas_matriz` para incluir `created_at`.

**Verificación:** `curl /gestor/obsoletas` y `curl /gestor/expiradas` devuelven JSON válido sin errores.

---

### TAREA 1.2: Unificar conexiones DB en pool compartido

**Problema:** 11+ endpoints devuelven `"error": "no_db"` o `"No DB connection"`. La causa: componentes que usan `_get_conn()` propio compiten con el pool compartido (`core/db_pool.py`, max=10). Cuando se agotan, fallan silenciosamente.

**Componentes afectados (buscar `_get_conn` o conexiones propias):**
- `core/model_observatory.py` — endpoints `/models/report`
- `core/tool_evolution.py` — endpoints `/tools/stats`, `/tools/rankings`, `/tools/evolution-report`
- `core/criticality_engine.py` — endpoints `/criticality/*`
- `core/information_layer.py` — endpoint `/info/redundancia`
- `core/metacognitive.py` — endpoint `/metacognitive/kalman`
- `core/predictive_controller.py` — endpoints `/predictive/trayectoria`, `/predictive/plan`

**Acción:**

1. Leer `core/db_pool.py` para entender la interfaz del pool compartido.

2. Subir el pool max de 10 a 25:
   - Buscar donde se configura `max_size` o `maxsize` del pool en `db_pool.py`
   - Cambiar de 10 a 25

3. Para CADA componente afectado:
   - Buscar funciones/métodos que crean conexiones propias (`_get_conn`, `asyncpg.connect`, `asyncpg.create_pool`, o similares)
   - Reemplazar por uso del pool compartido de `db_pool.py`
   - El patrón correcto es importar y usar el pool compartido, no crear conexiones nuevas

4. En `api.py`, asegurar que el pool se inicializa al startup y se pasa a todos los componentes.

**Verificación:** Después del cambio, estos endpoints deben devolver datos reales (no `"error": "no_db"`):
```
GET /models/report
GET /tools/stats
GET /tools/rankings
GET /tools/evolution-report
GET /criticality/temperatura
GET /criticality/avalanchas
GET /info/redundancia
GET /metacognitive/kalman
GET /predictive/trayectoria
GET /predictive/plan
```

---

### TAREA 1.3: Fix `/models/discover` (500 error)

**Problema:** `GET /models/discover` retorna 500 Internal Server Error. El ModelObservatory no puede descubrir modelos nuevos.

**Acción:**

1. Leer `core/model_observatory.py`, buscar el método que maneja `/models/discover`
2. Leer `api.py`, buscar la ruta `/models/discover` para ver cómo se llama
3. Ejecutar localmente o leer el traceback del error para identificar la causa
4. Fix el bug (probable: dependencia de DB no conectada, o API externa que falla)

**Verificación:** `GET /models/discover` retorna 200 con datos.

---

## FASE 2 — P1: Feedback loop funcional (~3h total)

### TAREA 2.1: Fix wiring Motor vN → programas_compilados

**Problema:** Hay 7 ejecuciones en tabla `ejecuciones` pero los 4 programas en `programas_compilados` tienen todos `n_ejecuciones=0` y `tasa_cierre_media=NULL`. El feedback loop está roto.

**Acción:**

1. Leer `core/motor_vn.py` — buscar dónde se registra una ejecución completada
2. Leer `core/gestor.py` — buscar dónde debería actualizarse `programas_compilados.n_ejecuciones` y `tasa_cierre_media`
3. Identificar el punto de desconexión: ¿el motor ejecuta pero no notifica al gestor? ¿El gestor recibe pero no actualiza la tabla?
4. Implementar el fix para que al completar una ejecución:
   - Se incremente `n_ejecuciones` en el programa correspondiente
   - Se recalcule `tasa_cierre_media` con los datapoints reales

**Verificación:** Ejecutar un análisis via `/gestor/compilar` o ruta equivalente, luego verificar que `programas_compilados` refleja la ejecución nueva.

---

### TAREA 2.2: Implementar consumo de marcas estigmérgicas

**Problema:** 7 alertas estigmérgicas de autopoiesis sin consumir (`marcas_estigmergicas` donde `consumida=false`). Nadie las lee ni actúa sobre ellas. El ciclo autopoiético está roto.

**Acción:**

1. Leer `core/mejora_continua.py` — entender el ciclo de mejora
2. Leer `core/gestor_scheduler.py` — el scheduler genera las marcas pero ¿quién las consume?
3. Implementar un consumidor de marcas:
   - Al inicio de cada ciclo del flywheel/autopoiesis, leer marcas no consumidas
   - Para alertas de tipo `alerta` con origen `gestor_scheduler`: disparar la acción correctiva correspondiente (ej: si `check_datapoints` falló, investigar por qué hay menos datapoints recientes)
   - Marcar como `consumida=true` después de procesar
4. Wiring: asegurar que el scheduler llama al consumidor

**Verificación:** 
- `GET /estigmergia/marcas` → las 7 alertas existentes pasan a `consumida=true`
- `GET /gestor/autopoiesis` → `ciclo_roto` debería cambiar (o al menos las alertas se procesaron)

---

## FASE 3 — P2: Limpieza y calidad (~2h total)

### TAREA 3.1: Separar scopes en knowledge_base

**Problema:** 27,133 de 27,482 entries (98.7%) son chunks de repo indexado. Solo 349 son knowledge real. El `hybrid_search` calcula sobre 99% de ruido.

**Acción:**

1. Leer `core/neural_db.py` — buscar la función `hybrid_search`
2. Modificar `hybrid_search` para que por defecto EXCLUYA scopes que empiecen con `repo` (ej: `repo`, `repo/documentation`, `repo/code`, etc.)
3. Añadir un parámetro `include_repo=False` que permita incluirlos explícitamente cuando sea necesario
4. El filtro SQL debería ser algo como: `WHERE scope NOT LIKE 'repo%'` por defecto

**Verificación:** `POST /neural/search` con una query genérica devuelve resultados de patrones/knowledge real, no chunks de código.

---

### TAREA 3.2: Limpiar duplicados en config

**Problema:** 
- `config_enjambre`: 10 rows para 5 tiers (2 por tier)
- `config_modelos`: duplicados en fontaneria (x2), razonador (x2), sintetizador (x2)

**Acción:**

1. Conectar a DB y diagnosticar duplicados:
```sql
-- Ver duplicados en config_enjambre
SELECT tier, count(*) FROM config_enjambre GROUP BY tier HAVING count(*) > 1;

-- Ver duplicados en config_modelos
SELECT rol, modelo, count(*) FROM config_modelos GROUP BY rol, modelo HAVING count(*) > 1;
```

2. Para cada grupo de duplicados, mantener el de `id` más alto (más reciente) y eliminar el otro:
```sql
-- Ejemplo para config_enjambre (ajustar IDs según resultado del diagnóstico)
DELETE FROM config_enjambre WHERE id IN (
  SELECT id FROM (
    SELECT id, ROW_NUMBER() OVER (PARTITION BY tier ORDER BY id DESC) as rn
    FROM config_enjambre
  ) t WHERE rn > 1
);

-- Ejemplo para config_modelos
DELETE FROM config_modelos WHERE id IN (
  SELECT id FROM (
    SELECT id, ROW_NUMBER() OVER (PARTITION BY rol, modelo ORDER BY id DESC) as rn
    FROM config_modelos
  ) t WHERE rn > 1
);
```

3. Añadir constraint UNIQUE para prevenir futuros duplicados:
```sql
ALTER TABLE config_enjambre ADD CONSTRAINT unique_tier UNIQUE (tier);
-- Para config_modelos, considerar: UNIQUE (rol, modelo) si aplica
```

**Verificación:** 
- `config_enjambre` tiene exactamente 5 rows (1 por tier)
- `config_modelos` no tiene duplicados

---

### TAREA 3.3: Unificar version string

**Problema:** Tres fuentes reportan versiones distintas:
- `api.py` FastAPI title: 2.0.0
- `/health`: 3.3.0
- `/version`: 3.4.0

**Acción:**

1. Crear o localizar un archivo de versión central. Opciones:
   - Variable en `core/__init__.py`: `VERSION = "3.4.0"`
   - O archivo `VERSION` en raíz del agent

2. Buscar en `api.py` todas las ocurrencias de version strings ("2.0.0", "3.3.0", "3.4.0") y reemplazarlas por import de la fuente central

3. La versión correcta es `3.4.0` (la más alta, la del endpoint `/version`)

**Verificación:**
- `GET /health` → version=3.4.0
- `GET /version` → version=3.4.0
- FastAPI docs title muestra 3.4.0

---

### TAREA 3.4: Setup pytest mínimo

**Problema:** 621 líneas de tests pero sin `pytest.ini`, sin forma estandarizada de ejecutarlos.

**Acción:**

1. Crear `motor_v1_validation/agent/pytest.ini`:
```ini
[pytest]
testpaths = tests core
python_files = test_*.py
python_functions = test_*
asyncio_mode = auto
```

2. Verificar que los tests existentes pasan:
```bash
cd motor_v1_validation/agent && python -m pytest tests/ core/test_*.py -v --tb=short
```

3. Si hay tests que fallan, documentar cuáles y por qué (no arreglarlos en este briefing, solo diagnosticar).

**Verificación:** `pytest` ejecuta sin errores de configuración. Los tests que funcionaban antes siguen funcionando.

---

## ORDEN DE EJECUCIÓN

```
1.1 (ALTER TABLE)           → 15 min
1.2 (Pool DB unificado)     → 1.5h
1.3 (Fix /models/discover)  → 30min
--- deploy parcial recomendado ---
2.1 (Fix feedback loop)     → 1.5h
2.2 (Consumo estigmergia)   → 1.5h
--- deploy parcial recomendado ---
3.1 (Scopes knowledge_base) → 30min
3.2 (Limpiar duplicados)    → 30min
3.3 (Version string)        → 15min
3.4 (pytest.ini)            → 30min
--- deploy final ---
```

## POST-EJECUCIÓN

Después de completar todas las tareas:

1. Ejecutar `pytest` completo y reportar resultado
2. Verificar los 16 endpoints que fallaban — reportar cuántos pasan ahora
3. Verificar `/gestor/autopoiesis` → ¿sigue `ciclo_roto=true`?
4. Verificar `/gestor/consistencia` → ¿mejoró?
5. Hacer `git add + commit + push` con mensaje: `fix: P0-P2 arreglos DB pool, ciclos rotos, limpieza config`
6. Deploy a fly.io
7. Actualizar `docs/sistema/ESTADO_REAL_SISTEMA.md` con los cambios realizados
