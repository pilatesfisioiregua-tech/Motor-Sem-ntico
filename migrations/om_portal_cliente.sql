-- Token permanente para portal del cliente (reutiliza om_onboarding_links)
-- Los enlaces completados se convierten en portal permanente
ALTER TABLE om_onboarding_links ADD COLUMN IF NOT EXISTS
    es_portal BOOLEAN DEFAULT false;

-- Índice para búsqueda rápida por cliente
CREATE INDEX IF NOT EXISTS idx_om_onboarding_portal
    ON om_onboarding_links(cliente_id) WHERE es_portal = true;
