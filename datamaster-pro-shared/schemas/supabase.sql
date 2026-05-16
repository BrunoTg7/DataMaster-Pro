"""
SQL Schema for DataMaster Pro Supabase
"""

# ==================== USUARIOS ====================
CREATE TABLE usuarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    nome VARCHAR(255) NOT NULL,
    plano_tipo VARCHAR(50) DEFAULT 'gratis',  -- gratis, pro, enterprise
    data_expiracao DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    INDEX(email),
    INDEX(plano_tipo)
);

# ==================== EXECUCOES ====================
CREATE TABLE execucoes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    ferramenta VARCHAR(100) NOT NULL,  -- consolidador, categorizador, etc
    linhas_processadas INTEGER NOT NULL,
    tempo_execucao_ms INTEGER NOT NULL,
    tempo_economizado_minutos INTEGER,
    resultado_arquivo TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    
    INDEX(usuario_id),
    INDEX(ferramenta),
    INDEX(created_at)
);

# ==================== CHECK UPDATES ====================
CREATE TABLE check_updates (
    id SERIAL PRIMARY KEY,
    versao_atual VARCHAR(20) NOT NULL,
    versao_disponivel VARCHAR(20),
    url_download TEXT,
    changelog TEXT,
    updated_at TIMESTAMP DEFAULT NOW(),
    
    INDEX(versao_disponivel)
);

# ==================== FAVORITOS ====================
CREATE TABLE favoritos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    ferramenta VARCHAR(100) NOT NULL,
    ordem INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(usuario_id, ferramenta),
    INDEX(usuario_id)
);

# ==================== SYNC QUEUE (Local) ====================
# Esta tabela é mantida apenas no SQLite local do desktop
# Estrutura:
-- CREATE TABLE sync_queue (
--     id TEXT PRIMARY KEY,
--     execution_id TEXT NOT NULL,
--     status TEXT DEFAULT 'pending',  -- pending, syncing, synced
--     error_message TEXT,
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     synced_at TIMESTAMP
-- );
