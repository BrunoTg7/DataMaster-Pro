# AUDITORIA COMPLETA - DataMaster Pro v1.5.0
## Preparação para Produção e Microsoft Store

---

## RESUMO EXECUTIVO

| Critério | Status | Observação |
|----------|--------|------------|
| **Empacotamento/Build** | ⚠️ Ajustar Urgente | PyInstaller + NSIS (não MSIX); version_info desatualizado |
| **Arquitetura Desktop** | ✅ OK | CustomTkinter + tkinterdnd2; single-instance; HWID; criptografia local |
| **5 Ferramentas Ativas** | ⚠️ Ajustar Urgente | Bugs críticos em OCR, Minerador, Gerador Laudos; stubs não implementados |
| **10 Ferramentas Futuras** | ⚠️ Ajustar Urgente | Código presente mas não isolado; interfaces ITool não implementadas |
| **Tratamento de Erros** | ✅ OK | Try/catch generalizado; circuit breaker; retry com backoff |
| **Funcionamento Offline** | ✅ OK | Ferramentas locais independentes; sync diferida |
| **Segurança/Dados** | ✅ OK | Criptografia AES+HWID; sem secrets no código; LGPD compliance |
| **Interface/Responsivo** | ✅ OK | CustomTkinter; grid/layout responsivo; temas |

---

## 1. CONFIGURAÇÃO E EMPACOTAMENTO (MSIX / EXE / Microsoft Store)

### [OK] - O que está correto
- ✅ **Caminhos de dados corretos**: `config.py` usa `LOCALAPPDATA` (`%USERPROFILE%\AppData\Local\DataMaster Pro`) para logs, DB, outputs, cache — evita `C:\Program Files`
- ✅ **Migração automática**: `_migrate_old_database()` copia dados de instalações antigas (Program Files) para AppData
- ✅ **Instalador NSIS profissional**: Cria atalhos, registro no Painel de Controle, desinstalador limpo, execução admin
- ✅ **PyInstaller spec completo**: Inclui todos os hiddenimports necessários (pandas, openpyxl, reportlab, playwright, bs4, cryptography, etc.)
- ✅ **Single-file executável**: Modo `--onedir` para performance + compatibilidade com `.env`
- ✅ **Version info**: `version_info.txt` com CompanyName, FileDescription, ProductName, ProductVersion
- ✅ **Ícone personalizado**: `datamaster.ico` embutido no EXE e instalador
- ✅ **UPX compression**: Reduz tamanho do binário (~50-60%)
- ✅ **Instance lock**: Socket na porta 47201 impede múltiplas instâncias

### [Ajustar Urgente] - Erros críticos/bloqueantes
| Item | Problema | Impacto | Correção |
|------|----------|---------|----------|
| **Package ID / Publisher** | NSIS usa `DataMaster` genérico; falta `Publisher ID` certificado pela Microsoft Store | Rejeição na submissão | Obter certificado EV Code Signing; configurar `Publisher` com CN do certificado |
| **Formato MSIX** | Build atual é **EXE + NSIS**, não MSIX | Microsoft Store exige MSIX | Migrar para `msix-packaging` ou usar `electron-builder`/`tauri` com target MSIX; ou usar Desktop Bridge (MSIX) via `makeappx` + assinatura |
| **AppxManifest.xml** | Ausente — necessário para identidade, capabilities, visual assets | Bloqueador Store | Gerar manifest com: `Identity Name="DataMasterPro" Publisher="CN=..." Version="1.5.0.0"`, `Capabilities: internetClient, documentsLibrary`, `uap:VisualElements` com tiles 150x150, 44x44, 71x71, 310x150, 310x310 |
| **Assinatura Digital** | EXE e instalador **não assinados** | SmartScreen bloqueia; Store rejeita | Comprar certificado EV (DigiCert, Sectigo, GlobalSign); assinar com `signtool` / `osslsigncode` |
| **Version Info desatualizada** | `version_info.txt` mostra `1.0.0.0` mas app é `1.5.0` / `1.2.8` | Confusão de versão | Sincronizar: `filevers=(1,5,0,0)`, `prodvers=(1,5,0,0)` |
| **Dependências nativas (Playwright)** | `playwright` instalado via pip mas **browsers não embutidos** (`playwright install chromium`) | Crash em máquina limpa | Adicionar step no build: `playwright install chromium --with-deps` ou usar `pyinstaller --add-binary` para browsers; ou remover Playwright se não essencial |
| **Tesseract OCR** | `pytesseract` requer binário `tesseract.exe` externo | OCR falha em máquina limpa | Embutir `tesseract.exe` + `tessdata` via `--add-binary` no spec; ou usar PaddleOCR (já no código v3) que é pure Python |
| **Poppler (pdf2image)** | `pdf2image` requer `poppler` binários | Conversão PDF→imagem falha | Embutir binários Poppler ou remover dependência |

