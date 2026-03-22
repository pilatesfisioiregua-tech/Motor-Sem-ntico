BEGIN;

-- Verificar dependencia
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'om_clientes') THEN
    RAISE EXCEPTION 'Tabla om_clientes no existe — ejecutar migrations anteriores primero';
  END IF;
END $$;

-- Tabla principal: piezas de conocimiento destiladas de chats
CREATE TABLE IF NOT EXISTS om_conocimiento_proyecto (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contenido TEXT NOT NULL,
    tipo VARCHAR(50) NOT NULL CHECK (tipo IN (
        'decision_cr1', 'principio', 'patron_validado',
        'error_no_repetir', 'arquitectura', 'implementacion',
        'insight', 'estado_sistema', 'otro'
    )),
    embedding vector(768),
    metadata JSONB DEFAULT '{}',
    -- metadata: {fecha_chat, titulo_chat, documentos_relacionados: [], F: [], L: [], INT: []}
    fuente VARCHAR(100) DEFAULT 'chat_destilado',
    fecha_conocimiento DATE DEFAULT CURRENT_DATE,
    relevancia_actual FLOAT DEFAULT 1.0,
    -- relevancia decae con el tiempo y cambia con el estado ACD
    ttl_dias INT,
    -- null = no caduca, >0 = caduca despues de N dias
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Indice vectorial para busqueda por similaridad
CREATE INDEX IF NOT EXISTS idx_conocimiento_embedding
    ON om_conocimiento_proyecto USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 10);

-- Indices de filtrado
CREATE INDEX IF NOT EXISTS idx_conocimiento_tipo
    ON om_conocimiento_proyecto (tipo);
CREATE INDEX IF NOT EXISTS idx_conocimiento_fecha
    ON om_conocimiento_proyecto (fecha_conocimiento DESC);

COMMIT;
