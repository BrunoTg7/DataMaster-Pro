


-- ========================================
-- DataMaster Pro - Migration v1.0.0 → v1.1.0
-- ========================================

-- 1. Adiciona UNIQUE constraint composta em execucoes.
--    Necessária para o upsert com on_conflict="usuario_id,created_at"
--    que o SyncManager usa para evitar duplicatas na sincronização.
--    Remove duplicatas existentes antes de criar a constraint.
DELETE FROM execucoes
WHERE id IN (
    SELECT id FROM (
        SELECT id, ROW_NUMBER() OVER (
            PARTITION BY usuario_id, created_at ORDER BY created_at DESC
        ) AS rn
        FROM execucoes
    ) t WHERE t.rn > 1
);

ALTER TABLE execucoes ADD CONSTRAINT execucoes_usuario_created_unique UNIQUE (usuario_id, created_at);

-- 4. Inserir ou Atualizar a versão v1.1.0
INSERT INTO public.check_updates (id, versao_atual, versao_disponivel, url_download, changelog, updated_at)
VALUES (
    2, 
    '1.4.0', 
    '1.4.0', 
    'https://github.com/BrunoTg7/DataMaster-Pro-Upgrade/releases/download/1.4.0/DataMaster.Pro.Setup.v1.4.0.exe', 
    '# v1.4.0 Pro\n\n- Atualização da versão 1.4.0\n- Correção: Upsert de execucoes, evitando duplicatas na sincronização. \n -Correção: performance geral nas ferramentas. \n -Correção: bugs corrigidos em geral. ' , 
    NOW()
)
ON CONFLICT (id) DO UPDATE SET
    versao_atual = EXCLUDED.versao_atual,
    versao_disponivel = EXCLUDED.versao_disponivel,
    url_download = EXCLUDED.url_download,
    changelog = EXCLUDED.changelog,
    updated_at = NOW();
