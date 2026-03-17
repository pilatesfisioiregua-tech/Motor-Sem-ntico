-- CODE OS — Supabase Schema
-- Execute in staging: https://jbfiylwbgxglqwvgsedh.supabase.co

-- Sesiones de Code OS
CREATE TABLE IF NOT EXISTS code_os_sessions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    mode TEXT NOT NULL,
    input_raw TEXT NOT NULL,
    project_dir TEXT,
    project_name TEXT,
    model_primary TEXT,
    strategy TEXT,
    status TEXT DEFAULT 'running',
    created_at TIMESTAMPTZ DEFAULT now(),
    finished_at TIMESTAMPTZ
);

-- Visiones traducidas
CREATE TABLE IF NOT EXISTS code_os_visions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id UUID REFERENCES code_os_sessions(id) ON DELETE CASCADE,
    vision_raw TEXT NOT NULL,
    spec_generated JSONB,
    questions_asked JSONB,
    clarifications JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Briefings generados
CREATE TABLE IF NOT EXISTS code_os_briefings (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id UUID REFERENCES code_os_sessions(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    content_md TEXT NOT NULL,
    approved BOOLEAN DEFAULT false,
    user_feedback TEXT,
    version INT DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Cada iteración del agent loop
CREATE TABLE IF NOT EXISTS code_os_iterations (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id UUID REFERENCES code_os_sessions(id) ON DELETE CASCADE,
    iteration_n INT NOT NULL,
    model_used TEXT NOT NULL,
    tool_called TEXT,
    tool_args JSONB,
    tool_result TEXT,
    is_error BOOLEAN DEFAULT false,
    tokens_in INT,
    tokens_out INT,
    cost_usd FLOAT,
    duration_ms INT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Archivos creados/modificados
CREATE TABLE IF NOT EXISTS code_os_files (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id UUID REFERENCES code_os_sessions(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    action TEXT NOT NULL,
    content_before TEXT,
    content_after TEXT,
    iteration_n INT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Resultado final de cada sesión
CREATE TABLE IF NOT EXISTS code_os_results (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id UUID REFERENCES code_os_sessions(id) ON DELETE CASCADE,
    pass_rate FLOAT,
    tests_passed INT,
    tests_total INT,
    total_cost_usd FLOAT,
    total_time_s FLOAT,
    total_tokens INT,
    total_iterations INT,
    stop_reason TEXT,
    files_changed JSONB,
    error_summary TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Índices para queries de contexto rápidas
CREATE INDEX IF NOT EXISTS idx_sessions_project ON code_os_sessions(project_name, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON code_os_sessions(status);
CREATE INDEX IF NOT EXISTS idx_iterations_session ON code_os_iterations(session_id, iteration_n);
CREATE INDEX IF NOT EXISTS idx_briefings_session ON code_os_briefings(session_id);
CREATE INDEX IF NOT EXISTS idx_files_session ON code_os_files(session_id);
CREATE INDEX IF NOT EXISTS idx_results_session ON code_os_results(session_id);

-- RLS policies (open for now, same pattern as existing tables)
ALTER TABLE code_os_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE code_os_visions ENABLE ROW LEVEL SECURITY;
ALTER TABLE code_os_briefings ENABLE ROW LEVEL SECURITY;
ALTER TABLE code_os_iterations ENABLE ROW LEVEL SECURITY;
ALTER TABLE code_os_files ENABLE ROW LEVEL SECURITY;
ALTER TABLE code_os_results ENABLE ROW LEVEL SECURITY;

CREATE POLICY IF NOT EXISTS "acceso_total" ON code_os_sessions FOR ALL USING (true);
CREATE POLICY IF NOT EXISTS "acceso_total" ON code_os_visions FOR ALL USING (true);
CREATE POLICY IF NOT EXISTS "acceso_total" ON code_os_briefings FOR ALL USING (true);
CREATE POLICY IF NOT EXISTS "acceso_total" ON code_os_iterations FOR ALL USING (true);
CREATE POLICY IF NOT EXISTS "acceso_total" ON code_os_files FOR ALL USING (true);
CREATE POLICY IF NOT EXISTS "acceso_total" ON code_os_results FOR ALL USING (true);
