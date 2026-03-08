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
