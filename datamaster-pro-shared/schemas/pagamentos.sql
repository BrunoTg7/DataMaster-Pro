-- Tabela de pagamentos para registrar assinaturas do Cakto
CREATE TABLE IF NOT EXISTS pagamentos (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  usuario_id UUID REFERENCES usuarios(id) ON DELETE CASCADE,
  plano TEXT NOT NULL,
  valor DECIMAL(10,2) DEFAULT 0,
  status TEXT NOT NULL,
  transacao_id TEXT,
  gateway TEXT NOT NULL,
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index para buscar pagamentos por usuário
CREATE INDEX IF NOT EXISTS idx_pagamentos_usuario ON pagamentos(usuario_id);

-- Index para buscar pagamentos por transação
CREATE INDEX IF NOT EXISTS idx_pagamentos_transacao ON pagamentos(transacao_id);

-- Index para buscar pagamentos por status
CREATE INDEX IF NOT EXISTS idx_pagamentos_status ON pagamentos(status);

-- Habilitar RLS
ALTER TABLE pagamentos ENABLE ROW LEVEL SECURITY;

-- Política de leitura (apenas admin)
CREATE POLICY "Admin only can read pagamentos" ON pagamentos
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM usuarios 
      WHERE id = auth.uid() 
      AND plano_tipo = 'enterprise'
    )
  );

-- Política de insert (ninguém pode inserir diretamente, apenas via webhook)
CREATE POLICY "Admin only can insert pagamentos" ON pagamentos
  FOR INSERT WITH CHECK (true);

-- Política de update (apenas admin)
CREATE POLICY "Admin only can update pagamentos" ON pagamentos
  FOR UPDATE USING (
    EXISTS (
      SELECT 1 FROM usuarios 
      WHERE id = auth.uid() 
      AND plano_tipo = 'enterprise'
    )
  );

-- Adicionar coluna expires_at na tabela usuarios se não existir
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'usuarios' AND column_name = 'data_expiracao'
  ) THEN
    ALTER TABLE usuarios ADD COLUMN data_expiracao DATE;
  END IF;
END
$$;