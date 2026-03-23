-- =================================================================
-- Migration 021: Enjambre Cognitivo — tabla de diagnósticos duales
-- 16 agentes: 3 lentes + 7 funciones + 6 clusters INT
-- =================================================================

-- Tabla de resultados del enjambre cognitivo
CREATE TABLE IF NOT EXISTS om_enjambre_diagnosticos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'authentic_pilates',
    estado_acd_base TEXT,
    resultado_lentes JSONB,
    resultado_funciones JSONB,
    resultado_clusters JSONB,
    señales_emitidas INT DEFAULT 0,
    tiempo_total_s NUMERIC(6,1),
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_enjambre_tenant ON om_enjambre_diagnosticos(tenant_id, created_at DESC);

-- Añadir todos los tipos al CHECK constraint del bus de señales
ALTER TABLE om_senales_agentes DROP CONSTRAINT IF EXISTS om_senales_agentes_tipo_check;
ALTER TABLE om_senales_agentes ADD CONSTRAINT om_senales_agentes_tipo_check
    CHECK (tipo IN ('DATO', 'ALERTA', 'DIAGNOSTICO', 'OPORTUNIDAD', 'PRESCRIPCION', 'ACCION',
                    'PERCEPCION', 'PERCEPCION_CAUSAL', 'PRESCRIPCION_ESTRATEGICA',
                    'RECOMPILACION', 'BRIEFING_PENDIENTE'));
