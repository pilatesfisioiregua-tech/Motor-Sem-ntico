# BRIEFING_11: Fontanería — 4 fixes para que el sistema funcione sin errores

Fecha: 2026-03-18
Prioridad: 1 (bloqueante para todo lo demás)
Prerequisito: pgvector F1 completado (BRIEFING_10/10B)

---

## CONTEXTO

67 endpoints, 51 OK, 16 con errores. Los errores se dividen en 2 categorías:
1. **Columnas SQL que no existen** — causan excepciones que se atrapan como "no_db"
2. **Datos inconsistentes** — duplicados, contadores rotos, huérfanos

Este briefing arregla las 4 causas raíz de golpe.

---

## FIX 1: Añadir `created_at` a `preguntas_matriz`

### Problema
- `/gestor/obsoletas` → ERROR: `column "created_at" does not exist`
- `/gestor/expiradas` → ERROR: `column "created_at" does not exist`
- Gestor pasos 8 y 10 fallan (poda y expiración de preguntas)

### Solución
Crear migración `migrations/013_fix_fontaneria.sql` con TODO junto:

```sql
-- =================================================================
-- Migration 013: Fontanería — fix columnas, limpiar duplicados
-- =================================================================

-- ── FIX 1: Añadir created_at a preguntas_matriz ──────────────────

ALTER TABLE preguntas_matriz 
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();

-- Backfill: las preguntas existentes se marcan como creadas hace 7 días
-- (para que no se expire todo de golpe)
UPDATE preguntas_matriz 
SET created_at = NOW() - INTERVAL '7 days'
WHERE created_at IS NULL;
```

### Verificación
```sql
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'preguntas_matriz' AND column_name = 'created_at';
-- Debe devolver 1 row
```

---

## FIX 2: Añadir `calibrado` a `datapoints_efectividad`

### Problema
`criticality_engine.py` línea ~58 hace:
```sql
WHERE timestamp > NOW() - INTERVAL '7 days' AND calibrado = true
```
Pero `datapoints_efectividad` NO tiene columna `calibrado`. Esto causa excepciones que se capturan genéricamente y se reportan como "no_db" o "error".

**Esto es la causa raíz de la mayoría de los 16 endpoints con errores.** No es el pool (ya tiene maxconn=25). Son SQL errors silenciosos.

### Investigación necesaria
Antes de añadir la columna, Claude Code DEBE buscar TODAS las referencias a `calibrado` en el código:

```bash
grep -rn "calibrado" /Users/jesusfernandezdominguez/omni-mind-cerebro/motor-semantico/motor_v1_validation/agent/core/
```

Así sabremos:
- Quién escribe `calibrado` (probablemente registrador.py)
- Quién lee `calibrado` (criticality_engine.py, y posiblemente otros)
- Qué lógica asume sobre su valor

### Solución (en la misma migración 013)
```sql
-- ── FIX 2: Añadir calibrado a datapoints_efectividad ────────────

ALTER TABLE datapoints_efectividad
    ADD COLUMN IF NOT EXISTS calibrado BOOLEAN DEFAULT false;

-- Marcar los 29 datapoints reales (motor_vn) como calibrados
UPDATE datapoints_efectividad SET calibrado = true 
WHERE consumidor = 'motor_vn';

-- Los seeds/tests quedan calibrado=false (no contaminan métricas)
```

### Verificación
```sql
SELECT calibrado, count(*) FROM datapoints_efectividad GROUP BY calibrado;
-- Debe devolver: true=29, false=133

-- Y criticality debe funcionar:
SELECT AVG(tasa_cierre), STDDEV(tasa_cierre), COUNT(*) 
FROM datapoints_efectividad 
WHERE timestamp > NOW() - INTERVAL '30 days' AND calibrado = true;
-- Debe devolver datos, no error
```

### Post-fix: Verificar que los endpoints "no_db" ahora funcionan
Después de aplicar FIX 2, probar estos endpoints:
```
GET /criticality/temperatura
GET /criticality/avalanchas
GET /criticality/estado
GET /metacognitive/kalman
GET /predictive/trayectoria
GET /predictive/plan
GET /info/redundancia
GET /models/report
GET /tools/stats
GET /tools/rankings
GET /tools/evolution-report
```

Si alguno sigue fallando, leer el traceback del error real (no el "no_db" genérico) y reportar la causa exacta.

---

## FIX 3: Diagnosticar y arreglar contadores de programas_compilados

### Problema
4 programas compilados, todos con `n_ejecuciones=0` y `tasa_cierre_media=NULL`. Las 7 ejecuciones del Motor no actualizaron los contadores.

### Investigación necesaria
1. Verificar si `_persistir_programa()` devuelve un ID válido:
```bash
grep -n "programa_db_id" /Users/jesusfernandezdominguez/omni-mind-cerebro/motor-semantico/motor_v1_validation/agent/core/motor_vn.py
```

2. Verificar los consumidor keys en la DB:
```sql
SELECT id, consumidor, n_ejecuciones, tasa_cierre_media FROM programas_compilados;
```

3. Comparar con los consumidor keys que el Motor genera:
   - El Motor usa `f"{consumidor}_{modo}"` → ej: `"motor_vn_analisis"`
   - Si la DB tiene keys diferentes, hay un mismatch

