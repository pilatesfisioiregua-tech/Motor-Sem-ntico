# B-ORG-F2 — Fase 2: Cimientos Pizarras + CQRS + Polish

**Fecha:** 24 marzo 2026
**Estimación:** ~7h
**Prerequisito:** B-ORG-PRODUCCION ejecutado (F0+F1)
**WIP:** 1 (secuencial)
**Principios:** P64 (11 pizarras), P65 (CQRS + LISTEN/NOTIFY + snapshots + HNSW), P66 (circuitos)

---

## OBJETIVO

Crear la infraestructura de pizarras (P64) que será el esqueleto del sistema. Las pizarras son tablas de LECTURA (capa de consulta). Las tablas operacionales (om_clientes, om_pagos, etc.) son la capa de ESCRITURA. CQRS natural.

Después: polish del código existente y limpieza de código muerto.

---

## ARCHIVOS A LEER ANTES DE EMPEZAR

```
src/main.py
src/pilates/cron.py
src/pilates/router.py
src/pilates/recompilador.py
src/pilates/director_opus.py
src/pilates/autofago.py
src/pilates/generativa.py
src/conocimiento.py
src/pilates/pizarra.py          (la pizarra Estado que ya existe)
migrations/020_redsys.sql        (para ver formato migraciones)
```

---

## PASO 0: MIGRACIÓN SQL (028_pizarras_cqrs.sql)

Crear archivo: `migrations/028_pizarras_cqrs.sql`

