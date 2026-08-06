# Inventario de APIs — DataMaster Pro

Catalogo completo de todos os endpoints, contratos e autenticacao.

---

## 1. FastAPI REST (Desktop Local)

**Base URL:** `http://127.0.0.1:8000`  
**Auth:** JWT Bearer Token  
**Rate Limit:** 60 req/min (padrao), 10 req/min (auth)

### 1.1 Health Check

```
GET /health
```

**Resposta:**
```json
{
  "status": "ok",
  "version": "1.5.0",
  "uptime": 3600
}
```

**Auth:** Nao requerida

---

### 1.2 Usuario Atual

```
GET /api/users/me
```

**Headers:** `Authorization: Bearer <jwt_token>`

**Resposta 200:**
```json
{
  "id": "uuid",
  "email": "user@email.com",
  "plano_tipo": "pro",
  "created_at": "2024-01-01T00:00:00Z"
}
```

**Erros:**
- `401` — Token invalido ou ausente
- `404` — Usuario nao encontrado

---

### 1.3 Listar Tarefas

```
GET /api/tasks?status=running&limit=50
```

**Query Params:**
| Param   | Tipo   | Obrigatorio | Descricao                     |
|---------|--------|-------------|-------------------------------|
| status  | string | Nao         | Filtrar por: pending, running, completed, failed |
| limit   | int    | Nao         | Maximo de resultados (padrao: 50) |

**Resposta 200:**
```json
{
  "tasks": [
    {
      "id": "task-uuid",
      "tool_name": "consolidador",
      "status": "running",
      "progress": 45,
      "created_at": "2024-01-01T10:00:00Z"
    }
  ],
  "total": 1
}
```

---

### 1.4 Tarefa Especifica

```
GET /api/tasks/{task_id}
```

**Resposta 200:**
```json
{
  "id": "task-uuid",
  "tool_name": "consolidador",
  "status": "completed",
  "progress": 100,
  "result": { "rows_processed": 1200 },
  "logs": ["Linha 1: Processando...", "Linha 2: Concluido"],
  "created_at": "2024-01-01T10:00:00Z",
  "completed_at": "2024-01-01T10:05:00Z"
}
```

**Erros:**
- `404` — Tarefa nao encontrada

---

### 1.5 Criar Tarefa

```
POST /api/tasks/submit
```

**Body:**
```json
{
  "tool_name": "consolidador",
  "input_params": {
    "files": ["/path/file1.xlsx", "/path/file2.xlsx"],
    "output_path": "/path/result.xlsx",
    "merge_strategy": "concat"
  }
}
```

**Resposta 201:**
```json
{
  "task_id": "task-uuid",
  "status": "pending",
  "message": "Tarefa criada com sucesso"
}
```

**Erros:**
- `400` — Parametros invalidos
- `409` — Ferramenta ja em execucao
- `429` — Limite de concorrencia atingido

---

### 1.6 Cancelar Tarefa

```
POST /api/tasks/{task_id}/cancel
```

**Resposta 200:**
```json
{
  "message": "Tarefa cancelada",
  "task_id": "task-uuid"
}
```

**Erros:**
- `404` — Tarefa nao encontrada
- `409` — Tarefa ja concluida

---

### 1.7 Estatisticas do Usuario

```
GET /api/stats?days=30
```

**Query Params:**
| Param | Tipo | Obrigatorio | Descricao              |
|-------|------|-------------|------------------------|
| days  | int  | Nao         | Periodo em dias (padrao: 30) |

**Resposta 200:**
```json
{
  "total_executions": 45,
  "time_saved_minutes": 225.5,
  "avg_roi_percentage": 94.2,
  "by_tool": {
    "consolidador": { "executions": 15, "time_saved": 75.0 },
    "categorizador": { "executions": 10, "time_saved": 50.0 }
  }
}
```

**Cache:** 30 segundos (MemoryCache TTL)

---

### 1.8 Listar Execucoes

