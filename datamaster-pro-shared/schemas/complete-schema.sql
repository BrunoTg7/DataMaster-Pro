-- ========================================
-- DataMaster Pro - Supabase Schema Completo
-- ========================================
-- Inclui: Tabelas, Functions, Triggers, RLS Policies
-- ========================================

-- ==================== ENUMS ====================

CREATE TYPE plan_type AS ENUM ('gratis', 'pro', 'enterprise');
CREATE TYPE sync_status AS ENUM ('pending', 'syncing', 'synced', 'failed');
CREATE TYPE execution_status AS ENUM ('pending', 'running', 'completed', 'failed');

-- ==================== TABELAS ====================

-- 1. USUARIOS
CREATE TABLE usuarios (
    id UUID PRIMARY KEY DEFAULT auth.uid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    nome VARCHAR(255) NOT NULL,
    plano_tipo plan_type DEFAULT 'gratis',
    data_expiracao DATE,
    ultima_sincronizacao TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT email_valid CHECK (email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$')
);

CREATE INDEX idx_usuarios_email ON usuarios(email);
CREATE INDEX idx_usuarios_plano ON usuarios(plano_tipo);
CREATE INDEX idx_usuarios_expiracao ON usuarios(data_expiracao);

-- 2. EXECUCOES (Histórico de processamento)
CREATE TABLE execucoes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    ferramenta VARCHAR(100) NOT NULL,
    linhas_processadas INTEGER NOT NULL,
    tempo_execucao_ms INTEGER NOT NULL,
    tempo_economizado_minutos INTEGER,
    resultado_arquivo TEXT,
    status execution_status DEFAULT 'completed',
    erro_mensagem TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT ferramenta_valida CHECK (ferramenta IN ('consolidador', 'categorizador', 'orcamentos', 'minerador', 'conciliador'))
);

CREATE INDEX idx_execucoes_usuario ON execucoes(usuario_id);
CREATE INDEX idx_execucoes_ferramenta ON execucoes(ferramenta);
CREATE INDEX idx_execucoes_created ON execucoes(created_at DESC);

-- 3. CHECK UPDATES (Versionamento)
CREATE TABLE check_updates (
    id SERIAL PRIMARY KEY,
    versao_atual VARCHAR(20) NOT NULL UNIQUE,
    versao_disponivel VARCHAR(20),
    url_download TEXT,
    changelog TEXT,
    data_release DATE,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 4. FAVORITOS (Ferramentas favoritas por usuário)
CREATE TABLE favoritos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    ferramenta VARCHAR(100) NOT NULL,
    ordem INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(usuario_id, ferramenta),
    CONSTRAINT ferramenta_valida CHECK (ferramenta IN ('consolidador', 'categorizador', 'orcamentos', 'minerador', 'conciliador'))
);

CREATE INDEX idx_favoritos_usuario ON favoritos(usuario_id);

-- 5. SYNC LOGS (Rastreamento de sincronizações)
CREATE TABLE sync_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    status sync_status,
    dados_sincronizados JSONB,
    erro_mensagem TEXT,
    duracao_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_sync_logs_usuario ON sync_logs(usuario_id);
CREATE INDEX idx_sync_logs_status ON sync_logs(status);
CREATE INDEX idx_sync_logs_created ON sync_logs(created_at DESC);

-- 6. EMAIL LOGS (Histórico de emails enviados)
CREATE TABLE email_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    tipo_email VARCHAR(100),  -- welcome, welcome_pro, upgrade, password_reset, etc
    destinatario VARCHAR(255) NOT NULL,
    assunto VARCHAR(255),
    status VARCHAR(50) DEFAULT 'enviado',  -- enviado, falha, bounce
    tentativas INTEGER DEFAULT 1,
    ultima_tentativa TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_email_logs_usuario ON email_logs(usuario_id);
CREATE INDEX idx_email_logs_tipo ON email_logs(tipo_email);
CREATE INDEX idx_email_logs_status ON email_logs(status);

