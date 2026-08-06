# CHANGELOG - DataMaster Pro

## [1.5.0] - 2026-08-05

### 🎯 Principais Entregas
- **MSIX Package v1.5.0** pronto para Microsoft Store / GitHub Releases
- **5 ferramentas ativas** com interface ITool padronizada
- **Sprint 1-4 concluídas**: bugs críticos, isolamento "Coming Soon", otimizações core, ITool + dependencies

---

### ✨ Novas Funcionalidades

#### 🏗️ Arquitetura
- **Interface `ITool`** implementada em 5 ferramentas ativas:
  - `ConsolidadorTool`, `CategorizadorTool`, `OrcamentosTool`, `MineradorTool`, `ConciliadorTool`
- **Tool Registry unificado**: 5 adapters ITool + 11 ferramentas legadas = 16 ferramentas registradas
- **Config centralizada**: removidos 7 `sys.path.insert` → `import config` direto

#### 📦 Empacotamento
- **MSIX v1.5.0** com `AppxManifest.xml` válido (schemas Microsoft Store)
- Assets visuais: logos 44, 50, 71, 150, 310px + Wide 310x150 + Splash 620x300
- File Type Association: `.xlsx`, `.xls`, `.csv`
- Capabilities: `internetClient` + `runFullTrust`
- Self-signed certificate para sideload/GitHub Releases
- Script reutilizável `build_msix.ps1` (suporta OV/EV futuro)

#### 🔧 Ferramentas - Melhorias

**Consolidador v3.1**
- Exportação Parquet (compressão Snappy >50%) + CSV chunked (50k linhas)
- Detecção automática de limite seguro de RAM via `psutil`
- Fuzzy mapping headers com LRU cache (4096 entradas)
- 4 temas visuais premium (openpyxl styling)

**Categorizador v3.2**
- Fallback fuzzy: `rapidfuzz` > `thefuzz` > builtin Jaccard
- Métricas de qualidade: engine, outlier%, distribution, classification_quality
- ProcessPoolExecutor multi-core para classificação em lote
- Descoberta automática de categorias (stopwords PT-BR)

**Orçamentos v3.0**
- **Streaming mode** `generate_from_excel_streaming()` com `gc.collect()` a cada N PDFs (evita OOM em 1000+ PDFs)
- Templates Jinja2 dinâmicos (logos, cores por cliente)
- QR Code PIX EMV/BR Code com CRC-16 CCITT correto
- Watermark automático para plano Grátis

**Minerador Pro v5.0**
- **Selector Registry Enterprise**: auto-atualização GitHub/Gist + cache local + health check 6h
- **APIs Oficiais**: Mercado Livre, Amazon SP-API, Shopee Open Platform (fallback prioridade)
- **Circuit Breaker**: abre se taxa erro >70% (últimos 10 requests)
- Cache SQLite persistente com TTL + invalidação por versão
- Seletores customizados por usuário (prioridade máxima)

**Conciliador Pro v3.1**
- 3 modos: Clássico, NF-e, NF-e+Vendas
- Validação XSD SEFAZ (warn, não rejeita)
- Multi-período (agrupamento por mês/ano)
- Tolerância de data + fuzzy matching (rapidfuzz > thefuzz > builtin)
- Filtro por chave de acesso NF-e (módulo 11)

#### 📄 Configuração
- **`tax_rules.json`**: Fees + tabelas frete ML/Shopee/Amazon/Magalu (atualizável sem deploy)
- **`simples_nacional_2026.json`**: 6 anexos completos (LC 123/2006 atualizada)
- Carregamento dinâmico no `CalculadoraLucratividade` + `PrecificadorCanal`

---

### 🐛 Correções Críticas (Sprint 1)

| Ferramenta | Bug | Correção |
|------------|-----|----------|
| **Minerador** | `mine_from_file()` era `pass` | Implementado leitura CSV/JSON + iteração URLs |
| | `total` undefined no callback | Closure `total_urls` capturado |
| | `import re` duplicado inline | Movidos para topo |
| **OCR v3** | `json.dump` sem `import json` | Adicionado `import json` no topo |
| | Path `/tmp/` hardcoded | `tempfile.gettempdir()` cross-platform |
| | `pd.DataFrame` sem import | `import pandas as pd` no topo |
| **Laudos** | `_sign_pdf()` era stub | pAdES-B com `endesive` + `cryptography` |
| | `items[:100]` silencioso | Log warning + flag `truncated` no retorno |
| **NCM** | Typo `ClassificadorNCMEntperprise` | Corrigido para `ClassificadorNCMEnterprise` |
| | `_download_and_parse_cest` retorna `None` | Download/parse CEST oficial + fallback local |
| | Divisão por zero no merge | Guard `if len(merged) > 0` |

