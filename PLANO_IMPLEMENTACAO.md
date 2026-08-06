# PLANO DE IMPLEMENTAÇÃO - DataMaster Pro v1.5.0
## Correções para Produção e Microsoft Store

---

## METODOLOGIA

- **Sprints de 2 dias** com entregas testáveis
- **Branch por sprint**: `fix/sprint-N`
- **PR obrigatório** com CI passando (lint + testes)
- **Deploy homologação** ao final de cada sprint

---

## ✅ SPRINT 0 - CONCLUÍDO (2026-08-05)
**Objetivo**: Build MSIX funcional + assets + manifest

| Tarefa | Status | Detalhes |
|--------|--------|----------|
| `AppxManifest.xml` válido | ✅ | Schema-compliant, `makeappx` OK |
| Assets visuais (logos 44,50,71,150,310 + Wide 310x150 + Splash 620x300) | ✅ | Gerados do `datamaster.ico` via PIL |
| `version_info.txt` = 1.5.0.0 | ✅ | `filevers=(1,5,0,0)` |
| Certificado self-signed gerado | ✅ | `datamaster_selfsigned.pfx` (senha: `datamaster2026`) |
| MSIX package criado | ✅ | `DataMasterPro_1.5.0.0_x64.msix` (322MB) |
| Assinatura self-signed | ✅ | `signtool sign /fd SHA256` |
| File Type Association | ✅ | `.xlsx`, `.xls`, `.csv` |
| Capabilities | ✅ | `internetClient` + `runFullTrust` |
| Executável PyInstaller | ✅ | Single-file `DataMaster Pro.exe` (324MB) |

**Artefatos gerados:**
- `DataMasterPro_1.5.0.0_x64.msix` — pronto para sideload/GitHub Releases
- `datamaster_selfsigned.pfx` — certificado para instalação local
- `AppxManifest.xml` — validado
- `build_msix.ps1` — script reutilizável para OV/EV futuro

**⚠️ NÃO FEITO (requer $89):**
- Certificado OV/EV real para Microsoft Store
- GitHub Actions pipeline

---

## ✅ SPRINT 1 - CONCLUÍDO (2026-08-05)
**Objetivo**: Corrigir bugs que impedem funcionamento básico das 10 ferramentas "Em Breve"

### 1.1 Minerador Enterprise (`src/tools/minerador/minerador_enterprise.py`)
| Bug | Linha | Status | Correção |
|-----|-------|--------|----------|
| `mine_from_file()` era `pass` | 659 | ✅ | Implementado leitura CSV/JSON + iteração URLs |
| `total` undefined no callback | 954 | ✅ | Capturar `len(urls)` no closure |
| `import re` duplicado inline | 772, 796 | ✅ | Movidos para topo |
| `SELECTOR_REGISTRY` não importado | - | ✅ | `from minerador_v2 import SELECTOR_REGISTRY` |

### 1.2 Conversor OCR v3 (`src/tools/conversor_ocr/conversor_ocr_v3.py`)
| Bug | Linha | Status | Correção |
|-----|-------|--------|----------|
| `json.dump` sem `import json` | 283 | ✅ | Adicionado `import json` no topo |
| Path `/tmp/` hardcoded | 204 | ✅ | Usa `tempfile.gettempdir()` cross-platform |
| `pd.DataFrame` sem import | 367 | ✅ | Adicionado `import pandas as pd` no topo |

### 1.3 Gerador Laudos Enterprise (`src/tools/gerador_laudos/gerador_laudos_enterprise.py`)
| Bug | Linha | Status | Correção |
|-----|-------|--------|----------|
| `_sign_pdf()` era stub | 618 | ✅ | Implementado pAdES-B com `endesive` |
| `items[:100]` truncamento silencioso | 428 | ✅ | Log warning + flag `truncated` no retorno |

### 1.4 Classificador NCM (`src/tools/classificador_ncm/ncm_pipeline.py`)
| Bug | Linha | Status | Correção |
|-----|-------|--------|----------|
| Typo `ClassificadorNCMEntperprise` | 378 | ✅ | Corrigido para `ClassificadorNCMEnterprise` |
| `_download_and_parse_cest` retorna `None` | 215 | ✅ | Implementado download/parse CEST oficial + fallback local |
| Guard divisão por zero | 308 | ✅ | Guard `if len(merged) > 0` |

### 1.5 Configurações Gerais
| Arquivo | Status | Ação |
|---------|--------|------|
| `datamaster-pro-desktop/tax_rules.json` | ✅ | Criado com fees + frete 4 marketplaces |
| `datamaster-pro-desktop/simples_nacional_2026.json` | ✅ | Criado com 6 anexos 2026 |
| `calculadora_lucratividade_v2.py` | ✅ | `import pandas` movido para topo; carrega `simples_nacional_2026.json` |
| `precificador_canal_v1.py` | ✅ | Carrega `tax_rules.json` (criado) |
| Imports frágeis (5 arquivos) | ✅ | `sys.path.append` removidos; usam `import config` |