### Probable causa
El Motor escribe `consumidor = "motor_vn_analisis"`, pero las 7 ejecuciones usan un consumidor diferente. O `_persistir_programa` falla silenciosamente y `programa_db_id` es None, así que `_actualizar_programa_post_ejecucion` early-returns.

### Solución
Depende de la investigación. Probables fixes:
- Si es mismatch de keys: UPDATE para alinear
- Si es `programa_db_id = None`: fix en `_persistir_programa` o en cómo se pasa el consumidor
- Backfill manual de contadores basado en datos de `ejecuciones`:

```sql
-- Backfill: contar ejecuciones reales por modo y actualizar
UPDATE programas_compilados SET n_ejecuciones = 7, 
       tasa_cierre_media = (SELECT AVG(score_calidad)/10.0 FROM ejecuciones WHERE modo = 'analisis')
WHERE consumidor = 'motor_vn_analisis';
```

**Claude Code debe diagnosticar primero, luego aplicar el fix correcto.**

---

## FIX 4: Limpiar duplicados en config

### Problema
- `config_enjambre`: 10 rows para 5 tiers (debería ser 5)
- `config_modelos`: Duplicados en fontaneria (×2), razonador (×2), sintetizador (×2)

### Solución (en la misma migración 013)

```sql
-- ── FIX 4A: Deduplicar config_enjambre ───────────────────────────
-- Mantener el más reciente por tier
DELETE FROM config_enjambre a
USING config_enjambre b
WHERE a.tier = b.tier 
  AND a.id < b.id;

-- Verificar
SELECT tier, count(*) FROM config_enjambre GROUP BY tier ORDER BY tier;
-- Debe devolver 5 rows, count=1 cada una

-- ── FIX 4B: Deduplicar config_modelos ────────────────────────────
-- Mantener el más reciente por rol
DELETE FROM config_modelos a
USING config_modelos b
WHERE a.rol = b.rol 
  AND a.modelo = b.modelo
  AND a.id < b.id;

-- Verificar
SELECT rol, modelo, count(*) FROM config_modelos GROUP BY rol, modelo HAVING count(*) > 1;
-- Debe devolver 0 rows

-- ── FIX 4C: Añadir UNIQUE constraint para prevenir futuros duplicados ──
-- (solo si no existe ya)
CREATE UNIQUE INDEX IF NOT EXISTS idx_config_enjambre_tier_unique ON config_enjambre(tier);
-- config_modelos: no poner unique en (rol) porque un rol puede tener múltiples modelos.
-- Pero sí en (rol, modelo):
CREATE UNIQUE INDEX IF NOT EXISTS idx_config_modelos_rol_modelo_unique ON config_modelos(rol, modelo);
```

### Verificación
```sql
SELECT count(*) FROM config_enjambre; -- Debe ser 5
SELECT count(*) FROM config_modelos;  -- Debe ser 8-10 (sin duplicados)
SELECT * FROM config_modelos ORDER BY rol;
```

---

## FIX 5 (bonus): Fix `/models/discover` → 500

### Problema
El endpoint `/models/discover` devuelve 500 Internal Server Error.

### Investigación
Claude Code debe:
1. Encontrar el endpoint en `api.py` (buscar `models/discover`)
2. Leer el handler y trazar la cadena de llamadas
3. Ejecutar el código relevante de `model_observatory.py` para ver el error real
4. Reportar el traceback y aplicar fix

---

## ORDEN DE EJECUCIÓN

```
PASO 1: Investigar (antes de tocar nada)
  - grep "calibrado" en todo core/ → listar todos los archivos que lo usan
  - SELECT consumidor FROM programas_compilados → ver keys actuales
  - Encontrar handler de /models/discover en api.py → leer traceback del 500

PASO 2: Crear y ejecutar migración 013
  - Escribir migrations/013_fix_fontaneria.sql con FIX 1 + 2 + 4
  - fly proxy 15432:5432 -a omni-mind-db (si no está activo)
  - psql ... -f migrations/013_fix_fontaneria.sql

PASO 3: Fix programas_compilados (FIX 3)
  - Basado en investigación del PASO 1, aplicar el fix correcto
  - Puede ser SQL directo o edición de código

PASO 4: Fix /models/discover (FIX 5)
  - Basado en investigación del PASO 1, aplicar fix

PASO 5: Verificar TODOS los endpoints que fallaban
  - curl cada uno de los 16 endpoints que tenían errores
  - Reportar cuáles se arreglaron y cuáles siguen rotos (con error REAL, no "no_db")
```

---

## CRITERIO DE ÉXITO

- [ ] `preguntas_matriz` tiene `created_at` — `/gestor/obsoletas` y `/gestor/expiradas` devuelven datos
- [ ] `datapoints_efectividad` tiene `calibrado` — endpoints de criticality/predictive/metacognitive funcionan
- [ ] `programas_compilados` tiene n_ejecuciones > 0 para al menos 1 programa
- [ ] `config_enjambre` tiene exactamente 5 rows (1 por tier)
- [ ] `config_modelos` no tiene duplicados
- [ ] `/models/discover` devuelve 200 (no 500)
- [ ] De los 16 endpoints rotos, al menos 12 ahora funcionan

## COSTE
$0 — solo SQL y ediciones de código