### [Melhorias] - Otimizações futuras
- Migrar para **MSIX** nativo (melhor integração Store, atualizações delta, sandbox)
- Adicionar **auto-update** via MSIX/Store (já tem `update_checker.py` mas só notifica)
- Otimizar tamanho: excluir `__pycache__`, `.pyc`, testes, docs do pacote final
- Usar `pyi-makespec` com `--runtime-hook` para configurações dinâmicas

---

## 2. AUDITORIA DOS MÓDULOS ESPECÍFICOS

### 2.1 Consolidador & Sanitizador (Planilhas) — `consolidador_v2.py`

| Critério | Status | Detalhes |
|----------|--------|----------|
| **Processamento assíncrono** | ✅ OK | Executado via `task_executor.submit()` em thread separada (daemon=True) — não trava UI |
| **Worker Threads** | ⚠️ Parcial | Usa `pandas` single-thread; para 100k+ linhas pode travar CPU; `ProcessPoolExecutor` não usado |
| **Liberação de RAM** | ✅ OK | `gc.collect()` implícito; DataFrames locais destruídos ao sair do escopo; `_get_safe_row_limit()` usa `psutil` |
| **Exportação multi-formato** | ✅ OK | Suporta XLSX (premium), Parquet (snappy), CSV chunked (50k linhas) |
| **Limite de linhas** | ✅ OK | Removido limite fixo 50k; detecta RAM disponível dinamicamente |
| **Fuzzy mapping headers** | ✅ OK | `thefuzz` + LRU cache (4096 entradas) para alinhar colunas similares |

**Gap crítico**: Para arquivos >200k linhas, considerar `ProcessPoolExecutor` ou `polars` (mais rápido, multithread nativo).

---

### 2.2 Categorizador & Conciliador — `categorizador_v2.py`, `conciliador_v2.py`

| Critério | Status | Detalhes |
|----------|--------|----------|
| **Otimização de arrays** | ✅ OK | `bisect` (busca binária O(log N)) + `defaultdict` para casamento exato; 3 passadas (exato → tolerância → fallback) |
| **Fuzzy matching** | ✅ OK | Fallback: `rapidfuzz` > `thefuzz` > builtin Jaccard — robusto a breaking changes |
| **Paralelização** | ✅ OK | `ProcessPoolExecutor` com `os.cpu_count()` workers para classificação em lote (`_classify_worker`) |
| **Métricas de qualidade** | ✅ OK | Retorna `quality_metrics`: engine, outlier%, distribution, classification_quality |
| **Conciliação NF-e** | ✅ OK | Parse XML com namespace SEFAZ; validação XSD opcional (warn only); multi-periodo implementado |

**Gap**: Categorizador usa `ProcessPoolExecutor` mas `pickle` pode falhar com closures; testar em Windows (spawn vs fork).

---

### 2.3 Orçamentos (Geração de PDF) — `orcamentos.py`

| Critério | Status | Detalhes |
|----------|--------|----------|
| **Tratamento arquivo aberto** | ✅ OK | `_get_unique_filepath()` adiciona sufixo `(1)`, `(2)` se arquivo existe; `PermissionError` capturado no Consolidator |
| **Memory leak 1000+ PDFs** | ⚠️ Parcial | `generate_from_excel_streaming()` com `gc.collect()` a cada batch (50 PDFs) — **mas não usado pela UI** (usa `generate_from_excel` simples) |
| **Watermark FREE** | ✅ OK | `_add_watermark()` via `pypdf` + ReportLab canvas — aplica apenas no plano Grátis |
| **QR Code PIX** | ✅ OK | Payload EMV/BR Code com CRC-16 CCITT correto; `qrcode[pil]` |
| **Templates dinâmicos** | ❌ Faltando | Hardcoded no `GeradorOrcamentoPDF`; sugerido Jinja2 no roadmap |

**Ação urgente**: UI deve chamar `generate_from_excel_streaming()` em vez de `generate_from_excel()` para evitar OOM.

---

### 2.4 Minerador (Web Scraping) — `minerador_enterprise.py`

