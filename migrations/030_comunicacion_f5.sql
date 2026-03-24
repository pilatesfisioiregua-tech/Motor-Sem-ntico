-- 030_comunicacion_f5.sql — Pizarra Comunicación + Mediador
-- Fase 5 del Roadmap v4 (P66)

-- 1. Pizarra Comunicación (#9) — intenciones programadas con tracking
CREATE TABLE IF NOT EXISTS om_pizarra_comunicacion (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'authentic_pilates',
    destinatario TEXT NOT NULL,
    destinatario_nombre TEXT,
    cliente_id UUID,
    canal TEXT DEFAULT 'whatsapp',
    tipo TEXT NOT NULL,
    mensaje TEXT NOT NULL,
    programado_para TIMESTAMPTZ,
    estado TEXT DEFAULT 'pendiente',
    fallback_canal TEXT,
    origen TEXT,
    metadata JSONB DEFAULT '{}',
    wa_message_id TEXT,
    entregado_at TIMESTAMPTZ,
    leido_at TIMESTAMPTZ,
    respondido_at TIMESTAMPTZ,
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_pcom_pendiente
    ON om_pizarra_comunicacion(estado, programado_para)
    WHERE estado = 'pendiente';
CREATE INDEX IF NOT EXISTS idx_pcom_cliente
    ON om_pizarra_comunicacion(cliente_id);
CREATE INDEX IF NOT EXISTS idx_pcom_tipo
    ON om_pizarra_comunicacion(tipo);

-- 2. Tabla mediación — registro de conflictos resueltos
CREATE TABLE IF NOT EXISTS om_mediaciones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'authentic_pilates',
    ciclo TEXT NOT NULL,
    conflicto JSONB NOT NULL,
    resolucion JSONB NOT NULL,
    af_involucrados TEXT[] NOT NULL,
    objeto_id UUID,
    objeto_tipo TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_med_ciclo ON om_mediaciones(tenant_id, ciclo);

-- 3. Trigger: marcar leído/respondido actualiza pizarra comunicación
CREATE OR REPLACE FUNCTION update_pcom_estado() RETURNS trigger AS $$
BEGIN
    -- Cuando WA webhook marca un mensaje como leído/respondido
    IF NEW.estado_wa = 'read' AND NEW.wa_message_id IS NOT NULL THEN
        UPDATE om_pizarra_comunicacion
        SET leido_at = now(), estado = 'leido', updated_at = now()
        WHERE wa_message_id = NEW.wa_message_id AND leido_at IS NULL;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Aplicar trigger si om_mensajes_wa tiene la columna
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'om_mensajes_wa') THEN
        -- Añadir columna estado_wa si no existe
        ALTER TABLE om_mensajes_wa ADD COLUMN IF NOT EXISTS estado_wa TEXT;
        DROP TRIGGER IF EXISTS trg_pcom_estado ON om_mensajes_wa;
        CREATE TRIGGER trg_pcom_estado
            AFTER UPDATE ON om_mensajes_wa
            FOR EACH ROW EXECUTE FUNCTION update_pcom_estado();
    END IF;
END $$;
