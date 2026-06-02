-- ============================================================================
-- DataMaster Pro - Plan Limits Schema
-- Novas tabelas para: ROI Logging, Task Scheduling, Tool Configurations
-- ============================================================================

-- ============================================================================
-- 1. EXECUTION_LOGS - Rastreamento de execuções e cálculo de ROI
-- ============================================================================
CREATE TABLE IF NOT EXISTS execution_logs (
    -- Primary Key
    execution_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Foreign Keys
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Dados de execução
    tool_name TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    duration_seconds REAL NOT NULL,
    lines_processed INTEGER NOT NULL DEFAULT 0,
    file_size_bytes INTEGER NOT NULL DEFAULT 0,
    
    -- Status
    status TEXT NOT NULL CHECK (status IN ('success', 'failed', 'cancelled')),
    error_message TEXT,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Índices para performance
    CONSTRAINT execution_logs_positive_duration CHECK (duration_seconds >= 0),
    CONSTRAINT execution_logs_positive_lines CHECK (lines_processed >= 0),
    CONSTRAINT execution_logs_positive_size CHECK (file_size_bytes >= 0)
);

-- Índices para queries rápidas
CREATE INDEX IF NOT EXISTS idx_execution_logs_user_id ON execution_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_execution_logs_tool_name ON execution_logs(tool_name);
CREATE INDEX IF NOT EXISTS idx_execution_logs_timestamp ON execution_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_execution_logs_status ON execution_logs(status);
CREATE INDEX IF NOT EXISTS idx_execution_logs_user_timestamp ON execution_logs(user_id, timestamp DESC);

-- RLS Policy - Usuários veem apenas seus próprios logs
ALTER TABLE execution_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own execution logs" ON execution_logs
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own execution logs" ON execution_logs
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own execution logs" ON execution_logs
    FOR DELETE USING (auth.uid() = user_id);


