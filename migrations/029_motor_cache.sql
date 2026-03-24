-- 029_motor_cache.sql — Caché semántico LLM + telemetría motor
-- Fase 4 del Roadmap v4 (P66)

-- 1. Caché semántico LLM (Pizarra Caché #10)
CREATE TABLE IF NOT EXISTS om_pizarra_cache_llm (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'authentic_pilates',
    prompt_hash TEXT NOT NULL,
    modelo TEXT NOT NULL,
    funcion TEXT,
    lente TEXT,
    respuesta TEXT NOT NULL,
    tokens_input INT DEFAULT 0,
    tokens_output INT DEFAULT 0,
    coste_usd FLOAT DEFAULT 0,
    hits INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),
    expires_at TIMESTAMPTZ DEFAULT (now() + interval '7 days')
);
CREATE INDEX IF NOT EXISTS idx_cache_hash ON om_pizarra_cache_llm(prompt_hash);
CREATE INDEX IF NOT EXISTS idx_cache_expires ON om_pizarra_cache_llm(expires_at);

-- 2. Telemetría de llamadas LLM
CREATE TABLE IF NOT EXISTS om_motor_telemetria (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'authentic_pilates',
    funcion TEXT,
    lente TEXT,
    modelo TEXT NOT NULL,
    tokens_input INT,
    tokens_output INT,
    coste_usd FLOAT,
    tiempo_ms INT,
    cache_hit BOOLEAN DEFAULT false,
    ciclo TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_telem_tenant_ciclo ON om_motor_telemetria(tenant_id, ciclo);
CREATE INDEX IF NOT EXISTS idx_telem_modelo ON om_motor_telemetria(modelo);

-- 3. Limpieza automática de caché expirado (función para cron)
CREATE OR REPLACE FUNCTION limpiar_cache_expirado() RETURNS void AS $$
    DELETE FROM om_pizarra_cache_llm WHERE expires_at < now();
$$ LANGUAGE sql;