```
GET /api/executions?limit=100
```

**Resposta 200:**
```json
{
  "executions": [
    {
      "id": "exec-uuid",
      "tool_name": "consolidador",
      "linhas_processadas": 1200,
      "tempo_execucao_ms": 5200,
      "status": "success",
      "created_at": "2024-01-01T10:00:00Z"
    }
  ]
}
```

---

### 1.9 Ferramentas Registradas

```
GET /api/tools
```

**Resposta 200:**
```json
{
  "tools": [
    {
      "key": "consolidador",
      "name": "Consolidador",
      "description": "Une multiplas planilhas em uma estrutura unica",
      "status": "available",
      "page_module": "consolidador_page"
    }
  ],
  "total": 15
}
```

---

## 2. Supabase Edge Functions

**Base URL:** `https://{project_ref}.supabase.co/functions/v1`

### 2.1 Cakto Webhook

```
POST /cakto-webhook
```

**Headers:**
- `Content-Type: application/json`
- `Authorization: Bearer {CAKTO_WEBHOOK_SECRET}`
- `x-cakto-signature: {signature}`

**Body (event: purchase.completed):**
```json
{
  "event": "purchase.completed",
  "data": {
    "customer_email": "user@email.com",
    "plan": "pro",
    "amount": 16000
  }
}
```

**Resposta 200:**
```json
{
  "message": "Processed",
  "usuario_id": "uuid",
  "novo_plano": "pro"
}
```

**Logica:**
1. Valida secret (timingSafeEqual)
2. Chama `processar_upgrade_cakto()` no BD
3. Atualiza `usuarios.plano_tipo`
4. Enfileira email de confirmacao

---

### 2.2 Send Email

```
POST /send-email
```

**Headers:** `Authorization: Bearer {SUPABASE_SERVICE_ROLE_KEY}`

**Body:**
```json
{
  "usuario_id": "uuid",
  "tipo_email": "welcome",
  "destinatario": "user@email.com",
  "assunto": "Bem-vindo ao DataMaster Pro"
}
```

**Templates Suportados:**
- `welcome` — Email de boas-vindas
- `upgrade_pro` — Confirmacao upgrade Pro
- `upgrade_enterprise` — Confirmacao upgrade Enterprise
- `roi_report` — Relatorio mensal de ROI
- `password_reset` — Recuperacao de senha

**Resposta 200:**
```json
{
  "email_id": "uuid",
  "status": "enviado"
}
```

---

### 2.3 Sync Background

```
POST /sync-background
```

**Headers:** `Authorization: Bearer {SUPABASE_SERVICE_ROLE_KEY}`

**Body:**
```json
{
  "usuario_id": "uuid"
}
```

**Logica:**
1. Busca `sync_logs` com status `pending`
2. Processa cada registro
3. Marca como `synced`
4. Atualiza `usuarios.ultima_sincronizacao`

**Resposta 200:**
```json
{
  "processados": 5,
  "sucesso": 5,
  "falhas": 0
}
```

---

## 3. Supabase RPC Functions

Chamadas via Supabase Client (Python ou TypeScript).

### 3.1 Validar Acesso a Ferramenta

```python
result = supabase.rpc("validar_acesso_ferramenta", {
    "p_usuario_id": "uuid",
    "p_ferramenta": "consolidador",
    "p_linhas": 1200
}).execute()

# result.data = {
#   "tem_acesso": True,
#   "plano": "pro",
#   "limite_linhas": 999999
# }
```

### 3.2 Registrar Execucao

```python
result = supabase.rpc("registrar_execucao", {
    "p_usuario_id": "uuid",
    "p_ferramenta": "consolidador",
    "p_linhas": 1200,
    "p_tempo_ms": 5200,
    "p_arquivo": "result.xlsx"
}).execute()

# result.data = {
#   "execucao_id": "uuid",
#   "tempo_economizado": 175.5
# }
```

### 3.3 Calcular ROI

