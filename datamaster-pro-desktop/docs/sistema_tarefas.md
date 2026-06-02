# Sistema de Tarefas — DataMaster Pro

## Visão Geral

O sistema de tarefas gerencia **execução, monitoramento, histórico e sincronização** de todas as operações realizadas pelas ferramentas do DataMaster Pro. Ele foi unificado a partir de três motores paralelos antigos (`task_manager`, `global_executor`, `execution_manager`) em um único motor central chamado `TaskExecutor`.

```
┌─────────────────────────────────────────────────────┐
│                   APLICAÇÃO                          │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │  Tool Pages  │  │  Scheduler   │  │    App     │ │
│  │  (13 tools)  │  │  Background  │  │   Main     │ │
│  └──────┬───────┘  └──────┬───────┘  └─────┬──────┘ │
│         │                 │                  │        │
│  ┌──────▼─────────────────▼──────────────────▼────┐  │
│  │              TaskExecutor (singleton)           │  │
│  │  submit() · create_task() · complete_task()     │  │
│  │  update_progress() · fail_task() · cancel()     │  │
│  └──────┬──────────────────┬──────────────────┬────┘  │
│         │                  │                  │        │
│  ┌──────▼──────┐  ┌───────▼───────┐  ┌──────▼──────┐ │
│  │  Storage    │  │   TaskBar     │  │  Execution  │ │
│  │  Manager    │  │   (UI Overlay)│  │  History    │ │
│  │  (SQLite)   │  │               │  │  Manager    │ │
│  └─────────────┘  └───────────────┘  └─────────────┘ │
│                                                       │
│  ┌─────────────────────────────────────────────────┐  │
│  │            SyncManager (Supabase)                │  │
│  │  Sincroniza execuções e tarefas agendadas        │  │
│  └─────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

---

## 1. TaskExecutor — Motor Central

**Arquivo:** `src/core/tasks/task_executor.py`
**Singleton:** `task_executor` (alias `task_manager`)

### 1.1 O que faz

Gerencia **todo o ciclo de vida** de uma tarefa:
criação → execução em thread → atualização de progresso → conclusão/erro/cancelamento → notificação → persistência.

### 1.2 Estruturas auxiliares

| Classe | Descrição |
|--------|-----------|
| `TaskStatus` | Constantes: `PENDING`, `RUNNING`, `COMPLETED`, `FAILED`, `CANCELLED`, `INTERRUPTED` |
| `TaskInfo` | Dados internos de cada tarefa em memória (id, nome, status, progresso, logs, thread, evento de cancelamento) |

### 1.3 Métodos Públicos

#### Submissão e Criação

| Método | Descrição |
|--------|-----------|
| `submit(tool_name, tool_display_name, execute_func, on_complete, user_id)` | Submete **qualquer função arbitrária** para executar em background. Cria TaskInfo, salva no SQLite, dispara thread daemon. Retorna `(task_id, None)` ou `(None, erro)`. |
| `create_task(tool_name, input_params, progress_callback, log_callback, auto_execute, tool_display_name)` | Cria tarefa para **ferramenta registrada** (via `register_tool`). Se `auto_execute=True`, já inicia execução automática chamando o método `execute()` ou `run()` da classe da ferramenta. |

#### Progresso e Ciclo de Vida

| Método | Descrição |
|--------|-----------|
| `update_progress(task_id, percent, message)` | Atualiza percentual [0-100] e mensagem de progresso. |
| `add_log(task_id, message)` | Adiciona mensagem com timestamp ao log da tarefa (mantém últimas 100). |
| `complete_task(task_id, output_path, rows, hours)` | Marca como COMPLETED, salva metadados, envia notificação desktop. |
| `fail_task(task_id, error)` | Marca como FAILED com mensagem de erro. |
| `cancel_task(task_id)` | Ativa evento de cancelamento (a thread percebe e para) e marca como CANCELLED. |
| `is_cancelled(task_id)` | Verifica se evento de cancelamento foi disparado. |

#### Consulta

| Método | Descrição |
|--------|-----------|
| `get_tasks(status_filter)` | Retorna lista de tasks como dicts (opcionalmente filtrado por status). |
| `get_task(task_id)` | Retorna dict de uma task específica. |
| `get_active_tasks()` | Retorna tasks com status PENDING ou RUNNING. |
| `get_running_count()` | Contagem de tasks ativas. |

#### Recuperação e Restart

| Método | Descrição |
|--------|-----------|
| `recover_interrupted_tasks()` | Chamado na inicialização do app. Marca tasks PENDING/RUNNING como INTERRUPTED (app foi fechado). |
| `restart_task(task_id)` | Só para tasks INTERRUPTED. Cria nova task com mesmos parâmetros (novo ID). |
| `requeue_task(task_id)` | Para tasks INTERRUPTED/CANCELLED/FAILED. Reseta status para PENDING com progresso 0. |

#### Manutenção

| Método | Descrição |
|--------|-----------|
| `clear_old_tasks(days=7)` | Remove da memória tasks completadas há mais de N dias. |
| `clear_completed_tasks()` | Remove todas as tasks COMPLETED/FAILED/CANCELLED da memória. |
| `export_tasks_for_web(user_id)` | Exporta tasks como dicts para consumo externo/web. |

### 1.4 Controle de Concorrência

- Usuários **PRO**: até **2** tarefas simultâneas
- Usuários **grátis**: até **1** tarefa simultânea
- Mesma ferramenta não pode ter mais de uma task ativa ao mesmo tempo

### 1.5 Callbacks de Notificação

| Método | Quando é chamado | Quem usa |
|--------|------------------|----------|
| `on_new_task(callback)` | Toda vez que uma nova task é criada | `TaskBar` (para se mostrar imediatamente) |
| `register_state_change_callback(callback)` | Quando o estado de alguma task ativa muda | Componentes que precisam reagir a mudanças |

---

## 2. TaskScheduler — Agendador de Tarefas

**Arquivo:** `src/core/task_scheduler.py`
**Singleton:** `get_task_scheduler()`

### 2.1 O que faz

Permite criar tarefas que executam **automaticamente em horários pré-definidos** (diário, semanal, mensal ou cron customizado).

### 2.2 Conexão com TaskExecutor

O `TaskScheduler` usa o `TaskExecutor` para **executar** as tarefas agendadas:

```python
def execute_task(self, task: ScheduledTask) -> bool:
    callback = self._task_callbacks[task.tool_name]
    task_id, error = self._executor.submit(
        tool_name=task.tool_name,
        tool_display_name=f"{task.tool_name} (Agendada)",
        execute_func=lambda: callback(task),
        user_id=task.user_id,
    )
