# DataMaster Pro - Estrutura Completa do Projeto

Visão geral da arquitetura de pastas e como os 3 subsistemas se conectam.

## 📦 Estrutura Raiz

```
ferramente-excel/
├── datamaster-pro-desktop/        # Aplicação Desktop (Python)
├── datamaster-pro-web/            # Plataforma Web (Next.js)
├── datamaster-pro-shared/         # Recursos Compartilhados
├── docs/
│   ├── superpowers/specs/         # Design specs
│   └── architecture/              # Documentação arquitetura
├── README.md
├── TODO.md
├── CHANGELOG.md
└── Tecnologia.md
```

---

## 🖥️ SUBSISTEMA 1: Desktop Application

**Localização:** `datamaster-pro-desktop/`  
**Linguagem:** Python 3.10+  
**Framework GUI:** CustomTkinter

### Objetivo

Processamento local de planilhas com 5 ferramentas + sincronização offline-first.

### Principais Componentes

| Pasta               | Responsabilidade             | Tecnologia                 |
| ------------------- | ---------------------------- | -------------------------- |
| `src/gui/`          | Interface visual             | CustomTkinter              |
| `src/core/auth/`    | Login + criptografia         | Supabase-py + cryptography |
| `src/core/sync/`    | Sincronização offline↔online | SQLite + requests          |
| `src/core/storage/` | Armazenamento local          | SQLite3                    |
| `src/tools/`        | As 5 ferramentas             | Pandas + Openpyxl          |
| `build/`            | Saída PyInstaller            | .exe + setup               |

### Fluxo de Execução

```
main.py
  ↓
App() [CustomTkinter]
  ├→ gui/pages/LoginPage
  ├→ gui/pages/DashboardPage
  ├→ gui/components/ToolCard
  │
  ├→ core/auth/AuthManager
  │  └→ Supabase + SQLite criptografado
  │
  ├→ core/sync/SyncManager
  │  └→ Fila offline + replicação
  │
  └→ tools/[ferramenta]/
     └→ Pandas + Openpyxl + lógica específica
```

### Stack Tecnológico

```
┌─────────────────────────────────┐
│   Camada GUI (CustomTkinter)    │
├─────────────────────────────────┤
│  Camada Core (Auth, Sync, DB)   │
├─────────────────────────────────┤
│  Camada Tools (5 ferramentas)   │
├─────────────────────────────────┤
│  Supabase API ← → SQLite Local  │
└─────────────────────────────────┘
```

---

## 🌐 SUBSISTEMA 2: Web Platform

**Localização:** `datamaster-pro-web/`  
**Linguagem:** TypeScript / JavaScript  
**Framework:** Next.js 14 (App Router)  
**Estilização:** Tailwind CSS

### Objetivo

Landing page de vendas + área de membros (download + gerenciamento).

### Principais Componentes

| Pasta                 | Responsabilidade          | Tecnologia            |
| --------------------- | ------------------------- | --------------------- |
| `app/landing/`        | Homepage                  | Next.js Pages         |
| `app/auth/`           | Login/Registro            | Supabase Auth         |
| `app/dashboard/`      | Área de membros           | React Components      |
| `app/downloads/`      | Central de download       | File management       |
| `components/landing/` | Hero, CTA, Grid de planos | React + Tailwind      |
| `lib/supabase/`       | Cliente Supabase          | @supabase/supabase-js |

### Fluxo de Navegação

```
/ (Landing Page)
  ├→ Hero Section
  ├→ Video Demonstrativo
  ├→ Grid de Planos
  └→ CTA "Começar Grátis" → /auth/register

/auth/register
  ├→ Cria usuário no Supabase
  ├→ Envia email de verificação
  └→ Redireciona para /auth/verify

/auth/verify
  └→ Valida email → /dashboard

/dashboard
  ├→ Status de licença
  ├→ Download center (.exe)
  ├→ Changelog
  └→ Logs de uso

/planos
  └→ Comparação de planos + upgrade
```

### Stack Tecnológico

```
┌──────────────────────────────────┐
│   Next.js Pages + React          │
│   (Servidor + Cliente)           │
├──────────────────────────────────┤
│   Tailwind CSS (Estilo)          │
├──────────────────────────────────┤
│   Supabase Client (Auth + DB)    │
├──────────────────────────────────┤
│   Deploy: Vercel / Netlify       │
└──────────────────────────────────┘
```

---

## 🔗 SUBSISTEMA 3: Shared Resources

**Localização:** `datamaster-pro-shared/`

### Objetivo

Compartilhar tipos, constantes e esquemas entre Desktop e Web.

