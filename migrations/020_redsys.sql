-- =================================================================
-- Migration 020: Redsys — Pagos via Caja Rural de Navarra
-- Tracking de pedidos, tokens COF, y columnas para cobros automáticos.
-- =================================================================

-- Tabla de pedidos Redsys (tracking de cada operación)
CREATE TABLE IF NOT EXISTS om_redsys_pedidos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'authentic_pilates',
    cliente_id UUID NOT NULL REFERENCES om_clientes(id),
    order_id TEXT NOT NULL,
    importe NUMERIC(10,2) NOT NULL,
    estado TEXT NOT NULL DEFAULT 'pendiente',  -- pendiente, ok, fallido
    tipo TEXT NOT NULL DEFAULT 'redireccion',  -- redireccion, cof_inicial, paygold, recurrente
    redsys_response_code TEXT,
    redsys_auth_code TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_redsys_order ON om_redsys_pedidos(order_id);
CREATE INDEX IF NOT EXISTS idx_redsys_cliente ON om_redsys_pedidos(cliente_id, tenant_id);

-- Añadir columna redsys_identifier a om_pago_recurrente
-- (reemplaza stripe_customer_id y stripe_payment_method_id)
ALTER TABLE om_pago_recurrente ADD COLUMN IF NOT EXISTS redsys_identifier TEXT;

-- Añadir columnas Redsys a om_cobros_automaticos
ALTER TABLE om_cobros_automaticos ADD COLUMN IF NOT EXISTS redsys_order TEXT;
ALTER TABLE om_cobros_automaticos ADD COLUMN IF NOT EXISTS redsys_response_code TEXT;
