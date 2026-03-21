-- migrations/003_registrador.sql
-- Tabla de datapoints de efectividad (§6.6 Maestro)

CREATE TABLE IF NOT EXISTS datapoints_efectividad (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ejecucion_id UUID REFERENCES ejecuciones(id),
    pregunta_id TEXT,
    inteligencia TEXT NOT NULL,
    modelo TEXT NOT NULL,
    caso_id TEXT,
    consumidor TEXT NOT NULL DEFAULT 'motor_vn',
    celda_objetivo TEXT,
    funcion TEXT,
    lente TEXT,
    gap_pre FLOAT,
    gap_post FLOAT,
    gap_cerrado FLOAT GENERATED ALWAYS AS (
        CASE WHEN gap_pre IS NOT NULL AND gap_post IS NOT NULL
        THEN gap_pre - gap_post ELSE NULL END
    ) STORED,
    tasa_cierre FLOAT GENERATED ALWAYS AS (
        CASE WHEN gap_pre IS NOT NULL AND gap_pre > 0 AND gap_post IS NOT NULL
        THEN (gap_pre - gap_post) / gap_pre ELSE NULL END
    ) STORED,
    operacion TEXT,
    score_calidad FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_dp_inteligencia ON datapoints_efectividad(inteligencia);
CREATE INDEX IF NOT EXISTS idx_dp_modelo ON datapoints_efectividad(modelo);
CREATE INDEX IF NOT EXISTS idx_dp_celda ON datapoints_efectividad(celda_objetivo);
CREATE INDEX IF NOT EXISTS idx_dp_created ON datapoints_efectividad(created_at DESC);

-- Tabla de perfil de gradientes por caso (estado del campo pre/post)
CREATE TABLE IF NOT EXISTS perfil_gradientes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ejecucion_id UUID REFERENCES ejecuciones(id),
    momento TEXT NOT NULL CHECK (momento IN ('pre', 'post')),
    vector_funcional JSONB NOT NULL,
    lentes JSONB NOT NULL,
    arquetipo_primario TEXT,
    arquetipo_score FLOAT,
    coalicion TEXT,
    perfil_lente TEXT,
    eslabon_debil TEXT,
    toxicidad_total FLOAT,
    estable BOOLEAN,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pg_ejecucion ON perfil_gradientes(ejecucion_id);