-- ============================================================================
-- 2. SCHEDULED_TASKS - Agendamento de tarefas com Cron
-- ============================================================================
CREATE TABLE IF NOT EXISTS scheduled_tasks (
    -- Primary Key
    task_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Foreign Keys
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Identificação da tarefa
    tool_name TEXT NOT NULL,
    tool_action TEXT NOT NULL,
    task_name TEXT,  -- Nome amigável da tarefa (ex: "Consolidação diária")
    
    -- Entrada
    input_files TEXT NOT NULL,  -- JSON array: ["file1.xlsx", "file2.xlsx"]
    
    -- Agendamento
    schedule_frequency TEXT NOT NULL CHECK (
        schedule_frequency IN ('daily', 'weekly', 'monthly', 'custom_cron')
    ),
    cron_expression TEXT,  -- Para schedule_frequency='custom_cron'
    time_of_day TEXT,  -- HH:MM para daily/weekly/monthly
    day_of_week INTEGER,  -- 0=Monday, 6=Sunday (para weekly)
    day_of_month INTEGER,  -- 1-31 (para monthly)
    
    -- Status
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- Histórico de execução
    last_run TEXT,  -- ISO timestamp
    next_run TEXT NOT NULL,  -- ISO timestamp
    execution_count INTEGER DEFAULT 0,
    last_status TEXT,  -- 'success', 'failed', 'pending'
    last_error TEXT,
    
    -- Configuração da ferramenta
    config TEXT,  -- JSON com parâmetros específicos da ferramenta
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT scheduled_tasks_day_of_week CHECK (day_of_week IS NULL OR (day_of_week >= 0 AND day_of_week <= 6)),
    CONSTRAINT scheduled_tasks_day_of_month CHECK (day_of_month IS NULL OR (day_of_month >= 1 AND day_of_month <= 31))
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_user_id ON scheduled_tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_tool_name ON scheduled_tasks(tool_name);
CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_enabled ON scheduled_tasks(enabled);
CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_next_run ON scheduled_tasks(next_run);
CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_user_enabled ON scheduled_tasks(user_id, enabled);

-- RLS Policy - Usuários veem apenas suas próprias tarefas
ALTER TABLE scheduled_tasks ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own scheduled tasks" ON scheduled_tasks
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create scheduled tasks" ON scheduled_tasks
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own scheduled tasks" ON scheduled_tasks
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own scheduled tasks" ON scheduled_tasks
    FOR DELETE USING (auth.uid() = user_id);


-- ============================================================================
-- 3. TOOL_CONFIGURATIONS - Armazenamento de configurações personalizadas
-- ============================================================================
CREATE TABLE IF NOT EXISTS tool_configurations (
    -- Primary Key
    config_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Foreign Keys
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Identificação
    tool_id TEXT NOT NULL,  -- ex: 'consolidador', 'categorizador'
    config_name TEXT NOT NULL,  -- Nome da configuração (ex: "Categorias de Vendas")
    
    -- Dados
    config_data TEXT NOT NULL,  -- JSON com dados da configuração
    
    -- Descrição
    description TEXT,
    
    -- Flags
    is_default BOOLEAN DEFAULT FALSE,  -- Se é a config padrão para este tool
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Constraints
    UNIQUE(user_id, tool_id, config_name)
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_tool_configurations_user_id ON tool_configurations(user_id);
CREATE INDEX IF NOT EXISTS idx_tool_configurations_tool_id ON tool_configurations(tool_id);
CREATE INDEX IF NOT EXISTS idx_tool_configurations_is_default ON tool_configurations(is_default);
CREATE INDEX IF NOT EXISTS idx_tool_configurations_user_tool ON tool_configurations(user_id, tool_id);

-- RLS Policy - Usuários veem apenas suas próprias configurações
ALTER TABLE tool_configurations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own tool configurations" ON tool_configurations
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create tool configurations" ON tool_configurations
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own tool configurations" ON tool_configurations
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own tool configurations" ON tool_configurations
    FOR DELETE USING (auth.uid() = user_id);


-- ============================================================================
-- VIEWS - Para facilitar queries comuns
-- ============================================================================

-- View: ROI Summary últimos 7 dias
CREATE OR REPLACE VIEW roi_summary_7days AS
SELECT
    el.user_id,
    el.tool_name,
    COUNT(*) as execution_count,
    COUNT(CASE WHEN el.status = 'success' THEN 1 END) as success_count,
    SUM(CASE WHEN el.status = 'success' THEN el.duration_seconds ELSE 0 END) as total_duration_seconds,
    SUM(CASE WHEN el.status = 'success' THEN el.lines_processed ELSE 0 END) as total_lines_processed,
    AVG(CASE WHEN el.status = 'success' THEN el.duration_seconds ELSE NULL END) as avg_duration_seconds,
    MAX(el.timestamp) as last_execution
FROM execution_logs el
WHERE el.timestamp >= (NOW() - INTERVAL '7 days')
AND el.status = 'success'
GROUP BY el.user_id, el.tool_name;


-- View: Próximas tarefas agendadas (próximas 24h)
CREATE OR REPLACE VIEW upcoming_scheduled_tasks AS
SELECT
    st.task_id,
    st.user_id,
    st.tool_name,
    st.task_name,
    st.next_run,
    st.schedule_frequency,
    st.enabled
FROM scheduled_tasks st
WHERE st.enabled = TRUE
AND st.next_run <= (NOW() + INTERVAL '24 hours')
AND st.next_run > NOW()
ORDER BY st.next_run ASC;


-- View: Configurações padrão por ferramenta
CREATE OR REPLACE VIEW default_tool_configurations AS
SELECT
    tc.user_id,
    tc.tool_id,
    tc.config_id,
    tc.config_name,
    tc.config_data
FROM tool_configurations tc
WHERE tc.is_default = TRUE;


-- ============================================================================
-- TRIGGERS - Atualizar updated_at automaticamente
-- ============================================================================

-- Trigger para scheduled_tasks
CREATE OR REPLACE FUNCTION update_scheduled_tasks_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_scheduled_tasks_updated_at
BEFORE UPDATE ON scheduled_tasks
FOR EACH ROW
EXECUTE FUNCTION update_scheduled_tasks_updated_at();


-- Trigger para tool_configurations
CREATE OR REPLACE FUNCTION update_tool_configurations_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_tool_configurations_updated_at
BEFORE UPDATE ON tool_configurations
FOR EACH ROW
EXECUTE FUNCTION update_tool_configurations_updated_at();


-- ============================================================================
-- COMENTÁRIOS - Documentação das tabelas
-- ============================================================================

COMMENT ON TABLE execution_logs IS 'Registra cada execução de ferramenta para cálculo de ROI e análise';
COMMENT ON COLUMN execution_logs.execution_id IS 'UUID único da execução';
COMMENT ON COLUMN execution_logs.user_id IS 'ID do usuário que executou';
COMMENT ON COLUMN execution_logs.tool_name IS 'Nome da ferramenta (consolidador, categorizador, etc)';
COMMENT ON COLUMN execution_logs.duration_seconds IS 'Tempo de execução em segundos';
COMMENT ON COLUMN execution_logs.lines_processed IS 'Número de linhas/registros processados';
COMMENT ON COLUMN execution_logs.file_size_bytes IS 'Tamanho do arquivo em bytes';

COMMENT ON TABLE scheduled_tasks IS 'Tarefas agendadas para execução automática';
COMMENT ON COLUMN scheduled_tasks.task_id IS 'UUID único da tarefa agendada';
COMMENT ON COLUMN scheduled_tasks.schedule_frequency IS 'Frequência: daily, weekly, monthly, custom_cron';
COMMENT ON COLUMN scheduled_tasks.cron_expression IS 'Expressão cron para agendamentos customizados';
COMMENT ON COLUMN scheduled_tasks.next_run IS 'Data/hora da próxima execução programada';
COMMENT ON COLUMN scheduled_tasks.input_files IS 'JSON array com paths dos arquivos de entrada';
COMMENT ON COLUMN scheduled_tasks.config IS 'JSON com configurações específicas da ferramenta';

COMMENT ON TABLE tool_configurations IS 'Configurações personalizadas salvas pelo usuário';
COMMENT ON COLUMN tool_configurations.config_id IS 'UUID único da configuração';
COMMENT ON COLUMN tool_configurations.tool_id IS 'ID da ferramenta (consolidador, categorizador, etc)';
COMMENT ON COLUMN tool_configurations.config_name IS 'Nome amigável (ex: "Categorias de Vendas")';
COMMENT ON COLUMN tool_configurations.config_data IS 'JSON com os dados da configuração';
COMMENT ON COLUMN tool_configurations.is_default IS 'Se é a configuração padrão para este tool';

-- ============================================================================
-- DADOS DE TESTE (Remover em produção)
-- ============================================================================

-- Descomentar para adicionar dados de teste

/*
-- Inserir log de teste
INSERT INTO execution_logs (
    execution_id,
    user_id, 
    tool_name, 
    timestamp, 
    duration_seconds, 
    lines_processed, 
    file_size_bytes, 
    status
) VALUES (
    gen_random_uuid(),
    (SELECT id FROM auth.users LIMIT 1),
    'consolidador',
    NOW()::TEXT,
    5.2,
    1200,
    524288,
    'success'
);

-- Inserir tarefa agendada de teste
INSERT INTO scheduled_tasks (
    task_id,
    user_id,
    tool_name,
    tool_action,
    task_name,
    input_files,
    schedule_frequency,
    time_of_day,
    next_run,
    enabled
) VALUES (
    gen_random_uuid(),
    (SELECT id FROM auth.users LIMIT 1),
    'consolidador',
    'consolidate',
    'Consolidação Diária',
    '["file1.xlsx", "file2.xlsx"]',
    'daily',
    '09:00',
    (NOW() + INTERVAL '1 day')::TEXT,
    TRUE
);

-- Inserir configuração de teste
INSERT INTO tool_configurations (
    config_id,
    user_id,
    tool_id,
    config_name,
    config_data,
    is_default
) VALUES (
    gen_random_uuid(),
    (SELECT id FROM auth.users LIMIT 1),
    'categorizador',
    'Categorias de Vendas',
    '{"categories": ["Vendas", "Devoluções", "Trocas"]}',
    TRUE
);
*/

-- ============================================================================
-- FIM DO SCRIPT
-- ============================================================================
