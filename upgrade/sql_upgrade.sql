


-- 4. Inserir ou Atualizar a versão v1.0.0
INSERT INTO public.check_updates (id, versao_atual, versao_disponivel, url_download, changelog, updated_at)
VALUES (
    2, 
    '1.1.0', 
    '1.1.0', 
    'https://github.com/BrunoTg7/DataMaster-Pro-Upgrade/releases/download/v1.1.0/DataMaster.Pro.Setup.exe', 
    '# v1.1.0 Pro\n\n- Atualização da versão 1.1.0\n- Otimização de performance\n- Correção de bugs\n- ', 
    NOW()
)
ON CONFLICT (id) DO UPDATE SET
    versao_atual = EXCLUDED.versao_atual,
    versao_disponivel = EXCLUDED.versao_disponivel,
    url_download = EXCLUDED.url_download,
    changelog = EXCLUDED.changelog,
    updated_at = NOW();
