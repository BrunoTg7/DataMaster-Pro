-- ============================================================================
-- 006_RLS_Missing_Tables.sql
-- Habilita RLS e cria policies para tabelas que estao sendo usadas
-- pela aplicacao mas nao tem policies definidas nas migrations anteriores
-- ============================================================================

-- ============================================================================
-- 1. USUARIOS - Tabela principal de usuarios
-- ============================================================================
-- Ja tem DELETE policy (002_lgpd_delete_policies.sql)
-- Adicionando SELECT, INSERT, UPDATE

ALTER TABLE usuarios ENABLE ROW LEVEL SECURITY;

-- Usuarios podem ver seus proprios dados
DROP POLICY IF EXISTS "usuarios_select" ON usuarios;
CREATE POLICY "usuarios_select" ON usuarios
    FOR SELECT USING (auth.uid() = id);

-- Usuarios podem atualizar seus proprios dados
DROP POLICY IF EXISTS "usuarios_update" ON usuarios;
CREATE POLICY "usuarios_update" ON usuarios
    FOR UPDATE USING (auth.uid() = id);

-- Insert e feito via service role (signup) - nao precisa de policy para authenticated
-- Mas habilitamos para o caso de uso futuro
DROP POLICY IF EXISTS "usuarios_insert" ON usuarios;
CREATE POLICY "usuarios_insert" ON usuarios
    FOR INSERT WITH CHECK (auth.uid() = id);


-- ============================================================================
-- 2. PAGAMENTOS - Historico de pagamentos
-- ============================================================================
-- Apenas service role deve acessar (webhook da Cakto)
-- Mas criamos policies para o caso de o usuario querer ver seus pagamentos

ALTER TABLE pagamentos ENABLE ROW LEVEL SECURITY;

-- Usuarios podem ver seus proprios pagamentos (por usuario_id)
DROP POLICY IF EXISTS "pagamentos_select" ON pagamentos;
CREATE POLICY "pagamentos_select" ON pagamentos
    FOR SELECT USING (auth.uid() = usuario_id);

-- Service role faz INSERT/UPDATE via webhook (bypass RLS)


-- ============================================================================
-- 3. FAVORITOS - Itens favoritos do usuario
-- ============================================================================

ALTER TABLE favoritos ENABLE ROW LEVEL SECURITY;

-- Usuarios podem ver seus proprios favoritos
DROP POLICY IF EXISTS "favoritos_select" ON favoritos;
CREATE POLICY "favoritos_select" ON favoritos
    FOR SELECT USING (auth.uid() = usuario_id);

-- Usuarios podem criar seus proprios favoritos
DROP POLICY IF EXISTS "favoritos_insert" ON favoritos;
CREATE POLICY "favoritos_insert" ON favoritos
    FOR INSERT WITH CHECK (auth.uid() = usuario_id);

-- Usuarios podem atualizar seus proprios favoritos
DROP POLICY IF EXISTS "favoritos_update" ON favoritos;
CREATE POLICY "favoritos_update" ON favoritos
    FOR UPDATE USING (auth.uid() = usuario_id);

-- Usuarios podem deletar seus proprios favoritos
DROP POLICY IF EXISTS "favoritos_delete" ON favoritos;
CREATE POLICY "favoritos_delete" ON favoritos
    FOR DELETE USING (auth.uid() = usuario_id);


-- ============================================================================
-- 4. WEBHOOKS_LOG - Logs de webhooks e formulário de contato
-- ============================================================================
-- Apenas service role deve acessar (API routes)
-- Nao expor para usuarios (contem dados sensiveis de outros usuarios)

ALTER TABLE webhooks_log ENABLE ROW LEVEL SECURITY;

-- Nenhuma policy para authenticated role
-- Apenas service role pode acessar (bypass RLS)


-- ============================================================================
-- 5. CONSENT_LOGS - Adicionar DELETE policy para LGPD
-- ============================================================================
-- Ja tem SELECT e INSERT (004_consent_logs.sql)
-- Adicionando DELETE para conformidade LGPD (Art. 18 - direito ao esquecimento)

DROP POLICY IF EXISTS "consent_logs_delete" ON consent_logs;
CREATE POLICY "consent_logs_delete" ON consent_logs
    FOR DELETE USING (auth.uid() = user_id);

-- Adicionando UPDATE tambem para re-consent
DROP POLICY IF EXISTS "consent_logs_update" ON consent_logs;
CREATE POLICY "consent_logs_update" ON consent_logs
    FOR UPDATE USING (auth.uid() = user_id);


-- ============================================================================
-- 6. EXECUCOES - Adicionar UPDATE policy (se necessario)
-- ============================================================================

DROP POLICY IF EXISTS "execucoes_update" ON execucoes;
CREATE POLICY "execucoes_update" ON execucoes
    FOR UPDATE USING (auth.uid() = usuario_id);


-- ============================================================================
-- 7. EXECUTION_LOGS - Adicionar UPDATE policy
-- ============================================================================

DROP POLICY IF EXISTS "execution_logs_update" ON execution_logs;
CREATE POLICY "execution_logs_update" ON execution_logs
    FOR UPDATE USING (auth.uid() = user_id);


-- ============================================================================
-- COMENTARIOS
-- ============================================================================

COMMENT ON TABLE usuarios IS 'Tabela principal de usuarios do sistema';
COMMENT ON TABLE pagamentos IS 'Historico de pagamentos e assinaturas (populado via webhook Cakto)';
COMMENT ON TABLE favoritos IS 'Itens favoritos dos usuarios';
COMMENT ON TABLE webhooks_log IS 'Logs de webhooks e formularios (apenas service role)';
COMMENT ON TABLE consent_logs IS 'Logs de consentimento LGPD dos usuarios';

-- ============================================================================
-- FIM
-- ============================================================================
