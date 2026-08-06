-- ============================================================================
-- DataMaster Pro - Execuções Table + ROI Function
-- Execute este script no Supabase SQL Editor
-- ============================================================================

-- ============================================================================
-- 1. EXECUÇÕES - Tabela principal de rastreamento de uso
-- ============================================================================
CREATE TABLE IF NOT EXISTS execucoes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    ferramenta TEXT NOT NULL,
    linhas_processadas INTEGER NOT NULL DEFAULT 0,
    tempo_execucao_ms INTEGER NOT NULL DEFAULT 0,
    tempo_economizado_minutos INTEGER NOT NULL DEFAULT 0,
    resultado_arquivo TEXT,
    status TEXT DEFAULT 'completed',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_execucoes_usuario_id ON execucoes(usuario_id);
CREATE INDEX IF NOT EXISTS idx_execucoes_ferramenta ON execucoes(ferramenta);
CREATE INDEX IF NOT EXISTS idx_execucoes_created_at ON execucoes(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_execucoes_usuario_created ON execucoes(usuario_id, created_at DESC);

-- RLS Policy
ALTER TABLE execucoes ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own execucoes" ON execucoes
    FOR SELECT USING (auth.uid() = usuario_id);

CREATE POLICY "Users can insert own execucoes" ON execucoes
    FOR INSERT WITH CHECK (auth.uid() = usuario_id);

CREATE POLICY "Users can delete own execucoes" ON execucoes
    FOR DELETE USING (auth.uid() = usuario_id);

-- ============================================================================
-- 2. FUNÇÃO calcular_roi - Usada pelo web dashboard
-- ============================================================================
DROP FUNCTION IF EXISTS calcular_roi(UUID, INTEGER);

CREATE OR REPLACE FUNCTION calcular_roi(p_usuario_id UUID, p_dias INTEGER DEFAULT 30)
RETURNS TABLE(
    total_linhas BIGINT,
    execucoes BIGINT,
    total_tempo_economizado_horas NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COALESCE(SUM(e.linhas_processadas), 0)::BIGINT AS total_linhas,
        COUNT(*)::BIGINT AS execucoes,
        COALESCE(SUM(e.tempo_economizado_minutos), 0)::NUMERIC / 60.0 AS total_tempo_economizado_horas
    FROM execucoes e
    WHERE e.usuario_id = p_usuario_id
      AND e.created_at >= NOW() - (p_dias || ' days')::INTERVAL;
END;
$$ LANGUAGE plpgsql STABLE;

-- ============================================================================
-- 3. PERMISSÕES
-- ============================================================================
GRANT SELECT, INSERT, DELETE ON execucoes TO authenticated;
GRANT EXECUTE ON FUNCTION calcular_roi(UUID, INTEGER) TO authenticated;

-- ============================================================================
-- FIM
-- ============================================================================
