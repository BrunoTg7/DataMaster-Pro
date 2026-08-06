# Guia do Usuário - DataMaster Pro v1.5.0

## Visão Geral

O **DataMaster Pro** é uma suíte desktop de automação e análise de dados para e-commerce, focada em **processamento local**, **web scraping**, **OCR** e **inteligência financeira**. Funciona 100% offline para as ferramentas principais.

---

## Ferramentas Disponíveis

### ✅ Ferramentas Ativas (5)

| Ferramenta | Descrição | Principais Features |
|------------|-----------|---------------------|
| **Consolidador** | Une múltiplas planilhas (Excel, CSV, JSON, Parquet) | Fuzzy mapping de cabeçalhos, 4 temas visuais, exportação Parquet/CSV chunked, detecção automática de RAM |
| **Categorizador** | Classifica transações por palavras-chave/Regex | 6 templates setoriais, descoberta automática de categorias, ProcessPoolExecutor, métricas de qualidade |
| **Orçamentos** | Gera PDFs profissionais em lote a partir de planilhas | Streaming (evita OOM), templates Jinja2, QR Code PIX, watermark FREE, QR Code PIX válido EMV |
| **Minerador** | Captura preços de sites (ML, Amazon, Shopee, Magalu) | Selector Registry auto-atualizável, APIs oficiais, circuit breaker, cache SQLite, fallback Playwright |
| **Conciliador** | Cruza extratos bancários com vendas/NF-e | 3 modos (Clássico, NF-e, NF-e+Vendas), tolerância de data/fuzzy, validação XSD, multi-período |

### 🚧 Em Desenvolvimento (10 - "Em Breve")

| Ferramenta | Status | Previsão |
|------------|--------|----------|
| Conversor OCR | PaddleOCR implementado, cross-platform | v2.0 |
| Validador de Links | Modo híbrido HEAD + Playwright | v2.0 |
| Classificador NCM | Pipeline ETL Receita Federal + CEST | v2.0 |
| Gerador de Laudos | Jinja2 + WeasyPrint + pAdES-B | v2.0 |
| Calculadora Lucratividade | Simples Nacional 2026 + Break-even | v2.0 |
| Analista Tendências | Google Trends + ML Bestsellers + TikTok | v2.0 |
| Extrator NF-e | NFC-e + validação chave acesso | v2.0 |
| Comissões | Volume tiers + PDF com gráficos | v2.0 |
| Data Sanitizer | Validação CPF/CNPJ + ViaCEP | v2.0 |
| Precificador Canal | API Melhor Envio + ICMS interestadual + What-if | v2.0 |

---

## Instalação

### Requisitos
- Windows 10/11 (x64)
- 4GB RAM mínimo (8GB recomendado para arquivos grandes)
- 2GB espaço em disco

### Via Microsoft Store (futuro)
> Aguardando certificado OV/EV

### Via GitHub Releases (atual)
1. Baixe `DataMasterPro_1.5.0.0_x64.msix` + `datamaster_selfsigned.pfx`
2. **PowerShell Admin**: Instale o certificado
   ```powershell
   $cert = Get-ChildItem Cert:\CurrentUser\My | Where-Object {$_.Subject -like "*DataMaster*"}
   $store = New-Object System.Security.Cryptography.X509Certificates.X509Store("TrustedPeople","LocalMachine")
   $store.Open("ReadWrite")
   $store.Add($cert)
   $store.Close()
   ```
3. `Add-AppxPackage DataMasterPro_1.5.0.0_x64.msix`

---

## Primeiros Passos

### 1. Login
- Use suas credenciais DataMaster Pro
- Suporte a Google OAuth
- Sessão persiste (refresh token automático a cada 50 min)

### 2. Dashboard
- Visão geral de execuções, limites do plano, status de conexão
- Acesso rápido às 5 ferramentas ativas

### 3. Configurações Iniciais
- **Tema**: Escuro/Claro/Sistema
- **Retenção histórico**: 1h a 6m (conforme plano)
- **Notificações**: Desktop + Email

---

## Guia Rápido por Ferramenta

### Consolidador
```
1. Arraste arquivos (Excel, CSV, JSON, Parquet, TXT)
2. Escolha estratégia: Concat (vertical) | Merge (horizontal) | Join (por chave)
3. Opções: Fuzzy headers, remover duplicatas, seleção de abas
4. Tema visual: Azul Corporativo | Verde Esmeralda | Laranja Moderno | Cinza Minimalista
5. Executar → Download Excel/Parquet/CSV
```
**Dica**: Para 500k+ linhas, use exportação Parquet (50% menor) ou CSV chunked.

### Categorizador
```
1. Selecione planilha de transações
2. Informe coluna de descrição (ex: "Historico", "Descrição")
3. Escolha template: Financeiro Pessoal | Empresarial (DRE) | E-commerce | CRM | RH
4. Opções: Fuzzy matching, palavras-chave negativas, Regex
5. Descubra categorias automáticas → Aplique sugestões
6. Executar → Planilha categorizada + métricas de qualidade
```

