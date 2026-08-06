# Plano de Contingencia — DataMaster Pro

Estrategias de recuperacao, tolerancia a falhas e procedimentos de emergencia.

---

## 1. Classificacao de Incidentes

| Nivel | Severidade | Exemplo                           | Tempo Max Resposta |
|-------|------------|-----------------------------------|--------------------|
| P1    | Critico    | Supabase down, dados corrompidos  | 15 minutos         |
| P2    | Alto       | Sync falhando, webhook erro       | 1 hora             |
| P3    | Medio      | Login lento, UI com bug           | 4 horas            |
| P4    | Baixo      | Feature faltante, melhoria        | Proximo sprint     |

---

## 2. Cenarios de Falha e Respostas

### 2.1 Supabase Indisponivel

**Sintoma:** Desktop nao consegue autenticar ou sincronizar.

**Resposta Automatica (Desktop):**
```
1. Circuit Breaker detecta falha (5 tentativas)
2. Estado muda: CLOSED → OPEN
3. App entra em modo offline completo
4. Dados persistem em SQLite local
5. Retry com backoff exponencial (1s, 2s, 4s, 8s, 16s, max 60s)
6. Apos 60s: circuito HALF_OPEN (1 tentativa)
7. Se sucesso: circuito CLOSED
8. Se falha: circuito OPEN novamente
```

**Resposta Manual:**
1. Verificar status em https://status.supabase.com
2. Se incidente confirmado: notificar usuarios via dashboard
3. Se prolongado (>2h): considerar manutencao programada
4. Apos restauracao: sync automatico respeita fila de prioridade

---

### 2.2 Banco de Dados SQLite Corrompido

**Sintoma:** App nao abre, erro de integridade, dados inconsistentes.

**Resposta Automatica:**
```
1. BackupManager detecta corrupcao via PRAGMA integrity_check
2. Restaura ultimo backup valido (rotacao de 5 backups)
3. Se backup corrompido: tenta penultimo backup
4. Se nenhum backup valido: cria novo DB vazio
5. Loga erro completo em audit_logger
```

**Procedimento Manual:**
```bash
# 1. Localizar backups
ls ~/.datamaster/backups/

# 2. Verificar integridade de cada backup
sqlite3 backup_2024-01-01.db "PRAGMA integrity_check;"

# 3. Restaurar manualmente
cp backup_valido.db ~/.datamaster/datamaster.db

# 4. Se nenhum backup funciona: recriar DB
python -c "from src.core.storage.storage_manager import StorageManager; StorageManager()"
```

---

### 2.3 Chaves de Seguranca Comprometidas

**Sintoma:** Atividade suspeita, acesso nao autorizado, vazamento de .env.

**Procedimento Imediato (15 min):**
```
1. SUPABASE: Regenerar ANON_KEY no Dashboard
2. SUPABASE: Regenerar SERVICE_ROLE_KEY no Dashboard
3. SCRAPERAPI: Regenerar API key
4. GOOGLE: Revogar OAuth client secret
5. CAKTO: Regenerar webhook secret
```

**Procedimento Seguinte (1h):**
```
6. Limpar .env de todos os repositorios
7. Adicionar .env ao .gitignore (se nao esta)
8. Usar git filter-branch ou BFG para remover .env do historico
9. Verificar se chaves antigas ainda funcionam (nao deveriam)
10. Notificar usuarios se dados foram expostos
```

**Prevencao:**
- Chaves em .pyc ofuscados (build_pyc_keys.py)
- Nunca commitar .env em repositorios publicos
- Service role key NUNCA em cliente desktop
- Usar secrets manager em producao

---

### 2.4 Webhook de Pagamento Falhando

**Sintoma:** Usuarios nao recebem upgrade apos pagamento.

**Diagnostico:**
```bash
# 1. Verificar logs do webhook
supabase functions logs cakto-webhook

# 2. Verificar tabela de pagamentos
SELECT * FROM webhooks_log ORDER BY created_at DESC LIMIT 10;

# 3. Verificar se usuario foi atualizado
SELECT email, plano_tipo, data_expiracao FROM usuarios WHERE email = 'user@email.com';
```

**Resolucao Manual:**
```sql
-- Se pagamento confirmado mas plano nao atualizado:
UPDATE usuarios
SET plano_tipo = 'pro',
    data_expiracao = '2025-01-01',
    updated_at = NOW()
WHERE email = 'user@email.com';

-- Se email nao enviado:
SELECT enfileirar_email(
    'usuario-uuid',
    'upgrade_pro',
    'user@email.com',
    'Seu upgrade para Pro foi confirmado!'
);
```

---

### 2.5 Dados Locais Perdidos (Desktop)

**Sintoma:** Usuario formata PC, HD corrompido, app desinstalado.

**Estrategia de Protecao:**
```
1. Backup automatico: a cada 50 operacoes ou 24h
2. Rotacao: ultimos 5 backups mantidos
3. Sync cloud: dados importantes replicados no Supabase
4. Exportacao LGPD: usuario pode exportar dados em JSON
```

**Recuperacao:**
```
1. reinstalar app
2. Login com mesmas credenciais
3. Sync automatico baixa dados do Supabase
4. Dados de execucoes restaurados do cloud
5. Configuracoes locais recriadas com defaults
```

---

### 2.6 Servidor de Download (.exe) Indisponivel

**Sintoma:** Usuarios nao conseguem baixar nova versao.

**Resposta:**
```
1. Verificar se servidor esta online
2. Se indisponivel: usar mirror alternativo (Google Drive, GitHub Releases)
3. Atualizar URL de download no Supabase (check_updates.url_download)
4. Desktop detecta mudanca e usa nova URL
```