```sql
-- 028_pizarras_cqrs.sql — 6 pizarras nuevas + snapshots + HNSW + LISTEN/NOTIFY
-- Fase 2 del Roadmap v4 (P64 + P65)

-- ============================================================
-- 1. PIZARRA DOMINIO — el "quién soy" del tenant
-- ============================================================
CREATE TABLE IF NOT EXISTS om_pizarra_dominio (
    tenant_id TEXT PRIMARY KEY,
    nombre TEXT NOT NULL,
    config JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

INSERT INTO om_pizarra_dominio (tenant_id, nombre, config)
VALUES ('authentic_pilates', 'Authentic Pilates', '{
    "timezone": "Europe/Madrid",
    "moneda": "EUR",
    "datos_clinicos": true,
    "funciones_activas": ["F1","F2","F3","F4","F5","F6","F7"],
    "telefono_dueno": "34607466631",
    "email": "pilatesfisioiregua@gmail.com",
    "idioma": "es",
    "ubicacion": "Albelda de Iregua, La Rioja",
    "clientes_activos_aprox": 90,
    "poblacion_aprox": 4000
}')
ON CONFLICT (tenant_id) DO NOTHING;

-- ============================================================
-- 2. PIZARRA COGNITIVA — recetas del Director para agentes
-- ============================================================
CREATE TABLE IF NOT EXISTS om_pizarra_cognitiva (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL,
    ciclo TEXT NOT NULL,
    funcion TEXT NOT NULL,
    lente TEXT,
    prioridad INT DEFAULT 5,
    ints TEXT[] NOT NULL DEFAULT '{}',
    ps TEXT[] DEFAULT '{}',
    rs TEXT[] DEFAULT '{}',
    prompt_imperativo TEXT,
    prompt_preguntas TEXT,
    prompt_provocacion TEXT,
    prompt_razonamiento TEXT,
    intencion TEXT,
    origen TEXT DEFAULT 'director',
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_pcog_tenant_ciclo ON om_pizarra_cognitiva(tenant_id, ciclo);
CREATE INDEX IF NOT EXISTS idx_pcog_funcion ON om_pizarra_cognitiva(funcion);

-- ============================================================
-- 3. PIZARRA TEMPORAL — qué ejecutar, en qué orden, en qué ciclo
-- ============================================================
CREATE TABLE IF NOT EXISTS om_pizarra_temporal (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL,
    ciclo TEXT NOT NULL,
    fase TEXT NOT NULL,
    orden INT NOT NULL,
    componente TEXT NOT NULL,
    activo BOOLEAN DEFAULT true,
    motivo TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_ptemp_tenant_ciclo ON om_pizarra_temporal(tenant_id, ciclo);

-- ============================================================
-- 4. PIZARRA MODELOS — qué modelo usar para qué función/lente/complejidad
-- ============================================================
CREATE TABLE IF NOT EXISTS om_pizarra_modelos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL,
    funcion TEXT NOT NULL,
    lente TEXT,
    complejidad TEXT DEFAULT 'media',
    modelo TEXT NOT NULL,
    score_historico FLOAT,
    ultima_evaluacion TIMESTAMPTZ,
    origen TEXT DEFAULT 'default',
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_pmod_lookup ON om_pizarra_modelos(tenant_id, funcion, lente, complejidad);

-- Seeds con modelos actuales
INSERT INTO om_pizarra_modelos (tenant_id, funcion, complejidad, modelo, origen) VALUES
    ('authentic_pilates', '*', 'baja', 'deepseek/deepseek-v3.2', 'default'),
    ('authentic_pilates', '*', 'media', 'openai/gpt-4o', 'default'),
    ('authentic_pilates', '*', 'alta', 'anthropic/claude-opus-4', 'default'),
    ('authentic_pilates', 'F5', 'alta', 'anthropic/claude-opus-4', 'default')
ON CONFLICT DO NOTHING;

-- ============================================================
-- 5. PIZARRA EVOLUCIÓN — patrones aprendidos por el sistema
-- ============================================================
CREATE TABLE IF NOT EXISTS om_pizarra_evolucion (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL,
    tipo TEXT NOT NULL,
    descripcion TEXT NOT NULL,
    datos JSONB,
    confianza FLOAT DEFAULT 0.5,
    evidencia_ciclos INT DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_pevo_tenant_tipo ON om_pizarra_evolucion(tenant_id, tipo);

-- ============================================================
-- 6. PIZARRA INTERFAZ — qué módulos mostrar y con qué prioridad
-- ============================================================
CREATE TABLE IF NOT EXISTS om_pizarra_interfaz (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL,
    ciclo TEXT NOT NULL,
    modulo TEXT NOT NULL,
    rol TEXT DEFAULT 'secundario',
    prioridad INT DEFAULT 5,
    motivo TEXT,
    origen TEXT DEFAULT 'default',
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_pint_tenant_ciclo ON om_pizarra_interfaz(tenant_id, ciclo);

-- ============================================================
-- 7. TABLA SNAPSHOTS — "git del organismo" (P65)
-- ============================================================
CREATE TABLE IF NOT EXISTS om_pizarra_snapshot (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL,
    ciclo TEXT NOT NULL,
    tipo_pizarra TEXT NOT NULL,
    contenido JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_snap_tenant_ciclo ON om_pizarra_snapshot(tenant_id, ciclo);
CREATE INDEX IF NOT EXISTS idx_snap_tipo ON om_pizarra_snapshot(tipo_pizarra);

-- ============================================================
-- 8. HNSW INDEX en corpus (P65) — ~800 vectores
-- ============================================================
-- Solo crear si la extensión pgvector está activa y la tabla existe
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'om_conocimiento') THEN
        EXECUTE 'CREATE INDEX IF NOT EXISTS idx_conocimiento_hnsw ON om_conocimiento USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64)';
    END IF;
END $$;

-- ============================================================
-- 9. CORPUS → GRAFO SEMÁNTICO (P65)
-- ============================================================
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'om_conocimiento') THEN
        ALTER TABLE om_conocimiento ADD COLUMN IF NOT EXISTS superseded_by UUID;
        ALTER TABLE om_conocimiento ADD COLUMN IF NOT EXISTS depends_on UUID[];
        ALTER TABLE om_conocimiento ADD COLUMN IF NOT EXISTS cluster TEXT;
        ALTER TABLE om_conocimiento ADD COLUMN IF NOT EXISTS relevancia_decreciente FLOAT DEFAULT 1.0;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_conocimiento_cluster ON om_conocimiento(cluster);

-- ============================================================
-- 10. LISTEN/NOTIFY para señales urgentes (P65)
-- ============================================================
CREATE OR REPLACE FUNCTION notify_senal_urgente() RETURNS trigger AS $$
BEGIN
    IF NEW.prioridad IS NOT NULL AND NEW.prioridad <= 2 THEN
        PERFORM pg_notify('senal_urgente', json_build_object(
            'id', NEW.id,
            'tipo', NEW.tipo_senal,
            'origen', NEW.origen,
            'prioridad', NEW.prioridad
        )::text);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Aplicar trigger si la tabla existe
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'om_senales_agentes') THEN
        DROP TRIGGER IF EXISTS trg_senal_urgente ON om_senales_agentes;
        CREATE TRIGGER trg_senal_urgente
            AFTER INSERT ON om_senales_agentes
            FOR EACH ROW EXECUTE FUNCTION notify_senal_urgente();
    END IF;
END $$;
```

