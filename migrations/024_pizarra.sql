-- 024_pizarra.sql — Pizarra Compartida: conciencia colectiva del organismo
-- Cada agente ESCRIBE lo que detecta/piensa/propone.
-- Cada agente LEE la pizarra ANTES de actuar.

CREATE TABLE IF NOT EXISTS om_pizarra (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'authentic_pilates',

    -- Quién escribe
    agente TEXT NOT NULL,
    capa TEXT NOT NULL,

    -- Qué escribe
    estado TEXT NOT NULL,
    detectando TEXT,
    interpretacion TEXT,
    accion_propuesta TEXT,
    necesita_de TEXT[],
    bloquea_a TEXT[],
    conflicto_con TEXT[],
    confianza NUMERIC(3,2) DEFAULT 0.5,
    prioridad INT DEFAULT 5,

    -- Contexto rico
    datos JSONB DEFAULT '{}',

    -- Temporal
    ciclo TEXT,
    version INT DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),

    -- Último en ganar: cada agente tiene UNA entrada activa por ciclo
    UNIQUE(tenant_id, agente, ciclo)
);

-- Índices para lectura rápida
CREATE INDEX IF NOT EXISTS idx_pizarra_tenant_ciclo ON om_pizarra(tenant_id, ciclo);
CREATE INDEX IF NOT EXISTS idx_pizarra_agente ON om_pizarra(tenant_id, agente);
CREATE INDEX IF NOT EXISTS idx_pizarra_capa ON om_pizarra(tenant_id, capa);
CREATE INDEX IF NOT EXISTS idx_pizarra_conflicto ON om_pizarra USING GIN (conflicto_con);
CREATE INDEX IF NOT EXISTS idx_pizarra_necesita ON om_pizarra USING GIN (necesita_de);
