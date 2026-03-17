-- Code OS v2 Migration — Session State + Knowledge + Custom Tools

-- Add session state for resume capability
ALTER TABLE code_os_sessions ADD COLUMN IF NOT EXISTS session_state JSONB;

-- Knowledge base for cross-session learning
CREATE TABLE IF NOT EXISTS code_os_knowledge (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    project_name TEXT NOT NULL,
    goal_text TEXT NOT NULL,
    approach_summary TEXT,
    model_used TEXT,
    pass_rate FLOAT,
    cost_usd FLOAT,
    session_id UUID REFERENCES code_os_sessions(id),
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_knowledge_project
    ON code_os_knowledge(project_name, pass_rate DESC);

-- Custom tools created by the agent itself
CREATE TABLE IF NOT EXISTS code_os_custom_tools (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    code TEXT NOT NULL,
    parameters_schema JSONB NOT NULL,
    test_code TEXT,
    project_name TEXT,
    created_by_session UUID REFERENCES code_os_sessions(id),
    verified BOOLEAN DEFAULT false,
    use_count INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_custom_tools_name
    ON code_os_custom_tools(name, project_name);