```python
result = supabase.rpc("calcular_roi", {
    "p_usuario_id": "uuid",
    "p_dias": 30
}).execute()

# result.data = {
#   "total_linhas": 50000,
#   "tempo_economizado": 225.5,
#   "execucoes": 45
# }
```

### 3.4 Sincronizar Usuario

```python
result = supabase.rpc("sincronizar_usuario", {
    "p_usuario_id": "uuid"
}).execute()
```

### 3.5 Enfileirar Email

```python
result = supabase.rpc("enfileirar_email", {
    "p_usuario_id": "uuid",
    "p_tipo_email": "welcome",
    "p_destinatario": "user@email.com",
    "p_assunto": "Bem-vindo!"
}).execute()
```

### 3.6 Processar Upgrade Cakto

```python
result = supabase.rpc("processar_upgrade_cakto", {
    "p_email": "user@email.com",
    "p_plano_novo": "pro",
    "p_data_expiracao": "2025-01-01"
}).execute()
```

---

## 4. Web Next.js Routes

### 4.1 Pages Estaticas/SSG

| Rota                  | Tipo | Descricao              |
|-----------------------|------|------------------------|
| `/`                   | SSG  | Landing page           |
| `/sobre`              | SSG  | Sobre o DataMaster     |
| `/planos`             | SSG  | Grid de planos         |
| `/ajuda`              | SSG  | Central de ajuda       |
| `/blog`               | SSG  | Blog                   |
| `/changelog`          | SSR  | Changelog              |
| `/status`             | SSG  | Status do sistema      |
| `/lgpd`               | SSG  | Politica LGPD          |
| `/privacidade`        | SSG  | Privacidade            |
| `/termos`             | SSG  | Termos de uso          |
| `/contato`            | SSG  | Contato                |
| `/carreiras`          | SSG  | Carreiras              |
| `/orcamentos-demo`    | SSG  | Demo de orcamentos     |

### 4.2 Pages Autenticadas (SSR + Middleware)

| Rota                       | Descricao           |
|----------------------------|---------------------|
| `/auth/login`              | Login               |
| `/auth/register`           | Registro            |
| `/auth/callback`           | OAuth callback      |
| `/auth/verify`             | Verificacao email   |
| `/dashboard`               | Area de membros     |
| `/dashboard/configuracoes` | Configuracoes       |
| `/downloads`               | Central de download |

### 4.3 API Routes

| Rota            | Metodo | Auth   | Descricao                    |
|-----------------|--------|--------|------------------------------|
| `/api/cako`     | POST   | Secret | Webhook Cakto (pagamentos)   |
| `/api/contact`  | POST   | Nao    | Formulario de contato        |
| `/api/account`  | POST   | JWT    | Gerenciamento de conta       |
| `/api/health`   | GET    | Nao    | Health check                 |

---

## 5. Contratos de Dados

### 5.1 Task Submission (Desktop → FastAPI)

```typescript
interface TaskSubmission {
  tool_name: string;        // Chave da ferramenta
  input_params: {
    files?: string[];       // Caminhos dos arquivos
    output_path?: string;   // Caminho de saida
    [key: string]: any;     // Params especificos da tool
  };
}
```

### 5.2 Task Response (FastAPI → Desktop)

```typescript
interface TaskResponse {
  id: string;
  tool_name: string;
  status: "pending" | "running" | "completed" | "failed" | "cancelled";
  progress: number;         // 0-100
  result?: any;
  logs?: string[];
  error?: string;
  created_at: string;
  completed_at?: string;
}
```

### 5.3 Webhook Cakto (Cakto → Supabase)

```typescript
interface CaktoWebhook {
  event: "purchase.completed" | "subscription.expired";
  data: {
    customer_email: string;
    plan: string;
    amount: number;
    transaction_id: string;
  };
}
```

---

*Inventario de APIs atualizado em 2026-06-21. Inclui todos os endpoints, contratos e autenticacao.*
