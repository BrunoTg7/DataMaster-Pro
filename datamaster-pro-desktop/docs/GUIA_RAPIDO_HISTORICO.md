# 🚀 Guia Rápido - Adicionar Histórico em uma Ferramenta

## 3 Passos Simples

### Passo 1: Importar Componentes

```python
# Em seu arquivo de ferramenta (ex: consolidador_page.py)

from src.gui.components.history_button import HistoryButton
```

### Passo 2: Adicionar Botão na UI

```python
def _create_content(self):
    content = ctk.CTkScrollableFrame(self)

    # ... resto da interface ...

    # ADICIONAR DEPOIS DO BOTÃO PRINCIPAL
    history_btn = HistoryButton(
        content,
        tool_name="consolidador",           # Chave da ferramenta
        tool_display_name="Consolidador"    # Nome exibição
    )
    history_btn.pack(fill="x", padx=20, pady=10)
```

### Passo 3: Registrar Arquivos Gerados

```python
def _worker(self):
    try:
        # ... processamento ...

        # Salvar arquivo de resultado
        output_file = "/path/to/resultado.xlsx"
        self.ferramenta.salvar_arquivo(output_file)

        # REGISTRAR ARQUIVO NO HISTÓRICO
        self.execution.register_generated_file(output_file)

        # Finalizar (salva automaticamente)
        self.execution.complete({
            "arquivos": 5,
            "linhas": 1000,
            "arquivo_saida": "resultado.xlsx"
        })

    except Exception as e:
        self.execution.fail(str(e))
```

---

## Template Completo

```python
import customtkinter as ctk
from tkinter import messagebox
import threading
import os

from src.gui.pages.tool_page import ToolPage
from src.gui.helpers.execution_helper import ExecutionHelper
from src.gui.components.history_button import HistoryButton


class MeuToolPage(ToolPage):
    def __init__(self, master, on_back, execution_tracker=None, user_id=None):
        self.ferramenta = MeuTool()
        self.execution = ExecutionHelper("meu_tool", "Meu Tool", user_id)
        super().__init__(master, "meu_tool", "Meu Tool", on_back, execution_tracker, user_id)

    def _create_content(self):
        content = ctk.CTkScrollableFrame(self)
        content.pack(fill="both", expand=True)

        # Interface
        titulo = ctk.CTkLabel(
            content,
            text="Meu Tool",
            font=("Segoe UI", 16, "bold")
        )
        titulo.pack(pady=20)

        # Botão de execução
        run_btn = ctk.CTkButton(
            content,
            text="Executar",
            command=self._run
        )
        run_btn.pack(pady=10)

        # BOTÃO DE HISTÓRICO ✨
        history_btn = HistoryButton(
            content,
            tool_name="meu_tool",
            tool_display_name="Meu Tool"
        )
        history_btn.pack(fill="x", padx=20, pady=10)

        # Label de status
        self.status_label = ctk.CTkLabel(
            content,
            text="Pronto",
            text_color="#a0a0a0"
        )
        self.status_label.pack(pady=10)

    def _run(self):
        # Criar tarefa
        task_id, error = self.execution.create_task()
        if error:
            messagebox.showerror("Erro", error)
            return

        # Lançar worker
        threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self):
        try:
            self.execution.add_log("Iniciando...")

            # Seu processamento
            resultado = self.ferramenta.processar()

            self.execution.update_progress(50, "50% processado")

            # Gerar arquivo
            output_file = f"{os.path.expanduser('~')}/resultado.xlsx"
            self.ferramenta.salvar_para(output_file)

            # REGISTRAR ARQUIVO ✨
            self.execution.register_generated_file(output_file)

            self.execution.update_progress(100, "Concluído!")

            # Finalizar
            self.execution.complete({
                "status": "sucesso",
                "arquivo": "resultado.xlsx"
            })

        except Exception as e:
            self.execution.fail(str(e))
```

---

## Checklist de Integração

- [ ] Importou `ExecutionHelper` em `__init__`
- [ ] Importou `HistoryButton` em `_create_content`
- [ ] Adicionou `self.execution = ExecutionHelper(...)` em `__init__`
- [ ] Adicionou botão de histórico na UI
- [ ] Chamou `register_generated_file()` para cada arquivo gerado
- [ ] Chamou `complete()` ou `fail()` ao terminar worker
- [ ] Testou abrir histórico
- [ ] Testou download de arquivo

---

## Onde Adicionar em Cada Ferramenta

| Ferramenta           | Arquivo                 | Onde                       | Status |
| -------------------- | ----------------------- | -------------------------- | ------ |
| Consolidador         | `consolidador_page.py`  | Depois botão "Consolidar"  | ⏳     |
| Categorizador        | `categorizador_page.py` | Depois botão "Categorizar" | ⏳     |
| Minerador            | `minerador_page.py`     | Depois botão "Minerar"     | ⏳     |
| Orçamentos           | `orcamentos_page.py`    | Depois botão "Gerar"       | ⏳     |
| Conciliador          | `conciliador_page.py`   | Depois botão "Conciliar"   | ⏳     |
| E todas as outras... | ...                     | Idem                       | ⏳     |

---

## Exemplo: Consolidador Completo

**Antes:**

```python
class ConsolidadorPage(ToolPage):
    def _create_content(self):
        # ... UI ...
        self.action_btn = self._create_action_button(
            content,
            "Consolidar Arquivos",
            self._run_consolidate
        )
```

**Depois:**

```python
from src.gui.components.history_button import HistoryButton

class ConsolidadorPage(ToolPage):
    def _create_content(self):
        # ... UI ...
        self.action_btn = self._create_action_button(
            content,
            "Consolidar Arquivos",
            self._run_consolidate
        )

        # ADICIONAR HISTÓRICO ✨
        history_btn = HistoryButton(
            content,
            tool_name="consolidador",
            tool_display_name="Consolidador"
        )
        history_btn.pack(fill="x", padx=20, pady=10)
```

---

## Arquivos Necessários

Já criados ✅:

- `src/core/tasks/execution_history_manager.py` - Gerenciador
- `src/gui/components/execution_history_modal.py` - Modal UI
- `src/gui/components/history_button.py` - Botão
- `src/gui/helpers/execution_helper.py` - Estendido com histórico

---

## Teste Rápido

```python
# Em qualquer lugar do seu código

from src.core.tasks.execution_history_manager import get_history_manager

manager = get_history_manager()

# Ver histórico do consolidador
history = manager.get_history_by_tool("consolidador")
for record in history:
    print(f"ID: {record.task_id}")
    print(f"Status: {record.status}")
    print(f"Arquivos: {len(record.generated_files)}")
    print(f"Duração: {record.duration_seconds}s")
    print()

# Ver estatísticas
stats = manager.get_tool_statistics("consolidador")
print(f"Total: {stats['total_executions']}")
print(f"Taxa sucesso: {stats['success_rate']}%")
```

---

## Dúvidas Frequentes

**P: Preciso modificar todas as ferramentas?**  
R: Não! Cada ferramenta é independente. Adicione quando quiser.

**P: O histórico é permanente?**  
R: Sim, salvo em `.execution_history/` localmente. Limpe com `clear_history()`.

**P: Posso sincronizar com Supabase depois?**  
R: Sim! A estrutura permite adicionar sync depois sem mudar código.

**P: Qual é o tamanho limite do histórico?**  
R: Nenhum limite, mas está em JSON. Para muita data, considere arquivar.

---

## Próximas Implementações

1. Integrar com as 15 ferramentas
2. Testar modal com histórico real
3. Testar download de arquivos
4. Adicionar filtros no histórico
5. Exportar histórico para CSV
