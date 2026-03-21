-- Añade preferencia de facturación aprendida por cliente
ALTER TABLE om_clientes ADD COLUMN IF NOT EXISTS
    preferencia_facturacion TEXT DEFAULT 'nunca'
    CHECK (preferencia_facturacion IN ('siempre', 'trimestral', 'esporadica', 'nunca'));
