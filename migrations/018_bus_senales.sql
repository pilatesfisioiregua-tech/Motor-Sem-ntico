-- =================================================================
-- Migration 018: Bus de señales inter-agente
-- Tabla unificada para señales entre todos los agentes del organismo.
-- Usada tanto por src/ (asyncpg) como por agent/core/ (psycopg2).
-- =================================================================

CREATE TABLE IF NOT EXISTS om_senales_agentes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT now(),
    tipo TEXT NOT NULL CHECK (tipo IN ('DATO', 'ALERTA', 'DIAGNOSTICO', 'OPORTUNIDAD', 'PRESCRIPCION', 'ACCION')),
    origen TEXT NOT NULL,
    destino TEXT,
    prioridad INTEGER DEFAULT 5 CHECK (prioridad BETWEEN 1 AND 10),
    payload JSONB NOT NULL DEFAULT '{}',
    estado TEXT NOT NULL DEFAULT 'pendiente' CHECK (estado IN ('pendiente', 'procesando', 'procesada', 'error')),
    procesada_por TEXT,
    procesada_at TIMESTAMPTZ,
    tenant_id TEXT NOT NULL DEFAULT 'authentic_pilates',
    error_detalle TEXT
);

CREATE INDEX IF NOT EXISTS idx_senales_pendientes
    ON om_senales_agentes(estado, prioridad, created_at)
    WHERE estado = 'pendiente';

CREATE INDEX IF NOT EXISTS idx_senales_tipo_origen
    ON om_senales_agentes(tipo, origen, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_senales_tenant
    ON om_senales_agentes(tenant_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_senales_destino
    ON om_senales_agentes(destino, estado)
    WHERE destino IS NOT NULL;