### Orçamentos
```
1. Configure dados da empresa (logo, endereço, PIX, banco)
2. Configure template PDF (cores, campos ativos, observações)
3. Selecione planilha de dados (colunas: numero, cliente, data, item, qtd, preco...)
4. Escolha diretório de saída
5. Executar → PDFs zipados + watermark (plano Grátis)
```
**Streaming**: Para 1000+ PDFs, usa `generate_from_excel_streaming` (gc.collect a cada 50 PDFs).

### Minerador
```
1. Cole URLs ou selecione arquivo (CSV/Excel com coluna "url")
2. Escolha marketplace: ML | Amazon | Shopee | Magalu | Genérico
3. Configure: max sucessos, usar API oficial, seletores customizados
4. Executar → Progresso em tempo real + circuit breaker
5. Exportar Excel com tema visual
```
**APIs Oficiais**: ML (Client ID/Secret), Amazon SP-API, Shopee Open Platform (configurar em `.env`).

### Conciliador
**Modo Clássico**: Extrato bancário ↔ Planilha de vendas
- Tolerância de valor (ex: 0.05) + janela de datas (ex: 2 dias) + fuzzy descrição (ex: 75%)

**Modo NF-e**: Pasta de XMLs ↔ Extrato bancário
- Cruzamento por valor + nome + data + validação XSD (warn)

**Modo NF-e + Vendas**: XMLs de NF-e ↔ Planilha de vendas do marketplace
- Chave: Número do Pedido (via infAdic) ou CPF/CNPJ destinatário

---

## Planos e Limites

| Recurso | Grátis | Starter | Pro |
|---------|--------|---------|-----|
| Linhas/mês (Consolidador) | 600 | 10.000 | Ilimitado |
| Execuções/mês (por ferramenta) | 2-5 | 6-10 | Ilimitado |
| Tarefas simultâneas | 1 | 2 | 2 |
| Temas visuais | 1 (Azul) | 4 | 4 |
| Histórico | 1h | 7d-6m | 7d-6m |
| Logo/Pagamento no PDF | ❌ | ✅ | ✅ |
| APIs Oficiais Minerador | ❌ | ✅ | ✅ |

---

## Configuração Avançada (`.env`)

```env
# Supabase (obrigatório)
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_ANON_KEY=sua-anon-key

# Criptografia local
ENCRYPTION_KEY=sua-chave-32-chars-minimo

# Minerador - APIs Oficiais (opcional)
ML_CLIENT_ID=seu-ml-client-id
ML_CLIENT_SECRET=seu-ml-secret
AMZ_LWA_CLIENT_ID=seu-amz-lwa-id
AMZ_LWA_CLIENT_SECRET=seu-amz-secret
AMZ_REFRESH_TOKEN=seu-refresh-token
SHOPEE_PARTNER_ID=seu-shopee-id
SHOPEE_PARTNER_KEY=seu-shopee-key
SHOPEE_SHOP_ID=sua-loja-id
```

---

## Atalhos de Teclado

| Atalho | Ação |
|--------|------|
| `Ctrl+O` | Abrir arquivo |
| `Ctrl+S` | Salvar configuração |
| `Ctrl+R` | Executar ferramenta atual |
| `Ctrl+Shift+C` | Copiar logs |
| `F11` | Fullscreen |
| `Esc` | Cancelar execução / Voltar |

---

## Solução de Problemas

| Erro | Causa | Solução |
|------|-------|---------|
| "Arquivo em uso" | Excel/PDF aberto em outro programa | Feche o arquivo e tente novamente |
| "Permissão negada" | Pasta protegida | Execute como Admin ou escolha outra pasta |
| "OOM / Memória insuficiente" | Arquivo muito grande | Use streaming (Orçamentos) ou Parquet (Consolidador) |
| "weasyprint não carrega" | GTK não instalado | Instale GTK Runtime no Windows |
| "Playwright falha" | Chromium não embutido | `playwright install chromium` |
| "Certificado não confiável" | Self-signed | Instale `.pfx` em Trusted People (Admin) |

---

## Atualizações

- **Automática**: Verifica no startup (Supabase `check_updates`)
- **Manual**: Menu Ajuda → Verificar Atualizações
- **Notificação**: Toast no app + badge no ícone

---

## Suporte

- **Email**: suporte@datamasterpro.com
- **Documentação**: https://docs.datamasterpro.com
- **Changelog**: Menu Ajuda → Histórico de Versões
- **Reportar Bug**: Menu Ajuda → Reportar Problema (inclui logs automaticamente)

---

## Licença

DataMaster Pro v1.5.0 - Proprietary
© 2026 DataMaster Team. Todos os direitos reservados.

---

*Última atualização: 2026-08-05 | Versão 1.5.0*


cd "C:\Users\Public\projetos\ferramente excel\datamaster-pro-desktop"
python -m PyInstaller datamaster.spec --clean

& "C:\Program Files (x86)\NSIS\makensis.exe" installer.nsi

ou 

.\build_v2_otimizado.bat