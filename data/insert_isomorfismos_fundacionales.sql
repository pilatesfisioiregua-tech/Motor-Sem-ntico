-- Catálogo fundacional de isomorfismos — Simbionte v6
-- Fecha: 2026-04-12
-- Verificado: Opus analizó 3490 textos (2990 ES + 500 EN), $0

-- Tabla de isomorfismos (requiere pgvector)
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS isomorfismos (
    id SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL UNIQUE,
    codigo TEXT NOT NULL UNIQUE,          -- Σ-P, Σ-E, Σ-C, Α-E, Τ-R
    definicion TEXT NOT NULL,
    ejes_dominantes TEXT[] NOT NULL,
    profundidad_tipica FLOAT NOT NULL,
    prevalencia FLOAT,                     -- % en corpus
    condicion_necesaria TEXT,              -- regla determinista
    variantes JSONB DEFAULT '[]',
    corpus_origen TEXT,
    vector_centroide vector(95),           -- geometría 95D para búsqueda coseno
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índice para búsqueda por similitud coseno
CREATE INDEX IF NOT EXISTS idx_isomorfismos_vector
    ON isomorfismos USING ivfflat (vector_centroide vector_cosine_ops)
    WITH (lists = 5);

-- 5 isomorfismos fundacionales
INSERT INTO isomorfismos (nombre, codigo, definicion, ejes_dominantes, profundidad_tipica, prevalencia, condicion_necesaria, variantes, corpus_origen)
VALUES
(
    'Sigma Profundo',
    'Σ-P',
    'Sistemas y Juegos codominan en los 4 niveles incluyendo N3. Interacción estratégica multi-agente auto-similar desde token hasta texto.',
    ARRAY['sistemas', 'juegos', 'topologia'],
    0.734,
    0.12,
    'juegos IN dominantes[N3]',
    '[{"nombre": "AEF-Escenario", "desc": "condicionales forward-looking dominantes"},
      {"nombre": "AEF-Balanceado", "desc": "sistemas y juegos en equilibrio perfecto"},
      {"nombre": "AEF-Topológico", "desc": "topología también en N1, densidad de referencias cruzadas"}]'::jsonb,
    'EN earnings calls Q4 2024 (cluster 0, 12%)'
),
(
    'Sigma Estable',
    'Σ-E',
    'Sistemas como atractor principal en todos los niveles. Juegos en N2 y N4. Topología en N3. Isomorfismo canónico universal del texto formal.',
    ARRAY['sistemas', 'juegos', 'topologia'],
    0.632,
    0.58,
    'sistemas IN dominantes[N1] como atractor único',
    '[{"nombre": "TSC-Puro", "desc": "operational update, juegos débil"},
      {"nombre": "TSC-Estratégico-Latente", "desc": "juegos prominente N2/N4, umbral para Σ-P"},
      {"nombre": "TSC-Topología-Reforzada", "desc": "topología en N2, condicionales implícitos"}]'::jsonb,
    'EN clusters 1+2 (88%), ES cluster 1 (parcial). Cross-idioma.'
),
(
    'Sigma Cibernético',
    'Σ-C',
    'Cibernética codomina con Sistemas en N2. Ciclos de feedback como principio organizador de párrafo. Textos procesuales o normativos.',
    ARRAY['sistemas', 'cibernetica', 'topologia'],
    0.621,
    NULL,  -- Variable, más en ES que EN
    'cibernetica IN dominantes[N2]',
    '[{"nombre": "SCH-Cibernético", "desc": "blogs narrativos, ciclos explícitos de proceso"},
      {"nombre": "SCH-Sistémico-Formal", "desc": "convergente con Σ-E, textos técnicos formales ES"},
      {"nombre": "SCH-Narrativo", "desc": "topología fuerte N2/N3, estructura temporal densa"}]'::jsonb,
    'ES cluster 1 (parcial). Ausente en EN.'
),
(
    'Alpha Estadístico',
    'Α-E',
    'Estadística domina múltiples niveles consecutivos desplazando marcos relacionales. Distribución de frecuencias como principio organizador.',
    ARRAY['estadistica', 'cibernetica'],
    0.56,
    0.15,  -- del cluster residual
    'estadistica IN dominantes[N2] AND dominantes[N3]',
    '[{"nombre": "FED-Técnico", "desc": "patentes, especificaciones experimentales"},
      {"nombre": "FED-Tutorial", "desc": "estructura didáctica sin coherencia fractal"},
      {"nombre": "FED-Indexical", "desc": "catálogos, índices, referencia pura"}]'::jsonb,
    'ES cluster 2 (variante técnica). Ausente en EN.'
),
(
    'Topo Referencial',
    'Τ-R',
    'Topología domina N2/N3 sin marcos relacionales fuertes. Organizado por conectividad estructural (referencias, enumeraciones).',
    ARRAY['topologia', 'sistemas'],
    0.54,
    0.15,  -- del cluster residual
    'topologia IN dominantes[N2] como único dominante',
    '[{"nombre": "Catálogo", "desc": "listados, directorios, FAQs"},
      {"nombre": "Guía", "desc": "estructura referencial con navegación"},
      {"nombre": "Índice", "desc": "pura conectividad sin argumentación"}]'::jsonb,
    'ES cluster 2 (variante indexical). Ausente en EN.'
);

-- Función de búsqueda por similitud
CREATE OR REPLACE FUNCTION buscar_isomorfismo(
    query_vector vector(95),
    umbral FLOAT DEFAULT 0.85,
    max_results INT DEFAULT 3
)
RETURNS TABLE (
    nombre TEXT,
    codigo TEXT,
    definicion TEXT,
    similitud FLOAT,
    ejes_dominantes TEXT[],
    profundidad_tipica FLOAT,
    variantes JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        i.nombre,
        i.codigo,
        i.definicion,
        1 - (i.vector_centroide <=> query_vector) AS similitud,
        i.ejes_dominantes,
        i.profundidad_tipica,
        i.variantes
    FROM isomorfismos i
    WHERE i.vector_centroide IS NOT NULL
      AND 1 - (i.vector_centroide <=> query_vector) >= umbral
    ORDER BY i.vector_centroide <=> query_vector
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql;

-- Vista rápida del catálogo
CREATE OR REPLACE VIEW catalogo_isomorfismos AS
SELECT
    codigo,
    nombre,
    profundidad_tipica AS prof,
    prevalencia AS prev,
    ejes_dominantes AS ejes,
    condicion_necesaria AS condicion,
    jsonb_array_length(variantes) AS n_variantes,
    corpus_origen AS corpus
FROM isomorfismos
ORDER BY profundidad_tipica DESC;
