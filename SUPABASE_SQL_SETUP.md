# Como Executar o SQL no Supabase

## Opção 1: Via Dashboard Supabase (Recomendado)

1. **Abra o Supabase Dashboard**
   - URL: https://app.supabase.com
   - Entre em seu projeto DataMaster Pro

2. **Vá para SQL Editor**
   - No menu lateral esquerdo: "SQL Editor"
   - Clique em "New Query"

3. **Cole o SQL Completo**
   - Copie todo o conteúdo de `plan_limits_schema.sql`
   - Cole na área de edição
   - Clique em "Run" (ou Cmd+Enter)

4. **Verifique a Execução**
   - Você deve ver mensagens de sucesso
   - Se houver erro, corrija e tente novamente

---

## Opção 2: Via Supabase CLI

```bash
# 1. Instale Supabase CLI (se ainda não tiver)
npm install -g supabase

# 2. Faça login
supabase login

# 3. Execute a migração
supabase db push

# 4. Se tiver arquivo SQL pronto, execute diretamente
supabase sql < plan_limits_schema.sql
```

---

## Opção 3: Via psql (linha de comando Postgres)

```bash
# 1. Obtenha a connection string no Supabase Dashboard
# Settings > Database > Connection Pooling > Connection string

# 2. Execute o SQL
psql "sua_connection_string" < plan_limits_schema.sql

# Ou execute linha por linha copiando do arquivo
```

---

## Verificar se as Tabelas Foram Criadas

Após executar o SQL, verifique no Supabase:

1. **Table Editor**
   - Menu lateral: "Table Editor"
   - Você deve ver 3 novas tabelas:
     - `execution_logs`
     - `scheduled_tasks`
     - `tool_configurations`

2. **Verifique Estrutura**
   ```sql
   -- Execute no SQL Editor
   SELECT table_name FROM information_schema.tables 
   WHERE table_schema = 'public' 
   AND table_name IN ('execution_logs', 'scheduled_tasks', 'tool_configurations');
   ```

3. **Verifique RLS (Row Level Security)**
   ```sql
   -- Deve retornar 'true' para todas
   SELECT tablename, rowsecurity FROM pg_tables 
   WHERE schemaname='public' 
   AND tablename IN ('execution_logs', 'scheduled_tasks', 'tool_configurations');
   ```

---

## Teste Rápido de Funcionamento

Execute este SQL para testar se tudo funciona:

```sql
-- Teste 1: Inserir log de execução
INSERT INTO execution_logs (
    execution_id, 
    user_id, 
    tool_name, 
    timestamp, 
    duration_seconds, 
    lines_processed, 
    file_size_bytes, 
    status
) VALUES (
    'test-exec-' || random()::TEXT,
    (SELECT id FROM auth.users LIMIT 1),
    'consolidador',
    NOW()::TEXT,
    5.2,
    1200,
    524288,
    'success'
) RETURNING *;

-- Teste 2: Verificar view de ROI
SELECT * FROM roi_summary_7days LIMIT 5;

-- Teste 3: Verificar upcoming tasks
SELECT * FROM upcoming_scheduled_tasks LIMIT 5;
```

---

## Possíveis Erros e Soluções

### Erro: "permission denied for schema public"
- **Solução**: Você não é owner da database. Entre em contato com administrador Supabase.

### Erro: "relation already exists"
- **Solução**: As tabelas já foram criadas. Tudo OK!
- Se precisar recriá-las, execute:
  ```sql
  DROP TABLE IF EXISTS execution_logs CASCADE;
  DROP TABLE IF EXISTS scheduled_tasks CASCADE;
  DROP TABLE IF EXISTS tool_configurations CASCADE;
  ```

### Erro: "invalid syntax"
- **Solução**: Copie o SQL novamente, certifique-se de que está inteiro e sem cortes.

### RLS policies não funcionam
- **Solução**: Certifique-se de que o Supabase Auth está configurado corretamente.
- Verifique: Settings > Authentication > Providers

---

## Próximo Passo

Após criar as tabelas, você precisa:

1. **Adicionar métodos ao `storage_manager.py`**
   - Para inserir/recuperar dados dessas tabelas

2. **Integrar nos tool_pages**
   - Para registrar logs de execução
   - Para criar/gerenciar tarefas agendadas

3. **Ver arquivo**: `INTEGRATION_GUIDE.md` para detalhes

---

## Suporte

Se encontrar problemas:
1. Verifique se a connection string está correta
2. Verifique se você é admin do projeto Supabase
3. Veja os logs no Supabase Dashboard: Settings > Database > Postgres Logs
