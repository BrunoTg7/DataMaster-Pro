-- ============================================================
-- Keep Project Alive - Evita pausa por inatividade (7 dias)
-- Schedule: a cada 6 dias
-- ============================================================

CREATE EXTENSION IF NOT EXISTS pg_cron;
CREATE EXTENSION IF NOT EXISTS pg_net;

SELECT cron.unschedule('keep-project-alive');

SELECT cron.schedule(
    'keep-project-alive',
    '0 8 */6 * *',
    $$SELECT net.http_get('https://aytpuefpisvmlxmqkbfm.supabase.co')$$
);

SELECT cron.schedule(
    'keep-alive-auth',
    '30 8 */6 * *',
    $$SELECT net.http_get('https://aytpuefpisvmlxmqkbfm.supabase.co/auth/v1/health')$$
);
