-- OMC-95: Simbionte escribe en Postgres, LLM consulta via tool_use
-- Tabla principal donde el Simbionte deposita resultados calculados.
-- El LLM NO recibe estos datos en el prompt — los consulta via REST.

CREATE TABLE IF NOT EXISTS resultados_simbionte (
    id              BIGSERIAL PRIMARY KEY,
    sesion_id       UUID NOT NULL DEFAULT gen_random_uuid(),
    -- Identificación
    nombre          TEXT NOT NULL,           -- nombre de la fórmula/métrica
    tipo            TEXT NOT NULL,           -- diagnostico, relaciones, riesgo, prescripcion, patron, cascada
    categoria       TEXT,                    -- subtipo: varianza, correlacion, elasticidad, gap, etc.
    -- Valores
    valor           DOUBLE PRECISION,        -- valor numérico calculado
    valor_texto     TEXT,                    -- clasificación: alto/bajo/normal/extremo
    texto_legible   TEXT,                    -- descripción en lenguaje natural
    -- Semántica (de la fórmula)
    pregunta        TEXT,                    -- qué pregunta responde esta fórmula
    polos           JSONB,                   -- eje semántico: ["polo_bajo", "polo_alto"]
    presupuestos    JSONB,                   -- lo que la fórmula asume sin decirlo
    razonamiento    TEXT,                    -- razonamiento paso a paso
    -- Contexto
    datos_origen    JSONB,                   -- qué series se usaron para calcular
    finalidad       TEXT,                    -- finalidad detectada del análisis
    paso_protocolo  INT,                     -- en qué paso del protocolo se calculó (NULL = precálculo)
    -- Patrones e isomorfismos
    patron_match    TEXT,                    -- patrón histórico que coincide (si aplica)
    isomorfismo     TEXT,                    -- isomorfismo cross-domain detectado
    precedentes     JSONB,                   -- precedentes históricos
    prescripcion    TEXT,                    -- prescripción del patrón
    -- Cascada
    enlaces         JSONB,                   -- preguntas que se desbloquean desde este resultado
    -- Metadata
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    modelo_llm      TEXT,                    -- qué modelo consumirá estos datos (para auditoría)
    coste_calculo   DOUBLE PRECISION DEFAULT 0  -- coste de calcular este resultado ($)
);

-- Índices para consultas rápidas del LLM
CREATE INDEX IF NOT EXISTS idx_res_simbionte_sesion ON resultados_simbionte(sesion_id);
CREATE INDEX IF NOT EXISTS idx_res_simbionte_tipo ON resultados_simbionte(tipo);
CREATE INDEX IF NOT EXISTS idx_res_simbionte_nombre ON resultados_simbionte(nombre);
CREATE INDEX IF NOT EXISTS idx_res_simbionte_sesion_tipo ON resultados_simbionte(sesion_id, tipo);

-- Tabla de auditoría: qué consultó el LLM y cuándo
CREATE TABLE IF NOT EXISTS auditorias_simbionte (
    id              BIGSERIAL PRIMARY KEY,
    sesion_id       UUID NOT NULL,
    tool_name       TEXT NOT NULL,           -- consultar_formula, consultar_patron, calcular, cascada
    input_params    JSONB NOT NULL,          -- parámetros de la consulta
    n_resultados    INT DEFAULT 0,           -- cuántos resultados devolvió
    tokens_respuesta INT DEFAULT 0,          -- tokens del resultado devuelto al LLM
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_audit_simbionte_sesion ON auditorias_simbionte(sesion_id);