| Critério | Status | Detalhes |
|----------|--------|----------|
| **Tratamento erros de rede** | ✅ OK | `retry` decorator (exponencial 1-30s); `RateLimiter` token bucket; `httpx` com timeout |
| **Timeout** | ✅ OK | `navigate_timeout` 18-25s; `page.goto` com `wait_until="domcontentloaded"` |
| **Bloqueios IP / Anti-bot** | ✅ OK | **Circuit Breaker**: abre se taxa erro >70% últimos 10 requests; User-Agent rotation; stealth scripts; viewport randomization |
| **Seletores auto-atualizáveis** | ✅ OK | `SelectorRegistryEnterprise`: GitHub/Gist + local + user custom; health check automático a cada 6h |
| **APIs oficiais** | ✅ OK | Clients para Mercado Livre, Amazon SP-API, Shopee Open Platform (fallback prioridade) |
| **Cache persistente** | ❌ Faltando | Roadmap prevê SQLite cache — **não implementado** |
| **BUG CRÍTICO** | 🔴 **Bloqueante** | `mine_from_file()` é `pass` (linha 668) — **não funciona** |
| **BUG ALTO** | 🔴 **Bloqueante** | Variável `total` não definida em callback `_mine_playwright` (linha 908) — `NameError` |

**Correções obrigatórias antes de produção**:
1. Implementar `mine_from_file()` (ler CSV/JSON, iterar URLs)
2. Corrigir closure `total` no callback de progresso
3. Remover `import re` duplicados inline (linhas 772, 796)

---

### 2.5 Módulos Inativos ("Em Breve / Atualização 2.0") — 10 ferramentas

| Ferramenta | Status Código | Status UI | Risco Store |
|------------|---------------|-----------|-------------|
| Conversor OCR | `conversor_ocr_v3.py` (PaddleOCR) | Página existe | 🔴 **BUG CRÍTICO**: `json.dump` sem `import json` (linha 281); `/tmp/` hardcoded (linha 204) — falha Windows |
| Validador Links | `validador_links_v2.py` | Página existe | ⚠️ Loop bug; Playwright pesado |
| Classificador NCM | `classificador_ncm_v1.py` + `ncm_pipeline.py` | Página existe | 🔴 **BUG ALTO**: `_download_and_parse_cest` retorna `None`; typo `ClassificadorNCMEntperprise` |
| Gerador Laudos | `gerador_laudos_enterprise.py` | Página existe | 🔴 **BUG ALTO**: `_sign_pdf()` é stub (não assina); `items[:100]` truncamento silencioso |
| Calculadora Lucratividade | `calculadora_lucratividade_v2.py` | Página existe | ⚠️ `import pandas` inline; Simples Nacional desatualizado |
| Analista Tendências | `analista_tendencias_enterprise.py` | Página existe | ⚠️ `pytrends`, `scikit-learn` não em requirements; `asyncio.run()` em método |
| Extrator NF-e | `extrator_nfe_v1.py` | Página existe | ⚠️ `sys.path.append`; sem NFC-e; sem validação chave |
| Comissões | `comissoes.py` | Página existe | ⚠️ Sem volume tiers; sem PDF com gráficos |
| Data Sanitizer | `data_sanitizer_v2.py` | Página existe | ⚠️ Sem validação CPF/CNPJ (dígito verificador); sem ViaCEP |
| Precificador Canal | `precificador_canal_v1.py` | Página existe | 🔴 **BUG ALTO**: `tax_rules.json` não existe (só `.example.json`) |

**Isolamento na UI**: 
- `config.py` linha 251-320: Ferramentas têm `"status": "coming_soon"` e `"features"` listadas
- Páginas existem mas **não há guard no `app.py`** para impedir navegação — usuário pode clicar e crashar
- `TOOL_PAGE_MODULES` em `app.py` inclui TODAS (linhas 29-44) — **carregam no startup** via `_preload_tool_pages()`

**Ação urgente**: 
1. Adicionar guard no `_show_tool_page()`: se `config.TOOLS[tool_key].get("status") == "coming_soon"` → mostrar modal "Em desenvolvimento" e não instanciar página
2. Remover do `_preload_tool_pages()` ou fazer lazy-load real
3. Corrigir bugs críticos das 3 ferramentas (OCR, Laudos, NCM) ou remover código do build

---

## 3. DESEMPENHO, ESTABILIDADE E TRATAMENTO DE ERROS

