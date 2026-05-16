# 📋 Guia Rápido - Estrutura DataMaster Pro

Aqui está um **roadmap visual** de todos os subsistemas, pastas e o que existe em cada um.

---

## 🏗️ Estrutura Completa

```
ferramente-excel/
│
├─ 🖥️  DESKTOP (Python + CustomTkinter)
│  └─ datamaster-pro-desktop/
│     ├─ src/
│     │  ├─ gui/              ← Interface CustomTkinter
│     │  │  ├─ pages/         ← Login, Dashboard, Ferramentas
│     │  │  └─ components/    ← Botões, Cards, etc
│     │  │
│     │  ├─ core/             ← Lógica principal
│     │  │  ├─ auth/          ← Supabase + Criptografia
│     │  │  ├─ sync/          ← Offline ↔ Online
│     │  │  └─ storage/       ← SQLite local
│     │  │
│     │  ├─ tools/            ← 14 ferramentas
│     │  │  ├─ consolidador/
│     │  │  ├─ categorizador/
│     │  │  ├─ orcamentos/
│     │  │  ├─ minerador/
│     │  │  ├─ conciliador/
│     │  │  ├─ validador_links/
│     │  │  ├─ extrator_reviews/
│     │  │  ├─ calculadora_lucratividade/
│     │  │  ├─ analista_tendencias/
│     │  │  ├─ data_sanitizer/
│     │  │  ├─ conversor_ocr/
│     │  │  └─ gerador_laudos/
│     │  │
│     │  └─ utils/            ← Funções auxiliares
│     │     ├─ encryption/    ← Criptografia
│     │     └─ validators/    ← Validações
│     │
│     ├─ main.py             ← Entry point
│     ├─ config.py           ← Configurações globais
│     ├─ .env.example        ← Template de variáveis
│     └─ requirements.txt    ← Dependências Python
│
├─ 🌐 WEB (Next.js + TypeScript + Tailwind)
│  └─ datamaster-pro-web/
│     ├─ app/                ← Páginas Next.js
│     │  ├─ landing/         ← Homepage
│     │  ├─ auth/            ← Login/Registro
│     │  ├─ dashboard/       ← Área de membros
│     │  ├─ planos/          ← Grid de planos
│     │  └─ downloads/       ← Download center
│     │
│     ├─ components/         ← Componentes React
│     │  ├─ landing/         ← Hero, CTA, Grid
│     │  └─ shared/          ← Header, Footer, etc
│     │
│     ├─ lib/               ← Utilitários
│     │  └─ supabase/       ← Cliente Supabase
│     │
│     ├─ public/            ← Arquivos estáticos
│     ├─ .env.example       ← Template de variáveis
│     ├─ next.config.js     ← Config Next.js
│     ├─ tailwind.config.js ← Config Tailwind
│     └─ package.json       ← Dependências npm
│
├─ 🔗 SHARED (Tipos, Constantes, Schemas)
│  └─ datamaster-pro-shared/
│     ├─ schemas/           ← SQL para Supabase
│     ├─ constants/         ← Planos, ferramentas, cores
│     └─ types/             ← Interfaces TypeScript
│
└─ 📚 DOCS
   ├─ superpowers/specs/    ← Design specifications
   └─ architecture/
      └─ PROJECT_STRUCTURE.md ← Este arquivo!
```

---

## 📊 Matriz: O que está em cada pasta

| Componente                    | Local                                      | Linguagem  | Propósito           |
| ----------------------------- | ------------------------------------------ | ---------- | ------------------- |
| **Interface Desktop**         | `datamaster-pro-desktop/src/gui/`          | Python     | CustomTkinter UI    |
| **Lógica de Ferramentas**     | `datamaster-pro-desktop/src/tools/`        | Python     | Pandas + Openpyxl   |
| **Autenticação**              | `datamaster-pro-desktop/src/core/auth/`    | Python     | Supabase + Cripto   |
| **Sincronização**             | `datamaster-pro-desktop/src/core/sync/`    | Python     | Offline/Online      |
| **BD Local**                  | `datamaster-pro-desktop/src/core/storage/` | Python     | SQLite              |
| **Landing Page**              | `datamaster-pro-web/app/landing/`          | TypeScript | Next.js             |
| **Auth Web**                  | `datamaster-pro-web/app/auth/`             | TypeScript | Supabase Auth       |
| **Dashboard Web**             | `datamaster-pro-web/app/dashboard/`        | TypeScript | Área de membros     |
| **Cliente Supabase**          | `datamaster-pro-web/lib/supabase/`         | TypeScript | @supabase/js        |
| **Constantes Compartilhadas** | `datamaster-pro-shared/constants/`         | Python/TS  | Planos, ferramentas |
| **Tipos Compartilhados**      | `datamaster-pro-shared/types/`             | Python/TS  | Interfaces          |
| **Schemas BD**                | `datamaster-pro-shared/schemas/`           | SQL        | Supabase tables     |

