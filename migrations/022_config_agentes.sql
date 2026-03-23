-- =================================================================
-- Migration 022: Config dinámica INT×P×R por agente (Recompilador)
-- Permite que el Recompilador modifique las herramientas cognitivas
-- de cada agente en runtime sin tocar código.
-- =================================================================

CREATE TABLE IF NOT EXISTS om_config_agentes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'authentic_pilates',
    agente TEXT NOT NULL,
    config JSONB NOT NULL,
    version INT DEFAULT 1,
    activa BOOLEAN DEFAULT TRUE,
    prescripcion_origen UUID,
    aprobada_por TEXT DEFAULT 'sistema',
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_config_agente ON om_config_agentes(tenant_id, agente, activa);
CREATE INDEX IF NOT EXISTS idx_config_version ON om_config_agentes(tenant_id, agente, version DESC);

-- Ampliar tipos válidos del bus para señales del enjambre v2 y recompilador
ALTER TABLE om_senales_agentes DROP CONSTRAINT IF EXISTS om_senales_agentes_tipo_check;
ALTER TABLE om_senales_agentes ADD CONSTRAINT om_senales_agentes_tipo_check
    CHECK (tipo IN (
        'DATO', 'ALERTA', 'DIAGNOSTICO', 'OPORTUNIDAD', 'PRESCRIPCION', 'ACCION',
        'PERCEPCION', 'PERCEPCION_CAUSAL', 'PRESCRIPCION_ESTRATEGICA',
        'RECOMPILACION', 'BRIEFING_PENDIENTE'
    ));