### [OK] - Pontos fortes
- ✅ **TaskExecutor singleton** com lock thread-safe (`RLock`); max 2 tarefas simultâneas (PRO) / 1 (GRÁTIS)
- ✅ **Recuperação de tarefas interrompidas**: `recover_interrupted_tasks()` no startup marca como `INTERRUPTED` e permite restart
- ✅ **Circuit Breaker** no Minerador (anti-bot) + `retry` decorator genérico com backoff exponencial
- ✅ **RateLimiter** token bucket thread-safe para APIs
- ✅ **Try/catch generalizado**: Todas as chamadas Supabase, I/O, rede, DB têm tratamento
- ✅ **Funcionamento Offline**: 
  - `check_internet_connection()` a cada 30s (configurável)
  - Footer mostra status Online/Offline
  - Ferramentas locais (Consolidador, Categorizador, Conciliador, Orçamentos) funcionam 100% offline
  - Sync diferida quando volta conexão (`_realtime_sync` + queue local)
- ✅ **Logging centralizado**: `logging_setup.py` com rotação, níveis, arquivo em `AppData\logs`
- ✅ **APM (Application Performance Monitoring)**: `apm.py` mede latência, throughput, erros

### [Ajustar Urgente] - Problemas
| Item | Problema | Risco |
|------|----------|-------|
| **Memory leak Orçamentos** | UI usa `generate_from_excel()` (não streaming) — acumula 1000+ PDFs na RAM | OOM em máquinas com 8GB RAM |
| **Playwright browsers não embutidos** | `playwright` instalado mas `chromium` não — crash em máquina limpa | Ferramenta Minerador inutilizável |
| **Tesseract/Poppler externos** | OCR e PDF→imagem dependem de binários de sistema | Falha silenciosa em produção |
| **`sys.path.insert(0, ...)` em 5+ arquivos** | Imports frágeis; quebra se estrutura mudar | Manutenibilidade baixa |
| **`import` inline em métodos** | `pandas`, `re`, `json` importados dentro de funções | Performance; linting falha |
| **Interface `ITool` não implementada** | 16 ferramentas ignoram contrato `execute()`, `get_progress()`, `cancel()` | Incompatibilidade com `task_executor` futuro |

### [Melhorias] - Otimizações
- Migrar para `polars` no Consolidador (10x mais rápido, multithread nativo)
- Adicionar `psutil` monitoramento de RAM em tempo real no footer
- Implementar `ITool` em todas as ferramentas (padronização)
- Substituir `sys.path.insert` por `src/` como package (`pyproject.toml` já configura `find:`)
- Adicionar testes de carga: 500k linhas Consolidador, 1000 PDFs Orçamentos

---

## 4. SEGURANÇA, INTERFACE E DADOS SENSÍVEIS