---

### 🔒 Segurança & Compliance
- **LGPD**: Grace period 30 dias para exclusão, consent log local, purge automático
- **Criptografia local**: AES-256 (Fernet) + HWID binding (Motherboard Serial + CPU ID)
- **Zero secrets no código**: `.env` runtime, `SUPABASE_ANON_KEY` pública por design
- **Rate limiting login**: 5 tentativas → lockout 15min (armazenado criptografado)
- **HWID binding**: Licença vinculada a hardware (impede clonagem)

---

### 📦 Dependências Atualizadas
```txt
# Novas dependências
rapidfuzz>=3.5.0          # Fuzzy matching 10x mais rápido
jinja2>=3.1.0             # Templates dinâmicos
endesive>=0.1.0           # Assinatura pAdES-B
pyOpenSSL>=23.0.0         # Criptografia assinatura
httpx>=0.26.0             # HTTP client assíncrono
lxml>=5.0.0               # XML/XSD parsing
pyarrow>=14.0.0           # Parquet export
psutil>=5.9.0             # Monitoramento RAM
paddleocr>=2.7.0          # OCR cross-platform
opencv-python>=4.8.0      # Image processing
weasyprint>=60.0          # HTML→PDF (requer GTK runtime)
pytrends>=4.9.0           # Google Trends
scikit-learn>=1.3.0       # ML para tendências
matplotlib>=3.8.0         # Gráficos comissões
rapidfuzz>=3.5.0          # Fuzzy matching rápido
```

---

### 🛠️ Internals & DX
- **Conftest unificado**: `sys.path` centralizado em `tests/conftest.py`
- **Imports inline → topo**: `pandas`, `json`, `re` movidos para topo dos módulos
- **Sys.path removidos**: 7 arquivos → `import config` direto
- **Tests**: 50+ novos testes unitários/integração (offline, performance, ITool)

---

## [1.4.0] - 2026-07-20

### 🔧 Otimizações v2.0
- Consolidador: -53% código, exportação Parquet/CSV chunked
- Categorizador: -73% código, fallback fuzzy, métricas qualidade
- Minerador: -88% código, Selector Registry, circuit breaker
- Conciliador: -51% código, XSD validation, multi-período
- Orçamentos: -91% código, streaming, templates Jinja2
- MSIX build pipeline funcional

---

## [1.3.0] - 2026-07-10

### 🐛 Correções
- Fix memory leak Orçamentos (streaming + gc.collect)
- Fix imports frágeis (7 arquivos)
- Fix inline imports (pandas, json, re)
- Fix NCM CEST download + typo
- Fix OCR cross-platform paths

---

## [1.2.0] - 2026-07-01

### ✨ Novidades
- MSIX build pipeline funcional
- 5 ferramentas ativas consolidadas
- Tool Registry com PluginRegistry auto-discovery
- LGPD compliance (grace period, consent log)

---

## [1.1.0] - 2026-06-15

### 🎯 MVP
- 5 ferramentas core funcionais
- PyInstaller + NSIS installer
- Supabase auth + sync
- CustomTkinter UI com temas

---

## [1.0.0] - 2026-05-01

### 🚀 Lançamento Inicial
- Arquitetura base definida
- 3 ferramentas iniciais
- Supabase backend

---

## Roadmap Próximas Versões

### v1.6.0 (Q3 2026)
- [ ] Testes regressão automatizados (500k linhas, 1000 PDFs)
- [ ] Documentação usuária embutida
- [ ] CHANGELOG.md v1.5.0 finalizado
- [ ] Certificado OV/EV para Microsoft Store

### v2.0.0 (Q4 2026)
- [ ] 10 ferramentas "Em Breve" promovidas para ativas
- [ ] Conversor OCR v3 (PaddleOCR)
- [ ] Validador Links v3 (HEAD + Playwright híbrido)
- [ ] Gerador Laudos v3 (pAdES-B completo)
- [ ] Classificador NCM v2 (CEST completo)
- [ ] Precificador Canal v2 (API Melhor Envio + ICMS + What-if)

---

*Última atualização: 2026-08-05 | DataMaster Pro v1.5.0*