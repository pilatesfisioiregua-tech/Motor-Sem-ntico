-- ============================================================
-- B-PIL-20a: BLOQUE VOZ ESTRATÉGICO — MODELO DE DATOS
-- Basado en B2.8 v3.0
-- REQUIERE: migrations previas que crean om_voz_isp,
--           om_voz_propuestas, om_voz_telemetria, om_voz_capa_a
-- ============================================================

BEGIN;

-- ── Verificar dependencias ──────────────────────────────────
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables
                   WHERE table_name = 'om_voz_isp') THEN
        RAISE EXCEPTION 'Tabla om_voz_isp no existe. Ejecutar migración de B-PIL-15 primero.';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables
                   WHERE table_name = 'om_voz_propuestas') THEN
        RAISE EXCEPTION 'Tabla om_voz_propuestas no existe. Ejecutar migración de B-PIL-01 primero.';
    END IF;
END $$;

-- ── 1. Identidad de comunicación (B2.8 §2 — Capa 1) ───────
CREATE TABLE IF NOT EXISTS om_voz_identidad (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'authentic_pilates',

    -- Estudio
    nombre_estudio TEXT,
    ubicacion TEXT,
    ubicacion_contexto TEXT,
    metodo_escuela TEXT,
    propuesta_valor TEXT,
    diferenciadores JSONB DEFAULT '[]',
    tono TEXT,
    personalidad TEXT,

    -- Target (3 niveles como define B2.8)
    target_primario JSONB DEFAULT '{}',
    target_secundario JSONB DEFAULT '{}',
    target_terciario JSONB DEFAULT '{}',

    -- Mercado
    nivel_conocimiento TEXT,
    confusiones_comunes JSONB DEFAULT '[]',
    competencia_percibida JSONB DEFAULT '[]',
    barreras_entrada JSONB DEFAULT '[]',

    -- Filosofía de comunicación
    principios_comunicacion JSONB DEFAULT '[]',
    lo_que_nunca_decir JSONB DEFAULT '[]',
    palabras_clave JSONB DEFAULT '[]',
    palabras_prohibidas JSONB DEFAULT '[]',

    -- Perfiles actuales (estado real)
    perfil_maps JSONB DEFAULT '{}',
    perfil_instagram JSONB DEFAULT '{}',
    perfil_whatsapp JSONB DEFAULT '{}',
    perfil_web JSONB DEFAULT '{}',
    perfil_facebook JSONB DEFAULT '{}',

    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),

    -- Un solo registro de identidad por tenant
    CONSTRAINT uq_voz_identidad_tenant UNIQUE (tenant_id)
);

-- ── 2. IRC por canal (B2.8 §4.2 — Eje 1 del Motor) ────────
-- Se recalcula semanalmente con 6 factores
CREATE TABLE IF NOT EXISTS om_voz_irc (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'authentic_pilates',
    canal TEXT NOT NULL,

    -- 6 factores del IRC (B2.8 §4.2)
    demanda_busqueda_local NUMERIC(4,2) DEFAULT 0,
    audiencia_objetivo_presente NUMERIC(4,2) DEFAULT 0,
    tasa_conversion_historica NUMERIC(4,2) DEFAULT 0,
    coste_tiempo_dueno NUMERIC(4,2) DEFAULT 0,
    capacidad_disponible NUMERIC(4,2) DEFAULT 0,
    afinidad_consumo_audiencia NUMERIC(4,2) DEFAULT 0,

    irc_score NUMERIC(4,2) DEFAULT 0,

    -- Pesos (ajustables por madurez del negocio)
    pesos JSONB DEFAULT '{"w1":0.2,"w2":0.2,"w3":0.2,"w4":0.1,"w5":0.1,"w6":0.2}',

    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT now(),

    -- Un IRC por canal por tenant
    CONSTRAINT uq_voz_irc_canal UNIQUE (tenant_id, canal)
);

CREATE INDEX IF NOT EXISTS idx_voz_irc_activo
    ON om_voz_irc(tenant_id, activo) WHERE activo = TRUE;

