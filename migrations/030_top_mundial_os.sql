-- Sprint Top Mundial: Event Sourcing, Grafo, Busqueda Hibrida
-- Requiere: 029_sprint4_6_matrioska.sql, pgvector extension

-- =============================================================
-- 1. Event Log (Event Sourcing — fuente de verdad inmutable)
-- =============================================================
CREATE TABLE IF NOT EXISTS om_event_log (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'default',
    tipo_evento TEXT NOT NULL,          -- ConocimientoCreado, PrescripcionEmitida, etc.
    agente TEXT NOT NULL DEFAULT 'sistema',
    datos JSONB NOT NULL DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    ciclo TEXT DEFAULT '',
    version INT DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indice para replay por tenant
CREATE INDEX IF NOT EXISTS idx_event_log_tenant
    ON om_event_log(tenant_id, id);

-- Indice para filtrar por tipo
CREATE INDEX IF NOT EXISTS idx_event_log_tipo
    ON om_event_log(tenant_id, tipo_evento);

-- Indice temporal para time travel
CREATE INDEX IF NOT EXISTS idx_event_log_created
    ON om_event_log(tenant_id, created_at);

-- =============================================================
-- 2. Grafo de Conocimiento (relaciones tipadas)
-- =============================================================
CREATE TABLE IF NOT EXISTS om_grafo_relaciones (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    origen_tipo TEXT NOT NULL,
    origen_clave TEXT NOT NULL,
    destino_tipo TEXT NOT NULL,
    destino_clave TEXT NOT NULL,
    tipo_relacion TEXT NOT NULL,       -- DEPENDE_DE, USA, CONFLICTO, etc.
    peso NUMERIC(5,3) DEFAULT 1.0,
    propiedades JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indice unico para evitar duplicados
CREATE UNIQUE INDEX IF NOT EXISTS idx_grafo_unico
    ON om_grafo_relaciones(tenant_id, origen_tipo, origen_clave,
                           destino_tipo, destino_clave, tipo_relacion);

-- Indices para traversal
CREATE INDEX IF NOT EXISTS idx_grafo_origen
    ON om_grafo_relaciones(tenant_id, origen_tipo, origen_clave);

CREATE INDEX IF NOT EXISTS idx_grafo_destino
    ON om_grafo_relaciones(tenant_id, destino_tipo, destino_clave);

-- =============================================================
-- 3. Busqueda Hibrida: embedding + tsvector en om_pizarra
-- =============================================================

-- Columna embedding (pgvector) si no existe
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'om_pizarra' AND column_name = 'embedding'
    ) THEN
        ALTER TABLE om_pizarra ADD COLUMN embedding vector(1536);
    END IF;
END $$;

-- Columna search_vector (tsvector) si no existe
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'om_pizarra' AND column_name = 'search_vector'
    ) THEN
        ALTER TABLE om_pizarra ADD COLUMN search_vector tsvector;
    END IF;
END $$;

-- Indice HNSW para busqueda vectorial
CREATE INDEX IF NOT EXISTS idx_pizarra_embedding_hnsw
    ON om_pizarra USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Indice GIN para full-text search
CREATE INDEX IF NOT EXISTS idx_pizarra_search_vector
    ON om_pizarra USING gin (search_vector);

-- Trigger para actualizar search_vector automaticamente
CREATE OR REPLACE FUNCTION fn_pizarra_update_search()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := to_tsvector('spanish',
        COALESCE(NEW.clave, '') || ' ' ||
        COALESCE(NEW.tipo, '') || ' ' ||
        COALESCE(NEW.valor::text, '')
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_pizarra_search ON om_pizarra;
CREATE TRIGGER trg_pizarra_search
    BEFORE INSERT OR UPDATE ON om_pizarra
    FOR EACH ROW EXECUTE FUNCTION fn_pizarra_update_search();

-- =============================================================
-- 4. Tabla de capabilities (audit trail)
-- =============================================================
CREATE TABLE IF NOT EXISTS om_capabilities_log (
    id BIGSERIAL PRIMARY KEY,
    token TEXT NOT NULL,
    titular TEXT NOT NULL,
    recurso TEXT NOT NULL,
    tipo_recurso TEXT NOT NULL,
    permisos TEXT NOT NULL,
    accion TEXT NOT NULL,           -- creada|atenuada|revocada|verificada
    resultado BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_capabilities_titular
    ON om_capabilities_log(titular, created_at);
