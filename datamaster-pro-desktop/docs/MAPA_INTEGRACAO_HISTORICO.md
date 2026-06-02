# 🗺️ MAPA DE INTEGRAÇÃO - Histórico nas 15 ferramentas

Guia passo a passo para adicionar HistoryButton + histórico em cada ferramenta.

---

## 1️⃣ CONSOLIDADOR

**Arquivo**: `src/gui/pages/tools/consolidador_page.py`

```python
# No import section, adicionar:
from src.gui.components.history_button import HistoryButton

# Em _create_content(), após self.action_btn:
history_btn = HistoryButton(content, "consolidador", "Consolidador")
history_btn.pack(fill="x", padx=20, pady=10)

# Em _worker(), após salvar arquivo:
self.execution.register_generated_file(output_path)

# Em complete():
self.execution.complete({"arquivos": count, "saida": "arquivo.xlsx"})
```

---

## 2️⃣ CATEGORIZADOR

**Arquivo**: `src/gui/pages/tools/categorizador_page.py`

```python
# No import section, adicionar:
from src.gui.components.history_button import HistoryButton

# Em _create_content(), após botão principal:
history_btn = HistoryButton(content, "categorizador", "Categorizador")
history_btn.pack(fill="x", padx=20, pady=10)

# Em _worker(), após processar:
self.execution.register_generated_file(result_file)

# Em complete():
self.execution.complete({"categorias": cat_count, "registros": row_count})
```

---

## 3️⃣ MINERADOR

**Arquivo**: `src/gui/pages/tools/minerador_page.py`

```python
# No import section, adicionar:
from src.gui.components.history_button import HistoryButton

# Em _create_content(), após botão de minerar:
history_btn = HistoryButton(content, "minerador", "Minerador de Preços")
history_btn.pack(fill="x", padx=20, pady=10)

# Em _worker(), ao salvar resultados:
self.execution.register_generated_file(prices_file)

# Em complete():
self.execution.complete({"produtos": product_count, "precos": price_count})
```

---

## 4️⃣ ORÇAMENTOS

**Arquivo**: `src/gui/pages/tools/orcamentos_page.py`

```python
# No import section, adicionar:
from src.gui.components.history_button import HistoryButton

# Em _create_content(), após botão gerar:
history_btn = HistoryButton(content, "orcamentos", "Orçamentos Automáticos")
history_btn.pack(fill="x", padx=20, pady=10)

# Em _worker(), ao salvar PDFs:
self.execution.register_generated_file(pdf_file)

# Em complete():
self.execution.complete({"pdfs_gerados": pdf_count})
```

---

## 5️⃣ CONCILIADOR

**Arquivo**: `src/gui/pages/tools/conciliador_page.py`

```python
# No import section, adicionar:
from src.gui.components.history_button import HistoryButton

# Em _create_content(), após botão conciliar:
history_btn = HistoryButton(content, "conciliador", "Conciliador Pro")
history_btn.pack(fill="x", padx=20, pady=10)

# Em _worker(), ao salvar resultado:
self.execution.register_generated_file(reconciled_file)

# Em complete():
self.execution.complete({"conciliados": count, "divergencias": divs})
```

---

## 6️⃣ VALIDADOR DE LINKS

**Arquivo**: `src/gui/pages/tools/validador_links_page.py`

```python
# No import section, adicionar:
from src.gui.components.history_button import HistoryButton

# Em _create_content(), após botão validar:
history_btn = HistoryButton(content, "validador_links", "Validador de Links")
history_btn.pack(fill="x", padx=20, pady=10)

# Em _worker(), ao salvar relatório:
self.execution.register_generated_file(report_file)

# Em complete():
self.execution.complete({"links_testados": count, "ativos": active})
```

---

## 7️⃣ EXTRATOR DE REVIEWS

**Arquivo**: `src/gui/pages/tools/extrator_reviews_page.py`

```python
# No import section, adicionar:
from src.gui.components.history_button import HistoryButton

# Em _create_content(), após botão extrair:
history_btn = HistoryButton(content, "extrator_reviews", "Extrator de Reviews")
history_btn.pack(fill="x", padx=20, pady=10)

# Em _worker(), ao salvar dados:
self.execution.register_generated_file(reviews_file)

# Em complete():
self.execution.complete({"reviews": count, "sentimento": sentiment_data})
```

---

## 8️⃣ CALCULADORA DE LUCRATIVIDADE

**Arquivo**: `src/gui/pages/tools/calculadora_lucratividade_page.py`

```python
# No import section, adicionar:
from src.gui.components.history_button import HistoryButton

# Em _create_content(), após botão calcular:
history_btn = HistoryButton(content, "calculadora_lucratividade", "Calculadora de Lucratividade")
history_btn.pack(fill="x", padx=20, pady=10)

# Em _worker(), ao salvar análise:
self.execution.register_generated_file(analysis_file)

# Em complete():
self.execution.complete({"margem_media": margin, "oportunidades": opps})
```

---

## 9️⃣ ANALISTA DE TENDÊNCIAS

**Arquivo**: `src/gui/pages/tools/analista_tendencias_page.py`

```python
# No import section, adicionar:
from src.gui.components.history_button import HistoryButton

# Em _create_content(), após botão analisar:
history_btn = HistoryButton(content, "analista_tendencias", "Analista de Tendências")
history_btn.pack(fill="x", padx=20, pady=10)

# Em _worker(), ao salvar tendências:
self.execution.register_generated_file(trends_file)

# Em complete():
self.execution.complete({"tendencias": count, "score": score})
```

