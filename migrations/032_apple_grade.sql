-- 032_apple_grade.sql — Seguridad Apple-grade: audit log + rate limit + RGPD

-- 1. Audit Log — Registro inmutable de acciones
CREATE TABLE IF NOT EXISTS om_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT now(),
    tenant_id TEXT NOT NULL,
    actor TEXT NOT NULL,          -- quién (usuario, sistema, agente)
    accion TEXT NOT NULL,         -- qué (CREATE, UPDATE, DELETE, EXPORT, LOGIN)
    entidad TEXT NOT NULL,        -- tabla afectada
    entidad_id TEXT,              -- ID del registro
    detalles JSONB DEFAULT '{}', -- campos modificados, motivo, etc.
    ip TEXT                       -- IP del request (si aplica)
);
CREATE INDEX IF NOT EXISTS idx_audit_tenant_ts ON om_audit_log(tenant_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_entidad ON om_audit_log(entidad, entidad_id);
CREATE INDEX IF NOT EXISTS idx_audit_actor ON om_audit_log(actor);

-- 2. Rate limit por IP — ventana deslizante
CREATE TABLE IF NOT EXISTS om_rate_limit (
    ip TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    window_start TIMESTAMPTZ DEFAULT now(),
    count INTEGER DEFAULT 1,
    PRIMARY KEY (ip, endpoint, window_start)
);
CREATE INDEX IF NOT EXISTS idx_rate_limit_window ON om_rate_limit(window_start);

-- 3. RGPD: estado borrado en cliente_tenant
DO $$ BEGIN
    ALTER TABLE om_cliente_tenant ADD COLUMN IF NOT EXISTS borrado_solicitado_at TIMESTAMPTZ;
EXCEPTION WHEN others THEN NULL;
END $$;

-- 4. Índices de rendimiento para queries frecuentes
CREATE INDEX IF NOT EXISTS idx_asist_cliente ON om_asistencias(cliente_id);
CREATE INDEX IF NOT EXISTS idx_cargos_cliente_estado ON om_cargos(cliente_id, estado);
CREATE INDEX IF NOT EXISTS idx_pagos_cliente ON om_pagos(cliente_id, tenant_id);
CREATE INDEX IF NOT EXISTS idx_sesiones_fecha ON om_sesiones(tenant_id, fecha);
CREATE INDEX IF NOT EXISTS idx_mensajes_wa_cliente ON om_mensajes_wa(cliente_id, tenant_id);
CREATE INDEX IF NOT EXISTS idx_senales_pendientes ON om_senales_agentes(tenant_id, estado) WHERE estado = 'pendiente';

-- 5. Limpieza automática rate limit (ejecutar en cron)
-- DELETE FROM om_rate_limit WHERE window_start < now() - interval '1 hour';