-- ── 3. PCA — Perfil de Consumo de Audiencia (B2.8 §4.4) ────
CREATE TABLE IF NOT EXISTS om_voz_pca (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'authentic_pilates',
    segmento TEXT NOT NULL,

    -- Dimensiones del PCA
    formato_preferido JSONB DEFAULT '[]',
    tono_que_resuena TEXT,
    temas_que_enganchan JSONB DEFAULT '[]',
    temas_que_no JSONB DEFAULT '[]',
    cuentas_referencia JSONB DEFAULT '[]',
    lenguaje_real JSONB DEFAULT '[]',
    horarios_consumo JSONB DEFAULT '{}',
    canal_interaccion_profunda TEXT,

    -- Fuentes de datos
    fuentes JSONB DEFAULT '[]',

    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),

    -- Un PCA por segmento por tenant
    CONSTRAINT uq_voz_pca_segmento UNIQUE (tenant_id, segmento)
);

-- ── 4. Estrategia activa de comunicación (B2.8 §3.1) ───────
-- Derivada del cruce: Identidad × ACD × IRC × PCA × Estacionalidad
CREATE TABLE IF NOT EXISTS om_voz_estrategia (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'authentic_pilates',

    -- Inputs
    estado_acd TEXT CHECK (estado_acd IN (
        'E1', 'E2', 'E3', 'E4',
        'operador_ciego', 'genio_mortal', 'automata_eterno',
        'piloto_sin_mapa', 'hiperactivo_fragil', 'equilibrio_esteril'
    )),
    lentes JSONB DEFAULT '{}',
    contexto_mercado TEXT,
    contexto_estacional TEXT,
    ocupacion_pct NUMERIC(5,2),
    irc_snapshot JSONB DEFAULT '{}',
    pca_snapshot JSONB DEFAULT '{}',

    -- Outputs (lo que genera el motor estratégico)
    foco_principal TEXT CHECK (foco_principal IN (
        'educar', 'captar', 'retener', 'fidelizar', 'activar', 'depurar'
    )),
    foco_secundario TEXT,
    narrativa TEXT,
    canales_prioridad JSONB DEFAULT '[]',
    tipos_contenido_prioridad JSONB DEFAULT '[]',
    frecuencia_recomendada JSONB DEFAULT '{}',
    evitar JSONB DEFAULT '[]',
    prescripciones JSONB DEFAULT '[]',

    activa BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_voz_estrategia_activa
    ON om_voz_estrategia(tenant_id, activa) WHERE activa = TRUE;

-- ── 5. Plantillas de perfiles (Arquitecto de Presencia §3.2) ─
CREATE TABLE IF NOT EXISTS om_voz_perfil_plantilla (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'authentic_pilates',
    canal TEXT NOT NULL,
    tipo TEXT NOT NULL,
    contenido TEXT NOT NULL,
    instrucciones TEXT,
    posicion_matricial TEXT,
    estado TEXT DEFAULT 'borrador'
        CHECK (estado IN ('borrador', 'aprobado', 'aplicado')),
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ── 6. Telemetría por canal (ciclo APRENDER de B2.8) ────────
CREATE TABLE IF NOT EXISTS om_voz_telemetria_canal (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'authentic_pilates',
    canal TEXT NOT NULL,
    periodo TEXT NOT NULL,

    -- Métricas de negocio (NO vanidad)
    leads_generados INTEGER DEFAULT 0,
    reservas_directas INTEGER DEFAULT 0,
    conversiones_cliente INTEGER DEFAULT 0,
    mensajes_respondidos INTEGER DEFAULT 0,
    tasa_respuesta NUMERIC(5,2),
    tasa_apertura NUMERIC(5,2),
    resenas_recibidas INTEGER DEFAULT 0,
    resenas_respondidas INTEGER DEFAULT 0,

    -- Métricas de contenido (para calibrar PCA)
    contenido_publicado INTEGER DEFAULT 0,
    mejor_formato TEXT,
    mejor_tema TEXT,
    engagement_medio NUMERIC(5,2),

    -- Atribución
    primer_contacto_pct NUMERIC(5,2),

    created_at TIMESTAMPTZ DEFAULT now(),

    -- Un registro por canal por periodo
    CONSTRAINT uq_telemetria_canal_periodo UNIQUE (tenant_id, canal, periodo)
);

CREATE INDEX IF NOT EXISTS idx_telemetria_canal
    ON om_voz_telemetria_canal(tenant_id, canal, periodo);

-- ── 7. Inteligencia de competidores (Outscraper data) ───────
CREATE TABLE IF NOT EXISTS om_voz_competidor (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'authentic_pilates',
    nombre TEXT NOT NULL,
    plataforma TEXT NOT NULL DEFAULT 'google_maps',
    place_id TEXT,

    -- Datos del competidor
    puntuacion NUMERIC(3,2),
    total_resenas INTEGER DEFAULT 0,
    categorias JSONB DEFAULT '[]',
    servicios JSONB DEFAULT '[]',
    precio_rango TEXT,
    horarios JSONB DEFAULT '{}',
    atributos JSONB DEFAULT '[]',

    -- Análisis cualitativo (generado por LLM sobre reseñas)
    fortalezas JSONB DEFAULT '[]',
    debilidades JSONB DEFAULT '[]',
    quejas_frecuentes JSONB DEFAULT '[]',
    lo_que_valoran JSONB DEFAULT '[]',
    oportunidad_para_nosotros TEXT,

    -- Fuente y frescura
    fuente TEXT DEFAULT 'outscraper',
    fecha_ultima_actualizacion DATE,
    activo BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),

    CONSTRAINT uq_competidor UNIQUE (tenant_id, nombre, plataforma)
);

-- ── 8. Señales detectadas (ciclo ESCUCHAR de B2.8) ─────────
CREATE TABLE IF NOT EXISTS om_voz_senales (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'authentic_pilates',
    origen TEXT NOT NULL,
    capa TEXT NOT NULL CHECK (capa IN ('A', 'B', 'C')),
    urgencia TEXT DEFAULT 'baja'
        CHECK (urgencia IN ('baja', 'media', 'alta', 'critica')),
    contenido JSONB NOT NULL,
    procesada BOOLEAN DEFAULT FALSE,
    -- Referencia a propuesta generada (si se convirtió en propuesta)
    propuesta_generada_id UUID,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_senales_pendientes
    ON om_voz_senales(tenant_id, procesada) WHERE procesada = FALSE;

-- ── 9. Extender om_voz_isp con campos estratégicos ─────────
ALTER TABLE om_voz_isp ADD COLUMN IF NOT EXISTS elementos_evaluados JSONB DEFAULT '[]';
ALTER TABLE om_voz_isp ADD COLUMN IF NOT EXISTS acciones_generadas JSONB DEFAULT '[]';
ALTER TABLE om_voz_isp ADD COLUMN IF NOT EXISTS posicion_matricial TEXT;
ALTER TABLE om_voz_isp ADD COLUMN IF NOT EXISTS automatico BOOLEAN DEFAULT FALSE;

-- ── 10. Calendario de contenido (planificación semanal) ─────
CREATE TABLE IF NOT EXISTS om_voz_calendario (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'authentic_pilates',

    -- Planificación
    semana TEXT NOT NULL,
    canal TEXT NOT NULL,
    tipo_contenido TEXT NOT NULL,
    dia_publicacion DATE,
    hora_publicacion TIME,

    -- Contenido (puede estar vacío si es solo plan)
    titulo TEXT,
    contenido TEXT,
    visual_sugerido TEXT,
    cta TEXT,

    -- Justificación (los 3 ejes)
    eje1_irc NUMERIC(4,2),
    eje2_posicion TEXT,
    eje3_formato_pca TEXT,
    justificacion TEXT,

    -- Estado
    estado TEXT DEFAULT 'planificado'
        CHECK (estado IN ('planificado', 'aprobado', 'publicado', 'descartado')),
    aprobado_por TEXT,
    publicado_at TIMESTAMPTZ,

    -- Resultado (retroalimentación)
    resultado JSONB DEFAULT '{}',

    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_calendario_semana
    ON om_voz_calendario(tenant_id, semana, estado);

COMMIT;
