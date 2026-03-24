-- 031_multi_tenant.sql — Segundo tenant: clínica fisioterapia

-- 1. Insertar tenant en pizarra dominio
INSERT INTO om_pizarra_dominio (tenant_id, nombre, config)
VALUES ('clinica_fisio', 'Clínica Fisioterapia', '{
    "timezone": "Europe/Madrid",
    "moneda": "EUR",
    "datos_clinicos": true,
    "funciones_activas": ["F1","F2","F3","F4","F5","F6","F7"],
    "idioma": "es",
    "ubicacion": "Logroño, La Rioja",
    "rgpd_art9": true,
    "datos_clinicos_encriptados": true
}')
ON CONFLICT (tenant_id) DO NOTHING;

-- 2. Seeds modelos para fisio (mismos defaults)
INSERT INTO om_pizarra_modelos (tenant_id, funcion, complejidad, modelo, origen)
SELECT 'clinica_fisio', funcion, complejidad, modelo, 'default'
FROM om_pizarra_modelos
WHERE tenant_id = 'authentic_pilates' AND origen = 'default'
ON CONFLICT DO NOTHING;

-- 3. Cron state para fisio
INSERT INTO om_cron_state (tenant_id, tarea, ultima_ejecucion, resultado)
VALUES ('clinica_fisio', 'diaria', now(), 'seed')
ON CONFLICT DO NOTHING;

-- 4. Campo encriptación para datos clínicos RGPD Art.9
ALTER TABLE om_datos_clinicos
    ADD COLUMN IF NOT EXISTS datos_encriptados BYTEA,
    ADD COLUMN IF NOT EXISTS encryption_key_id TEXT;

-- 5. Tabla de claves de encriptación por tenant (para RGPD Art.9)
CREATE TABLE IF NOT EXISTS om_encryption_keys (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    key_encrypted BYTEA NOT NULL,
    algorithm TEXT DEFAULT 'AES-256-GCM',
    created_at TIMESTAMPTZ DEFAULT now(),
    revoked_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_enc_keys_tenant ON om_encryption_keys(tenant_id);