```

Ou seja: uma tarefa agendada vira uma task normal do `TaskExecutor`, ganhando todo o ciclo de vida (progresso, notificações, persistência, etc.).

### 2.3 Polling Automático

- `start_polling(interval_seconds=60)` → inicia thread daemon que verifica a cada N segundos se há tarefas agendadas pendentes
- `stop_polling()` → para a thread

### 2.4 Classes

| Classe | Descrição |
|--------|-----------|
| `ScheduledTask` | Dataclass com `task_id`, `user_id`, `tool_name`, `input_files`, `schedule_frequency`, `cron_expression`, `enabled`, `last_run`, `next_run`, etc. |
| `ScheduleFrequency` | Enum: `DAILY`, `WEEKLY`, `MONTHLY`, `CUSTOM_CRON` |

### 2.5 Métodos

| Método | Descrição |
|--------|-----------|
| `register_task_callback(tool_name, callback)` | Registra função que sabe executar cada ferramenta agendada. |
| `create_task(user_id, tool_name, ...)` | Cria e persiste nova tarefa agendada, calcula `next_run`. |
| `get_tasks_for_user(user_id)` | Retorna tarefas agendadas habilitadas de um usuário. |
| `get_due_tasks(user_id)` | Retorna tarefas agendadas que já deveriam ter executado. |
| `disable_task(task_id)` | Desabilita tarefa agendada. |
| `delete_task(task_id)` | Remove tarefa agendada. |
| `execute_task(task)` | Submete ao TaskExecutor para execução, atualiza last_run/next_run. |

### 2.6 Windows Task Scheduler (Enterprise)

`create_windows_scheduled_task()` gera script Python + cria tarefa real no Windows Task Scheduler para executar **mesmo com o app fechado**.

---

## 3. TaskBar — Overlay Visual de Tarefas

**Arquivo:** `src/gui/components/task_bar.py`

### 3.1 O que faz

Overlay flutuante no canto inferior esquerdo da tela que mostra **todas as tarefas em tempo real**, agrupadas por data, com ícones de status, barra de progresso e botões de cancelar/continuar.

### 3.2 Componentes

| Classe | Descrição |
|--------|-----------|
| `TaskBar(ctk.CTkFrame)` | Overlay principal com lista scrollável de cards |
| `TaskBadge(ctk.CTkLabel)` | Badge pequeno mostrando contagem de tarefas ativas (ex: "2") |

### 3.3 Polling Adaptativo

- **Tarefas ativas:** atualiza a cada **1 segundo**
- **Cooldown (30s após última ativa):** atualiza a cada **2 segundos**
- **Inativo:** atualiza a cada **5 minutos**

O intervalo se ajusta automaticamente para economizar CPU quando não há atividade.

### 3.4 Agrupamento por Data

As tarefas são divididas em três seções:
- **📍 Hoje** — criadas hoje
- **📅 Ontem** — criadas ontem
- **📦 Anteriores** — criadas antes de ontem

### 3.5 Cards de Tarefa

Cada tarefa vira um card com:

| Status | Conteúdo do Card |
|--------|------------------|
| **running** | Barra de progresso + percentual + mensagem |
| **pending** | "⏳ Aguardando..." |
| **completed** | "✅ X linhas processadas" ou "✅ Concluído" |
| **failed** | "❌ Mensagem do erro" |
| **cancelled** | "🚫 Cancelado" |
| **interrupted** | "⚠️ Parou" + botão "▶ Continuar" |

Todos os cards têm o ícone de status + nome da ferramenta no cabeçalho. Tasks ativas (running/pending) têm borda azul e botão ✕ para cancelar.

### 3.6 Otimização de Renderização

- Se o status continua **running**, apenas a barra de progresso e texto são atualizados (sem recriar widgets)
- Se o status **muda**, o corpo do card é destruído e recriado com os widgets adequados
- Cards de tarefas que não existem mais são destruídos

---

## 4. ExecutionHelper — Helper para Tool Pages

**Arquivo:** `src/gui/helpers/execution_helper.py`

### 4.1 O que faz

Classe helper que **cada página de ferramenta** instancia para gerenciar sua tarefa. Simplifica a interação com o `TaskExecutor` e integra com o histórico.

### 4.2 Métodos

| Método | Descrição |
|--------|-----------|
| `__init__(tool_key, tool_display_name, user_id)` | Guarda identificação da ferramenta |
| `create_task(on_progress, on_log)` | Cria task via `TaskExecutor.create_task()` com `auto_execute=False` |
| `update_progress(percent, message)` | Atualiza progresso |
| `add_log(message)` | Adiciona linha de log |
| `complete(result_data, generated_files)` | Marca como concluída E salva no histórico |
| `fail(error)` | Marca como falha E salva no histórico |
| `cancel()` | Cancela tarefa |
| `is_cancelled()` | Verifica se foi cancelada |
| `get_duration_seconds()` | Tempo decorrido desde a criação |
| `get_task()` | Obtém dict da tarefa atual |
| `get_history(limit)` | Obtém histórico da ferramenta |
| `get_statistics()` | Estatísticas da ferramenta (total, sucessos, falhas, taxa, etc.) |
| `register_generated_file(file_path)` | Registra arquivo gerado no histórico |

### 4.3 Uso Típico numa Tool Page

```python
helper = ExecutionHelper("minha_ferramenta", "Minha Ferramenta")
task_id, error = helper.create_task()

