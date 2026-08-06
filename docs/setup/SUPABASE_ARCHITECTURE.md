# 🗂️ Supabase - Estrutura Completa

Resumo visual da arquitetura SQL + Edge Functions do DataMaster Pro.

---

## 📊 Tabelas (8 no total)

```
┌─ USUARIOS (Core)
│  ├─ id (UUID, PK, auth.uid())
│  ├─ email, nome
│  ├─ plano_tipo (ENUM: gratis, pro, enterprise)
│  ├─ data_expiracao
│  └─ ultima_sincronizacao
│
├─ EXECUCOES (Analytics)
│  ├─ id, usuario_id (FK)
│  ├─ ferramenta (qual tool foi usada)
│  ├─ linhas_processadas
│  ├─ tempo_execucao_ms
│  ├─ tempo_economizado_minutos (calculado)
│  └─ resultado_arquivo (path)
│
├─ CHECK_UPDATES (Versionamento)
│  ├─ versao_atual, versao_disponivel
│  ├─ url_download, changelog
│  └─ data_release
│
├─ FAVORITOS (UX)
│  ├─ usuario_id (FK)
│  ├─ ferramenta
│  └─ ordem (position)
│
├─ SYNC_LOGS (Auditoria)
│  ├─ usuario_id (FK)
│  ├─ status (pending, syncing, synced, failed)
│  ├─ dados_sincronizados (JSONB)
│  └─ duracao_ms
│
├─ EMAIL_LOGS (Auditoria)
│  ├─ usuario_id (FK)
│  ├─ tipo_email (welcome, upgrade, roi_report, etc)
│  ├─ status (enviado, falha, bounce)
│  └─ tentativas
│
├─ WEBHOOKS_LOG (Auditoria)
│  ├─ fonte (cakto, stripe, etc)
│  ├─ tipo_evento
│  ├─ payload (JSONB)
│  └─ usuario_id (FK, nullable)
│
└─ (Future) CONFIGS_USUARIO
   ├─ usuario_id (FK)
   ├─ tema, idioma
   └─ preferências locais
```

---

## ⚙️ Functions (7 no total)

### Data Functions (Rodam no BD)

```
1. sincronizar_usuario(usuario_id)
   └─ Marca como sincronizado
   └─ Retorna { execucoes_sincronizadas, ultima_execucao }

2. calcular_roi(usuario_id, dias=30)
   └─ ROI de período (padrão 30 dias)
   └─ Retorna { total_linhas, tempo_economizado, execucoes }

3. validar_acesso_ferramenta(usuario_id, ferramenta, linhas)
   └─ Valida plano vs ferramenta/limites
   └─ Retorna { tem_acesso, plano, limite_linhas, erro? }

4. registrar_execucao(usuario_id, ferramenta, linhas, tempo_ms, arquivo)
   └─ Registra execução + calcula ROI
   └─ Enfileira no sync_logs como "pending"
   └─ Retorna { execucao_id, tempo_economizado }

5. enfileirar_email(usuario_id, tipo_email, destinatario, assunto)
   └─ Cria registro em email_logs
   └─ Retorna { email_id, status: 'enfileirado' }

6. processar_upgrade_cakto(email, plano_novo, data_expiracao)
   └─ Webhook de pagamento
   └─ Atualiza plano, enfileira email
   └─ Retorna { usuario_id, novo_plano, data_expiracao }

7. update_updated_at_column() [TRIGGER]
   └─ Atualiza automaticamente o campo updated_at
```

---

## 🌐 Edge Functions (3 no total)

Rodam server-side, permitem chamar APIs externas:

```
1. cakto-webhook
   │
   ├─ Event: purchase.completed
   │  └─ Chama: processar_upgrade_cakto()
   │
   └─ Event: subscription.expired
      └─ Atualiza usuario.plano_tipo = 'gratis'

2. send-email
   │
   ├─ Templates: welcome, upgrade_pro, upgrade_enterprise, etc
   │
   ├─ Integra com: SendGrid (SMTP)
   │
   └─ Atualiza: email_logs.status = 'enviado'

3. sync-background
   │
   ├─ Processa: sync_logs com status 'pending'
   │
   ├─ Marca como: 'synced' quando sucesso
   │
   └─ Atualiza: usuarios.ultima_sincronizacao
```

---

## 🔐 RLS Policies