**Test 0.1:** `SELECT count(*) FROM om_pizarra_dominio WHERE tenant_id='authentic_pilates'` → 1
**Test 0.2:** `SELECT count(*) FROM om_pizarra_modelos` → 4
**Test 0.3:** `SELECT config->>'telefono_dueno' FROM om_pizarra_dominio WHERE tenant_id='authentic_pilates'` → `34607466631`

---

## PASO 1: HELPER pizarras.py — lectura universal

Crear archivo: `src/pilates/pizarras.py`

```python
"""Pizarras — lectura universal de las 11 pizarras del organismo (P64).

Cada función lee de DB con fallback a defaults razonables.
Las pizarras son CAPA DE LECTURA (CQRS). Nunca escriben datos operacionales.

Pizarras:
  1. Estado      → om_pizarra (ya existe)
  2. Conocimiento → corpus MCP (externo)
  3. Dominio     → om_pizarra_dominio
  4. Cognitiva   → om_pizarra_cognitiva
  5. Temporal    → om_pizarra_temporal
  6. Modelos     → om_pizarra_modelos
  7. Evolución   → om_pizarra_evolucion
  8. Interfaz    → om_pizarra_interfaz
  9. Comunicación → (Fase 5)
  10. Caché LLM   → (Fase 4)
  11. Identidad   → (Fase 7)
"""
from __future__ import annotations

import json
import structlog
from datetime import datetime
from typing import Optional
from uuid import UUID

log = structlog.get_logger()

DEFAULT_TENANT = "authentic_pilates"

DEFAULT_DOMINIO = {
    "tenant_id": DEFAULT_TENANT,
    "nombre": "Authentic Pilates",
    "config": {
        "timezone": "Europe/Madrid",
        "moneda": "EUR",
        "datos_clinicos": True,
        "funciones_activas": ["F1", "F2", "F3", "F4", "F5", "F6", "F7"],
        "idioma": "es",
        "ubicacion": "Albelda de Iregua, La Rioja",
    },
}


async def _get_pool():
    from src.db.client import get_pool
    return await get_pool()


# ============================================================
# PIZARRA DOMINIO (#3)
# ============================================================

async def leer_dominio(tenant_id: str = DEFAULT_TENANT) -> dict:
    """Lee configuración del tenant desde pizarra dominio."""
    try:
        pool = await _get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM om_pizarra_dominio WHERE tenant_id = $1", tenant_id)
            if row:
                config = row["config"] if isinstance(row["config"], dict) else json.loads(row["config"])
                return {
                    "tenant_id": row["tenant_id"],
                    "nombre": row["nombre"],
                    "config": config,
                }
    except Exception as e:
        log.warning("pizarra_dominio_fallback", error=str(e)[:80])
    return DEFAULT_DOMINIO


async def leer_timezone(tenant_id: str = DEFAULT_TENANT) -> str:
    """Shortcut: timezone del tenant."""
    dom = await leer_dominio(tenant_id)
    return dom["config"].get("timezone", "Europe/Madrid")


async def leer_telefono_dueno(tenant_id: str = DEFAULT_TENANT) -> str:
    """Shortcut: teléfono del dueño."""
    dom = await leer_dominio(tenant_id)
    return dom["config"].get("telefono_dueno", "")


# ============================================================
# PIZARRA MODELOS (#6)
# ============================================================

async def leer_modelo(tenant_id: str, funcion: str, lente: str = None,
                      complejidad: str = "media") -> str:
    """Devuelve el modelo óptimo para función+lente+complejidad.

    Búsqueda: función+lente+complejidad → función+complejidad → *+complejidad → default.
    """
    try:
        pool = await _get_pool()
        async with pool.acquire() as conn:
            # Intento 1: match exacto
            if lente:
                modelo = await conn.fetchval("""
                    SELECT modelo FROM om_pizarra_modelos
                    WHERE tenant_id=$1 AND funcion=$2 AND lente=$3 AND complejidad=$4
                    ORDER BY score_historico DESC NULLS LAST LIMIT 1
                """, tenant_id, funcion, lente, complejidad)
                if modelo:
                    return modelo

            # Intento 2: función + complejidad (sin lente)
            modelo = await conn.fetchval("""
                SELECT modelo FROM om_pizarra_modelos
                WHERE tenant_id=$1 AND funcion=$2 AND lente IS NULL AND complejidad=$3
                ORDER BY score_historico DESC NULLS LAST LIMIT 1
            """, tenant_id, funcion, complejidad)
            if modelo:
                return modelo

            # Intento 3: wildcard
            modelo = await conn.fetchval("""
                SELECT modelo FROM om_pizarra_modelos
                WHERE tenant_id=$1 AND funcion='*' AND complejidad=$2
                ORDER BY score_historico DESC NULLS LAST LIMIT 1
            """, tenant_id, complejidad)
            if modelo:
                return modelo

    except Exception as e:
        log.warning("pizarra_modelos_fallback", error=str(e)[:80])

    # Fallback hardcoded
    defaults = {"baja": "deepseek/deepseek-v3.2", "media": "openai/gpt-4o", "alta": "anthropic/claude-opus-4"}
    return defaults.get(complejidad, "openai/gpt-4o")


# ============================================================
# PIZARRA COGNITIVA (#4)
# ============================================================

async def leer_recetas_ciclo(tenant_id: str, ciclo: str) -> list[dict]:
    """Lee todas las recetas del Director para un ciclo."""
    try:
        pool = await _get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM om_pizarra_cognitiva
                WHERE tenant_id=$1 AND ciclo=$2
                ORDER BY prioridad ASC
            """, tenant_id, ciclo)
            return [dict(r) for r in rows]
    except Exception:
        return []


# ============================================================
# PIZARRA TEMPORAL (#5)
# ============================================================

async def leer_plan_ciclo(tenant_id: str, ciclo: str) -> list[dict]:
    """Lee el plan temporal (qué componentes ejecutar, en qué orden)."""
    try:
        pool = await _get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM om_pizarra_temporal
                WHERE tenant_id=$1 AND ciclo=$2 AND activo=true
                ORDER BY fase, orden
            """, tenant_id, ciclo)
            return [dict(r) for r in rows]
    except Exception:
        return []


# ============================================================
# PIZARRA EVOLUCIÓN (#7)
# ============================================================

async def leer_patrones(tenant_id: str, tipo: str = None,
                        min_confianza: float = 0.3) -> list[dict]:
    """Lee patrones aprendidos, filtrados por tipo y confianza."""
    try:
        pool = await _get_pool()
        async with pool.acquire() as conn:
            query = """
                SELECT * FROM om_pizarra_evolucion
                WHERE tenant_id=$1 AND confianza >= $2
            """
            params = [tenant_id, min_confianza]
            if tipo:
                query += " AND tipo = $3"
                params.append(tipo)
            query += " ORDER BY confianza DESC, evidencia_ciclos DESC"
            rows = await conn.fetch(query, *params)
            return [dict(r) for r in rows]
    except Exception:
        return []


# ============================================================
# PIZARRA INTERFAZ (#8)
# ============================================================

async def leer_layout_ciclo(tenant_id: str, ciclo: str) -> list[dict]:
    """Lee el layout del cockpit para un ciclo."""
    try:
        pool = await _get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM om_pizarra_interfaz
                WHERE tenant_id=$1 AND ciclo=$2
                ORDER BY prioridad ASC
            """, tenant_id, ciclo)
            return [dict(r) for r in rows]
    except Exception:
        return []


# ============================================================
# SNAPSHOTS (P65) — "git del organismo"
# ============================================================

async def crear_snapshot(tenant_id: str, ciclo: str, tipo_pizarra: str,
                         contenido: dict) -> Optional[UUID]:
    """Crea un snapshot de una pizarra para un ciclo."""
    try:
        pool = await _get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO om_pizarra_snapshot (tenant_id, ciclo, tipo_pizarra, contenido)
                VALUES ($1, $2, $3, $4::jsonb)
                RETURNING id
            """, tenant_id, ciclo, tipo_pizarra, json.dumps(contenido, default=str))
            return row["id"] if row else None
    except Exception as e:
        log.warning("snapshot_error", error=str(e)[:80])
        return None


async def snapshot_todas(tenant_id: str, ciclo: str) -> dict:
    """Crea snapshots de TODAS las pizarras existentes para un ciclo.

    Se llama al final de cada ciclo semanal.
    """
    resultados = {}

    # Dominio
    dom = await leer_dominio(tenant_id)
    sid = await crear_snapshot(tenant_id, ciclo, "dominio", dom)
    resultados["dominio"] = str(sid) if sid else "error"

    # Cognitiva
    recetas = await leer_recetas_ciclo(tenant_id, ciclo)
    sid = await crear_snapshot(tenant_id, ciclo, "cognitiva", {"recetas": recetas})
    resultados["cognitiva"] = str(sid) if sid else "error"

    # Temporal
    plan = await leer_plan_ciclo(tenant_id, ciclo)
    sid = await crear_snapshot(tenant_id, ciclo, "temporal", {"plan": plan})
    resultados["temporal"] = str(sid) if sid else "error"

    # Modelos
    try:
        pool = await _get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM om_pizarra_modelos WHERE tenant_id=$1", tenant_id)
            modelos = [dict(r) for r in rows]
    except Exception:
        modelos = []
    sid = await crear_snapshot(tenant_id, ciclo, "modelos", {"modelos": modelos})
    resultados["modelos"] = str(sid) if sid else "error"

    # Evolución
    patrones = await leer_patrones(tenant_id, min_confianza=0.0)
    sid = await crear_snapshot(tenant_id, ciclo, "evolucion", {"patrones": patrones})
    resultados["evolucion"] = str(sid) if sid else "error"

    # Interfaz
    layout = await leer_layout_ciclo(tenant_id, ciclo)
    sid = await crear_snapshot(tenant_id, ciclo, "interfaz", {"layout": layout})
    resultados["interfaz"] = str(sid) if sid else "error"

    # Estado (om_pizarra existente)
    try:
        pool = await _get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM om_pizarra WHERE tenant_id=$1", tenant_id)
            estado = [dict(r) for r in rows]
    except Exception:
        estado = []
    sid = await crear_snapshot(tenant_id, ciclo, "estado", {"estado": estado})
    resultados["estado"] = str(sid) if sid else "error"

    log.info("snapshot_todas_ok", ciclo=ciclo, pizarras=len(resultados))
    return resultados
```

