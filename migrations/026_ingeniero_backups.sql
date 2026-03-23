-- 026_ingeniero_backups.sql — Backups del Ingeniero para rollback seguro

CREATE TABLE IF NOT EXISTS om_ingeniero_backups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'authentic_pilates',
    archivo TEXT NOT NULL,
    contenido_original TEXT NOT NULL,
    instruccion JSONB,
    revertido BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_ingeniero_backups ON om_ingeniero_backups(tenant_id, archivo, created_at DESC);
