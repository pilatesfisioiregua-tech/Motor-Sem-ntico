-- Catálogo Completo: Semántica + Isomorfismos + Red de Preguntas para pgvector
-- Fecha: 2026-04-13
-- 362 fórmulas + 40 isomorfismos + 69 enlaces

-- ============================================================
-- TABLA: catalogo_formulas (362 fórmulas con semántica)
-- ============================================================
CREATE TABLE IF NOT EXISTS catalogo_formulas (
    id SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL UNIQUE,
    formula TEXT,
    rama TEXT NOT NULL,               -- micro, macro, econometria, finanzas, matematica, conductual, optimizacion, estadistica
    finalidad TEXT[],                  -- DIAGNOSTICAR, RELACIONAR, PRESCRIBIR, VERIFICAR, PREDECIR, DESCOMPONER, MEDIR_RIESGO, OPTIMIZAR, VALORAR, COMPARAR

    -- Gramática (operaciones primitivas)
    gramatica TEXT[],                 -- ['ACUMULAR', 'NORMALIZAR', 'COMPARAR', ...]
    lectura TEXT,                     -- Lectura como oración
    resultado TEXT,                   -- Tipo de resultado (adjetivo, sujeto, prescripción, ...)

    -- Semántica (4 capas)
    polo_bajo TEXT,                   -- Polo bajo del eje
    polo_alto TEXT,                   -- Polo alto del eje
    eje TEXT,                         -- Nombre del eje semántico
    presupuestos TEXT[],              -- Lo que asume sin decirlo
    razonamiento JSONB,              -- [{"paso": "...", "operacion": "...", "produce": "..."}]
    si_alto TEXT,                     -- Interpretación cuando valor alto
    si_bajo TEXT,                     -- Interpretación cuando valor bajo
    pregunta TEXT,                    -- Pregunta que responde

    -- Para búsqueda semántica
    embedding vector(1536),           -- Embedding del texto completo (para búsqueda por significado)

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índice para búsqueda semántica
CREATE INDEX IF NOT EXISTS idx_formulas_embedding
    ON catalogo_formulas USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 20);

-- Índice por rama y finalidad
CREATE INDEX IF NOT EXISTS idx_formulas_rama ON catalogo_formulas(rama);
CREATE INDEX IF NOT EXISTS idx_formulas_finalidad ON catalogo_formulas USING GIN(finalidad);

-- ============================================================
-- TABLA: isomorfismos_gramatica (fórmulas con misma gramática)
-- ============================================================
CREATE TABLE IF NOT EXISTS isomorfismos_gramatica (
    id SERIAL PRIMARY KEY,
    gramatica TEXT[] NOT NULL,        -- Secuencia de operaciones compartida
    gramatica_texto TEXT NOT NULL,    -- "COMPARAR→NORMALIZAR"
    formulas TEXT[] NOT NULL,         -- Nombres de fórmulas isomorfas
    ramas TEXT[] NOT NULL,            -- Ramas que cruza
    n_formulas INT NOT NULL,
    es_cross_domain BOOLEAN NOT NULL, -- true si cruza ≥2 ramas
    significado TEXT,                 -- Qué significa compartir esta gramática
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- TABLA: red_preguntas (enlaces entre fórmulas)
-- ============================================================
CREATE TABLE IF NOT EXISTS red_preguntas (
    id SERIAL PRIMARY KEY,
    formula_origen TEXT NOT NULL REFERENCES catalogo_formulas(nombre),
    condicion TEXT NOT NULL,          -- 'alto', 'bajo', 'extremo', 'siempre'
    formula_destino TEXT NOT NULL REFERENCES catalogo_formulas(nombre),
    razon TEXT NOT NULL,              -- Por qué se desbloquea
    nivel INT DEFAULT 1,             -- Profundidad en la cascada
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(formula_origen, condicion, formula_destino)
);

CREATE INDEX IF NOT EXISTS idx_red_origen ON red_preguntas(formula_origen);
CREATE INDEX IF NOT EXISTS idx_red_destino ON red_preguntas(formula_destino);

-- ============================================================
-- TABLA: patrones_historicos (pgvector isomorfismos económicos)
-- ============================================================
CREATE TABLE IF NOT EXISTS patrones_historicos (
    id SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL UNIQUE,
    descripcion TEXT NOT NULL,
    señales JSONB NOT NULL,           -- {"metrica": [">", 0.3], ...}
    precedentes TEXT[] NOT NULL,      -- ["UK 1970s", "USA 1973-75"]
    prescripcion_historica TEXT NOT NULL,
    vector_señales vector(50),        -- Vector de señales para búsqueda coseno
    confianza_minima FLOAT DEFAULT 0.5,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_patrones_vector
    ON patrones_historicos USING ivfflat (vector_señales vector_cosine_ops)
    WITH (lists = 5);

-- ============================================================
-- FUNCIÓN: buscar fórmulas por significado (semántica)
-- ============================================================
CREATE OR REPLACE FUNCTION buscar_formula_por_significado(
    query_embedding vector(1536),
    max_results INT DEFAULT 10
)
RETURNS TABLE (
    nombre TEXT,
    pregunta TEXT,
    eje TEXT,
    polo_bajo TEXT,
    polo_alto TEXT,
    similitud FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        f.nombre,
        f.pregunta,
        f.eje,
        f.polo_bajo,
        f.polo_alto,
        1 - (f.embedding <=> query_embedding) AS similitud
    FROM catalogo_formulas f
    WHERE f.embedding IS NOT NULL
    ORDER BY f.embedding <=> query_embedding
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- FUNCIÓN: obtener cascada de preguntas desde una fórmula
-- ============================================================
CREATE OR REPLACE FUNCTION cascada_preguntas(
    formula_inicio TEXT,
    max_profundidad INT DEFAULT 3
)
RETURNS TABLE (
    nivel INT,
    origen TEXT,
    condicion TEXT,
    destino TEXT,
    razon TEXT,
    pregunta_destino TEXT,
    eje_destino TEXT
) AS $$
BEGIN
    RETURN QUERY
    WITH RECURSIVE cascada AS (
        -- Nivel 0: enlaces directos desde la fórmula inicial
        SELECT
            1 AS nivel,
            r.formula_origen AS origen,
            r.condicion,
            r.formula_destino AS destino,
            r.razon
        FROM red_preguntas r
        WHERE r.formula_origen = formula_inicio

        UNION ALL

        -- Niveles siguientes
        SELECT
            c.nivel + 1,
            r.formula_origen,
            r.condicion,
            r.formula_destino,
            r.razon
        FROM cascada c
        JOIN red_preguntas r ON r.formula_origen = c.destino
        WHERE c.nivel < max_profundidad
    )
    SELECT
        c.nivel,
        c.origen,
        c.condicion,
        c.destino,
        c.razon,
        f.pregunta AS pregunta_destino,
        f.eje AS eje_destino
    FROM cascada c
    LEFT JOIN catalogo_formulas f ON f.nombre = c.destino
    ORDER BY c.nivel, c.destino;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- VISTA: catálogo resumen
-- ============================================================
CREATE OR REPLACE VIEW v_catalogo_resumen AS
SELECT
    nombre,
    rama,
    finalidad,
    polo_bajo || ' ↔ ' || polo_alto AS eje_completo,
    pregunta,
    array_length(gramatica, 1) AS n_operaciones,
    array_length(presupuestos, 1) AS n_presupuestos
FROM catalogo_formulas
ORDER BY rama, nombre;
