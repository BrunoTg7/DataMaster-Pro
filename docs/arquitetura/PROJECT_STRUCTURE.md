# DataMaster Pro — Diagrama de Arquitetura Completo

Visao geral do sistema, componentes, fluxos e decisoes tecnicas.

---

## 1. Estrutura do Projeto

```
ferramente-excel/
├── datamaster-pro-desktop/          # App Desktop (Python)
│   ├── src/
│   │   ├── gui/                     # Interface CustomTkinter
│   │   ├── core/                    # Logica principal
│   │   ├── tools/                   # 15 ferramentas Excel
│   │   ├── domain/                  # Entidades e interfaces (Clean Arch)
│   │   ├── application/             # Use cases
│   │   ├── infrastructure/          # Adaptadores (DI Container)
│   │   ├── api/                     # FastAPI REST
│   │   └── utils/                   # Helpers
│   ├── tests/                       # Testes unitarios
│   ├── main.py                      # Entry point
│   └── config.py                    # Configuracoes globais
│
├── datamaster-pro-web/              # Plataforma Web (Next.js)
│   ├── app/                         # Pages (22 diretorios)
│   │   ├── landing/                 # Homepage
│   │   ├── auth/                    # Login/Registro
│   │   ├── dashboard/               # Area de membros
│   │   ├── downloads/               # Central de download
│   │   ├── planos/                  # Grid de planos
│   │   ├── api/                     # API routes (4 endpoints)
│   │   └── ...                      # Paginas estaticas
│   ├── components/                  # React Components
│   └── lib/                         # Supabase client
│
├── datamaster-pro-shared/           # Recursos Compartilhados
│   ├── constants/                   # Planos, ferramentas, cores
│   └── types/                       # Interfaces TypeScript
│
└── docs/                            # Documentacao centralizada
    ├── arquitetura/                 # Docs de arquitetura
    ├── seguranca/                   # Analise de seguranca
    ├── setup/                       # Guias de setup
    ├── specs/                       # Design specs
    ├── integracao/                  # Guias de integracao
    ├── sistemas/                    # Documentacao de sistemas
    └── desenvolvimento/             # Analises e desenvolvimento
```

---

## 2. Diagrama de Componentes

### 2.1 Desktop — Clean Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        PRESENTATION                             │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐ │
│  │  GUI Pages   │  │  Tool Pages  │  │  Components           │ │
│  │  (Login,     │  │  (15 tools)  │  │  (Toast, TaskBar,     │ │
│  │   Dashboard) │  │              │  │   HistoryButton)      │ │
│  └──────┬───────┘  └──────┬───────┘  └───────────────────────┘ │
│         │                 │                                      │
├─────────▼─────────────────▼──────────────────────────────────────┤
│                    APPLICATION SERVICES                          │
│  ┌──────────────────┐  ┌──────────────────┐                     │
│  │   ToolService    │  │   UserService    │                     │
│  │  (submit, cancel │  │  (login, logout, │                     │
│  │   progress)      │  │   session)       │                     │
│  └────────┬─────────┘  └────────┬─────────┘                     │
│           │                     │                                │
├───────────▼─────────────────────▼────────────────────────────────┤
│                        DOMAIN                                    │
│  ┌─────────┐  ┌──────────┐  ┌─────────────┐  ┌──────────────┐  │
│  │Entities │  │Interfaces│  │PluginRegistry│  │  ITool       │  │
│  │(User,   │  │(IUserRepo│  │(auto-disc.) │  │  Interface   │  │
│  │ Task,   │  │ ITaskRepo│  │             │  │              │  │
│  │ Exec)   │  │ ISync..) │  │             │  │              │  │
│  └─────────┘  └──────────┘  └─────────────┘  └──────────────┘  │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│                    INFRAESTRUTURA                                │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │  SQLite  │ │ Supabase │ │ Playwright│ │ FastAPI  │           │
│  │  Storage │ │  Sync    │ │  Browser  │ │   REST   │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Cross-Cutting Concerns                       │   │
│  │  CircuitBreaker | FeatureFlags | MemoryCache | APM       │   │
│  │  AuditLogger | Retry/Backoff | RateLimiter               │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Web — Next.js App Router

