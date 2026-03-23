-- 025_director_manual.sql — Tabla para almacenar el manual del Director Opus en DB
-- Permite actualizar el manual sin redeploy (prioridad sobre filesystem)

CREATE TABLE IF NOT EXISTS om_director_manual (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'authentic_pilates',
    contenido TEXT NOT NULL,
    version INT DEFAULT 1,
    activo BOOLEAN DEFAULT TRUE,
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(tenant_id, activo)
);