**Prevencao:**
- Manter .exe em multiplos servidores
- GitHub Releases como backup
- URL de download configuravel via Supabase

---

## 3. Mecanismos de Tolerancia a Falhas Implementados

### 3.1 Circuit Breaker

```
Estados: CLOSED → OPEN → HALF_OPEN
Threshold: 5 falhas consecutivas
Recovery: 60 segundos
Max tentativas HALF_OPEN: 1
```

**Servicos protegidos:**
- Supabase upload (sync)
- Supabase download (sync)
- Supabase scheduled tasks
- ScraperAPI (minerador)
- Playwright (validador_links, minerador)

### 3.2 Retry com Backoff Exponencial

```
Max tentativas: 3
Base delay: 1.0s
Max delay: 30.0s
Jitter: ±20%
```

**Aplicado em:**
- Todas as chamadas HTTP externas
- Operacoes de banco de dados
- Upload/download de sync

### 3.3 Rate Limiting

```
Desktop API: 60 req/min (geral), 10 req/min (auth)
Web: 30 req/min (webhook), 10 req/min (auth)
ScraperAPI: 10 req/s (configuravel)
```

### 3.4 Cache com TTL

```
MemoryCache:
  - Stats do usuario: 30s TTL
  - Ultima tarefa por tool: 10s TTL
  - Maximo 1000 entradas
  - Limpeza automatica a cada 60s
```

### 3.5 Backup Automatico

```
Trigger: a cada 50 operacoes OU 24 horas
Formato: SQLite backup (sqlite3.backup())
Rotacao: ultimos 5 backups
Verificacao: PRAGMA integrity_check
Criptografia: Fernet (AES-128-CBC)
Local: ~/.datamaster/backups/
```

---

## 4. Procedimentos de Recuperacao de Desastres

### 4.1 Restauracao Completa do Supabase

**Cenario:** Banco Supabase perdido ou corrompido.

```bash
# 1. Criar novo projeto Supabase
# 2. Executar schema completo
supabase db push < docs/setup/complete-schema.sql

# 3. Restaurar dados do ultimo backup
# (Supabase Dashboard → Database → Backups)

# 4. Redeploy Edge Functions
supabase functions deploy cakto-webhook
supabase functions deploy send-email
supabase functions deploy sync-background

# 5. Atualizar chaves no desktop
# (copiar novas anon_key e url para .env)
```

### 4.2 Restauracao do Desktop

**Cenario:** Computador do usuario formatado.

```
1. Download do .exe (site ou mirror)
2. Instalacao via instalador
3. Login com credenciais existentes
4. Sync automatico: dados do Supabase → SQLite
5. Configuracoes: defaults + ultima sincronizacao
```

### 4.3 Migração entre Versoes

**Cenario:** Atualizacao quebrante de schema.

```
1. Desktop detecta versao incompativel
2. Migra SQLite automaticamente (config.py:migrate_db)
3. Sync pausa durante migracao
4. Apos migracao: sync resume
5. Se falha: rollback para backup anterior
```

---

## 5. Contatos de Emergencia

| Servico     | Contato                          | URL                                |
|-------------|----------------------------------|------------------------------------|
| Supabase    | Dashboard → Support              | https://app.supabase.com           |
| Vercel      | Dashboard → Support              | https://vercel.com/dashboard       |
| Google OAuth| Console → APIs & Services        | https://console.cloud.google.com   |
| Cakto       | Dashboard → Suporte              | https://app.cakto.com.br           |
| ScraperAPI  | Dashboard → Support              | https://www.scraperapi.com         |

---

## 6. Monitoramento e Alertas

### 6.1 Metricas Chave (APM)

| Metrica                      | Threshold Alerta  |
|------------------------------|-------------------|
| Tempo de sync                | > 30 segundos     |
| Tempo de execucao de tool    | > 120 segundos    |
| Taxa de erro de API          | > 5%              |
| Circuit Breaker OPEN         | Qualquer ativacao |
| Backup falhou                | Qualquer falha    |
| Memoria SQLite               | > 500MB           |

### 6.2 Logs de Auditoria

```
Eventos logados:
- login / logout
- plan_change (upgrade/downgrade)
- export (LGPD)
- tool_execution (start/complete/fail)
- sync (upload/download/fail)
- backup (create/restore/fail)
- security (key_rotation, breach_detection)
```

### 6.3 Health Checks

```
Desktop:
  - SQLite: PRAGMA integrity_check (a cada 24h)
  - Sync: fila de pendencias > 100? (alerta)
  - Backup: ultimo backup > 48h? (alerta)

Web:
  - GET /api/health (a cada 5 min via UptimeRobot)
  - Supabase: connection test (a cada 1 min)
```

---

## 7. Plano de Comunicacao

### 7.1 Manutencao Programada

```
1. Anunciar com 72h de antecedencia (dashboard + email)
2. Modo manutencao: mensagem no app
3. Dados preservados: sync pausa, nao perde
4. Apos manutencao: sync automatico retoma
```

### 7.2 Incidente de Seguranca

```
1. Identificar escopo (15 min)
2. Rotacionar chaves comprometidas (15 min)
3. Notificar usuarios afetados (1h)
4. Relatorio publico (24h)
5. Correcao de causa raiz (48h)
```

---

*Plano de contingencia atualizado em 2026-06-21. Cobertura: 6 cenarios de falha, 5 mecanismos de tolerancia, procedimentos de recuperacao.*