**Test 1.1:** `python -c "from src.pilates.pizarras import leer_dominio; print('ok')"` → ok (importación sin error)
**Test 1.2:** Después del deploy: `leer_dominio('authentic_pilates')` → dict con config.telefono_dueno = "34607466631"
**Test 1.3:** `leer_modelo('authentic_pilates', 'F5', 'sentido', 'alta')` → "anthropic/claude-opus-4"
**Test 1.4:** `leer_modelo('authentic_pilates', 'F99', None, 'baja')` → "deepseek/deepseek-v3.2" (wildcard fallback)

---

## PASO 2: SNAPSHOTS EN CRON SEMANAL (src/pilates/cron.py)

En `_tarea_semanal()`, al FINAL del bloque (después del briefing WA del paso 8 de B-ORG-PRODUCCION, antes del except), añadir:

```python
        # 11. Snapshot de todas las pizarras (P65 — "git del organismo")
        try:
            from src.pilates.pizarras import snapshot_todas
            semana_iso = _hora_madrid().isocalendar()
            ciclo = f"W{semana_iso[1]:02d}-{semana_iso[0]}"
            snap = await snapshot_todas("authentic_pilates", ciclo)
            log.info("cron_semanal_snapshot_ok", ciclo=ciclo, pizarras=len(snap))
        except Exception as e:
            log.error("cron_semanal_snapshot_error", error=str(e))
```

