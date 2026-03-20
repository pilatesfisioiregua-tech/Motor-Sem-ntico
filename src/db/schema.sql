-- src/db/schema.sql

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ==========================================
-- INTELIGENCIAS Y META-RED
-- ==========================================

CREATE TABLE IF NOT EXISTS inteligencias (
    id TEXT PRIMARY KEY,
    nombre TEXT NOT NULL,
    categoria TEXT NOT NULL,
    firma TEXT NOT NULL,
    punto_ciego TEXT NOT NULL,
    objetos_exclusivos TEXT[],
    es_irreducible BOOLEAN DEFAULT FALSE,
    raices_dominio TEXT[],            -- [v2] raíces pre-categoriales de esta inteligencia
    preguntas JSONB NOT NULL,
    modos_naturales TEXT[],           -- [v2] modos donde opera bien: ['analizar','percibir',...]
    modos_forzados TEXT[]             -- [v2] modos donde opera mal
);

-- Aristas del grafo de complementariedad
CREATE TABLE IF NOT EXISTS aristas_grafo (
    id SERIAL PRIMARY KEY,
    origen TEXT REFERENCES inteligencias(id),
    destino TEXT REFERENCES inteligencias(id),
    tipo TEXT NOT NULL CHECK (tipo IN ('composicion', 'fusion', 'diferencial', 'redundancia')),
    peso FLOAT NOT NULL,
    direccion_optima TEXT,
    hallazgo_emergente TEXT,
    UNIQUE(origen, destino, tipo)
);

-- ==========================================
-- MARCO LINGÜÍSTICO (datos operativos)
-- ==========================================

-- Las 8 operaciones primitivas
CREATE TABLE IF NOT EXISTS operaciones_sintacticas (
    id SERIAL PRIMARY KEY,
    nombre TEXT UNIQUE NOT NULL,
    input_tipo TEXT NOT NULL,
    output_tipo TEXT NOT NULL,
    propiedad_clave TEXT NOT NULL,
    pregunta_detectora TEXT NOT NULL,
    propiedades_algebraicas JSONB
);

-- Las 9 capas del sistema (constituyentes sintácticos)
CREATE TABLE IF NOT EXISTS capas_sistema (
    id SERIAL PRIMARY KEY,
    nombre TEXT UNIQUE NOT NULL,
    categoria_gramatical TEXT NOT NULL,
    pregunta TEXT NOT NULL,
    verbo_existencial TEXT,
    operacion_primaria TEXT
);

-- Los 6 tipos de acople
CREATE TABLE IF NOT EXISTS tipos_acople (
    id SERIAL PRIMARY KEY,
    conjuncion TEXT UNIQUE NOT NULL,
    tipo TEXT NOT NULL,
    diagnostico TEXT NOT NULL
);

-- Falacias aritméticas (errores de tipo lógico)
CREATE TABLE IF NOT EXISTS falacias_aritmeticas (
    id SERIAL PRIMARY KEY,
    nombre TEXT UNIQUE NOT NULL,
    operacion_incorrecta TEXT NOT NULL,
    correccion TEXT NOT NULL,
    ejemplo TEXT
);

-- Mapeo sufijo → operación → capa (para Capa 0)
CREATE TABLE IF NOT EXISTS sufijos_operaciones (
    id SERIAL PRIMARY KEY,
    sufijo TEXT NOT NULL,
    transforma_en TEXT NOT NULL,
    capa_destino TEXT
);

-- ==========================================
-- TELEMETRÍA Y RETROALIMENTACIÓN
-- ==========================================

CREATE TABLE IF NOT EXISTS ejecuciones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT now(),
    input TEXT NOT NULL,
    contexto TEXT,
    modo TEXT NOT NULL,
    huecos_detectados JSONB,          -- [v2] output de Capa 0
    algoritmo_usado JSONB NOT NULL,
    resultado JSONB NOT NULL,
    coste_usd FLOAT,
    tiempo_s FLOAT,
    score_calidad FLOAT,
    falacias_detectadas JSONB,        -- [v2] falacias encontradas por Capa 5
    feedback_usuario JSONB
);

