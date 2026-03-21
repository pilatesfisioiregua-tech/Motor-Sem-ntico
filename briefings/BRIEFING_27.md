# BRIEFING_27: Fix bugs Fase 1 — Sistema Cognitivo Operativo

Fecha: 2026-03-18
Contexto: Plan aprobado CR1 en `docs/operativo/PLAN_SISTEMA_COGNITIVO_v1.md`
Objetivo: Resolver los 10 bugs identificados en la auditoría del sistema cognitivo

---

## Pre-condiciones
- App desplegada en fly.io como `chief-os-omni`
- DB: `omni_mind` en `motor-semantico-db` (fly.io Postgres, Amsterdam)
- Código en: `motor_v1_validation/agent/`

## FIX 1: SQL `created_at` en endpoints (YA APLICADO en api.py)
Los endpoints `/gestor/obsoletas` y `/gestor/expiradas` ya fueron fixeados:
- Se eliminó `created_at` del SELECT y ORDER BY
- Se usa `ORDER BY id DESC` en su lugar
**Acción:** Verificar que el fix está en api.py (líneas ~1782 y ~1831). NO tocar.

## FIX 2: DB migration — añadir `created_at` a `preguntas_matriz`
Aunque los endpoints ya no lo necesitan, otros componentes podrían beneficiarse.
```sql
ALTER TABLE preguntas_matriz ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();
```
**Ejecutar contra la DB de fly.io.**

## FIX 3: Verificar/crear tablas faltantes
`proactive.py` referencia `presupuestos` y `costes_llm`. `registrador.py` referencia `celdas_matriz`.
Verificar si existen. Si no, crear con schema mínimo:

```sql
-- Presupuestos (para proactive.py health_check)
CREATE TABLE IF NOT EXISTS presupuestos (
    id SERIAL PRIMARY KEY,
    consumidor TEXT NOT NULL,
    limite_mensual_usd FLOAT DEFAULT 50.0,
    activo BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Costes LLM (para proactive.py y tracking de costes)
CREATE TABLE IF NOT EXISTS costes_llm (
    id SERIAL PRIMARY KEY,
    consumidor TEXT NOT NULL,
    modelo TEXT NOT NULL,
    tokens_in INTEGER DEFAULT 0,
    tokens_out INTEGER DEFAULT 0,
    coste_total_usd FLOAT DEFAULT 0.0,
    componente TEXT,
    operacion TEXT,
    celda TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Celdas Matriz (para registrador.py update incremental)
CREATE TABLE IF NOT EXISTS celdas_matriz (
    id TEXT PRIMARY KEY,
    funcion TEXT NOT NULL,
    lente TEXT NOT NULL,
    n_datapoints INTEGER DEFAULT 0,
    tasa_media FLOAT DEFAULT 0.0,
    grado_actual FLOAT DEFAULT 0.0,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Seed celdas_matriz con las 21 celdas (3 lentes × 7 funciones)
INSERT INTO celdas_matriz (id, funcion, lente)
SELECT f || 'x' || l, f, l
FROM (VALUES ('Conservar'),('Captar'),('Depurar'),('Distribuir'),('Frontera'),('Adaptar'),('Replicar')) AS funciones(f)
CROSS JOIN (VALUES ('Salud'),('Sentido'),('Continuidad')) AS lentes(l)
ON CONFLICT (id) DO NOTHING;

-- Seed presupuesto default
INSERT INTO presupuestos (consumidor, limite_mensual_usd)
VALUES ('sistema', 50.0), ('motor_vn', 20.0), ('code_os', 30.0)
ON CONFLICT DO NOTHING;
```

## FIX 4: Limpiar duplicados en config
```sql
-- Dedup config_enjambre: mantener solo 1 row por tier (el más reciente)
DELETE FROM config_enjambre
WHERE id NOT IN (
    SELECT MAX(id) FROM config_enjambre GROUP BY tier
);

-- Dedup config_modelos: mantener solo 1 row por rol (el más reciente)
DELETE FROM config_modelos
WHERE id NOT IN (
    SELECT MAX(id) FROM config_modelos GROUP BY rol
);
```

