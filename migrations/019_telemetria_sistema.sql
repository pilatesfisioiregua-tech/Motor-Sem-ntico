-- =================================================================
-- Migration 019: Telemetría del organismo
-- Snapshots periódicos del rendimiento del sistema nervioso.
-- =================================================================

CREATE TABLE IF NOT EXISTS om_telemetria_sistema (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT now(),
    tenant_id TEXT NOT NULL DEFAULT 'authentic_pilates',
    periodo TEXT NOT NULL,                -- 'diario', 'semanal'

    -- Bus de señales
    senales_emitidas INTEGER DEFAULT 0,
    senales_procesadas INTEGER DEFAULT 0,
    senales_error INTEGER DEFAULT 0,
    senales_pendientes INTEGER DEFAULT 0,
    latencia_media_min FLOAT,             -- minutos entre creación y procesamiento

    -- Agentes: conteo de señales por origen
    actividad_agentes JSONB DEFAULT '{}', -- {"OBSERVADOR": 12, "AF1": 3, "VIGIA": 96, ...}
    agentes_silenciosos TEXT[],           -- agentes que no emitieron en el periodo

    -- ACD drift
    acd_estado TEXT,                      -- último estado diagnóstico
    acd_lentes JSONB,                     -- {salud, sentido, continuidad}
    acd_delta_lentes JSONB,               -- delta vs snapshot anterior {salud: +0.05, ...}

    -- Mecánico
    fixes_fontaneria INTEGER DEFAULT 0,
    mejoras_arquitecturales INTEGER DEFAULT 0,
    propuestas_autofagia INTEGER DEFAULT 0,

    -- Operativo
    endpoints_llamados JSONB DEFAULT '{}', -- si tenemos logs de acceso
    errores_500 INTEGER DEFAULT 0,

    metadata JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_telemetria_periodo
    ON om_telemetria_sistema(periodo, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_telemetria_tenant
    ON om_telemetria_sistema(tenant_id, created_at DESC);
