-- 015_lista_espera.sql
CREATE TABLE IF NOT EXISTS om_lista_espera (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'authentic_pilates',
    cliente_id UUID NOT NULL REFERENCES om_clientes(id),
    dia_semana INTEGER,              -- 0=lunes, 1=martes, ... NULL=cualquier día
    franja TEXT,                      -- 'manana', 'tarde', 'cualquiera'
    hora_preferida TIME,             -- NULL = cualquier hora
    grupo_id UUID REFERENCES om_grupos(id),  -- NULL = cualquier grupo
    estado TEXT NOT NULL DEFAULT 'activa',    -- activa, notificada, expirada, cancelada
    fecha_creacion TIMESTAMPTZ DEFAULT now(),
    fecha_notificacion TIMESTAMPTZ,
    notas TEXT,
    CONSTRAINT fk_cliente FOREIGN KEY (cliente_id) REFERENCES om_clientes(id)
);

CREATE INDEX IF NOT EXISTS idx_lista_espera_activa ON om_lista_espera(tenant_id, estado) WHERE estado = 'activa';

-- Tabla para log de conversaciones portal (analytics)
CREATE TABLE IF NOT EXISTS om_portal_conversaciones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'authentic_pilates',
    cliente_id UUID NOT NULL,
    mensaje_cliente TEXT NOT NULL,
    mensaje_respuesta TEXT NOT NULL,
    tools_usadas JSONB DEFAULT '[]',
    coste_usd NUMERIC(8,6) DEFAULT 0,
    tiempo_ms INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now()
);
