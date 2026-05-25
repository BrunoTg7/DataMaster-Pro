# Sistema de Execução Paralela e Persistente - Guia de Integração

## Overview

O novo sistema permite que ferramentas executem tarefas em paralelo com persistência automática de estado. Quando o usuário sai e volta da página, o progresso é mantido.

## Arquitetura

```
┌─────────────────────────────────────────────┐
│         ExecutionManager (Singleton)        │
│  - Gerencia até 2 tarefas simultâneas       │
│  - Persiste em .execution_state.json        │
│  - Dispara callbacks de atualização         │
└─────────────────────────────────────────────┘
         ↓                          ↓
    ┌────────────┐         ┌──────────────┐
    │ ToolPage   │         │ExecutionPanel│
    │(local UI)  │         │(Flutuante UI)│
    └────────────┘         └──────────────┘
         ↓
  ┌──────────────────┐
  │ ExecutionHelper  │
  │ (API Simples)    │
  └──────────────────┘
```

## Como Usar em uma Ferramenta

### 1. Importar e Inicializar

```python
from src.gui.helpers.execution_helper import ExecutionHelper

class MinhaFerramentaPage(ToolPage):
    def __init__(self, master, on_back, **kwargs):
        super().__init__(master, "minha_ferramenta", "Minha Ferramenta", on_back, **kwargs)

        # Criar helper de execução
        self.execution = ExecutionHelper(
            tool_key="minha_ferramenta",
            tool_display_name="Minha Ferramenta",
            user_id=self.user_id
        )
```

### 2. Criar uma Tarefa ao Executar

```python
def _execute_action(self):
    # Criar tarefa
    task_id, error = self.execution.create_task(
        on_progress=self._on_progress,
        on_log=self._on_log
    )

    if error:
        messagebox.showerror("Erro", error)
        return

    # Lançar em thread
    thread = threading.Thread(
        target=self._execute_worker,
        daemon=True
    )
    thread.start()

def _execute_worker(self):
    try:
        self.execution.add_log("Iniciando processamento...")

        # Processar dados
        for i in range(100):
            # Verificar se cancelada
            if self.execution.is_cancelled():
                self.execution.add_log("Cancelado pelo usuário")
                return

            # Atualizar progresso
            self.execution.update_progress(i + 1, f"Processando {i+1}/100...")
            self.execution.add_log(f"Item {i+1} processado")
            time.sleep(0.1)  # Simular processamento

        # Sucesso
        self.execution.add_log("✓ Concluído com sucesso!")
        self.execution.complete({
            "total_items": 100,
            "output_file": "/path/to/output"
        })

    except Exception as e:
        self.execution.fail(str(e))
        self.execution.add_log(f"✕ Erro: {e}")
```

### 3. Callbacks para Atualizar UI Local

```python
def _on_progress(self, percent: int, message: str):
    """Atualiza UI local da ferramenta"""
    self.after(0, lambda: self.progress_bar.set(percent / 100))
    self.after(0, lambda: self.status_label.configure(text=message))

def _on_log(self, message: str):
    """Atualiza log local"""
    self.after(0, lambda: self._add_log_entry(message))
```

## Persistência Automática

O estado é automaticamente persistido em:

```
c:\Users\Public\projetos\ferramente excel\.execution_state.json
```

Isso permite:

- ✓ Ver progresso mesmo saindo e voltando da página
- ✓ Recuperar histórico de execuções
- ✓ Gerenciar múltiplas tarefas paralelas

## Painel Flutuante

O `ExecutionFloatingPanel` mostra:

- Nome da ferramenta
- Barra de progresso
- Status (Aguardando / Em Execução / Concluído / Erro)
- Últimas 3 linhas de log
- Botão para cancelar

### Características:

- ✓ Atualiza em tempo real (500ms)
- ✓ Pode ser minimizado/expandido
- ✓ Posicionado no canto superior direito
- ✓ Segue a navegação entre páginas

## Exemplo Completo (Consolidador)

```python
class ConsolidadorPage(ToolPage):
    def _run_consolidation(self):
        # Criar tarefa
        task_id, error = self.execution.create_task(
            on_progress=self._update_progress,
            on_log=self._log_message
        )

        if error:
            messagebox.showerror("Erro", error)
            return

        # Executar em thread
        thread = threading.Thread(
            target=self._consolidation_worker,
            args=(self.files, self.config),
            daemon=True
        )
        thread.start()

    def _consolidation_worker(self, files, config):
        try:
            self.execution.add_log(f"Consolidando {len(files)} arquivos...")

            for idx, file in enumerate(files):
                if self.execution.is_cancelled():
                    return

                percent = int((idx / len(files)) * 100)
                self.execution.update_progress(
                    percent,
                    f"Processando: {os.path.basename(file)}"
                )
                self.execution.add_log(f"✓ {os.path.basename(file)}")

                # Processar arquivo
                # ... lógica ...

            self.execution.complete({
                "output_path": output_file,
                "rows_processed": total_rows
            })
        except Exception as e:
            self.execution.fail(str(e))
```

## Limitações Propostas

1. **Máximo 2 tarefas simultâneas** (configurável)
2. **Mesma ferramenta não pode executar 2x** (evita conflitos)
3. **Tarefas são persistidas por 7 dias** (limpeza automática)

## Métodos do ExecutionHelper

```python
# Criar e executar
task_id, error = execution.create_task(on_progress, on_log)

# Atualizar progresso
execution.update_progress(percent: int, message: str)

# Adicionar log
execution.add_log(message: str)

# Marcar como concluído
execution.complete(result_data: Dict)

# Marcar como falhou
execution.fail(error: str)

# Cancelar
execution.cancel()

# Verificar se foi cancelada
is_cancelled = execution.is_cancelled()

# Obter duração
duration = execution.get_duration_seconds()

# Obter objeto da tarefa
task = execution.get_task()
```

## Diagrama de Estados

```
    PENDING
       ↓
    RUNNING
       ├─→ COMPLETED
       ├─→ FAILED
       └─→ CANCELLED
```

## Sincronização com Web

O `ExecutionManager.export_tasks_for_web()` pode exportar tarefas para sincronização com a API web, mantendo histórico centralizado.

---

## Próximas Etapas

1. Integrar ExecutionManager em todas as ferramentas
2. Adicionar persistência em Supabase
3. Implementar real-time updates via Realtime DB
4. Criar dashboard web de execuções
