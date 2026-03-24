-- 032_identidad_presencia.sql — Pizarra Identidad (#11) + contenido + presencia digital
-- Fase 7 del Roadmap v4 (P67)

-- 1. PIZARRA IDENTIDAD (#11) — ADN del exocórtex
CREATE TABLE IF NOT EXISTS om_pizarra_identidad (
    tenant_id TEXT PRIMARY KEY,
    -- Quién soy
    esencia TEXT,
    narrativa TEXT,
    valores TEXT[],
    propuesta_valor TEXT,
    metodo TEXT,
    -- Qué NO soy
    anti_identidad TEXT[],
    depuraciones_deliberadas TEXT[],
    -- Voz y estética
    tono TEXT,
    tono_ejemplos JSONB DEFAULT '[]',
    estilo_visual JSONB DEFAULT '{}',
    -- Posición desde ACD
    posicion_lentes JSONB DEFAULT '{}',
    angulo_diferencial TEXT,
    -- Configuración por canal
    canales JSONB DEFAULT '{}',
    -- Metadata
    ultima_revision TIMESTAMPTZ,
    origen TEXT DEFAULT 'seed',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Seed desde voz_identidad.py existente
INSERT INTO om_pizarra_identidad (tenant_id, esencia, narrativa, valores, propuesta_valor, metodo,
    anti_identidad, depuraciones_deliberadas, tono, angulo_diferencial, origen)
VALUES ('authentic_pilates',
    'Pilates auténtico con atención real en un pueblo de La Rioja. No somos un gimnasio.',
    'Jesús dejó su carrera anterior para dedicarse a lo que le apasiona: enseñar Pilates de verdad. En Albelda de Iregua, cada persona tiene nombre, historia y un cuerpo único.',
    ARRAY['autenticidad', 'atención_individual', 'método_original', 'cercanía', 'rigor'],
    'Pilates auténtico con atención real. Cada sesión es única porque cada persona es única.',
    'EEDAP de Fabien Menegon — Escuela de Educación del Authentic Pilates',
    ARRAY['gimnasio masivo', 'clases de 20 personas', 'entrenadores sin formación', 'descuentos agresivos', 'marketing de urgencia'],
    ARRAY['nunca publicar ofertas tipo "50% descuento"', 'nunca copiar estética de cadenas fitness', 'nunca hablar de "transformación corporal en 30 días"'],
    'cercano, profesional, sin jerga fitness. Como habla un vecino que sabe mucho de su oficio.',
    'El único estudio con método EEDAP en La Rioja. Grupos de máximo 4 personas. No vendemos abdominales, vendemos que tu cuerpo funcione bien.',
    'seed')
ON CONFLICT (tenant_id) DO NOTHING;

-- 2. CONTENIDO — Calendario + publicaciones
CREATE TABLE IF NOT EXISTS om_contenido (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'authentic_pilates',
    ciclo TEXT NOT NULL,
    canal TEXT NOT NULL,
    tipo TEXT NOT NULL,
    titulo TEXT,
    cuerpo TEXT NOT NULL,
    hashtags TEXT[],
    media_url TEXT,
    funcion TEXT,
    lente TEXT,
    ints TEXT[],
    -- Estado
    estado TEXT DEFAULT 'borrador',
    filtro_identidad TEXT DEFAULT 'pendiente',
    filtro_motivo TEXT,
    programado_para TIMESTAMPTZ,
    publicado_at TIMESTAMPTZ,
    -- Métricas post-publicación
    alcance INT,
    engagement INT,
    clicks INT,
    guardados INT,
    compartidos INT,
    coherencia_score FLOAT,
    -- Metadata
    origen TEXT DEFAULT 'director',
    aprobado_por TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_contenido_ciclo ON om_contenido(tenant_id, ciclo);
CREATE INDEX IF NOT EXISTS idx_contenido_estado ON om_contenido(estado);
CREATE INDEX IF NOT EXISTS idx_contenido_canal ON om_contenido(canal);

-- 3. COMPETENCIA — Perfiles públicos monitorizados
CREATE TABLE IF NOT EXISTS om_competencia (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'authentic_pilates',
    nombre TEXT NOT NULL,
    canal TEXT NOT NULL,
    handle TEXT,
    url TEXT,
    tipo TEXT DEFAULT 'directo',
    followers INT,
    engagement_rate FLOAT,
    ultima_recogida TIMESTAMPTZ,
    datos JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_comp_tenant ON om_competencia(tenant_id);

-- 4. LEADS EXTERNOS — Leads que llegan por canales digitales
CREATE TABLE IF NOT EXISTS om_leads_externos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'authentic_pilates',
    canal TEXT NOT NULL,
    nombre TEXT,
    contacto TEXT,
    mensaje TEXT,
    compatible_identidad BOOLEAN,
    score_compatibilidad FLOAT,
    estado TEXT DEFAULT 'nuevo',
    asignado_a TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_leads_ext_estado ON om_leads_externos(estado);

-- 5. Trigger: contenido publicado → señal bus
CREATE OR REPLACE FUNCTION notify_contenido_publicado() RETURNS trigger AS $$
BEGIN
    IF NEW.estado = 'publicado' AND (OLD.estado IS NULL OR OLD.estado != 'publicado') THEN
        PERFORM pg_notify('contenido_publicado', json_build_object(
            'id', NEW.id, 'canal', NEW.canal, 'tipo', NEW.tipo
        )::text);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_contenido_publicado ON om_contenido;
CREATE TRIGGER trg_contenido_publicado
    AFTER INSERT OR UPDATE ON om_contenido
    FOR EACH ROW EXECUTE FUNCTION notify_contenido_publicado();

-- Seeds competencia Albelda/Logroño
INSERT INTO om_competencia (tenant_id, nombre, canal, handle, tipo) VALUES
    ('authentic_pilates', 'Pilates Logroño Centro', 'instagram', NULL, 'directo'),
    ('authentic_pilates', 'Gimnasio Municipal Albelda', 'gbp', NULL, 'indirecto'),
    ('authentic_pilates', 'Fisio + Pilates Rioja', 'instagram', NULL, 'directo')
ON CONFLICT DO NOTHING;