## FIX 5: Unificar versión
En `core/__init__.py`, la versión ya es "3.4.0". El title de FastAPI ya fue actualizado a "Code OS v3 API".
Incrementar a "3.5.0" para marcar esta sesión de fixes:
```python
# core/__init__.py
VERSION = "3.5.0"
```

## FIX 6: Fix contadores programas_compilados
En `core/registrador.py`, dentro de `registrar_ejecucion()`, después del commit de datapoints, añadir:
```python
# Incrementar n_ejecuciones en programas_compilados del consumidor
try:
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE programas_compilados
            SET n_ejecuciones = n_ejecuciones + 1
            WHERE consumidor = %s AND activo = true
        """, [consumidor])
    conn.commit()
except Exception:
    try:
        conn.rollback()
    except Exception:
        pass
```

## FIX 7: Consumir alertas estigmérgicas stale
```sql
UPDATE marcas_estigmergicas SET consumida = true
WHERE consumida = false AND tipo = 'alerta'
  AND contenido->>'tipo' = 'autopoiesis_roto';
```

## FIX 8: Fix `/models/discover` — robustecer subprocess
En `core/model_observatory.py`, el método `discover_models()` usa `subprocess.run(curl...)`.
El 500 probablemente viene de que en fly.io no hay curl o la API key no está disponible.
Envolver en try/except más robusto y devolver error descriptivo en vez de 500.

Buscar la función `discover_models` y asegurar que:
1. El try/except captura CUALQUIER excepción
2. Devuelve JSON con error descriptivo, nunca 500
3. Si no hay OPENROUTER_API_KEY, devuelve error limpio

## FIX 9: Limpiar KB noise
NO purgar los 27K chunks de repo por ahora — podrían ser útiles para Code OS.
En su lugar, añadir un flag para que neural_db search pueda filtrarlos:
```sql
-- Añadir columna para marcar scope como indexable o no
-- (no cambiar nada más por ahora)
```
**SKIP** — esto se aborda en Fase 3 cuando tengamos datos reales.

## FIX 10: Fix pool de conexiones
Los 16 endpoints con "no_db" usan `_get_conn()` local en vez de `db_pool.get_conn()`.
Verificar que `model_observatory.py`, `tool_evolution.py`, `criticality_engine.py`,
`information_layer.py`, `metacognitive.py`, `predictive_controller.py` y `flywheel.py`
todos importan de `db_pool` correctamente.

El patrón correcto es:
```python
from .db_pool import get_conn, put_conn
```

Si alguno usa su propio `_get_conn()`, verificar que internamente llama a `db_pool.get_conn()`.

---

## Criterios PASS/FAIL

### PASS si:
1. `SELECT COUNT(*) FROM preguntas_matriz WHERE created_at IS NOT NULL` > 0 (migration aplicada)
2. `SELECT COUNT(*) FROM presupuestos` > 0 (tabla creada y seeded)
3. `SELECT COUNT(*) FROM celdas_matriz` = 21 (21 celdas seeded)
4. `SELECT COUNT(*) FROM config_enjambre` = 5 (dedup OK)
5. `SELECT COUNT(*) FROM marcas_estigmergicas WHERE consumida = false AND tipo = 'alerta'` = 0
6. VERSION en core/__init__.py es "3.5.0"
7. Los endpoints `/gestor/obsoletas` y `/gestor/expiradas` no dan SQL error
8. Deploy exitoso a fly.io

### FAIL si:
- Cualquier SQL error en la migration
- Deploy falla
- Endpoints siguen devolviendo SQL error post-deploy

---

## Orden de ejecución
1. Aplicar SQL migrations contra DB de fly.io (FIX 2, 3, 4, 7)
2. Editar código (FIX 5, 6, 8, 10)
3. Verificar FIX 1 ya aplicado
4. Deploy a fly.io
5. Hit endpoints para verificar (FIX 1 especialmente)
6. Reportar PASS/FAIL con evidencia
