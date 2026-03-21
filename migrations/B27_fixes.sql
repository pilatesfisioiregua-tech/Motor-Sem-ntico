-- B27 SQL Migration — ejecutar contra fly.io Postgres
-- Comando: cat migrations/B27_fixes.sql | fly postgres connect -a motor-semantico-db -d omni_mind

-- FIX 2: Añadir created_at a preguntas_matriz
ALTER TABLE preguntas_matriz ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();

-- FIX 3: Crear tablas faltantes
CREATE TABLE IF NOT EXISTS presupuestos (
    id SERIAL PRIMARY KEY,
    consumidor TEXT NOT NULL,
    limite_mensual_usd FLOAT DEFAULT 50.0,
    activo BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS costes_llm (
    id SERIAL PRIMARY KEY,
    consumidor TEXT NOT NULL,
    modelo TEXT NOT NULL,
    tokens_in INTEGER DEFAULT 0,
    tokens_out INTEGER DEFAULT 0,
    coste_total_usd FLOAT DEFAULT 0.0,
    componente TEXT,
    operacion TEXT,
    celda TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS celdas_matriz (
    id TEXT PRIMARY KEY,
    funcion TEXT NOT NULL,
    lente TEXT NOT NULL,
    n_datapoints INTEGER DEFAULT 0,
    tasa_media FLOAT DEFAULT 0.0,
    grado_actual FLOAT DEFAULT 0.0,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Seed celdas_matriz (21 celdas = 3L x 7F)
INSERT INTO celdas_matriz (id, funcion, lente)
SELECT f || 'x' || l, f, l
FROM (VALUES ('Conservar'),('Captar'),('Depurar'),('Distribuir'),('Frontera'),('Adaptar'),('Replicar')) AS funciones(f)
CROSS JOIN (VALUES ('Salud'),('Sentido'),('Continuidad')) AS lentes(l)
ON CONFLICT (id) DO NOTHING;

-- Seed presupuestos
INSERT INTO presupuestos (consumidor, limite_mensual_usd)
VALUES ('sistema', 50.0), ('motor_vn', 20.0), ('code_os', 30.0)
ON CONFLICT DO NOTHING;

-- FIX 4: Dedup config_enjambre (mantener 1 por tier)
DELETE FROM config_enjambre
WHERE id NOT IN (
    SELECT MAX(id) FROM config_enjambre GROUP BY tier
);

-- FIX 4: Dedup config_modelos (mantener 1 por rol)
DELETE FROM config_modelos
WHERE id NOT IN (
    SELECT MAX(id) FROM config_modelos GROUP BY rol
);

-- FIX 7: Consumir alertas estigmergicas stale
UPDATE marcas_estigmergicas SET consumida = true
WHERE consumida = false AND tipo = 'alerta'
  AND contenido->>'tipo' = 'autopoiesis_roto';

-- Verificaciones
SELECT 'preguntas_matriz.created_at' as fix, COUNT(*) as result FROM information_schema.columns WHERE table_name = 'preguntas_matriz' AND column_name = 'created_at';
SELECT 'presupuestos' as fix, COUNT(*) as result FROM presupuestos;
SELECT 'celdas_matriz' as fix, COUNT(*) as result FROM celdas_matriz;
SELECT 'config_enjambre' as fix, COUNT(*) as result FROM config_enjambre;
SELECT 'config_modelos' as fix, COUNT(*) as result FROM config_modelos;
SELECT 'alertas_stale' as fix, COUNT(*) as result FROM marcas_estigmergicas WHERE consumida = false AND tipo = 'alerta';