-- 7. WEBHOOKS LOG (Cakto, Supabase, etc)
CREATE TABLE webhooks_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fonte VARCHAR(100),  -- cakto, stripe, supabase
    tipo_evento VARCHAR(100),
    payload JSONB,
    processado BOOLEAN DEFAULT false,
    usuario_id UUID REFERENCES usuarios(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_webhooks_fonte ON webhooks_log(fonte);
CREATE INDEX idx_webhooks_processado ON webhooks_log(processado);

-- ==================== FUNCTIONS ====================

-- 1. UPDATE TIMESTAMP FUNCTION
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 2. FUNCTION: Sincronizar Usuario (marca como sincronizado)
CREATE OR REPLACE FUNCTION sincronizar_usuario(p_usuario_id UUID)
RETURNS json AS $$
DECLARE
    v_resultado json;
    v_execucoes_count INT;
    v_ultima_exec TIMESTAMP;
BEGIN
    -- Obter contagem de execuções e última
    SELECT COUNT(*), MAX(created_at) INTO v_execucoes_count, v_ultima_exec
    FROM execucoes
    WHERE usuario_id = p_usuario_id;
    
    -- Atualizar ultima_sincronizacao
    UPDATE usuarios
    SET ultima_sincronizacao = NOW()
    WHERE id = p_usuario_id;
    
    -- Registrar no sync_logs
    INSERT INTO sync_logs (usuario_id, status, dados_sincronizados)
    VALUES (p_usuario_id, 'synced'::sync_status, json_build_object(
        'execucoes_sincronizadas', v_execucoes_count,
        'ultima_execucao', v_ultima_exec,
        'timestamp_sync', NOW()
    ));
    
    v_resultado := json_build_object(
        'sucesso', true,
        'executoes_sincronizadas', v_execucoes_count,
        'ultima_execucao', v_ultima_exec
    );
    
    RETURN v_resultado;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 3. FUNCTION: Calcular ROI (tempo economizado)
CREATE OR REPLACE FUNCTION calcular_roi(p_usuario_id UUID, p_dias INT DEFAULT 30)
RETURNS json AS $$
DECLARE
    v_total_linhas BIGINT;
    v_total_tempo_ms BIGINT;
    v_total_tempo_economizado INT;
    v_execucoes_count INT;
BEGIN
    SELECT 
        SUM(linhas_processadas),
        SUM(CAST(tempo_execucao_ms AS BIGINT)),
        SUM(tempo_economizado_minutos),
        COUNT(*)
    INTO v_total_linhas, v_total_tempo_ms, v_total_tempo_economizado, v_execucoes_count
    FROM execucoes
    WHERE usuario_id = p_usuario_id
    AND created_at > NOW() - INTERVAL '1 day' * p_dias;
    
    RETURN json_build_object(
        'total_linhas', COALESCE(v_total_linhas, 0),
        'total_tempo_ms', COALESCE(v_total_tempo_ms, 0),
        'total_tempo_economizado_minutos', COALESCE(v_total_tempo_economizado, 0),
        'total_tempo_economizado_horas', COALESCE(v_total_tempo_economizado, 0) / 60.0,
        'execucoes', v_execucoes_count,
        'periodo_dias', p_dias
    );
END;
$$ LANGUAGE plpgsql;

-- 4. FUNCTION: Validar Acesso a Ferramenta
CREATE OR REPLACE FUNCTION validar_acesso_ferramenta(
    p_usuario_id UUID,
    p_ferramenta VARCHAR(100),
    p_linhas INT
)
RETURNS json AS $$
DECLARE
    v_plano plan_type;
    v_ferramentas_permitidas TEXT[];
    v_limite_linhas INT;
    v_tem_acesso BOOLEAN;
    v_erro TEXT;
BEGIN
    -- Obter plano do usuário
    SELECT plano_tipo INTO v_plano
    FROM usuarios
    WHERE id = p_usuario_id AND data_expiracao > NOW();
    
    IF v_plano IS NULL THEN
        RETURN json_build_object(
            'tem_acesso', false,
            'erro', 'Plano expirado ou usuário não encontrado'
        );
    END IF;
    
    -- Definir ferramentas e limites por plano
    CASE v_plano
        WHEN 'gratis' THEN
            v_ferramentas_permitidas := ARRAY['consolidador', 'categorizador'];
            v_limite_linhas := 10;
        WHEN 'pro' THEN
            v_ferramentas_permitidas := ARRAY['consolidador', 'categorizador', 'orcamentos', 'minerador', 'conciliador'];
            v_limite_linhas := NULL;  -- Ilimitado
        WHEN 'enterprise' THEN
            v_ferramentas_permitidas := ARRAY['consolidador', 'categorizador', 'orcamentos', 'minerador', 'conciliador'];
            v_limite_linhas := NULL;  -- Ilimitado
    END CASE;
    
    -- Validar ferramenta
    v_tem_acesso := p_ferramenta = ANY(v_ferramentas_permitidas);
    
    IF NOT v_tem_acesso THEN
        v_erro := 'Ferramenta não permitida no plano ' || v_plano;
        RETURN json_build_object('tem_acesso', false, 'erro', v_erro);
    END IF;
    
    -- Validar limite de linhas
    IF v_limite_linhas IS NOT NULL AND p_linhas > v_limite_linhas THEN
        v_erro := 'Limite de linhas (' || v_limite_linhas || ') excedido para plano ' || v_plano;
        RETURN json_build_object('tem_acesso', false, 'erro', v_erro, 'limite', v_limite_linhas);
    END IF;
    
    RETURN json_build_object(
        'tem_acesso', true,
        'plano', v_plano,
        'ferramentas_permitidas', v_ferramentas_permitidas,
        'limite_linhas', v_limite_linhas
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 5. FUNCTION: Registrar Execução e Calcular ROI
CREATE OR REPLACE FUNCTION registrar_execucao(
    p_usuario_id UUID,
    p_ferramenta VARCHAR(100),
    p_linhas INT,
    p_tempo_ms INT,
    p_arquivo TEXT
)
RETURNS json AS $$
DECLARE
    v_tempo_economizado INT;
    v_execucao_id UUID;
    v_acesso json;
BEGIN
    -- Validar acesso
    v_acesso := validar_acesso_ferramenta(p_usuario_id, p_ferramenta, p_linhas);
    
    IF NOT (v_acesso->>'tem_acesso')::BOOLEAN THEN
        RETURN json_build_object(
            'sucesso', false,
            'erro', v_acesso->>'erro'
        );
    END IF;
    
    -- Calcular tempo economizado (aproximadamente 5 segundos por linha em processamento manual)
    v_tempo_economizado := (p_linhas * 5) / 60;  -- converter para minutos
    
    -- Inserir execução
    INSERT INTO execucoes (
        usuario_id, ferramenta, linhas_processadas,
        tempo_execucao_ms, tempo_economizado_minutos, resultado_arquivo, status
    ) VALUES (
        p_usuario_id, p_ferramenta, p_linhas,
        p_tempo_ms, v_tempo_economizado, p_arquivo, 'completed'::execution_status
    ) RETURNING id INTO v_execucao_id;
    
    -- Registrar no sync_logs como pendente
    INSERT INTO sync_logs (usuario_id, status, dados_sincronizados)
    VALUES (p_usuario_id, 'pending'::sync_status, json_build_object(
        'execucao_id', v_execucao_id,
        'ferramenta', p_ferramenta
    ));
    
    RETURN json_build_object(
        'sucesso', true,
        'execucao_id', v_execucao_id,
        'tempo_economizado_minutos', v_tempo_economizado,
        'tempo_economizado_horas', v_tempo_economizado / 60.0
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 6. FUNCTION: Enviar Email (será chamada por Edge Function)
CREATE OR REPLACE FUNCTION enfileirar_email(
    p_usuario_id UUID,
    p_tipo_email VARCHAR(100),
    p_destinatario VARCHAR(255),
    p_assunto VARCHAR(255)
)
RETURNS json AS $$
DECLARE
    v_email_id UUID;
BEGIN
    INSERT INTO email_logs (usuario_id, tipo_email, destinatario, assunto, status)
    VALUES (p_usuario_id, p_tipo_email, p_destinatario, p_assunto, 'enfileirado')
    RETURNING id INTO v_email_id;
    
    RETURN json_build_object(
        'sucesso', true,
        'email_id', v_email_id,
        'mensagem', 'Email enfileirado para envio'
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 7. FUNCTION: Processar Upgrade (Webhook Cakto)
CREATE OR REPLACE FUNCTION processar_upgrade_cakto(
    p_email VARCHAR(255),
    p_plano_novo plan_type,
    p_data_expiracao DATE
)
RETURNS json AS $$
DECLARE
    v_usuario_id UUID;
BEGIN
    -- Encontrar usuário
    SELECT id INTO v_usuario_id
    FROM usuarios
    WHERE email = p_email;
    
    IF v_usuario_id IS NULL THEN
        RETURN json_build_object(
            'sucesso', false,
            'erro', 'Usuário não encontrado'
        );
    END IF;
    
    -- Atualizar plano
    UPDATE usuarios
    SET plano_tipo = p_plano_novo,
        data_expiracao = p_data_expiracao,
        updated_at = NOW()
    WHERE id = v_usuario_id;
    
    -- Enfileirar email de confirmação
    PERFORM enfileirar_email(
        v_usuario_id,
        'upgrade_' || p_plano_novo,
        p_email,
        'Bem-vindo ao DataMaster Pro! Seu plano foi atualizado'
    );
    
    RETURN json_build_object(
        'sucesso', true,
        'usuario_id', v_usuario_id,
        'novo_plano', p_plano_novo,
        'data_expiracao', p_data_expiracao
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ==================== TRIGGERS ====================

-- 1. TRIGGER: Update usuarios.updated_at
CREATE TRIGGER trigger_usuarios_updated_at
    BEFORE UPDATE ON usuarios
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 2. TRIGGER: Update execucoes.updated_at
CREATE TRIGGER trigger_execucoes_updated_at
    BEFORE UPDATE ON execucoes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 3. TRIGGER: Log ao enviar email
CREATE OR REPLACE FUNCTION log_envio_email()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'enviado' THEN
        NEW.ultima_tentativa := NOW();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_email_logs_update
    BEFORE UPDATE ON email_logs
    FOR EACH ROW
    EXECUTE FUNCTION log_envio_email();

-- ==================== RLS POLICIES ====================

-- Enable RLS
ALTER TABLE usuarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE execucoes ENABLE ROW LEVEL SECURITY;
ALTER TABLE favoritos ENABLE ROW LEVEL SECURITY;
ALTER TABLE sync_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE webhooks_log ENABLE ROW LEVEL SECURITY;

-- Policies for usuarios
CREATE POLICY "usuarios_select" ON usuarios FOR SELECT
    USING (auth.uid() = id OR auth.role() = 'authenticated');

CREATE POLICY "usuarios_insert" ON usuarios FOR INSERT
    WITH CHECK (auth.uid() = id);

CREATE POLICY "usuarios_update" ON usuarios FOR UPDATE
    USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

-- Policies for execucoes
CREATE POLICY "execucoes_select" ON execucoes FOR SELECT
    USING (usuario_id = auth.uid());

CREATE POLICY "execucoes_insert" ON execucoes FOR INSERT
    WITH CHECK (usuario_id = auth.uid());

-- Policies for favoritos
CREATE POLICY "favoritos_all" ON favoritos
    USING (usuario_id = auth.uid())
    WITH CHECK (usuario_id = auth.uid());

-- Policies for sync_logs
CREATE POLICY "sync_logs_select" ON sync_logs FOR SELECT
    USING (usuario_id = auth.uid());

-- Policies for email_logs
CREATE POLICY "email_logs_select" ON email_logs FOR SELECT
    USING (usuario_id = auth.uid());

-- Policies for webhooks_log (service role only)
CREATE POLICY "webhooks_log_service_role" ON webhooks_log
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- ==================== GRANT PERMISSIONS ====================

-- Dar acesso anon/authenticated às funções públicas
GRANT EXECUTE ON FUNCTION validar_acesso_ferramenta(UUID, VARCHAR, INT) TO authenticated;
GRANT EXECUTE ON FUNCTION registrar_execucao(UUID, VARCHAR, INT, INT, TEXT) TO authenticated;
GRANT EXECUTE ON FUNCTION calcular_roi(UUID, INT) TO authenticated;
GRANT EXECUTE ON FUNCTION sincronizar_usuario(UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION enfileirar_email(UUID, VARCHAR, VARCHAR, VARCHAR) TO service_role;
GRANT EXECUTE ON FUNCTION processar_upgrade_cakto(VARCHAR, plan_type, DATE) TO service_role;

-- Dar acesso às tabelas
GRANT SELECT, INSERT, UPDATE ON usuarios TO authenticated;
GRANT SELECT, INSERT ON execucoes TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON favoritos TO authenticated;
GRANT SELECT ON check_updates TO authenticated, anon;
GRANT SELECT ON sync_logs TO authenticated;
GRANT SELECT ON email_logs TO authenticated;
GRANT ALL ON webhooks_log TO service_role;
GRANT ALL ON email_logs TO service_role;

-- ==================== INITIAL DATA ====================

-- Inserir versão atual
INSERT INTO check_updates (versao_atual, versao_disponivel, url_download, changelog)
VALUES (
    '1.0.0',
    '1.0.0',
    'https://datamaster.pro/downloads/datamaster-pro-1.0.0.exe',
    '# v1.0.0\n\n- Release inicial\n- 5 ferramentas core\n- Suporte offline-first'
)
ON CONFLICT (versao_atual) DO NOTHING;
