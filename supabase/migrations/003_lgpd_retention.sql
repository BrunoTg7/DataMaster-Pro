-- ============================================================
-- LGPD Retention Policy
-- Limpeza automática de dados de execução com mais de 2 anos
-- ============================================================

CREATE OR REPLACE FUNCTION limpar_dados_antigos_lgpd()
RETURNS void AS $$
BEGIN
    -- Limpar histórico da tabela execucoes
    DELETE FROM execucoes
    WHERE created_at < NOW() - INTERVAL '2 years';
    
    -- Limpar histórico da tabela execution_logs
    DELETE FROM execution_logs
    WHERE created_at < NOW() - INTERVAL '2 years';
    
    -- Limpar sync_logs antigos
    DELETE FROM sync_logs
    WHERE created_at < NOW() - INTERVAL '2 years';

    -- Limpar email_logs antigos
    DELETE FROM email_logs
    WHERE created_at < NOW() - INTERVAL '2 years';
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Agendar a limpeza para rodar todo dia às 3:00 da manhã
CREATE EXTENSION IF NOT EXISTS pg_cron;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM cron.job WHERE jobname = 'limpar-dados-antigos-lgpd') THEN
        PERFORM cron.unschedule('limpar-dados-antigos-lgpd');
    END IF;
END
$$;

SELECT cron.schedule(
    'limpar-dados-antigos-lgpd',
    '0 3 * * *',
    $$SELECT limpar_dados_antigos_lgpd()$$
);