-- Vectores para router futuro (pgvector)
CREATE TABLE IF NOT EXISTS embeddings_inteligencias (
    id TEXT PRIMARY KEY REFERENCES inteligencias(id),
    embedding vector(1024),
    texto_base TEXT
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_aristas_origen ON aristas_grafo(origen);
CREATE INDEX IF NOT EXISTS idx_aristas_destino ON aristas_grafo(destino);
CREATE INDEX IF NOT EXISTS idx_aristas_tipo ON aristas_grafo(tipo);
CREATE INDEX IF NOT EXISTS idx_ejecuciones_modo ON ejecuciones(modo);
CREATE INDEX IF NOT EXISTS idx_ejecuciones_created ON ejecuciones(created_at DESC);

-- =================================================================
-- ACD — tablas para Álgebra Cognitiva Diagnóstica
-- 4 tablas nuevas: tipos_pensamiento, tipos_razonamiento,
--                  estados_diagnosticos, diagnosticos
-- =================================================================

-- ── TABLA 1: Tipos de Pensamiento (15 entradas) ─────────────────

CREATE TABLE IF NOT EXISTS tipos_pensamiento (
    id TEXT PRIMARY KEY,                -- P01-P15
    nombre TEXT NOT NULL,
    descripcion TEXT,
    lente_preferente TEXT NOT NULL,      -- "salud", "sentido", "continuidad", "salud+sentido", etc.
    funciones_naturales TEXT[],          -- {"F3", "F5"}
    razonamientos_asociados TEXT[],      -- {"R03", "R09"}
    nivel_logico INTEGER,               -- 1-5
    ints_compatibles TEXT[],
    ints_incompatibles TEXT[],
    pregunta_activadora TEXT,
    cuando_usar TEXT,
    datos JSONB                          -- campos adicionales sin esquema fijo
);

-- ── TABLA 2: Tipos de Razonamiento (12 entradas) ────────────────

CREATE TABLE IF NOT EXISTS tipos_razonamiento (
    id TEXT PRIMARY KEY,                -- R01-R12
    nombre TEXT NOT NULL,
    descripcion TEXT,
    lente_preferente TEXT NOT NULL,
    funciones_naturales TEXT[],
    ints_compatibles TEXT[],
    genera TEXT,                         -- "Certeza operativa", "Transferencia cross-dominio", etc.
    limite TEXT,
    pregunta_activadora TEXT,
    datos JSONB
);

-- ── TABLA 3: Estados Diagnósticos (10 entradas) ─────────────────

CREATE TABLE IF NOT EXISTS estados_diagnosticos (
    id TEXT PRIMARY KEY,                -- E1, E2, E3, E4, operador_ciego, etc.
    nombre TEXT NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN ('equilibrado', 'desequilibrado')),
    descripcion TEXT,
    perfil_lentes TEXT,                 -- "S↑ Se↓ C↓" para desequilibrados, NULL para equilibrados
    condiciones JSONB NOT NULL,         -- umbrales numéricos
    flags TEXT[],                       -- {"peligro_oculto", "invisible_metricas_convencionales"}
    ints_tipicas_activas TEXT[],
    ints_tipicas_ausentes TEXT[],
    prescripcion_ps TEXT[],             -- P que hay que activar
    prescripcion_rs TEXT[],             -- R que hay que activar
    objetivo_prescripcion TEXT,         -- "CUESTIONAR", "EJECUTAR", "TRANSFERIR", etc.
    transiciones JSONB                  -- [{destino, via, nota}]
);

-- ── TABLA 4: Diagnósticos (historial por caso) ──────────────────

CREATE TABLE IF NOT EXISTS diagnosticos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT now(),
    caso_input TEXT,                    -- texto del caso original
    ejecucion_id UUID,                  -- referencia a ejecuciones(id) si existe
    -- Pre-intervención
    vector_pre JSONB,                   -- {F1: 0.50, F2: 0.30, ...}
    lentes_pre JSONB,                   -- {salud: 0.40, sentido: 0.60, continuidad: 0.20}
    estado_pre TEXT,                    -- "genio_mortal", "E3", etc.
    flags_pre TEXT[],                   -- {"automata_oculto", "zona_toxica"}
    repertorio_inferido JSONB,          -- {ints_activas, ints_atrofiadas, ps_activos, rs_activos}
    -- Prescripción
    prescripcion JSONB,                 -- {ints, ps, rs, secuencia_funciones, frenar, modo, nivel_logico}
    -- Post-intervención
    vector_post JSONB,
    lentes_post JSONB,
    estado_post TEXT,
    flags_post TEXT[],
    -- Resultado
    resultado TEXT CHECK (resultado IN ('cierre', 'inerte', 'toxico', 'pendiente')),
    metricas JSONB                      -- {delta_se, delta_gap, repertorio_expansion, funciones_se_activas}
);

-- ── ÍNDICES ACD ─────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_diagnosticos_estado_pre ON diagnosticos(estado_pre);
CREATE INDEX IF NOT EXISTS idx_diagnosticos_resultado ON diagnosticos(resultado);
CREATE INDEX IF NOT EXISTS idx_diagnosticos_created ON diagnosticos(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_estados_tipo ON estados_diagnosticos(tipo);

-- =================================================================
-- V4: Extensiones para Maestro V4 (3L×7F×18INT×15P×12R)
-- =================================================================

-- V4 §2.3: Afinidad de lente por inteligencia
ALTER TABLE inteligencias ADD COLUMN IF NOT EXISTS lente_primaria TEXT;
ALTER TABLE inteligencias ADD COLUMN IF NOT EXISTS lentes_secundarias TEXT[];