```
┌─────────────────────────────────────────────────┐
│              Next.js (Server + Client)           │
│  ┌────────────┐  ┌────────────┐  ┌───────────┐ │
│  │  Landing   │  │   Auth     │  │ Dashboard │ │
│  │  (SSG)     │  │  (SSR)     │  │  (CSR)    │ │
│  └────────────┘  └────────────┘  └───────────┘ │
│  ┌────────────┐  ┌────────────┐  ┌───────────┐ │
│  │  API Routes│  │ Middleware  │  │  Static   │ │
│  │  (4 endpoints)│ │(auth+rate) │  │  Pages    │ │
│  └────────────┘  └────────────┘  └───────────┘ │
├─────────────────────────────────────────────────┤
│              Supabase Client (SSR)              │
│  Auth | Database | Realtime                     │
├─────────────────────────────────────────────────┤
│              Vercel (Deploy)                    │
└─────────────────────────────────────────────────┘
```

---

## 3. Diagrama de Sequencia

### 3.1 Login Desktop

```
┌──────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│ User │     │LoginPage │     │AuthManager│    │ Supabase │
└──┬───┘     └────┬─────┘     └────┬──────┘     └────┬─────┘
   │  email+pass  │                │                  │
   │─────────────>│                │                  │
   │              │  login(email,  │                  │
   │              │  password)     │                  │
   │              │───────────────>│                  │
   │              │                │  POST /auth/v1/  │
   │              │                │  token?grant_type│
   │              │                │─────────────────>│
   │              │                │   JWT tokens     │
   │              │                │<─────────────────│
   │              │   session      │                  │
   │              │<───────────────│                  │
   │              │  save encrypted│                  │
   │              │  token SQLite  │                  │
   │  dashboard   │                │                  │
   │<─────────────│                │                  │
```

### 3.2 Uso de Ferramenta (Offline → Sync)

```
┌──────┐  ┌──────────┐  ┌───────────┐  ┌──────────┐  ┌──────────┐
│ User │  │ ToolPage  │  │ToolService│  │TaskExec. │  │SyncManager│
└──┬───┘  └────┬─────┘  └─────┬─────┘  └────┬─────┘  └────┬─────┘
   │  upload   │              │              │              │
   │  file     │              │              │              │
   │──────────>│              │              │              │
   │           │  submit()    │              │              │
   │           │─────────────>│              │              │
   │           │              │  create_task()│             │
   │           │              │─────────────>│              │
   │           │              │              │  thread exec │
   │           │              │              │────┐         │
   │           │              │              │    │ process │
   │           │              │              │<───┘         │
   │           │  progress    │              │              │
   │           │<─────────────│──────────────│              │
   │  bar      │              │              │              │
   │<──────────│              │              │              │
   │           │  complete()  │              │              │
   │           │              │─────────────>│              │
   │           │              │              │  queue sync  │
   │           │              │              │─────────────>│
   │  result   │              │              │              │ upload
   │<──────────│              │              │              │ cloud
```

### 3.3 Webhook de Pagamento

```
┌──────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│ Cakto│  │Webhook   │  │Edge Func.│  │Database  │  │ SendGrid │
└──┬───┘  │ Route    │  │          │  │          │  │          │
   │ POST │          │          │          │          │
   │ /api/cako      │          │          │          │
   │────────────────>│          │          │          │
   │        │  validate secret  │          │          │
   │        │──────────>│       │          │          │
   │        │          │ processar_upgrade │          │
   │        │          │──────────────────>│          │
   │        │          │  UPDATE plano     │          │
   │        │          │<──────────────────│          │
   │        │          │ enfileirar_email  │          │
   │        │          │──────────────────>│          │
   │        │  200 OK  │          │          │          │
   │        │<─────────│          │          │          │
   │        │          │ send-email        │          │
   │        │          │──────────────────────────────>│
   │        │          │          │          │  SEND   │
```

---

## 4. Diagrama de Dados

### 4.1 Modelo Supabase (Cloud)

