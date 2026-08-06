-- ============================================================
-- LGPD Delete Policies
-- Permite que usuários deletem suas próprias contas e registros
-- ============================================================

-- Habilitar RLS de DELETE para usuarios
DROP POLICY IF EXISTS "usuarios_delete" ON usuarios;
CREATE POLICY "usuarios_delete" ON usuarios FOR DELETE
    USING (auth.uid() = id);

-- Habilitar RLS de DELETE para execucoes
DROP POLICY IF EXISTS "execucoes_delete" ON execucoes;
CREATE POLICY "execucoes_delete" ON execucoes FOR DELETE
    USING (usuario_id = auth.uid());

-- Habilitar RLS de DELETE para sync_logs
DROP POLICY IF EXISTS "sync_logs_delete" ON sync_logs;
CREATE POLICY "sync_logs_delete" ON sync_logs FOR DELETE
    USING (usuario_id = auth.uid());

-- Habilitar RLS de DELETE para email_logs
DROP POLICY IF EXISTS "email_logs_delete" ON email_logs;
CREATE POLICY "email_logs_delete" ON email_logs FOR DELETE
    USING (usuario_id = auth.uid());