def run():
    helper.update_progress(10, "Iniciando...")
    # ... processamento ...
    helper.update_progress(100, "Finalizado")
    helper.complete(result_data={...}, generated_files=[...])

threading.Thread(target=run, daemon=True).start()
```

---

## 5. ExecutionHistoryManager — Histórico de Execuções

**Arquivo:** `src/core/tasks/execution_history_manager.py`
**Singleton:** `get_history_manager()`

### 5.1 O que faz

Persiste o **histórico completo** de cada execução em arquivos JSON no diretório `.execution_history/`, organizado por ferramenta.

### 5.2 Estrutura

```
.execution_history/
├── index.json              # Índice geral (by_tool, all_tasks)
├── categorizador/
│   ├── uuid-task-1.json   # Resultados, logs, arquivos gerados
│   └── uuid-task-2.json
├── consolidador/
│   └── uuid-task-3.json
└── ...
```

### 5.3 `ExecutionHistoryRecord`

| Campo | Descrição |
|-------|-----------|
| `task_id` | ID único da tarefa |
| `tool_name` | Nome da ferramenta |
| `status` | completed / failed / cancelled |
| `result_data` | Dict com dados de resultado |
| `generated_files` | Lista de arquivos gerados (path, nome, size, data) |
| `logs` | Últimas 100 linhas de log |
| `duration_seconds` | Duração total |
| `error_message` | Mensagem de erro (se falhou) |

### 5.4 Métodos

| Método | Descrição |
|--------|-----------|
| `save_record(record)` | Salva registro + atualiza índice |
| `get_history_by_tool(tool_name, limit)` | Retorna histórico de uma ferramenta |
| `get_all_history(limit)` | Retorna histórico de todas as ferramentas |
| `get_record(tool_name, task_id)` | Busca registro específico |
| `add_generated_file(tool_name, task_id, file_path)` | Adiciona arquivo gerado a um registro |
| `download_file(tool_name, task_id, file_name, destination)` | Baixa arquivo gerado |
| `get_tool_statistics(tool_name)` | Estatísticas: total, sucessos, taxa, duração média |
| `clear_history(tool_name, days_old)` | Limpa histórico + remove backups vinculados |
| `set_retention(retention_key)` | Define retenção (1h, 7d, 15d, 1m, 6m) |

---

## 6. StorageManager — Persistência SQLite

**Arquivo:** `src/core/storage/storage_manager.py`

### 6.1 Tabela de Tarefas (`tasks`)

Usada pelo `TaskExecutor` para persistir cada tarefa (insert/update).

### 6.2 Tabela de Tarefas Agendadas (`scheduled_tasks_local`)

Usada pelo `TaskScheduler` e pelo `SyncManager`.

| Coluna | Descrição |
|--------|-----------|
| `task_id` | PK |
| `user_id` | Dono da tarefa |
| `tool_name` | Ferramenta |
| `schedule_frequency` | daily / weekly / monthly / custom_cron |
| `cron_expression` | Expressão cron (para custom_cron) |
| `time_of_day` | HH:MM |
| `enabled` | 0 ou 1 |
| `last_run` / `next_run` | Timestamps ISO |
| `input_files` | JSON |
| `config` | JSON |

### 6.3 Métodos Relevantes

| Método | Descrição |
|--------|-----------|
| `save_task(dict)` | Insere task na tabela `tasks` |
| `update_task(task_id, dict)` | Atualiza task |
| `get_task(task_id)` | Busca task por ID |
| `save_scheduled_task(ScheduledTask)` | INSERT OR REPLACE em `scheduled_tasks_local` |
| `get_scheduled_tasks(user_id)` | Retorna tarefas **habilitadas** de um usuário |
| `get_all_scheduled_tasks(user_id)` | Retorna **todas** (habilitadas e desabilitadas) |
| `update_scheduled_task(ScheduledTask)` | Atualiza last_run, next_run, etc. |
| `disable_scheduled_task(task_id)` | Seta enabled = 0 |
| `delete_scheduled_task(task_id)` | Deleta linha |
| `replace_scheduled_tasks_for_user(user_id, remote_tasks)` | Deleta todas do usuário e reinsere as remotas (usado no sync) |

---

## 7. SyncManager — Sincronização com Supabase

**Arquivo:** `src/core/sync/sync_manager.py`

### 7.1 O que faz

Sincroniza **execuções** e **tarefas agendadas** entre o SQLite local e o Supabase (nuvem).

### 7.2 Fluxo de `sync_now()`

```
sync_now():
  1. Upload: fila de execuções pendentes → Supabase tabela "execucoes"
  2. Download: Supabase "execucoes" → local (espelho)
  3. Upload: tarefas agendadas locais → Supabase tabela "scheduled_tasks"
  4. Download: Supabase "scheduled_tasks" → local (espelho)
  5. Limpeza da fila de sync