```
┌──────────────────┐     ┌──────────────────┐
│     usuarios     │     │     execucoes     │
├──────────────────┤     ├──────────────────┤
│ id (UUID, PK)    │<────│ usuario_id (FK)  │
│ email            │     │ ferramenta       │
│ nome             │     │ linhas_processadas│
│ plano_tipo       │     │ tempo_execucao_ms│
│ data_expiracao   │     │ resultado_arquivo│
│ hwid             │     │ created_at       │
│ created_at       │     └──────────────────┘
│ updated_at       │
└──────────────────┘     ┌──────────────────┐
                         │  scheduled_tasks  │
┌──────────────────┐     ├──────────────────┤
│   check_updates  │     │ task_id (PK)     │
├──────────────────┤     │ user_id (FK)     │
│ versao_atual     │     │ tool_name        │
│ versao_disponivel│     │ frequency        │
│ url_download     │     │ cron_expression  │
│ changelog        │     │ enabled          │
└──────────────────┘     │ next_run         │
                         └──────────────────┘
┌──────────────────┐     ┌──────────────────┐
│  execution_logs  │     │tool_configurations│
├──────────────────┤     ├──────────────────┤
│ execution_id (PK)│     │ config_id (PK)   │
│ user_id (FK)     │     │ user_id (FK)     │
│ tool_name        │     │ tool_id          │
│ duration_seconds │     │ config_data (JSON)│
│ lines_processed  │     │ created_at       │
│ status           │     └──────────────────┘
└──────────────────┘
```

### 4.2 Modelo SQLite (Local Desktop)

```
┌──────────────────┐     ┌──────────────────┐
│      users       │     │    executions    │
├──────────────────┤     ├──────────────────┤
│ id               │<────│ user_id          │
│ email            │     │ ferramenta       │
│ plano_tipo       │     │ resultado        │
│ token_cripto     │     │ status           │
│ hwid             │     │ timestamp        │
└──────────────────┘     └──────────────────┘

┌──────────────────┐     ┌──────────────────┐
│      tasks       │     │   sync_queue     │
├──────────────────┤     ├──────────────────┤
│ task_id          │     │ id               │
│ user_id          │     │ user_id          │
│ tool_name        │     │ dados (JSON)     │
│ status           │     │ status           │
│ progress         │     │ tentativas       │
│ result           │     │ created_at       │
└──────────────────┘     └──────────────────┘
```

---

## 5. Diagrama de Implantacao

### 5.1 Ambientes

```
┌─────────────────────────────────────────────────────────┐
│                     PRODUCAO                            │
│                                                         │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │   Vercel    │  │  Supabase    │  │   Servidor    │  │
│  │  (Web)      │  │  (Cloud)     │  │  (.exe)       │  │
│  │             │  │              │  │               │  │
│  │ Next.js     │  │ PostgreSQL   │  │  Download     │  │
│  │ Edge Fn     │  │ Auth         │  │  Center       │  │
│  │ Middleware   │  │ Realtime     │  │               │  │
│  └──────┬──────┘  └──────┬───────┘  └───────┬───────┘  │
│         │                │                   │          │
│         └────────────────┼───────────────────┘          │
│                          │                              │
│                    HTTPS │ API                          │
│                          │                              │
└──────────────────────────┼──────────────────────────────┘
                           │
              ┌────────────┴────────────┐
              │      Desktop App        │
              │  ( Distribuido .exe )   │
              │  - SQLite local         │
              │  - Sync offline-first   │
              │  - 15 ferramentas       │
              └─────────────────────────┘
```

### 5.2 Pipeline de Deploy

```
Desktop:
  Python Code → PyInstaller → datamaster.spec → .exe → Upload servidor
  ↓
  check_updates.versao_disponivel ← Atualiza no Supabase
  ↓
  Desktop detecta → Download → Instalador → Replace

Web:
  TypeScript Code → npm run build → .next/ → Vercel Deploy
  ↓
  www.datamaster.pro

Edge Functions:
  Deno Code → supabase functions deploy → Supabase Cloud
```

---

## 6. Inventario de APIs

### 6.1 FastAPI REST (Desktop - localhost:8000)

| Metodo | Endpoint           | Descricao                   | Auth  |
|--------|--------------------|-----------------------------|-------|
| GET    | `/health`          | Health check                | Nao   |
| GET    | `/api/users/me`    | Info do usuario atual       | JWT   |
| GET    | `/api/tasks`       | Listar tarefas              | JWT   |
| GET    | `/api/tasks/{id}`  | Tarefa especifica           | JWT   |
| POST   | `/api/tasks/submit`| Criar tarefa                | JWT   |
| POST   | `/api/tasks/{id}/cancel` | Cancelar tarefa       | JWT   |
| GET    | `/api/stats`       | Estatisticas do usuario     | JWT   |
| GET    | `/api/executions`  | Listar execucoes            | JWT   |
| GET    | `/api/tools`       | Ferramentas registradas     | JWT   |