**Test 2.1:** `grep "snapshot_todas" src/pilates/cron.py` → match
**Test 2.2:** Tras ejecutar tarea semanal: `SELECT count(*) FROM om_pizarra_snapshot WHERE ciclo LIKE 'W%'` → ≥7

---

## PASO 3: LISTEN/NOTIFY LISTENER (src/pilates/cron.py)

En `cron_loop()`, ANTES del `while True:`, añadir la task de listener:

```python
    # Listener de señales urgentes (LISTEN/NOTIFY, P65)
    asyncio.create_task(_escuchar_senales_urgentes())
```

Y añadir la función ANTES de `cron_loop()`:

```python
async def _escuchar_senales_urgentes():
    """Listener permanente de señales urgentes via LISTEN/NOTIFY (P65).

    Cuando om_senales_agentes recibe una señal con prioridad ≤ 2,
    el trigger notify_senal_urgente() dispara un NOTIFY que llegamos aquí.
    """
    try:
        from src.db.client import get_pool
        pool = await get_pool()
        conn = await pool.acquire()

        def callback(conn_ref, pid, channel, payload):
            import json as _json
            try:
                data = _json.loads(payload)
                log.warning("senal_urgente_recibida",
                           tipo=data.get("tipo"), origen=data.get("origen"),
                           prioridad=data.get("prioridad"))
                # En futuro: disparar Reactivo inmediatamente
            except Exception as e:
                log.error("senal_urgente_parse_error", error=str(e))

        await conn.add_listener("senal_urgente", callback)
        log.info("listen_notify_activo", canal="senal_urgente")

        # Mantener la conexión viva
        while True:
            await asyncio.sleep(3600)
    except Exception as e:
        log.error("listen_notify_error", error=str(e))
```

