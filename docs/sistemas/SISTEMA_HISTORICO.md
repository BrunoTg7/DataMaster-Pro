# 📋 Sistema de Histórico de Execução

## Visão Geral

Sistema profissional para rastreamento de execuções de ferramentas, armazenando:

- ✅ Resultados de cada execução
- 📁 Arquivos gerados pela ferramenta
- 📝 Logs completos
- ⏱️ Duração da execução
- 📊 Estatísticas por ferramenta
- ↩️ Download de arquivos gerados

**Dados salvos em**: `.execution_history/` (local, sem Supabase)

---

## Arquitetura

### 1. ExecutionHistoryManager (`src/core/tasks/execution_history_manager.py`)

Gerenciador singleton que:

- Persiste histórico em JSON local
- Organiza por ferramenta
- Permite buscar, filtrar e limpar histórico
- Calcula estatísticas

### 2. ExecutionHistoryRecord

Modelo de dados para cada execução:

```python
{
  "task_id": "uuid-123",
  "tool_name": "consolidador",
  "tool_display_name": "Consolidador",
  "status": "completed",
  "result_data": { "rows": 1000, "output": "arquivo.xlsx" },
  "generated_files": [
    {
      "path": "/full/path/arquivo.xlsx",
      "name": "arquivo.xlsx",
      "size": 524288,
      "created_at": "2024-05-18T10:30:00"
    }
  ],
  "logs": ["Log 1", "Log 2", ...],
  "duration_seconds": 5.23,
  "completed_at": "2024-05-18T10:30:05",
  "error_message": null
}
```

### 3. ExecutionHelper (Estendido)

Novos métodos:

```python
execution.register_generated_file(file_path)  # Registra arquivo
execution.get_history(limit=50)               # Obtém histórico
execution.get_statistics()                    # Obtém stats
```

### 4. ExecutionHistoryModal (`src/gui/components/execution_history_modal.py`)

UI Modal com:

- 📊 Estatísticas gerais
- 📜 Lista de execuções
- 🔍 Detalhes de cada execução
- ⬇️ Download de arquivos
- 📝 Visualização de logs

### 5. HistoryButton (`src/gui/components/history_button.py`)

Botão customizado para abrir histórico em qualquer ferramenta

---

## Como Usar

### Passo 1: Registrar Arquivo Gerado

**Em seu worker/função que gera arquivo:**

```python
def _worker(self):
    try:
        # ... processamento ...

        # Gerar arquivo de saída
        output_file = "/path/to/resultado.xlsx"
        self.ferramenta.salvar_arquivo(output_file)

        # REGISTRAR NO HISTÓRICO ✨
        self.execution.register_generated_file(output_file)

        # Finalizar
        self.execution.complete({
            "rows_processed": 1000,
            "output_file": "resultado.xlsx"
        })
    except Exception as e:
        self.execution.fail(str(e))
```

### Passo 2: Adicionar Botão de Histórico na UI

**Em sua página de ferramenta:**

```python
from src.gui.components.history_button import HistoryButton

class MeuToolPage(ToolPage):
    def _create_content(self):
        content = ctk.CTkScrollableFrame(self)

        # ... resto da UI ...

        # ADICIONAR BOTÃO DE HISTÓRICO
        history_btn = HistoryButton(
            content,
            tool_name="minha_ferramenta",
            tool_display_name="Minha Ferramenta"
        )
        history_btn.pack(fill="x", padx=20, pady=10)
```

### Passo 3: Acessar Histórico Programaticamente

```python
# Obter histórico
history = self.execution.get_history(limit=10)
for record in history:
    print(f"Execução: {record.completed_at}")
    print(f"Status: {record.status}")
    print(f"Arquivos: {len(record.generated_files)}")
    print(f"Duração: {record.duration_seconds}s")

# Obter estatísticas
stats = self.execution.get_statistics()
print(f"Total: {stats['total_executions']}")
print(f"Taxa sucesso: {stats['success_rate']}%")
print(f"Tempo médio: {stats['average_duration_seconds']}s")
```

---

## Fluxo Automático

Todo o histórico é **salvo automaticamente** quando você usa ExecutionHelper:

```python
# Criar tarefa (começa a registrar)
task_id, error = self.execution.create_task()

# ... trabalho ...

# Finalizar (automaticamente salva no histórico)
self.execution.complete({...})  # ✅ Salva automaticamente
# OU
self.execution.fail("erro")     # ✅ Salva automaticamente
```

**O que é salvo automaticamente:**

- ✅ Status de execução
- ✅ Resultado (result_data)
- ✅ Logs
- ✅ Duração
- ✅ Hora de conclusão
- ✅ Mensagem de erro (se houver)

---

## Estrutura de Arquivos

```
.execution_history/
├── index.json                 # Índice global
├── consolidador/              # Por ferramenta
│   ├── uuid-1.json           # Execução 1
│   ├── uuid-2.json
│   └── uuid-3.json
├── minerador/
│   ├── uuid-1.json
│   └── uuid-2.json
└── orcamentos/
    ├── uuid-1.json
    └── uuid-2.json

index.json:
{
  "by_tool": {
    "consolidador": [
      { "task_id": "uuid-1", "completed_at": "...", "status": "completed" },
      ...
    ]
  },
  "all_tasks": [...]
}
```