---

## 🎯 Por onde começar?

### 1️⃣ Setup Inicial

**Desktop:**

```bash
cd datamaster-pro-desktop
pip install -r requirements.txt
python main.py
```

**Web:**

```bash
cd datamaster-pro-web
npm install
npm run dev
```

---

### 2️⃣ Implementar Banco de Dados

- [ ] Acessar Supabase dashboard
- [ ] Executar queries em `datamaster-pro-shared/schemas/supabase.sql`
- [ ] Criar tabelas: `usuarios`, `execucoes`, `check_updates`, `favoritos`

---

### 3️⃣ Implementar Desktop (por ordem)

1. **GUI Base** (`src/gui/pages/LoginPage`)
   - Formulário de login
   - Integração com Supabase

2. **Dashboard** (`src/gui/pages/DashboardPage`)
   - Grid de 14 ferramentas
   - Sistema de favoritos
   - Status LED (online/offline)

3. **Cada Ferramenta** (`src/tools/[nome]/`)
   - Consolidador → Pandas merge
   - Categorizador → Keyword matching
   - Orçamentos → PDF fill (ReportLab)
   - Minerador → Web scraping (requests)
   - Conciliador → Fuzzy matching
   - Validador Links → Playwright
   - Extrator Reviews → TextBlob/NLTK
   - Calculadora Lucratividade → Arbitragem
   - Analista Tendências → Content mining
   - Data Sanitizer → Regex/Normalização
   - Conversor OCR → Tesseract
   - Gerador Laudos → ReportLab

4. **Core Features** (`src/core/`)
   - Auth manager (login + cripto)
   - Sync manager (fila offline)
   - Storage manager (SQLite)

---

### 4️⃣ Implementar Web (por ordem)

1. **Landing Page** (`app/landing/`)
   - Hero section
   - Video demo
   - Plan grid
   - CTAs

2. **Auth** (`app/auth/`)
   - Login page
   - Register page
   - Email verification

3. **Dashboard** (`app/dashboard/`)
   - License status
   - Download center
   - Changelog viewer

---

## 🔄 Fluxo de Dados

```
┌─────────────────────┐
│   Website Landing   │
└────────────┬────────┘
             ↓
    Usuário faz login
             ↓
┌─────────────────────────┐
│   Supabase Auth        │
│   (usuarios table)     │
└────────────┬────────────┘
             ↓
   Plano atualizado? ✓
             ↓
┌────────────────────────────┐
│   Desktop App detecta      │
│   (sync do SQLite)         │
└────────────┬───────────────┘
             ↓
   Habilita ferramentas
      conforme plano
             ↓
┌─────────────────────┐
│   Usa ferramenta    │
│   (offline ou on)   │
└────────────┬────────┘
             ↓
  Execução salva em:
  - SQLite (local)
  - Fila sync
             ↓
   Reconecta?
             ↓
┌────────────────────────┐
│   Sync Manager         │
│   (envia para cloud)   │
└────────────┬───────────┘
             ↓
┌────────────────────────┐
│   Supabase Execucoes   │
│   (analytics/ROI)      │
└────────────────────────┘
```

---

## 📁 Arquivos Importantes

**Config & Setup:**

- `datamaster-pro-desktop/config.py` — Configurações globais
- `datamaster-pro-desktop/.env.example` — Variáveis de ambiente
- `datamaster-pro-web/.env.example` — Variáveis web

**Tipos & Constantes Compartilhados:**

- `datamaster-pro-shared/constants/__init__.py` — Planos, ferramentas, cores
- `datamaster-pro-shared/types/__init__.py` — Interfaces
- `datamaster-pro-shared/schemas/supabase.sql` — Schema BD

**Entry Points:**

- `datamaster-pro-desktop/main.py` — Inicia app desktop
- `datamaster-pro-web/app/page.tsx` — Homepage web

---

## ✅ Checklist de Status

- [x] Estrutura de pastas criada
- [x] README em cada subsistema
- [x] Config files (.env.example)
- [x] Constants e types compartilhados
- [x] SQL schemas definidos
- [x] Documentação de arquitetura
- [ ] Implementação desktop (em progresso)
- [ ] Implementação web (em progresso)
- [ ] Testes
- [ ] Deploy

---

## 🚀 Próximas Fases

**Fase 2: Monetização & Planos**

- Refinar estratégia de preços
- Implementar limites por plano
- Upsell na interface

**Fase 3: Segurança & Offline**

- Implementar criptografia completa
- Testes de sincronização
- Performance offline

---

## 📞 Suporte

Para dúvidas sobre a estrutura:

- Veja os READMEs em cada pasta
- Consulte `PROJECT_STRUCTURE.md` (este arquivo)
- Verifique os arquivos de exemplo (.env.example, config.py, etc)
