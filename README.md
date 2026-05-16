# DataMaster Pro

Ferramentas de automação para planilhas Excel com tecnologia de ponta.

## Funcionalidades

### Ferramentas de Dados
- **Consolidador**: Une múltiplas planilhas em uma estrutura única
- **Categorizador**: Classifica transações por palavras-chave
- **Conciliador**: Cruza extratos bancários com vendas
- **Data Sanitizer**: Limpa e normaliza dados (CPF, CNPJ, telefones, endereços)
- **Conversor OCR**: Extrai tabelas de imagens/PDFs escaneados para Excel

### Ferramentas de Precificação
- **Minerador**: Captura preços de sites concorrentes
- **Validador de Links**: Verifica se links estão ativos e produtos disponíveis
- **Extrator de Reviews**: Extrai e analisa sentimento de reviews de marketplaces
- **Calculadora de Lucratividade**: Calcula margem de lucro e identifica arbitragem

### Ferramentas de Análise
- **Analista de Tendências**: Identifica produtos trending em nichos específicos
- **Gerador de Laudos**: Gera PDFs de conformidade cruzando extratos com notas fiscais

### Outras
- **Orçamentos**: Preenche templates de PDF em massa

## Tech Stack

- **Desktop**: Python, CustomTkinter, Pandas, Supabase
- **Web**: Next.js 14, TypeScript, Tailwind CSS, Supabase SSR
- **Backend**: Supabase (Auth, Database, Edge Functions)

## Quick Start

### Pré-requisitos

- Python 3.12+
- Node.js 18+

### Desktop (Python)

```bash
# 1. Clone o projeto
cd datamaster-pro-desktop

# 2. Crie o ambiente virtual
python -m venv .venv

# 3. Ative o ambiente
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# 4. Instale as dependências
pip install -r requirements.txt

# 5. Configure as variáveis de ambiente
cp .env.example .env
# Edite .env com sua URL e keys do Supabase

# 6. Execute a aplicação
python main.py
```

### Web (Next.js)

```bash
cd datamaster-pro-web

# Install dependencies
npm install

# Configure .env
cp .env.local.example .env.local

# Development
npm run dev

# Build
npm run build
```

### Testes

```bash
cd datamaster-pro-desktop
pip install pytest pytest-cov
pytest tests/ -v
```

### Build .exe

```bash
cd datamaster-pro-desktop
pip install pyinstaller
pyinstaller datamaster.spec --clean
```

## Variáveis de Ambiente

| Variável | Descrição |
|----------|-----------|
| `SUPABASE_URL` | URL do projeto Supabase |
| `SUPABASE_ANON_KEY` | Chave anônima do Supabase |
| `SUPABASE_SERVICE_ROLE_KEY` | Chave de serviço (apenas server) |
| `ENVIRONMENT` | `development` ou `production` |
| `APP_VERSION` | Versão da aplicação |

## Estrutura do Projeto

```
datamaster-pro-desktop/
├── src/
│   ├── core/         # Auth, Storage, Sync
│   ├── gui/          # Pages e Components
│   │   └── tools/    # 14 páginas de ferramentas
│   ├── tools/        # Backend das ferramentas
│   │   ├── consolidador/
│   │   ├── categorizador/
│   │   ├── orcamentos/
│   │   ├── minerador/
│   │   ├── conciliador/
│   │   ├── validador_links/
│   │   ├── extrator_reviews/
│   │   ├── calculadora_lucratividade/
│   │   ├── analista_tendencias/
│   │   ├── data_sanitizer/
│   │   ├── conversor_ocr/
│   │   └── gerador_laudos/
│   └── utils/        # Helpers
├── tests/            # Testes unitários
├── config.py         # Configurações
└── main.py          # Entry point

datamaster-pro-web/
├── app/              # Next.js App Router
├── components/       # React Components
└── lib/             # Supabase client
```

## Deploy

### Web (Vercel)

```bash
cd datamaster-pro-web
vercel deploy --prod
```

### Edge Functions

```bash
supabase functions deploy cakto-webhook
supabase functions deploy send-email
supabase functions deploy sync-background
```

## Licença

Proprietary © 2024 DataMaster Team