**Test 3.1:** En logs de startup: "listen_notify_activo" con canal="senal_urgente"

---

## PASO 4: ELIMINAR STRIPE (código muerto)

### 4.1 Mover stripe_pagos.py a archivo

```bash
mkdir -p docs/archivo/codigo_muerto
mv src/pilates/stripe_pagos.py docs/archivo/codigo_muerto/stripe_pagos.py.bak
```

### 4.2 Verificar que no hay más imports de stripe

Buscar en todo `src/pilates/`:
```bash
grep -r "stripe" src/pilates/ --include="*.py"
```

Si hay más referencias (excepto en `docs/` o `archivo/`), eliminarlas. La referencia en `automatismos.py` ya se corrigió en B-ORG-PRODUCCION (stripe→redsys).

**Test 4.1:** `ls src/pilates/stripe_pagos.py` → "No such file"
**Test 4.2:** `grep -r "stripe" src/pilates/ --include="*.py"` → 0 resultados

---

## PASO 5: LIMPIEZA BUS EN AUTÓFAGO (src/pilates/autofago.py)

En `ejecutar_autofagia()`, añadir una sección de limpieza de señales antiguas. Buscar dónde se hace la limpieza de datos caducados y añadir:

```python
    # Limpieza de señales procesadas > 30 días
    try:
        hace_30_dias = datetime.now() - timedelta(days=30)
        eliminadas = await conn.execute("""
            DELETE FROM om_senales_agentes
            WHERE tenant_id = $1 AND procesada = true AND created_at < $2
        """, TENANT, hace_30_dias)
        # También limpiar bus_senales procesadas antiguas
        try:
            eliminadas_bus = await conn.execute("""
                DELETE FROM om_bus_senales
                WHERE tenant_id = $1 AND procesada = true AND created_at < $2
            """, TENANT, hace_30_dias)
        except Exception:
            pass  # tabla puede no existir
        resultado["senales_limpiadas"] = True
    except Exception as e:
        log.warning("autofago_limpieza_bus_error", error=str(e))
```

**Nota:** Ajustar la variable `resultado` al nombre real del dict de retorno en la función. Leer el archivo antes de editar para encontrar el punto exacto de inserción.

**Test 5.1:** `grep "senales_limpiadas" src/pilates/autofago.py` → match

---

## PASO 6: REACTOR V4 EN CRON MENSUAL (src/pilates/cron.py)

En `_tarea_mensual()`, ANTES del bloque de cristalizador, añadir:

```python
    # Reactor v4: detectar patrones en datos reales → pizarra evolución
    try:
        from src.reactor.v4_telemetria import detectar_patrones
        informe = await detectar_patrones()
        # Escribir hallazgos en pizarra evolución
        if informe and hasattr(informe, 'to_dict'):
            datos = informe.to_dict()
            if datos.get("patrones"):
                from src.pilates.pizarras import _get_pool as piz_pool
                pool = await piz_pool()
                async with pool.acquire() as conn:
                    for patron in datos["patrones"][:10]:  # max 10 por mes
                        await conn.execute("""
                            INSERT INTO om_pizarra_evolucion
                                (tenant_id, tipo, descripcion, datos, confianza)
                            VALUES ('authentic_pilates', 'reactor_v4', $1, $2::jsonb, $3)
                        """, patron.get("descripcion", "")[:500],
                            json.dumps(patron, default=str),
                            patron.get("confianza", 0.5))
        log.info("cron_mensual_reactor_v4_ok")
    except Exception as e:
        log.error("cron_mensual_reactor_v4_error", error=str(e))
```

**Nota:** Añadir `import json` al inicio de cron.py si no está.

**Test 6.1:** `grep "v4_telemetria" src/pilates/cron.py` → match
**Test 6.2:** `grep "pizarra_evolucion" src/pilates/cron.py` → match