**Critério de aceitação Sprint 1**: ✅ ATENDIDO - Todas as 10 ferramentas "Em Breve" carregam sem crash; Minerador processa CSV; OCR roda no Windows; Laudos assinam; NCM pipeline roda.

---

## ✅ SPRINT 2 - CONCLUÍDO (2026-08-05)
**Objetivo**: Impedir acesso a ferramentas não prontas na UI

### 2.1 Guard no `src/gui/app.py` - `_show_tool_page()`
```python
def _show_tool_page(self, tool_key: str):
    tool_config = config.TOOLS.get(tool_key, {})
    if tool_config.get("status") == "coming_soon":
        from tkinter import messagebox
        messagebox.showinfo(
            "Em Desenvolvimento",
            f"A ferramenta '{tool_config.get('name', tool_key)}' está em desenvolvimento.\n"
            f"Previsão: Atualização 2.0\n\n"
            f"Funcionalidades planejadas:\n" + 
            "\n".join(f"• {f}" for f in tool_config.get("features", []))
        )
        return
    # ... resto existente
```

### 2.2 `_preload_tool_pages()` pula ferramentas "coming_soon"
```python
def _preload_tool_pages(self):
    for tool_key in list(TOOL_PAGE_MODULES.keys()):
        if config.TOOLS.get(tool_key, {}).get("status") == "coming_soon":
            continue  # Pula lazy-load
        try:
            self._get_tool_page_class(tool_key)
        except Exception as e:
            log.error("Erro pré-carregando %s: %s", tool_key, e)
```

**Critério**: ✅ ATENDIDO - Clicar em "Em Breve" → modal informativo; não crasha; não carrega no startup.

---

## ✅ SPRINT 3 - CONCLUÍDO (2026-08-05)
**Objetivo**: Memory leak, imports, dependências nativas

### 3.1 Orçamentos - Usar Streaming (`src/gui/pages/tools/orcamentos_page.py`)
```python
def execute():
    from src.tools.orcamentos.orcamentos import Orcamentos as Orc
    o = Orc()
    return o.generate_from_excel_streaming(
        self.data_file, output_dir, watermark=has_watermark, config=cfg,
        batch_size=50  # gc.collect a cada 50 PDFs
    )
```

### 3.2 Limpeza Imports Frágeis (6 arquivos)
| Arquivo | Linha | Fix |
|---------|-------|-----|
| `calculadora_lucratividade_v2.py` | 26 | `import config` no topo |
| `minerador_enterprise.py` | 30 | `import config` no topo |
| `validador_links_v2.py` | 22 | `import config` no topo |
| `extrator_reviews_v2.py` | 17 | `import config` no topo |
| `analista_tendencias_v2.py` | 15 | `import config` no topo |
| `extrator_nfe_v1.py` | 350 → 29 | `import config` no topo |
| `classificador_ncm_v1.py` | 236 → 22 | `import config` no topo |

### 3.3 Mover Imports Inline para Topo
- ✅ `import pandas` em `calculadora_lucratividade_v2.py:172` → topo
- ✅ `import json` em `conversor_ocr_v3.py:283` → topo  
- ✅ `import re` duplicado em `minerador_enterprise.py:772,796` → topo
- ✅ `import pandas as pd` em `conversor_ocr_v3.py:367` → topo

### 3.4 Embutir Binários Nativos (opcional, para depois)
- `playwright install chromium --with-deps` no build
- Tesseract + Poppler no `datamaster.spec` via `--add-binary`

**Critério de aceitação Sprint 3**: ✅ ATENDIDO - Orçamentos usa streaming (evita OOM); imports frágeis removidos; inline imports movidos.

---

### ✅ SPRINT 4 - ITOOL + DEPENDÊNCIAS (CONCLUÍDO 2026-08-05)
**Objetivo**: Padronizar contratos + requirements

### 4.1 Implementar `ITool` nas 16 ferramentas
Template base em `src/tools/itool.py` → aplicado em 5 ferramentas ativas + 11 legadas:

| Ferramenta | Arquivo Adapter | Status |
|------------|-----------------|--------|
| Consolidador | `src/tools/consolidador/consolidador_tool.py` | ✅ |
| Categorizador | `src/tools/categorizador/categorizador_tool.py` | ✅ |
| Orçamentos | `src/tools/orcamentos/orcamentos_tool.py` | ✅ |
| Minerador | `src/tools/minerador/minerador_tool.py` | ✅ |
| Conciliador | `src/tools/conciliador/conciliador_tool.py` | ✅ |
| Comissoes | Legado (mantido) | ⏳ |
| Calculadora Lucratividade | Legado (mantido) | ⏳ |
| Analista Tendencias | Legado (mantido) | ⏳ |
| Data Sanitizer | Legado (mantido) | ⏳ |
| Extrator Reviews | Legado (mantido) | ⏳ |
| Validador Links | Legado (mantido) | ⏳ |
| Conversor OCR | Legado (mantido) | ⏳ |
| Gerador Laudos | Legado (mantido) | ⏳ |
| Precificador Canal | Legado (mantido) | ⏳ |
| Extrator NF-e | Legado (mantido) | ⏳ |
| Classificador NCM | Legado (mantido) | ⏳ |

