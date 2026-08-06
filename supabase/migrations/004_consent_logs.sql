-- Tabela de logs de consentimento LGPD
CREATE TABLE IF NOT EXISTS consent_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    necessary BOOLEAN NOT NULL DEFAULT true,
    analytics BOOLEAN NOT NULL DEFAULT false,
    marketing BOOLEAN NOT NULL DEFAULT false,
    ip_address TEXT,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS: apenas o proprio usuario pode ler seus logs de consentimento
ALTER TABLE consent_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own consent logs"
    ON consent_logs FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own consent logs"
    ON consent_logs FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Indice para consultas por usuario
CREATE INDEX IF NOT EXISTS idx_consent_logs_user ON consent_logs(user_id, created_at DESC);