---

## 🔟 DATA SANITIZER

**Arquivo**: `src/gui/pages/tools/data_sanitizer_page.py`

```python
# No import section, adicionar:
from src.gui.components.history_button import HistoryButton

# Em _create_content(), após botão limpar:
history_btn = HistoryButton(content, "data_sanitizer", "Data Sanitizer")
history_btn.pack(fill="x", padx=20, pady=10)

# Em _worker(), ao salvar dados limpos:
self.execution.register_generated_file(clean_file)

# Em complete():
self.execution.complete({"registros_limpos": count, "erros_corrigidos": errors})
```

---

## 1️⃣1️⃣ CONVERSOR OCR

**Arquivo**: `src/gui/pages/tools/conversor_ocr_page.py`

```python
# No import section, adicionar:
from src.gui.components.history_button import HistoryButton

# Em _create_content(), após botão converter:
history_btn = HistoryButton(content, "conversor_ocr", "Conversor OCR Premium")
history_btn.pack(fill="x", padx=20, pady=10)

# Em _worker(), ao salvar texto:
self.execution.register_generated_file(output_file)

# Em complete():
self.execution.complete({"arquivos_convertidos": count, "caracteres": chars})
```

---

## 1️⃣2️⃣ GERADOR DE LAUDOS

**Arquivo**: `src/gui/pages/tools/gerador_laudos_page.py`

```python
# No import section, adicionar:
from src.gui.components.history_button import HistoryButton

# Em _create_content(), após botão gerar:
history_btn = HistoryButton(content, "gerador_laudos", "Gerador de Laudos")
history_btn.pack(fill="x", padx=20, pady=10)

# Em _worker(), ao salvar laudos:
self.execution.register_generated_file(laudo_file)

# Em complete():
self.execution.complete({"laudos": count})
```

---

## 1️⃣3️⃣ COMISSÕES

**Arquivo**: `src/gui/pages/tools/comissoes_page.py`

```python
# No import section, adicionar:
from src.gui.components.history_button import HistoryButton

# Em _create_content(), após botão calcular:
history_btn = HistoryButton(content, "comissoes", "Comissões")
history_btn.pack(fill="x", padx=20, pady=10)

# Em _worker(), ao salvar relatório:
self.execution.register_generated_file(report_file)

# Em complete():
self.execution.complete({"comissoes": total, "vendedores": count})
```

---

## ⚡ Template Genérico

```python
# 1. Import
from src.gui.components.history_button import HistoryButton

# 2. Em _create_content()
history_btn = HistoryButton(content, "TOOL_KEY", "Tool Display Name")
history_btn.pack(fill="x", padx=20, pady=10)

# 3. Em _worker(), após gerar arquivo
self.execution.register_generated_file(output_file)

# 4. Em complete()
self.execution.complete({"key": value, "key2": value2})
```

---

## ✅ Checklist de Integração

Para cada ferramenta, marque:

- [ ] Importou HistoryButton
- [ ] Adicionou botão em \_create_content()
- [ ] Chamou register_generated_file() em \_worker()
- [ ] Completou com result_data em complete()
- [ ] Testou abrir histórico
- [ ] Testou ver execução no histórico
- [ ] Testou download de arquivo

---

## Status de Integração

| Ferramenta          | Import | Button | Register | Complete | Testado |
| ------------------- | ------ | ------ | -------- | -------- | ------- |
| Consolidador        | ⏳     | ⏳     | ⏳       | ⏳       | ⏳      |
| Categorizador       | ⏳     | ⏳     | ⏳       | ⏳       | ⏳      |
| Minerador           | ⏳     | ⏳     | ⏳       | ⏳       | ⏳      |
| Orçamentos          | ⏳     | ⏳     | ⏳       | ⏳       | ⏳      |
| Conciliador         | ⏳     | ⏳     | ⏳       | ⏳       | ⏳      |
| Validador Links     | ⏳     | ⏳     | ⏳       | ⏳       | ⏳      |
| Extrator Reviews    | ⏳     | ⏳     | ⏳       | ⏳       | ⏳      |
| Calc Lucratividade  | ⏳     | ⏳     | ⏳       | ⏳       | ⏳      |
| Analista Tendências | ⏳     | ⏳     | ⏳       | ⏳       | ⏳      |
| Data Sanitizer      | ⏳     | ⏳     | ⏳       | ⏳       | ⏳      |
| Conversor OCR       | ⏳     | ⏳     | ⏳       | ⏳       | ⏳      |
| Gerador Laudos      | ⏳     | ⏳     | ⏳       | ⏳       | ⏳      |
| Comissões           | ⏳     | ⏳     | ⏳       | ⏳       | ⏳      |

---

## 💡 Dicas

- Use Ctrl+H para buscar/substituir e automatizar imports
- Copie o template genérico e adapte para cada tool
- Teste uma por vez (comece com Consolidador)
- Observe o arquivo sendo salvo em `.execution_history/`

---

## 📞 Dúvidas

Se alguma ferramenta não tiver um local óbvio para adicionar o botão ou registrar arquivo, verifique:

1. Onde fica o botão de ação principal?
2. Onde o arquivo é salvo/processado?
3. Qual é a chave/nome único da ferramenta?

Depois aplique o template genérico.
