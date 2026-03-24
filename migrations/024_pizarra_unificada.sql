-- 024: Pizarra unificada (Sprint 2 Matrioska)
-- 8 tipos de pizarra en tabla genérica con LISTEN/NOTIFY
-- No afecta tablas existentes (om_pizarra_dominio, om_pizarra_modelos, etc.)

CREATE TABLE IF NOT EXISTS om_pizarra (
    id         UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    tenant_id  TEXT NOT NULL,
    tipo       TEXT NOT NULL CHECK (tipo IN (
        'estado', 'cognitiva', 'dominio', 'temporal',
        'modelos', 'evolucion', 'interfaz', 'identidad'
    )),
    clave      TEXT NOT NULL,
    valor      JSONB NOT NULL DEFAULT '{}',
    ciclo      TEXT NOT NULL DEFAULT '',
    ttl_horas  INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Índice principal: tenant + tipo + clave (lookup rápido)
CREATE INDEX IF NOT EXISTS idx_pizarra_tenant_tipo_clave
    ON om_pizarra (tenant_id, tipo, clave, created_at DESC);

-- Índice para cleanup de entradas expiradas
CREATE INDEX IF NOT EXISTS idx_pizarra_ttl
    ON om_pizarra (created_at)
    WHERE ttl_horas > 0;

-- RLS: cada tenant solo ve sus pizarras
ALTER TABLE om_pizarra ENABLE ROW LEVEL SECURITY;

CREATE POLICY IF NOT EXISTS pizarra_tenant_isolation ON om_pizarra
    USING (tenant_id = current_setting('app.tenant_id', true))
    WITH CHECK (tenant_id = current_setting('app.tenant_id', true));

-- Función de notificación automática en INSERT
CREATE OR REPLACE FUNCTION fn_pizarra_notify()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM pg_notify(
        'pg_pizarra_' || replace(NEW.tenant_id, '-', '_'),
        json_build_object('tipo', NEW.tipo, 'clave', NEW.clave)::text
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger solo para entradas con notificación explícita
-- (la mayoría de escrituras NO necesitan notify)
-- Se activa manualmente desde PizarraUnificada.escribir(notificar=True)

COMMENT ON TABLE om_pizarra IS 'Pizarra unificada Matrioska: 8 tipos × N claves por tenant. Sprint 2.';