```
Tabela        | SELECT  | INSERT  | UPDATE  | DELETE
───────────────────────────────────────────────────
usuarios      | own     | own     | own     | admin
execucoes     | own     | own     | -       | -
favoritos     | own     | own     | own     | own
sync_logs     | own     | -       | -       | admin
email_logs    | own     | -       | -       | admin
webhooks_log  | admin   | admin   | admin   | admin
check_updates | public  | -       | -       | -

* own = auth.uid() = id
* admin = auth.role() = 'service_role'
* public = qualquer um pode ler
```

---

## 🔄 Fluxos de Dados

### Fluxo 1: Registrar Execução (Desktop)

```
App Desktop
    │
    ├─ Usuario usa ferramenta offline
    │   └─ Salva no SQLite local
    │
    └─ Reconecta online
        └─ Chama registrar_execucao()
            │
            ├─ Valida acesso [validar_acesso_ferramenta]
            ├─ Calcula ROI
            ├─ Insere em execucoes
            └─ Enfileira sync_logs (status=pending)
                │
                └─ Edge Function: sync-background
                    └─ Processa async
                    └─ Marca como synced
```

### Fluxo 2: Webhook de Pagamento

```
Usuário faz checkout (Cakto)
    │
    └─ Cakto webhook → https://.../cakto-webhook
        │
        ├─ Edge Function recebe evento
        ├─ Valida token (x-cakto-token)
        │
        ├─ Se purchase.completed:
        │   └─ Chama processar_upgrade_cakto()
        │       ├─ Atualiza usuarios.plano_tipo
        │       ├─ Atualiza data_expiracao
        │       └─ Enfileira email de confirmação
        │
        └─ Edge Function: send-email
            └─ Envia via SendGrid
```

### Fluxo 3: Email Automático

```
Evento de negócio (upgrade, welcome, etc)
    │
    └─ enfileirar_email() cria registro
        │
        └─ Edge Function: send-email
            ├─ Busca template
            ├─ Substitui variáveis
            ├─ Chama SendGrid API
            └─ Atualiza status em email_logs
```

---

## 📈 Diagrama Completo

```
┌──────────────────────────────────────────────────────────────┐
│                      SUPABASE PROJECT                         │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─ Database (PostgreSQL)                                   │
│  │  ├─ 8 Tabelas (usuarios, execucoes, etc)                 │
│  │  ├─ 7 Functions (validar, registrar, sincronizar, etc)   │
│  │  ├─ 3 Triggers (update_at automáticos)                   │
│  │  └─ RLS Policies (segurança row-level)                   │
│  │                                                           │
│  ├─ Auth (Supabase Auth / OAuth)                            │
│  │  ├─ Usuários autenticados                                │
│  │  ├─ JWT tokens                                           │
│  │  └─ Senhas hashadas                                      │
│  │                                                           │
│  ├─ Storage (Arquivos processados - opcional)               │
│  │  └─ Resultados de execuções                              │
│  │                                                           │
│  ├─ Realtime (Broadcast - opcional)                         │
│  │  └─ Notificações live para sincronizações                │
│  │                                                           │
│  └─ Edge Functions                                          │
│     ├─ cakto-webhook (recebe pagamentos)                    │
│     ├─ send-email (envia emails via SendGrid)               │
│     └─ sync-background (processa fila async)                │
│                                                               │
└──────────────────────────────────────────────────────────────┘
          ↑                                ↓
    (Entrada)                      (Saída)

    App Desktop          ←→         Web (Next.js)
    Cakto Webhook        ←→         SendGrid
    Stripe               ←→         Webhooks
```

---

## ✅ Checklist de Setup

- [ ] Criar projeto Supabase
- [ ] Executar `complete-schema.sql`
- [ ] Verificar 8 tabelas criadas
- [ ] Verificar 7 functions criadas
- [ ] Verificar 3 triggers criados
- [ ] RLS policies habilitadas
- [ ] Deploy 3 edge functions
- [ ] Setar secrets (SendGrid, Cakto)
- [ ] Testar webhook Cakto
- [ ] Testar envio de email
- [ ] Testar RLS policies
- [ ] Documentar URLs das functions

---

## 🚀 URLs das Functions

```
Cakto Webhook:
https://[PROJECT_REF].supabase.co/functions/v1/cakto-webhook

Send Email:
https://[PROJECT_REF].supabase.co/functions/v1/send-email

Sync Background:
https://[PROJECT_REF].supabase.co/functions/v1/sync-background
```

Replace `[PROJECT_REF]` com seu project ID do Supabase.