### Componentes

| Pasta        | Conteúdo                   |
| ------------ | -------------------------- |
| `schemas/`   | SQL scripts para Supabase  |
| `constants/` | Planos, ferramentas, cores |
| `types/`     | Interfaces TypeScript      |

### Exemplo de Compartilhamento

```
Desktop (Python):
  from shared.constants import PLANOS
  if user_plan == PLANOS.PRO:
    enable_all_tools()

Web (TypeScript):
  import { PLANOS } from '@shared/constants'
  const isUpgradeable = PLANOS[plan].preco > 0
```

---

## 🔄 Fluxo de Dados Entre Subsistemas

### Cenário 1: Usuário Nova Compra

```
1. Usuário acessa Website
   ↓
2. Faz login em /auth → Supabase
   ↓
3. Vai para /planos → Escolhe Pro
   ↓
4. Checkout na Cakto → Webhook
   ↓
5. Supabase atualiza plano_tipo='pro'
   ↓
6. App Desktop detecta atualização (sync)
   ↓
7. Desktop: Habilita todas as 5 ferramentas
```

### Cenário 2: Usuário Usa Offline

```
Desktop (Offline):
  1. Abre app sem internet
  2. Carrega dados do SQLite
  3. Usa ferramenta normalmente
  4. Salva resultado localmente

Desktop (Reconecta):
  5. Detecta internet
  6. Sincroniza fila com Supabase
  7. Atualiza analytics

Website:
  8. Dashboard mostra última execução
```

### Cenário 3: Atualização de App

```
1. Desenvolvedor faz build em `build/`
2. Envia .exe para servidor
3. Atualiza `check_updates` no Supabase
4. Desktop consulta tabela periodicamente
5. Exibe notificação "Nova versão"
6. Faz download e reinstala
```

---

## 📱 Base de Dados Supabase

### Tabelas Principais

```
┌──────────────┐
│   usuarios   │
├──────────────┤
│ id (PK)      │
│ email        │
│ plano_tipo   │
│ expiracao    │
└──────────────┘

┌──────────────┐
│  execucoes   │
├──────────────┤
│ id (PK)      │
│ usuario_id   │
│ ferramenta   │
│ linhas       │
│ timestamp    │
└──────────────┘

┌──────────────┐
│ check_upd... │
├──────────────┤
│ versao_atual │
│ versao_nova  │
│ url_download │
└──────────────┘
```

---

## 🚀 Fluxo de Build & Deploy

### Desktop (.exe)

```
Python Code
  ↓
PyInstaller
  ↓
build/datamaster-pro.exe
  ↓
Upload servidor
  ↓
Atualizar check_updates.versao_disponivel
```

### Website

```
TypeScript Code
  ↓
npm run build
  ↓
.next/ folder
  ↓
Deploy Vercel
  ↓
www.datamaster.pro
```

---

## 📊 Estratégia de Sincronização

### Local (Desktop - SQLite)

```
usuarios_local
├─ id
├─ email
├─ plano_tipo
├─ token_criptografado
└─ data_sincronizacao

execucoes_local (fila)
├─ id
├─ ferramenta
├─ status (pending | synced)
└─ timestamp
```

### Cloud (Supabase)

```
usuarios_cloud
├─ id
├─ email
├─ plano_tipo
└─ last_sync

execucoes_cloud
├─ id
├─ usuario_id
├─ ferramenta
└─ timestamp
```

### Algoritmo de Sync

```
Se OFFLINE:
  - Salva execução em fila local
  - Trabalha com SQLite

Se ONLINE:
  - Compara timestamps local vs cloud
  - Envia dados novos para cloud
  - Atualiza dados cloud para local
  - Marca como synced
```

---

## 🔐 Segurança

### Desktop

- Tokens armazenados criptografados (cryptography)
- SQLite com encryption
- Senha do usuário nunca salva

### Web

- Autenticação Supabase (OAuth)
- JWT tokens
- CORS configurado
- Rate limiting

---

## ✅ Checklist de Implementação

- [ ] Setup desktop (Python + CustomTkinter)
- [ ] Setup web (Next.js + Tailwind)
- [ ] Supabase: Criar schemas
- [ ] Shared: Definir tipos e constantes
- [ ] Desktop: Implementar as 5 ferramentas
- [ ] Desktop: Implementar sincronização
- [ ] Web: Landing page completa
- [ ] Web: Auth flow
- [ ] Web: Download center
- [ ] Testes de sincronização offline/online
- [ ] Build .exe
- [ ] Deploy web
- [ ] Documentação