### [OK] - Pontos fortes
- ✅ **Zero secrets no código**: `.env` carregado runtime; `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `ENCRYPTION_KEY` só no `.env`
- ✅ **Criptografia local AES-256 (Fernet)**: `ENCRYPTION_KEY` derivada de `SHA256(key + HWID)` — única por máquina
- ✅ **HWID binding**: `SecurityManager.get_hwid()` usa Motherboard Serial + CPU ID (SHA-256); valida no login Supabase
- ✅ **LGPD Compliance**: 
  - Grace period 30 dias para exclusão (`request_account_deletion`)
  - Consent log local (`save_consent`)
  - Purge automático contas expiradas (`purge_expired_accounts`)
  - Retenção de histórico configurável (1h a 6m)
- ✅ **Rate limiting login**: 5 tentativas → lockout 15min (armazenado criptografado)
- ✅ **Session refresh automático**: A cada 50 min (silencioso); inactivity logout 2h
- ✅ **Interface responsiva**: CustomTkinter + grid/flex; `CTkScrollableFrame`; breakpoints implícitos; temas Dark/Light/System
- ✅ **Drag & Drop**: `tkinterdnd2` para arquivos
- ✅ **Notificações desktop**: `winotify` (Windows 10/11 toast)

### [Ajustar Urgente] - Problemas
| Item | Problema | Risco |
|------|----------|-------|
| **`tax_rules.json` ausente** | `precificador_canal_v1.py` e `calculadora_lucratividade_v2.py` leem arquivo que não existe (só `.example.json`) | Crash em ferramentas financeiras |
| **Ferramentas "coming_soon" expostas** | Usuário pode acessar páginas que crasham (OCR, Laudos, NCM) | Experiência ruim; possível rejeição Store |
| **Supabase Anon Key no cliente** | `config._r1()` expõe chave anônima — **aceitável** (público por design Supabase) | Baixo (RLS no banco protege) |

### [Melhorias] - Otimizações
- Adicionar **Code Signing** no build CI/CD (GitHub Actions + `signtool`)
- Implementar **Windows Hello / Biometria** para login opcional
- Adicionar **Telemetria anônima opt-in** (crash reports, usage stats)
- Melhorar acessibilidade: `aria-label`, navegação por teclado, alto contraste

---

## CHECKLIST FINAL PARA SUBMISSÃO MICROSOFT STORE

### 🔴 BLOQUEANTES (Devem ser resolvidos ANTES do build final)

| # | Item | Arquivo/Location | Ação |
|---|------|------------------|------|
| 1 | **Migrar para MSIX** | Build pipeline | Criar `AppxManifest.xml`; usar `makeappx` + certificado EV; ou Electron/Tauri |
| 2 | **AppxManifest.xml** | `AppxManifest.xml` | `Name="DataMasterPro" Publisher="CN=..." Version="1.5.0.0"` |
| 3 | **Visual Assets (tiles)** | `assets/` | 150x150, 44x44, 71x71, 310x150, 310x310, 620x300 (Store logo) |
| 4 | **Capabilities declaradas** | `AppxManifest.xml` | `internetClient`, `documentsLibrary`, `removableStorage` |
| 5 | **Corrigir `mine_from_file()`** | `minerador_enterprise.py:668` | Implementar leitura CSV/JSON + iteração |
| 6 | **Corrigir `total` undefined** | `minerador_enterprise.py:908` | Capturar via closure |
| 7 | **Corrigir OCR imports** | `conversor_ocr_v3.py:281,204` | `import json`; `tempfile.gettempdir()` |
| 8 | **Corrigir Laudos `_sign_pdf()`** | `gerador_laudos_enterprise.py:630` | Implementar pAdES-B com `endesive` |
| 9 | **Corrigir NCM CEST** | `ncm_pipeline.py:221` | Implementar download/parse CEST oficial |
| 10 | **Corrigir typo NCM** | `ncm_pipeline.py:378` | `ClassificadorNCMEntperprise` → `ClassificadorNCMEnterprise` |
| 11 | **Criar `tax_rules.json`** | `datamaster-pro-desktop/` | Copiar de `.example.json` com dados reais |
| 12 | **Isolar ferramentas "coming_soon"** | `app.py:_show_tool_page()` | Guard: se status="coming_soon" → modal aviso |
| 13 | **Remover do preload** | `app.py:_preload_tool_pages()` | Pular ferramentas com status="coming_soon" |
| 14 | **Usar streaming Orçamentos** | `orcamentos_page.py:_run_generate()` | Chamar `generate_from_excel_streaming()` |
| 15 | **Embutir Playwright Chromium** | `build_v2_otimizado.bat` | `playwright install chromium` no step de build |
| 16 | **Embutir Tesseract/Poppler** | `datamaster.spec` | `--add-binary` para binários + `tessdata` |
| 17 | **Atualizar `version_info.txt`** | `version_info.txt` | `filevers=(1,5,0,0)`, `prodvers=(1,5,0,0)` |
| 18 | **Remover `sys.path.insert`** | 5+ arquivos | Usar imports de package (`from src...`) |
| 19 | **Mover imports inline para topo** | 10+ arquivos | `pandas`, `re`, `json`, `importlib` no topo |

### 🟡 ALTA PRIORIDADE (Resolver na v1.5.1 / Sprint 1)

| # | Item | Ação |
|---|------|------|
| 20 | Implementar `ITool.execute()` em todas as 16 ferramentas | Padronizar contrato |
| 21 | Adicionar `psutil`, `pyarrow`, `rapidfuzz`, `jinja2`, `endesive`, `httpx`, `lxml`, `matplotlib`, `phonenumbers`, `paddleocr`, `opencv-python` ao `requirements.txt` |
| 22 | Implementar cache SQLite persistente no Minerador | `PersistentCache` class |
| 23 | Health check automático seletores Minerador | Já tem registry — ativar agendamento |
| 24 | Orçamentos: templates Jinja2 dinâmicos | `TemplateEngine` class |
| 25 | Categorizador: fallback `rapidfuzz` + métricas acurácia | `_fuzzy_score` engine detection |
| 26 | Consolidador: export Parquet/CSV chunked já funciona — testar 500k linhas |
| 27 | Precificador Canal: API Melhor Envio + ICMS interestadual | `FreteCalculator` class |
| 28 | Calculadora Lucratividade: Simples Nacional JSON + break-even | Tabela externa 2026 |
| 29 | Validador Links: modo híbrido HEAD + Playwright | `HybridValidator` class |
| 30 | Comissões: volume tiers + PDF com gráficos matplotlib | `volume_tiers` type |
| 31 | Data Sanitizer: validação CPF/CNPJ (módulo 11) + ViaCEP | `_validate_cpf`, `_validate_cnpj` |
| 32 | Extrator NF-e: suporte NFC-e + validação chave acesso | `_parse_nfce`, `_validar_chave_acesso` |
| 33 | Conciliador: validação XSD SEFAZ + multi-periodo | `_validate_nfe_schema`, `reconcile_multi_period` |

### 🟢 MÉDIA PRIORIDADE (v1.6+)

| # | Item |
|---|------|
| 34 | Migrar build para GitHub Actions + MSIX + assinatura automática |
| 35 | Auto-update via MSIX/Store (já tem `update_checker` — integrar) |
| 36 | Telemetria anônima opt-in (crash reports, feature usage) |
| 37 | Windows Hello / Biometria para login |
| 38 | Acessibilidade completa (WCAG 2.1 AA) |
| 39 | Testes de carga automatizados (500k linhas, 1000 PDFs, 100 URLs) |
| 40 | Documentação usuário final (PDF/HTML) embutida no app |
| 41 | Internacionalização (i18n) pt-BR / en-US / es-ES |

---

## VEREDITO FINAL

| Critério | Pronto para Produção? | Pronto para Microsoft Store? |
|----------|----------------------|------------------------------|
| **Core Desktop App** | ✅ Sim | ❌ **Não** (precisa MSIX + assinatura) |
| **5 Ferramentas Ativas** | ⚠️ **Com ressalvas** (Orçamentos memory leak; Minerador bugs) | ❌ **Não** |
| **10 Ferramentas Futuras** | ❌ **Não** (bugs críticos, não isoladas) | ❌ **Não** |
| **Segurança/LGPD** | ✅ Sim | ✅ Sim |
| **Offline/Resilience** | ✅ Sim | ✅ Sim |

### **TEMPO ESTIMADO PARA PRODUÇÃO + STORE: 10-14 dias**

- **Dias 1-3**: Correções bloqueantes (linhas 1-19 acima) + build MSIX + assinatura
- **Dias 4-7**: Correções alta prioridade (linhas 20-33) + testes de regressão
- **Dias 8-10**: Polimento UI, assets Store, documentação, submissão
- **Dias 11-14**: Buffer para revisão Microsoft (certificação costuma levar 3-7 dias)

---

## ARQUIVOS-CHAVE PARA CORREÇÃO IMEDIATA

```
datamaster-pro-desktop/
├── datamaster.spec                    # Adicionar binários Playwright/Tesseract/Poppler; atualizar version_info
├── version_info.txt                   # Corrigir versão para 1.5.0.0
├── installer.nsi                      # Ajustar Publisher para CN do certificado EV
├── config.py                          # Adicionar guard status="coming_soon" no TOOLS
├── src/gui/app.py                     # Guard em _show_tool_page(); pular coming_soon no _preload_tool_pages
├── src/tools/minerador/minerador_enterprise.py  # Implementar mine_from_file(); corrigir total closure
├── src/tools/conversor_ocr/conversor_ocr_v3.py  # import json; tempfile.gettempdir()
├── src/tools/gerador_laudos/gerador_laudos_enterprise.py  # Implementar _sign_pdf() pAdES-B
├── src/tools/classificador_ncm/ncm_pipeline.py  # Corrigir CEST; typo ClassificadorNCMEnterprise
├── src/tools/precificador_canal/precificador_canal_v1.py  # Criar tax_rules.json real
├── src/tools/calculadora_lucratividade/calculadora_lucratividade_v2.py  # Mover imports; JSON Simples Nacional
├── src/tools/orcamentos/orcamentos.py  # UI deve usar generate_from_excel_streaming()
├── build_v2_otimizado.bat             # Adicionar: playwright install chromium; signtool
└── requirements.txt                   # Adicionar dependências faltantes
```

---

**Data**: 2026-08-05  
**Classificação**: Confidencial - Uso Interno DataMaster Pro