```

### 7.3 Upload de Tarefas Agendadas

- Lê **todas** as tarefas agendadas locais do usuário
- Faz `upsert` no Supabase com conflito resolvido por `task_id`
- Mapeia todos os campos (incluindo `input_files` e `config` como JSON)

### 7.4 Download de Tarefas Agendadas

- Consulta Supabase por `user_id`
- Usa `replace_scheduled_tasks_for_user()` que apaga tudo local e reinsere os dados remotos
- Estratégia **espelho completo** (o que está na nuvem vira verdade local)

---

## 8. Como as 13 Tool Pages Usam o Sistema

Todas as 13 páginas de ferramentas seguem o mesmo padrão:

1. **Importam** `task_executor` e `ExecutionHelper`
2. **Instanciam** `ExecutionHelper(tool_key, tool_display_name)`
3. **Criam task** com `helper.create_task()`
4. **Executam** em thread separada, chamando `helper.update_progress()` e `helper.add_log()`
5. **Finalizam** com `helper.complete()` ou `helper.fail()`

| Tool Page | Ferramenta |
|-----------|------------|
| `analista_tendencias_page.py` | Analista de Tendências |
| `calculadora_lucratividade_page.py` | Calculadora de Lucratividade |
| `extrator_reviews_page.py` | Extrator de Reviews |
| `gerador_laudos_page.py` | Gerador de Laudos |
| `validador_links_page.py` | Validador de Links |
| `consolidador_page.py` | Consolidador |
| `categorizador_page.py` | Categorizador |
| `comissoes_page.py` | Comissões |
| `conciliador_page.py` | Conciliador |
| `conversor_ocr_page.py` | Conversor OCR |
| `data_sanitizer_page.py` | Data Sanitizer |
| `minerador_page.py` | Minerador |
| `orcamentos_page.py` | Orçamentos |

---

## 9. Fluxo Completo de uma Execução

```
1. Usuário clica "Executar" na tool page
        │