### 6.2 Supabase Edge Functions

| Funcao             | URL                                            | Metodo | Auth       |
|--------------------|------------------------------------------------|--------|------------|
| cakto-webhook      | `.../functions/v1/cakto-webhook`               | POST   | Secret     |
| send-email         | `.../functions/v1/send-email`                  | POST   | Service    |
| sync-background    | `.../functions/v1/sync-background`             | POST   | Service    |

### 6.3 Supabase RPC Functions

| Funcao                          | Parametros                              | Retorno            |
|---------------------------------|-----------------------------------------|--------------------|
| `sincronizar_usuario`           | `usuario_id`                            | `{execucoes, ...}` |
| `calcular_roi`                  | `usuario_id, dias`                      | `{total_linhas,}`  |
| `validar_acesso_ferramenta`     | `usuario_id, ferramenta, linhas`        | `{tem_acesso,}`    |
| `registrar_execucao`            | `usuario_id, ferramenta, linhas, ...`   | `{execucao_id,}`   |
| `enfileirar_email`              | `usuario_id, tipo, destino, assunto`    | `{email_id,}`      |
| `processar_upgrade_cakto`       | `email, plano, data_exp`                | `{usuario_id,}`    |
| `update_updated_at_column`      | (trigger)                               | -                  |

### 6.4 Web Next.js Routes

| Rota                  | Tipo       | Descricao                     |
|-----------------------|------------|-------------------------------|
| `/`                   | Page       | Landing page                  |
| `/auth/login`         | Page       | Login                         |
| `/auth/register`      | Page       | Registro                      |
| `/auth/callback`      | Route      | OAuth callback                |
| `/dashboard`          | Page       | Area de membros               |
| `/dashboard/configuracoes` | Page  | Configuracoes                 |
| `/planos`             | Page       | Planos e precos               |
| `/downloads`          | Page       | Central de download           |
| `/api/cako`           | Route      | Webhook Cakto                 |
| `/api/contact`        | Route      | Formulario de contato         |
| `/api/account`        | Route      | Gerenciamento de conta        |
| `/api/health`         | Route      | Health check                  |
| `/sobre`              | Page       | Sobre                         |
| `/contato`            | Page       | Contato                       |
| `/blog`               | Page       | Blog                          |
| `/changelog`          | Page       | Changelog                     |
| `/status`             | Page       | Status do sistema             |
| `/lgpd`               | Page       | Politica de privacidade       |
| `/privacidade`        | Page       | Privacidade                   |
| `/termos`             | Page       | Termos de uso                 |
| `/ajuda`              | Page       | Central de ajuda              |
| `/carreiras`          | Page       | Carreiras                     |
| `/orcamentos-demo`    | Page       | Demo de orcamentos            |

---

## 7. Requisitos Nao-Funcionais

| Requisito        | Implementacao                                          |
|------------------|-------------------------------------------------------|
| **Performance**  | MemoryCache TTL, Circuit Breaker, APM, Browser Pool   |
| **Seguranca**    | JWT auth, RLS, CSP, Rate Limiting, encrypted storage   |
| **Escalabilidade**| Plugin system, DI Container, Clean Architecture      |
| **Disponibilidade**| Offline-first, sync queue, retry/backoff             |
| **Manutenibilidade**| 277 testes, conftest.py, pyproject.toml, logging    |
| **Compliance**   | LGPD (exportacao de dados, delete policy)             |

---

## 8. Seguranca

### Desktop
- Tokens criptografados com Fernet (cryptography)
- SQLite com encryption (AES via Fernet)
- Chaves API ofuscadas em .pyc (build_pyc_keys.py)
- HWID binding (anti-pirataria)
- Instance lock via socket TCP

### Web
- Autenticacao Supabase SSR (cookies HttpOnly)
- Middleware protege /dashboard e /configuracoes
- Open redirect protection
- CSP headers (Content-Security-Policy)
- Rate limiting (middleware customizado)
- Seletive column queries (sem select('*'))

### Supabase
- RLS policies em todas as tabelas
- Service role key apenas server-side
- Webhook com autenticacao de secret
- Timing-safe comparison (timingSafeEqual)

---

*Atualizado em 2026-06-21. Reflete a estrutura atual do projeto.*
