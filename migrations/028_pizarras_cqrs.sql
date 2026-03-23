-- 028_pizarras_cqrs.sql — 6 pizarras nuevas + snapshots + HNSW + LISTEN/NOTIFY
-- Fase 2 del Roadmap v4 (P64 + P65)

-- ============================================================
-- 1. PIZARRA DOMINIO — el "quién soy" del tenant
-- ============================================================
CREATE TABLE IF NOT EXISTS om_pizarra_dominio (
    tenant_id TEXT PRIMARY KEY,
    nombre TEXT NOT NULL,
    config JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

INSERT INTO om_pizarra_dominio (tenant_id, nombre, config)
VALUES ('authentic_pilates', 'Authentic Pilates', '{
    "timezone": "Europe/Madrid",
    "moneda": "EUR",
    "datos_clinicos": true,
    "funciones_activas": ["F1","F2","F3","F4","F5","F6","F7"],
    "telefono_dueno": "34607466631",
    "email": "pilatesfisioiregua@gmail.com",
    "idioma": "es",
    "ubicacion": "Albelda de Iregua, La Rioja",
    "clientes_activos_aprox": 90,
    "poblacion_aprox": 4000
}')
ON CONFLICT (tenant_id) DO NOTHING;

-- ============================================================
-- 2. PIZARRA COGNITIVA — recetas del Director para agentes
-- ============================================================
CREATE TABLE IF NOT EXISTS om_pizarra_cognitiva (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL,
    ciclo TEXT NOT NULL,
    funcion TEXT NOT NULL,
    lente TEXT,
    prioridad INT DEFAULT 5,
    ints TEXT[] NOT NULL DEFAULT '{}',
    ps TEXT[] DEFAULT '{}',
    rs TEXT[] DEFAULT '{}',
    prompt_imperativo TEXT,
    prompt_preguntas TEXT,
    prompt_provocacion TEXT,
    prompt_razonamiento TEXT,
    intencion TEXT,
    origen TEXT DEFAULT 'director',
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_pcog_tenant_ciclo ON om_pizarra_cognitiva(tenant_id, ciclo);
CREATE INDEX IF NOT EXISTS idx_pcog_funcion ON om_pizarra_cognitiva(funcion);

-- ============================================================
-- 3. PIZARRA TEMPORAL — qué ejecutar, en qué orden, en qué ciclo
-- ============================================================
CREATE TABLE IF NOT EXISTS om_pizarra_temporal (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL,
    ciclo TEXT NOT NULL,
    fase TEXT NOT NULL,
    orden INT NOT NULL,
    componente TEXT NOT NULL,
    activo BOOLEAN DEFAULT true,
    motivo TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_ptemp_tenant_ciclo ON om_pizarra_temporal(tenant_id, ciclo);

-- ============================================================
-- 4. PIZARRA MODELOS — qué modelo usar para qué función/lente/complejidad
-- ============================================================
CREATE TABLE IF NOT EXISTS om_pizarra_modelos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL,
    funcion TEXT NOT NULL,
    lente TEXT,
    complejidad TEXT DEFAULT 'media',
    modelo TEXT NOT NULL,
    score_historico FLOAT,
    ultima_evaluacion TIMESTAMPTZ,
    origen TEXT DEFAULT 'default',
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_pmod_lookup ON om_pizarra_modelos(tenant_id, funcion, lente, complejidad);

-- Seeds con modelos actuales
INSERT INTO om_pizarra_modelos (tenant_id, funcion, complejidad, modelo, origen) VALUES
    ('authentic_pilates', '*', 'baja', 'deepseek/deepseek-v3.2', 'default'),
    ('authentic_pilates', '*', 'media', 'openai/gpt-4o', 'default'),
    ('authentic_pilates', '*', 'alta', 'anthropic/claude-opus-4', 'default'),
    ('authentic_pilates', 'F5', 'alta', 'anthropic/claude-opus-4', 'default')
ON CONFLICT DO NOTHING;

-- ============================================================
-- 5. PIZARRA EVOLUCIÓN — patrones aprendidos por el sistema
-- ============================================================
CREATE TABLE IF NOT EXISTS om_pizarra_evolucion (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL,
    tipo TEXT NOT NULL,
    descripcion TEXT NOT NULL,
    datos JSONB,
    confianza FLOAT DEFAULT 0.5,
    evidencia_ciclos INT DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_pevo_tenant_tipo ON om_pizarra_evolucion(tenant_id, tipo);

-- ============================================================
-- 6. PIZARRA INTERFAZ — qué módulos mostrar y con qué prioridad
-- ============================================================
CREATE TABLE IF NOT EXISTS om_pizarra_interfaz (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL,
    ciclo TEXT NOT NULL,
    modulo TEXT NOT NULL,
    rol TEXT DEFAULT 'secundario',
    prioridad INT DEFAULT 5,
    motivo TEXT,
    origen TEXT DEFAULT 'default',
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_pint_tenant_ciclo ON om_pizarra_interfaz(tenant_id, ciclo);

-- ============================================================
-- 7. TABLA SNAPSHOTS — "git del organismo" (P65)
-- ============================================================
CREATE TABLE IF NOT EXISTS om_pizarra_snapshot (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL,
    ciclo TEXT NOT NULL,
    tipo_pizarra TEXT NOT NULL,
    contenido JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_snap_tenant_ciclo ON om_pizarra_snapshot(tenant_id, ciclo);
CREATE INDEX IF NOT EXISTS idx_snap_tipo ON om_pizarra_snapshot(tipo_pizarra);

-- ============================================================
-- 8. HNSW INDEX en corpus (P65) — ~800 vectores
-- ============================================================
-- Solo crear si la extensión pgvector está activa y la tabla existe
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'om_conocimiento') THEN
        EXECUTE 'CREATE INDEX IF NOT EXISTS idx_conocimiento_hnsw ON om_conocimiento USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64)';
    END IF;
END $$;

-- ============================================================
-- 9. CORPUS → GRAFO SEMÁNTICO (P65)
-- ============================================================
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'om_conocimiento') THEN
        ALTER TABLE om_conocimiento ADD COLUMN IF NOT EXISTS superseded_by UUID;
        ALTER TABLE om_conocimiento ADD COLUMN IF NOT EXISTS depends_on UUID[];
        ALTER TABLE om_conocimiento ADD COLUMN IF NOT EXISTS cluster TEXT;
        ALTER TABLE om_conocimiento ADD COLUMN IF NOT EXISTS relevancia_decreciente FLOAT DEFAULT 1.0;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_conocimiento_cluster ON om_conocimiento(cluster);

-- ============================================================
-- 10. LISTEN/NOTIFY para señales urgentes (P65)
-- ============================================================
CREATE OR REPLACE FUNCTION notify_senal_urgente() RETURNS trigger AS $$
BEGIN
    IF NEW.prioridad IS NOT NULL AND NEW.prioridad <= 2 THEN
        PERFORM pg_notify('senal_urgente', json_build_object(
            'id', NEW.id,
            'tipo', NEW.tipo_senal,
            'origen', NEW.origen,
            'prioridad', NEW.prioridad
        )::text);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Aplicar trigger si la tabla existe
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'om_senales_agentes') THEN
        DROP TRIGGER IF EXISTS trg_senal_urgente ON om_senales_agentes;
        CREATE TRIGGER trg_senal_urgente
            AFTER INSERT ON om_senales_agentes
            FOR EACH ROW EXECUTE FUNCTION notify_senal_urgente();
    END IF;
END $$;