2. ToolPage cria ExecutionHelper(tool_key, display_name)
        │
3. helper.create_task()
        │
        ▼
4. TaskExecutor.create_task()
   ├─ Gera UUID
   ├─ Cria TaskInfo (status = PENDING)
   ├─ task_executor._tasks[task_id] = task
   ├─ Persiste no SQLite (StorageManager.save_task)
   └─ Dispara on_new_task() callbacks
        │
        ▼
5. TaskBar recebe notificação → se mostra na tela
        │
6. ToolPage inicia thread com a execução
        │
7. helper.update_progress(percent, message)
        │
        ▼
8. TaskExecutor.update_progress()
   ├─ Atualiza TaskInfo em memória
   ├─ Persiste no SQLite (StorageManager.update_task)
   └─ Notifica state_change callbacks
        │
        ▼
9. TaskBar (polling a cada 1s) atualiza barra de progresso
        │
10. helper.complete(result_data, generated_files)
        │
        ▼
11. TaskExecutor.complete_task()
    ├─ TaskInfo.status = COMPLETED
    ├─ Salva rows_processed, output_path, hours_saved
    ├─ Persiste no SQLite
    └─ Envia notificação desktop
        │
12. ExecutionHelper.save_to_history()
    └─ ExecutionHistoryManager.save_record()
       ├─ Salva JSON em .execution_history/{tool}/{task_id}.json
       ├─ Atualiza index.json
       └─ Limpa registros antigos conforme retenção
        │
13. TaskBar (polling) atualiza card com "✅ X linhas processadas"
```

---

## 10. Diagrama de Arquivos

```
src/
├── core/
│   ├── tasks/
│   │   ├── __init__.py                    # Exports: TaskExecutor, TaskStatus, TaskInfo, task_manager, task_executor
│   │   ├── task_executor.py               # Motor central (542 linhas)
│   │   └── execution_history_manager.py   # Histórico em JSON (424 linhas)
│   ├── task_scheduler.py                  # Agendador (372 linhas)
│   ├── storage/
│   │   └── storage_manager.py            # SQLite (1166 linhas) — tasks + scheduled_tasks_local
│   └── sync/
│       └── sync_manager.py               # Supabase sync (619 linhas)
│
├── gui/
│   ├── components/
│   │   └── task_bar.py                   # Overlay visual + badge (480 linhas)
│   ├── helpers/
│   │   └── execution_helper.py           # Helper para tool pages (163 linhas)
│   └── app.py                            # Main app — conecta storage, recover na inicialização
│
└── gui/pages/tools/
    ├── consolidador_page.py              # Usa task_executor.submit() + ExecutionHelper
    ├── categorizador_page.py             # Usa task_executor.submit() + ExecutionHelper
    ├── ... (13 tool pages ao total)
```
