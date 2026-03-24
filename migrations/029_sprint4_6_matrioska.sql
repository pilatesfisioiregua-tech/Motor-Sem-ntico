-- Sprint 4-6 Matrioska: tablas para Director, Enjambre, Multi-tenant, Cockpit
-- Requiere: om_pizarra existente (Sprint 2)

-- =============================================================
-- 1. Tabla telemetria del motor (si no existe)
-- =============================================================
CREATE TABLE IF NOT EXISTS om_motor_telemetria (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'default',
    funcion TEXT,                    -- F1-F7 o *
    lente TEXT,                      -- salud, sentido, continuidad
    modelo TEXT NOT NULL,
    tokens_input INT DEFAULT 0,
    tokens_output INT DEFAULT 0,
    coste_usd NUMERIC(10,6) DEFAULT 0,
    tiempo_ms INT DEFAULT 0,
    cache_hit BOOLEAN DEFAULT FALSE,
    ciclo TEXT,                      -- W13-2026
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_telemetria_tenant_ciclo
    ON om_motor_telemetria(tenant_id, ciclo);

-- =============================================================
-- 2. Cache LLM semantico
-- =============================================================
CREATE TABLE IF NOT EXISTS om_pizarra_cache_llm (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'default',
    prompt_hash TEXT NOT NULL,
    modelo TEXT NOT NULL,
    funcion TEXT,
    lente TEXT,
    respuesta TEXT NOT NULL,
    hits INT DEFAULT 0,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_cache_hash_modelo
    ON om_pizarra_cache_llm(prompt_hash, modelo);

CREATE INDEX IF NOT EXISTS idx_cache_expires
    ON om_pizarra_cache_llm(expires_at);

-- =============================================================
-- 3. Tabla pizarra unificada (Sprint 2, reforzada Sprint 4)
-- =============================================================
CREATE TABLE IF NOT EXISTS om_pizarra (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'default',
    tipo TEXT NOT NULL,              -- estado|cognitiva|dominio|temporal|modelos|evolucion|interfaz|identidad
    clave TEXT NOT NULL,
    valor JSONB NOT NULL DEFAULT '{}',
    ciclo TEXT DEFAULT '',
    ttl_horas INT DEFAULT 0,        -- 0 = sin expiracion
    origen TEXT DEFAULT 'sistema',   -- quien escribio
    prioridad INT DEFAULT 5,        -- 1=urgente
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indice unico para UPSERT por tenant+tipo+clave+ciclo
CREATE UNIQUE INDEX IF NOT EXISTS idx_pizarra_upsert
    ON om_pizarra(tenant_id, tipo, clave, ciclo);

-- Indice para lecturas frecuentes
CREATE INDEX IF NOT EXISTS idx_pizarra_tenant_tipo
    ON om_pizarra(tenant_id, tipo);

-- Indice para TTL cleanup
CREATE INDEX IF NOT EXISTS idx_pizarra_ttl
    ON om_pizarra(created_at, ttl_horas)
    WHERE ttl_horas > 0;

-- =============================================================
-- 4. Snapshots de pizarra (para auditing)
-- =============================================================
CREATE TABLE IF NOT EXISTS om_pizarra_snapshot (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    ciclo TEXT NOT NULL,
    snapshot JSONB NOT NULL,
    n_entradas INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_snapshot_tenant_ciclo
    ON om_pizarra_snapshot(tenant_id, ciclo);

-- =============================================================
-- 5. Tabla de prescripciones (historico de recetas)
-- =============================================================
CREATE TABLE IF NOT EXISTS om_prescripciones (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    funcion TEXT NOT NULL,           -- F1-F7
    lente TEXT,
    receta JSONB NOT NULL,
    origen TEXT DEFAULT 'enjambre',  -- enjambre|director|manual|cross_tenant
    verificacion_score NUMERIC(3,2) DEFAULT 0,
    coste_usd NUMERIC(10,6) DEFAULT 0,
    estado TEXT DEFAULT 'propuesta', -- propuesta|aprobada|ejecutada|cerrada|fallida
    aprobada_por TEXT,               -- CR1: quien aprobo
    ciclo TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    ejecutada_at TIMESTAMPTZ,
    cerrada_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_prescripciones_tenant
    ON om_prescripciones(tenant_id, estado);

-- =============================================================
-- 6. Transferencias cross-tenant (ecosistema)
-- =============================================================
CREATE TABLE IF NOT EXISTS om_transferencias (
    id BIGSERIAL PRIMARY KEY,
    origen_tenant TEXT NOT NULL,
    destino_tenant TEXT NOT NULL,
    gap TEXT NOT NULL,               -- F3_baja, F6_baja, etc.
    receta JSONB NOT NULL,
    similaridad NUMERIC(5,4) DEFAULT 0,
    confianza NUMERIC(5,4) DEFAULT 0,
    evidencia TEXT,
    estado TEXT DEFAULT 'propuesta', -- propuesta|aprobada|rechazada|aplicada
    requiere_cr1 BOOLEAN DEFAULT TRUE,
    aprobada_por TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_transferencias_destino
    ON om_transferencias(destino_tenant, estado);

-- =============================================================
-- 7. Trigger LISTEN/NOTIFY para pizarra (Sprint 2, confirmado Sprint 4)
-- =============================================================
CREATE OR REPLACE FUNCTION fn_pizarra_notify()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM pg_notify(
        'pg_pizarra_' || replace(NEW.tenant_id, '-', '_'),
        json_build_object(
            'tipo', NEW.tipo,
            'clave', NEW.clave,
            'tenant_id', NEW.tenant_id
        )::text
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Solo activar trigger si la columna notificar no existe
-- (compatibilidad: el trigger se activa en todos los INSERT/UPDATE)
DROP TRIGGER IF EXISTS trg_pizarra_notify ON om_pizarra;

-- =============================================================
-- 8. Limpieza de cache expirado (funcion para cron)
-- =============================================================
CREATE OR REPLACE FUNCTION fn_limpiar_cache_llm()
RETURNS INT AS $$
DECLARE
    n INT;
BEGIN
    DELETE FROM om_pizarra_cache_llm WHERE expires_at < NOW();
    GET DIAGNOSTICS n = ROW_COUNT;
    RETURN n;
END;
$$ LANGUAGE plpgsql;

-- =============================================================
-- 9. Limpieza de pizarra con TTL (funcion para cron)
-- =============================================================
CREATE OR REPLACE FUNCTION fn_limpiar_pizarra_ttl()
RETURNS INT AS $$
DECLARE
    n INT;
BEGIN
    DELETE FROM om_pizarra
    WHERE ttl_horas > 0
      AND created_at + make_interval(hours => ttl_horas) < NOW();
    GET DIAGNOSTICS n = ROW_COUNT;
    RETURN n;
END;
$$ LANGUAGE plpgsql;