---

## API Completa

### ExecutionHistoryManager

```python
from src.core.tasks.execution_history_manager import get_history_manager

manager = get_history_manager()

# Salvar execução
manager.save_record(record)

# Obter histórico
manager.get_history_by_tool("consolidador", limit=50)
manager.get_all_history(limit=100)

# Obter registro específico
manager.get_record("consolidador", task_id)

# Registrar arquivo
manager.add_generated_file("consolidador", task_id, "/path/file.xlsx")

# Baixar arquivo
manager.download_file("consolidador", task_id, "file.xlsx", "/dest/path.xlsx")

# Estatísticas
manager.get_tool_statistics("consolidador")

# Limpar histórico
manager.clear_history("consolidador")  # Por ferramenta
manager.clear_history()                # Todos
```

### ExecutionHelper

```python
# Registrar arquivo gerado
execution.register_generated_file("/path/to/file.xlsx")

# Acessar histórico
execution.get_history(limit=20)

# Obter estatísticas
execution.get_statistics()

# Salvar manualmente (chamado automaticamente por complete/fail)
execution.save_to_history(
    status="completed",
    result_data={"rows": 1000},
    generated_files=["/path/file.xlsx"],
    logs=["log1", "log2"]
)
```

---

## Exemplo Completo: Consolidador com Histórico

```python
class ConsolidadorPage(ToolPage):
    def __init__(self, master, on_back, execution_tracker=None, user_id=None):
        # ... setup ...
        self.execution = ExecutionHelper("consolidador", "Consolidador", user_id)
        super().__init__(...)

    def _create_content(self):
        content = ctk.CTkScrollableFrame(self)
        content.pack(...)

        # ... interface ...

        # Adicionar botão de histórico
        from src.gui.components.history_button import HistoryButton
        history_btn = HistoryButton(
            content,
            tool_name="consolidador",
            tool_display_name="Consolidador"
        )
        history_btn.pack(fill="x", padx=20, pady=10)

    def _run_consolidate(self):
        # Criar tarefa
        task_id, error = self.execution.create_task()
        if error:
            messagebox.showerror("Erro", error)
            return

        # Lançar worker
        threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self):
        try:
            self.execution.add_log("Iniciando consolidação...")

            output_file = "/path/consolidated.xlsx"

            for i, arquivo in enumerate(self.uploaded_files):
                if self.execution.is_cancelled():
                    return

                self.consolidador.processar(arquivo)

                percent = int((i + 1) / len(self.uploaded_files) * 100)
                self.execution.update_progress(
                    percent,
                    f"Processado {i+1}/{len(self.uploaded_files)}"
                )

            # Salvar resultado
            self.consolidador.salvar_para(output_file)

            # REGISTRAR ARQUIVO ✨
            self.execution.register_generated_file(output_file)

            # Finalizar (salva automaticamente no histórico)
            self.execution.complete({
                "arquivos_consolidados": len(self.uploaded_files),
                "arquivo_saida": "consolidated.xlsx"
            })

        except Exception as e:
            self.execution.fail(str(e))
```

---

## UI Modal de Histórico

Mostra em tempo real:

- 📊 **Estatísticas**: Total, taxa sucesso, tempo médio, arquivos
- 📜 **Lista**: Todas as execuções (últimas 100)
- 🔍 **Detalhes**: Status, duração, resultados, logs
- 📁 **Arquivos**: Nomes, tamanhos, botão download
- 📝 **Logs**: Últimas 20 linhas

**Cores:**

- 🟢 Completado: Verde
- 🔴 Falhou: Vermelho
- 🟠 Cancelado: Laranja
- 🟡 Executando: Azul

---

## Benefícios

✅ **Rastreabilidade completa** - Cada execução registrada  
✅ **Recuperação de arquivos** - Download direto da UI  
✅ **Análise de performance** - Tempo médio, taxa sucesso  
✅ **Debugging** - Acesso a logs completos  
✅ **Sem servidor** - Tudo local em JSON  
✅ **Thread-safe** - Sincronização com locks  
✅ **Escalável** - Suporta muitos registros

---

## Limpeza de Histórico

```python
manager = get_history_manager()

# Limpar histórico de ferramenta específica
deleted = manager.clear_history("consolidador")

# Limpar todo histórico
deleted = manager.clear_history()
```

---

## Próximas Melhorias (Opcional)

- [ ] Exportar histórico para CSV/Excel
- [ ] Filtrar por data/status
- [ ] Comparar resultados de 2 execuções
- [ ] Agendamento com histórico
- [ ] Sincronizar com Supabase (opcional)
- [ ] Gráficos de performance
- [ ] Alertas automáticos

---

## Troubleshooting

**P: Histórico não está sendo salvo**  
R: Verifique que `complete()` ou `fail()` é chamado ao final do worker

**P: Arquivos não aparecem no histórico**  
R: Use `register_generated_file()` ANTES de chamar `complete()`

**P: Modal não abre**  
R: Verifique que HistoryButton foi adicionado ao layout e tk.mainloop() está rodando

**P: Erro ao baixar arquivo**  
R: Verifique que o arquivo ainda existe no caminho original