---

## PASO 7: G4 OPUS PRIMERO (src/pilates/recompilador.py)

Esto viene del B-ORG-POLISH pendiente. El problema: G4 ejecuta Sonnet ($0.05) Y DESPUÉS Opus ($0.40), pero Opus sobrescribe las configs de Sonnet. Desperdicio.

En `ejecutar_g4_con_recompilacion()`, **invertir el orden**: Opus primero, Sonnet solo si Opus falla.

Buscar este patrón:
```python
    # 5. Recompilar (Sonnet — fallback si Opus falla)
```

Y reestructurar a:
```python
    # 5. Director Opus primero — diseña prompts D_híbrido
    director_ok = False
    try:
        from src.pilates.director_opus import dirigir_orquesta
        director = await dirigir_orquesta()
        g4["director_opus"] = director
        if director.get("status") == "ok":
            director_ok = True
            log.info("g4_director_opus_ok",
                     configs=director.get("configs_aplicadas"),
                     tiempo=director.get("tiempo_s"))
    except Exception as e:
        log.warning("g4_director_opus_error", error=str(e))

    # 6. Recompilar con Sonnet SOLO si Opus falló (fallback)
    if not director_ok:
        prescripcion = g4.get("prescripcion_completa", {})
        if prescripcion and "error" not in prescripcion:
            recomp = await recompilar(
                prescripcion.get("prescripcion_nivel_1", prescripcion),
                diagnostico_id=None,
            )
            g4["recompilacion"] = recomp
            log.info("g4_recompilador_sonnet_fallback")
        else:
            g4["recompilacion"] = {"status": "skip", "razon": "Sin prescripción válida"}
    else:
        g4["recompilacion"] = {"status": "skip", "razon": "Opus ya configuró"}
```

**Nota:** Leer `recompilador.py` completo para encontrar las líneas exactas. El bloque original tiene ~20 líneas con los pasos 5 y 6. Hay que invertirlos.

**Test 7.1:** `grep "Director Opus primero" src/pilates/recompilador.py` → match
**Test 7.2:** `grep "Sonnet SOLO si Opus falló" src/pilates/recompilador.py` → match

---

## PASO 8: json_utils.py COMPARTIDO (del B-ORG-POLISH)

Crear: `src/pilates/json_utils.py`

```python
"""Extracción robusta de JSON desde respuestas LLM."""
from __future__ import annotations

import json
import re
import structlog

log = structlog.get_logger()


def extraer_json(texto: str, fallback: dict = None) -> dict:
    """Extrae JSON de una respuesta LLM que puede contener markdown, texto extra, etc.

    Estrategia:
    1. Intenta parsear directo
    2. Busca bloque ```json ... ```
    3. Busca primer { ... último }
    4. Devuelve fallback
    """
    if not texto:
        return fallback or {}

    texto = texto.strip()

    # 1. Directo
    try:
        return json.loads(texto)
    except (json.JSONDecodeError, TypeError):
        pass

    # 2. Bloque markdown
    match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', texto, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except (json.JSONDecodeError, TypeError):
            pass

    # 3. Primer { ... último }
    start = texto.find('{')
    end = texto.rfind('}')
    if start != -1 and end > start:
        try:
            return json.loads(texto[start:end + 1])
        except (json.JSONDecodeError, TypeError):
            pass

    # 4. Array?
    start = texto.find('[')
    end = texto.rfind(']')
    if start != -1 and end > start:
        try:
            arr = json.loads(texto[start:end + 1])
            return {"items": arr}
        except (json.JSONDecodeError, TypeError):
            pass

    log.warning("json_extract_failed", preview=texto[:100])
    return fallback or {}


def extraer_json_lista(texto: str) -> list:
    """Extrae una lista JSON de una respuesta LLM."""
    result = extraer_json(texto, fallback={"items": []})
    if isinstance(result, list):
        return result
    return result.get("items", [])
```

Después, buscar en estos archivos cualquier extracción manual de JSON y reemplazar por `extraer_json()`:
- `src/pilates/director_opus.py`
- `src/pilates/recompilador.py`
- `src/pilates/estratega.py`
- `src/pilates/voz_estrategia.py`
- `src/pilates/buscador.py`
- `src/pilates/metacognitivo.py`
- `src/pilates/ingeniero.py`

Patrón a buscar (variantes):
```python
json.loads(texto)          # sin protección
response_text.strip()      # seguido de json.loads
```

