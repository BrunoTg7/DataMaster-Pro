# 📋 Setup Supabase - DataMaster Pro

Guia completo para configurar o banco de dados Supabase com todas as tabelas, functions e edge functions.

## 🚀 Pré-requisitos

1. **Criar projeto Supabase**
   - Acesse [supabase.com](https://supabase.com)
   - Clique em "New Project"
   - Escolha organização e banco de dados
   - Guarde o `PROJECT_REF` (usado em URLs e CLI)

2. **Instalar Supabase CLI**

   ```bash
   npm install -g supabase
   ```

3. **Autenticar**
   ```bash
   supabase login
   ```

---

## 📊 Passo 1: Executar Schema SQL

### Opção A: Via Dashboard Supabase (Mais fácil)

1. Ir para **SQL Editor** no dashboard
2. Clicar em **"New Query"**
3. Copiar conteúdo de `datamaster-pro-shared/schemas/complete-schema.sql`
4. Colar no editor
5. Clicar em **"Run"** (ou `Ctrl+Enter`)
6. Verificar se todas as queries passaram ✅

### Opção B: Via CLI (Recomendado para produção)

1. Copiar schema para uma pasta local

   ```bash
   cp datamaster-pro-shared/schemas/complete-schema.sql migrations/
   ```

2. Executar no projeto Supabase

   ```bash
   supabase db push --linked
   ```

3. Verificar
   ```bash
   supabase db list
   ```

---

## 🔑 Passo 2: Configurar Variáveis de Ambiente

### No projeto local (.env)

```bash
# .env.local (Web)
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJxxxxx...
SUPABASE_SERVICE_ROLE_KEY=eyJxxxxx...

# .env (Desktop)
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJxxxxx...
SUPABASE_SERVICE_ROLE_KEY=eyJxxxxx...

# Email (configurado via Dashboard, não precisa de API key)
SUPABASE_EMAIL_FROM=noreply@datamaster.pro
SUPABASE_EMAIL_REPLY_TO=support@datamaster.pro

# Cakto (Pagamento)
NEXT_PUBLIC_CAKTO_API_KEY=cakto_xxxxx
CAKTO_WEBHOOK_SECRET=sk_xxxxx
```

### Como obter as chaves

1. Ir para **Settings** → **API** no dashboard
2. Copiar `Project URL` e `Anon Key`
3. Copiar `Service Role Key` (usar com cuidado!)

---

## ⚡ Passo 3: Deploy das Edge Functions

### 1. Dentro da pasta do projeto

```bash
cd datamaster-pro-shared/edge-functions
```

### 2. Setando secrets

```bash
# Autenticar
supabase login

# Ligar ao projeto (use PROJECT_REF)
supabase link --project-ref YOUR_PROJECT_REF

# Setar secrets
supabase secrets set SENDGRID_API_KEY="your-sendgrid-key"
supabase secrets set CAKTO_WEBHOOK_SECRET="your-webhook-secret"

# Verificar secrets
supabase secrets list
```

### 3. Deploy das functions

```bash
supabase functions deploy cakto-webhook
supabase functions deploy send-email
supabase functions deploy sync-background

# Verificar deployment
supabase functions list
```

### 4. Testar local (opcional)

```bash
supabase functions serve
# Agora acessível em http://localhost:54321/functions/v1/
```

---

## 🧪 Passo 4: Testar Schema e Functions

### Test 1: Autenticação e Usuário

```sql
-- Criar usuário (via Supabase Auth dashboard ou programaticamente)
-- Depois verificar se aparece em usuarios table

SELECT * FROM usuarios LIMIT 1;
```

### Test 2: Validar Acesso a Ferramenta

```sql
-- Testar para usuário Grátis
SELECT validar_acesso_ferramenta(
  'user-uuid-here',
  'consolidador',
  5
);  -- Deve retornar tem_acesso: true

SELECT validar_acesso_ferramenta(
  'user-uuid-here',
  'orcamentos',
  5
);  -- Deve retornar tem_acesso: false (Grátis não pode)
```

### Test 3: Registrar Execução

```sql
-- Registrar uma execução bem-sucedida
SELECT registrar_execucao(
  'user-uuid-here',
  'consolidador',
  100,
  2500,
  '/path/to/arquivo.xlsx'
);
```

### Test 4: Calcular ROI

```sql
-- Obter ROI do último mês
SELECT calcular_roi('user-uuid-here', 30);
```

### Test 5: Verificar RLS Policies

```sql
-- Como usuário autenticado, deve ver apenas suas execuções
SELECT * FROM execucoes;  -- Mostra apenas deste usuário

-- Como anon, deve receber erro
-- (a RLS policy bloqueia)
```

---

## 🔐 Passo 5: Configurar Webhook do Cakto

### 1. No dashboard Cakto

1. Ir para **Webhooks** → **Add New**
2. URL: `https://[PROJECT_REF].supabase.co/functions/v1/cakto-webhook`
3. Events: Selecionar `purchase.completed`, `subscription.expired`
4. Headers: Adicionar `x-cakto-token: seu-webhook-secret`
5. Salvar

### 2. Testar webhook (opcional)

```bash
curl -X POST https://[PROJECT_REF].supabase.co/functions/v1/cakto-webhook \
  -H "Content-Type: application/json" \
  -H "x-cakto-token: seu-webhook-secret" \
  -d '{
    "event": "purchase.completed",
    "data": {
      "email": "test@example.com",
      "plan": "pro",
      "expiration_date": "2026-05-06"
    }
  }'
```

Esperar por `{"success": true}`

---

## 📧 Passo 6: Configurar Supabase Email (SMTP)

### 1. No Dashboard Supabase - Settings → Email

1. Ir para **Settings** → **Email** no dashboard
2. Selecionar **Email Templates** (ou **Custom SMTP** se preferir)
3. Escolher uma das opções:

#### Opção A: Usar Email Templates padrão do Supabase

```
✅ Mais fácil para começar
✅ Emails automáticos (auth, recovery)
✅ Custom templates disponível
❌ Limitado a tipos pré-definidos
```

#### Opção B: Custom SMTP (Recomendado)

Usando seu próprio servidor SMTP:

1. Ir para **Settings** → **Email** → **Configure SMTP**
2. Preencher:
   - **SMTP Host:** seu-smtp-host.com
   - **SMTP Port:** 587 (TLS) ou 465 (SSL)
   - **Username:** seu-email@dominio.com
   - **Password:** sua-senha-app
   - **From Email:** noreply@datamaster.pro
   - **From Name:** DataMaster Pro

3. Testar conexão
4. Salvar

### 2. Configurar no arquivo .env

```bash
# .env (Desktop e Web)
SUPABASE_EMAIL_FROM="noreply@datamaster.pro"
SUPABASE_EMAIL_REPLY_TO="support@datamaster.pro"
```

### 3. Testar envio de email

```bash
curl -X POST https://[PROJECT_REF].supabase.co/functions/v1/send-email \
  -H "Authorization: Bearer YOUR_ANON_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "email_id": "550e8400-e29b-41d4-a716-446655440000",
    "tipo_email": "welcome",
    "destinatario": "seu-email@example.com",
    "variaveisTemplate": {}
  }'
```

### ✅ Verificar Status

```
Dashboard Supabase → Email → Logs
(Mostra histórico de envios, erros, etc)
```

---

## 🧪 Teste de Integração Completa

### Fluxo: Novo Usuário → Compra → Upgrade

```bash
# 1. Usuário se registra (auth automático)
# → Tabela usuarios é criada
# → Email "welcome" é enfileirado

# 2. Usuário vai para /planos e clica "Upgrade Pro"
# → Redireciona para Cakto checkout

# 3. Usuário completa pagamento
# → Cakto envia webhook
# → processar_upgrade_cakto() atualiza plano
# → Email "upgrade_pro" é enfileirado

# 4. App desktop faz sync
# → Detecta novo plano
# → Habilita todas as 5 ferramentas
# → Notificação visual no LED

# 5. Usuário usa ferramenta
# → registrar_execucao() cria registro
# → Sincroniza com cloud quando online
```

---

## 🔍 Verificar Status

### Dashboard Supabase

```
✅ Tables: 8 criadas (usuarios, execucoes, etc)
✅ Functions: 7 criadas (validar_acesso, registrar_execucao, etc)
✅ Triggers: 3 criadas (update_at automáticos)
✅ RLS Policies: Ativadas em todas as tabelas
✅ Edge Functions: 3 deployadas
```

### CLI

```bash
supabase tables list
supabase functions list
supabase migrations list --local
```

---

## 🐛 Troubleshooting

### Erro: "CORS policy"

→ Verificar se Edge Function retorna `corsHeaders`

### Erro: "RLS policy violation"

→ Verificar se usuário está autenticado e permissions estão corretas

### Erro: "Function not found"

→ Verificar se função foi deployada: `supabase functions list`

### Email não chega

→ Verificar `email_logs` table para status
→ Validar SendGrid API key

---

## 📝 Próximos Passos

- [ ] Teste completo de sincronização
- [ ] Teste de backup automático
- [ ] Configurar Realtime para notificações live
- [ ] Implementar 2FA (optional)
- [ ] Setup de monitoring/alertas

---

## 🎯 Resumo de Endpoints

| Função          | Endpoint                        | Método | Autenticação  |
| --------------- | ------------------------------- | ------ | ------------- |
| Cakto Webhook   | `/functions/v1/cakto-webhook`   | POST   | x-cakto-token |
| Send Email      | `/functions/v1/send-email`      | POST   | Service Role  |
| Sync Background | `/functions/v1/sync-background` | POST   | Authenticated |

---

## 📚 Links Úteis

- [Supabase Docs](https://supabase.com/docs)
- [Edge Functions Guide](https://supabase.com/docs/guides/functions)
- [RLS Tutorial](https://supabase.com/docs/guides/auth/row-level-security)
- [SendGrid Docs](https://docs.sendgrid.com/api-reference)
