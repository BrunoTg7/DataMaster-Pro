# Refatoração Enterprise — Melhorias Otimizadas (Fase 2)

Este plano descreve as otimizações a serem implementadas nas 4 ferramentas que apresentavam limitações de escalabilidade para uso corporativo, conforme a [Auditoria Técnica](file:///c:/Users/Public/projetos/ferramente%20excel/datamaster-pro-desktop/docs/analysis_results.md).

## User Review Required

> [!IMPORTANT]
> Vou implementar essas 4 melhorias sequencialmente para garantir a integridade da suíte de ferramentas. O Categorizador utilizará `concurrent.futures` em vez de bibliotecas C-extension complexas (como Aho-Corasick) para manter a compatibilidade cross-platform do instalador Windows.
> Se você estiver de acordo com o plano abaixo, é só aprovar!

## Proposed Changes

---

### 1. Validador de Links (`validador_links_v2.py`)
**Objetivo:** Reduzir o tempo de validação e o consumo de recursos do Playwright em links mortos.
- **Como:** Adicionar uma requisição HTTP leve (usando `aiohttp` ou fallback síncrono rápido) antes de instanciar o navegador.
- **Implementação:**
  - Importar `aiohttp`.
  - Criar um método auxiliar `_quick_head_check` para fazer um GET stream/HEAD rápido.
  - Se o link retornar 404, 500, ou não existir (DNS error), pular o Playwright completamente e registrar como `broken`.

#### [MODIFY] [validador_links_v2.py](file:///c:/Users/Public/projetos/ferramente%20excel/datamaster-pro-desktop/src/tools/validador_links/validador_links_v2.py)

---

### 2. Consolidador (`consolidador_v2.py`)
**Objetivo:** Prevenir erros de *Out-Of-Memory* (OOM) ao lidar com arquivos de faturamento de centenas de megabytes.
- **Como:** Melhorar o carregamento do Pandas para lidar graciosamente com arquivos muito grandes. Para a escrita, `openpyxl` pode ser muito custoso na memória ao gravar centenas de milhares de linhas estilizadas.
- **Implementação:**
  - Aplicar `engine="openpyxl"` no modo iterativo ao ler Excel (se possível) e gerenciar limites.
  - Ao salvar `_save_premium_excel`, usar `wb.write_only = True` se aplicável, ou implementar um aviso/proteção (`max_rows` safety cap) para planilhas acima de um limite seguro (ex: 50.000 linhas) preservando o estilo premium, ou usar `xlsxwriter` se necessário. 

#### [MODIFY] [consolidador_v2.py](file:///c:/Users/Public/projetos/ferramente%20excel/datamaster-pro-desktop/src/tools/consolidador/consolidador_v2.py)

---

### 3. Categorizador (`categorizador_v2.py`)
**Objetivo:** Reduzir o tempo de processamento CPU-bound causado pelas iterações de Expressões Regulares (`Regex`).
- **Como:** Paralelizar o loop que aplica `_classify` nas linhas do DataFrame.
- **Implementação:**
  - Importar `concurrent.futures.ProcessPoolExecutor`.
  - No método `categorize`, dividir a coluna de descrição em chunks com `np.array_split`.
  - Processar os chunks em paralelo usando os núcleos da CPU para acelerar a classificação em grandes volumes de dados.

#### [MODIFY] [categorizador_v2.py](file:///c:/Users/Public/projetos/ferramente%20excel/datamaster-pro-desktop/src/tools/categorizador/categorizador_v2.py)

---

### 4. Comissões (`comissoes.py`)
**Objetivo:** Evitar travamentos na interface visual ao gerar relatórios em PDF para milhares de representantes comerciais.
- **Como:** Paralelizar a criação dos PDFs individuais com multithreading.
- **Implementação:**
  - Em `generate_pdf_reports`, utilizar `concurrent.futures.ThreadPoolExecutor`.
  - Agrupar as gerações via `executor.map` ou `submit`.
  - Manter o callback de progresso de forma *thread-safe* para atualizar a interface fluida.

#### [MODIFY] [comissoes.py](file:///c:/Users/Public/projetos/ferramente%20excel/datamaster-pro-desktop/src/tools/comissoes/comissoes.py)

## Verification Plan

### Manual Verification
- Simularei chamadas às 4 ferramentas (via scripts isolados ou chamando suas instâncias `__main__`) para verificar que estão inicializando e rodando sem erros após a refatoração.