Reemplazar por:
```python
from src.pilates.json_utils import extraer_json
resultado = extraer_json(response_text, fallback={...})
```

**Test 8.1:** `python -c "from src.pilates.json_utils import extraer_json; print(extraer_json('```json\n{\"a\":1}\n```'))"` → `{'a': 1}`
**Test 8.2:** `grep -r "from src.pilates.json_utils" src/pilates/ --include="*.py" | wc -l` → ≥3

---

## RESUMEN DE CAMBIOS

| Archivo | Cambio | Paso |
|---------|--------|------|
| `migrations/028_pizarras_cqrs.sql` | **NUEVO** — 6 tablas pizarra + snapshot + HNSW + grafo + trigger | 0 |
| `src/pilates/pizarras.py` | **NUEVO** — helper lectura universal + snapshots | 1 |
| `src/pilates/json_utils.py` | **NUEVO** — extracción JSON robusta | 8 |
| `src/pilates/cron.py` | +snapshot semanal + LISTEN/NOTIFY listener + reactor v4 mensual | 2, 3, 6 |
| `src/pilates/stripe_pagos.py` | **ELIMINADO** → archivo | 4 |
| `src/pilates/autofago.py` | +limpieza señales >30 días | 5 |
| `src/pilates/recompilador.py` | G4 Opus primero, Sonnet fallback | 7 |
| `src/pilates/director_opus.py` + 6 más | Usar json_utils.extraer_json | 8 |

## TESTS FINALES (PASS/FAIL)

```
T1:  SELECT count(*) FROM om_pizarra_dominio → 1                                   [PASS/FAIL]
T2:  SELECT config->>'email' FROM om_pizarra_dominio → pilatesfisioiregua@gmail.com [PASS/FAIL]
T3:  SELECT count(*) FROM om_pizarra_modelos → 4                                    [PASS/FAIL]
T4:  python -c "from src.pilates.pizarras import leer_dominio" → sin error          [PASS/FAIL]
T5:  python -c "from src.pilates.json_utils import extraer_json" → sin error        [PASS/FAIL]
T6:  ls src/pilates/stripe_pagos.py → "No such file"                                [PASS/FAIL]
T7:  grep -r "stripe" src/pilates/ --include="*.py" → 0 resultados                  [PASS/FAIL]
T8:  grep "snapshot_todas" src/pilates/cron.py → match                              [PASS/FAIL]
T9:  grep "senal_urgente" src/pilates/cron.py → match                               [PASS/FAIL]
T10: grep "Director Opus primero" src/pilates/recompilador.py → match               [PASS/FAIL]
T11: grep "senales_limpiadas" src/pilates/autofago.py → match                       [PASS/FAIL]
T12: grep "v4_telemetria" src/pilates/cron.py → match                               [PASS/FAIL]
T13: EXPLAIN ANALYZE query en om_conocimiento → usa HNSW index scan                 [PASS/FAIL]
T14: SELECT count(*) FROM om_pizarra_snapshot → tabla existe                        [PASS/FAIL]
```

## ORDEN DE EJECUCIÓN

1. Crear `migrations/028_pizarras_cqrs.sql` (Paso 0)
2. Crear `src/pilates/pizarras.py` (Paso 1)
3. Crear `src/pilates/json_utils.py` (Paso 8)
4. Editar `src/pilates/cron.py` (Pasos 2, 3, 6)
5. Mover `src/pilates/stripe_pagos.py` → archivo (Paso 4)
6. Editar `src/pilates/autofago.py` (Paso 5)
7. Editar `src/pilates/recompilador.py` (Paso 7)
8. Reemplazar json.loads manual en 7 archivos (Paso 8)
9. Deploy a fly.io
10. Verificar tests T1-T14

## NOTAS

- El paso de tenant_context.py (reemplazar TENANT en 47 archivos) se DEFER a un briefing dedicado B-ORG-TENANT porque toca demasiados archivos para mezclar con esto.
- Las pizarras se crean VACÍAS (excepto dominio y modelos con seeds). Se llenarán en F4 (Director Opus escribe) y F5 (Reactor/Evaluador/Memoria escriben).
- LISTEN/NOTIFY es infraestructura. El Reactivo que responda a señales urgentes vendrá en F5.
- Los triggers de proyección operacional→pizarra (om_pagos→om_pizarra) se DEFER a F3 (frontend) porque requieren definir qué métricas mostrar.
