# DataMaster Pro - Web Platform

Plataforma web em Next.js para landing page, autenticação e gerenciamento de downloads/licenças.

## Estrutura do Projeto

```
datamaster-pro-web/
├── app/                           # Páginas Next.js 13+ (App Router)
│   ├── landing/                   # Landing page (/)
│   ├── auth/                      # Login, registro (/auth/*)
│   ├── dashboard/                 # Área de membros (/dashboard/*)
│   ├── planos/                    # Grade de planos (/planos)
│   └── downloads/                 # Central de download (/downloads)
│
├── components/                    # Componentes React reutilizáveis
│   ├── landing/                   # Componentes da landing page
│   │   ├── Hero.tsx
│   │   ├── VideoDemo.tsx
│   │   ├── PlanGrid.tsx
│   │   └── CTA.tsx
│   │
│   └── shared/                    # Componentes globais
│       ├── Header.tsx
│       ├── Footer.tsx
│       ├── AuthGuard.tsx
│       └── StatusIndicator.tsx
│
├── lib/                           # Lógica e utilitários
│   ├── supabase/                  # Cliente Supabase
│   │   ├── client.ts
│   │   ├── auth.ts
│   │   └── database.ts
│   │
│   └── api/                       # Funções de API
│
├── public/                        # Arquivos estáticos
│   ├── images/
│   ├── videos/
│   └── icons/
│
├── styles/                        # Estilos globais (Tailwind)
├── next.config.js                 # Configuração Next.js
├── tailwind.config.js             # Configuração Tailwind CSS
├── tsconfig.json                  # Configuração TypeScript
└── package.json                   # Dependências npm
```

## Tecnologias

- **Next.js 14** - Framework React full-stack
- **TypeScript** - Tipagem estática
- **Tailwind CSS** - Estilização
- **Supabase** - Backend/Auth/Database
- **React Query** - Gerenciamento de dados
- **Next Auth** - Autenticação

## Dependências Principais

```
next==14.0.0
react==18.2.0
@supabase/supabase-js==2.38.0
tailwindcss==3.3.0
typescript==5.2.0
@tanstack/react-query==5.0.0
```

## Páginas

### Landing Page (/)

- Hero section com promessa de valor
- Vídeo demonstrativo
- Grade de planos
- CTA buttons para checkout (Cakto)

### Auth (/auth/\*)

- Login
- Registro
- Recuperação de senha
- Email verification

### Dashboard (/dashboard)

- Status de licença
- Download center
- Changelog
- Logs de uso

### Planos (/planos)

- Grade comparativa de planos
- Informações detalhadas
- Botões de upgrade

### Downloads (/downloads)

- Download do instalador .exe
- Histórico de versões
- Release notes

## Paleta de Cores (Tailwind Config)

```
Fundo: #0F172A (slate-950)
Cards: #1E293B (slate-800)
Bordas: #334155 (slate-700)
Destaque: #10B981 (emerald-500)
Alerta: #F59E0B (amber-500)
Texto primário: #F1F5F9 (slate-100)
Texto secundário: #94A3B8 (slate-400)
```

## Variáveis de Ambiente

```
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
CAKTO_API_KEY=your-cakto-api-key
```

## Como Executar

### Desenvolvimento

```bash
npm install
npm run dev
```

Acesse em `http://localhost:3000`

### Build Production

```bash
npm run build
npm run start
```

## Fluxo de Autenticação

1. Usuário acessa landing page
2. Clica "Começar Grátis" → vai para /auth/register
3. Cria conta (armazenada no Supabase)
4. Recebe email de verificação
5. Após verificação, acessa /dashboard
6. Faz checkout na Cakto
7. Automação: plano atualizado no Supabase
8. App desktop detecta plano ativo

## Next Steps

- [ ] Setup Next.js + Tailwind
- [ ] Integração Supabase
- [ ] Componentes landing page
- [ ] Fluxo de auth
- [ ] Download center
- [ ] Deploy na Vercel/Netlify