**Tool Registry atualizado**: `src/tools/tool_registry.py` importa os 5 adapters ITool e mantém 11 legados.

### 4.2 `requirements.txt` + `pyproject.toml` Completos
```txt
# Adicionados:
psutil>=5.9.0
pyarrow>=14.0.0
rapidfuzz>=3.5.0
jinja2>=3.1.0
endesive>=0.1.0
httpx>=0.26.0
lxml>=5.0.0
matplotlib>=3.8.0
phonenumbers>=8.13.0
paddleocr>=2.7.0
opencv-python>=4.8.0
pytrends>=4.9.0
scikit-learn>=1.3.0
weasyprint>=60.0
pyOpenSSL>=23.0.0
```

**Critério de aceitação Sprint 4**: ✅ ATENDIDO - 5 ferramentas ativas com ITool adapter; tool_registry unificado; requirements + pyproject.toml sincronizados.

## COMANDOS ÚTEIS ATUALIZADOS

```bash
# Build MSIX (self-signed ou real)
cd datamaster-pro-desktop
.\build_msix.ps1 -SkipPyInstaller              # self-signed
.\build_msix.ps1 -CertPath "real.pfx" -CertPassword "senha" -SkipPyInstaller  # OV/EV

# Testar MSIX local (PowerShell Admin)
Add-AppxPackage DataMasterPro_1.5.0.0_x64.msix

# PyInstaller build
python -m PyInstaller datamaster.spec --clean

# Lint
ruff check src/ && ruff format src/

# Testes
pytest tests/ -v --tb=short -x
```

---

## CHECKLIST ATUALIZADO

### ✅ Sprint 0 - MSIX BUILD (CONCLUÍDO 2026-08-05)
- [x] `AppxManifest.xml` válido
- [x] Assets visuais gerados
- [x] `version_info.txt` = 1.5.0.0
- [x] Certificado self-signed gerado
- [x] MSIX package criado e assinado
- [x] File Type Association (.xlsx, .xls, .csv)
- [x] Capabilities: internetClient + runFullTrust
- [x] Executável single-file 324MB
- [ ] Certificado OV/EV real ($89)
- [ ] GitHub Actions pipeline

### ✅ Sprint 1 - Bugs Críticos (CONCLUÍDO 2026-08-05)
- [x] `mine_from_file()` implementado
- [x] Closure `total` corrigido
- [x] OCR: `import json` + path cross-platform
- [x] Laudos: `_sign_pdf()` pAdES-B
- [x] NCM: typo + CEST + guard divisão zero
- [x] `tax_rules.json` + `simples_nacional_2026.json` criados
- [x] Imports frágeis removidos (7 arquivos)

### ✅ Sprint 2 - Isolamento "Coming Soon" (CONCLUÍDO 2026-08-05)
- [x] Guard `_show_tool_page()`
- [x] `_preload_tool_pages()` pula futuras
- [x] Modal informativo

### ✅ Sprint 3 - Otimizações Core (CONCLUÍDO 2026-08-05)
- [x] Orçamentos usa streaming
- [x] `sys.path.insert` removidos (7 arquivos)
- [x] Imports inline movidos para topo

### ✅ Sprint 4 - ITool + Requirements (CONCLUÍDO 2026-08-05)
- [x] `ITool` em 5 ferramentas ativas (Consolidador, Categorizador, Orçamentos, Minerador, Conciliador)
- [x] `tool_registry.py` unificado com adapters ITool + legados
- [x] `requirements.txt` completo
- [x] `pyproject.toml` sincronizado (v1.5.0)

### 🟣 Sprint 5 - Testes + Polish
- [ ] Testes regressão passando
- [ ] Documentação usuária
- [ ] `CHANGELOG.md` v1.5.0

### ⚫ Sprint 6 - Microsoft Store (QUANDO TIVER $89)
- [ ] Certificado OV comprado
- [ ] MSIX re-assinado
- [ ] Submetido Partner Center
- [ ] Publicado na Store

---

## RISCOS ATUALIZADOS

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Certificado OV $89 indisponível | Alta | Bloqueia Store | Distribuir via GitHub Releases + site próprio (já funciona) |
| `endesive` falha PDFs complexos | Média | Laudos não assinam | Testar 10 PDFs variados; fallback warning |
| Minerador Playwright 200MB | Média | MSIX grande | Usar API oficial prioritário; embutir seletivo |
| 10 ferramentas "Em Breve" visíveis | Baixa | Rejeição Store | Sprint 2 isola com guard; descrição Store menciona "roadmap" |

---

## COMUNICAÇÃO

- **Daily**: Async (Teams/Slack)
- **Demo**: Final de cada sprint
- **Canal**: `#datamaster-prod-release`

---

**Atualizado**: 2026-08-05  
**Próxima ação**: Iniciar Sprint 5 - Testes regressão (500k linhas, 1000 PDFs, offline mode) + Documentação + CHANGELOG  
**Responsável**: Engenheiro DevOps/Arquiteto