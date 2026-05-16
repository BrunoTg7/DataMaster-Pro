# DataMaster Pro - Shared Resources

Recursos compartilhados entre a aplicação desktop e web.

## Estrutura

```
datamaster-pro-shared/
├── schemas/                       # Esquemas de dados (Supabase)
│   ├── usuarios.sql
│   ├── planos.sql
│   ├── execucoes.sql
│   ├── favoritos.sql
│   └── check_updates.sql
│
├── constants/                     # Constantes compartilhadas
│   ├── planos.ts                  # Tipos de planos e limites
│   ├── tools.ts                   # Metadados das ferramentas
│   └── colors.ts                  # Paleta de cores
│
└── types/                         # Tipos TypeScript/Interfaces
    ├── user.ts
    ├── plan.ts
    ├── execution.ts
    ├── tool.ts
    └── sync.ts
```

## Schemas SQL (Supabase)

### Tabela: usuarios

```sql
- id (UUID, PK)
- email (string, unique)
- nome (string)
- plano_tipo (enum: 'gratis', 'pro', 'enterprise')
- data_expiracao (date)
- created_at (timestamp)
- updated_at (timestamp)
```

### Tabela: execucoes

```sql
- id (UUID, PK)
- usuario_id (UUID, FK)
- ferramenta (string)
- linhas_processadas (int)
- tempo_execucao_ms (int)
- tempo_economizado_minutos (int)
- resultado_arquivo (string)
- created_at (timestamp)
```

### Tabela: check_updates

```sql
- id (int, PK)
- versao_atual (string)
- versao_disponivel (string)
- url_download (string)
- changelog (text)
- updated_at (timestamp)
```

## Constants

### Planos (planos.ts)

```typescript
export const PLANOS = {
  GRATIS: {
    id: "gratis",
    name: "Grátis",
    limit_linhas: 10,
    limit_ferramentas: ["consolidador", "categorizador"],
    watermark: true,
    preco: 0,
  },
  PRO: {
    id: "pro",
    name: "Pro",
    limit_linhas: null,
    limit_ferramentas: [
      "consolidador",
      "categorizador",
      "orcamentos",
      "minerador",
      "conciliador",
    ],
    watermark: false,
    preco: 29.9,
  },
  ENTERPRISE: {
    id: "enterprise",
    name: "Enterprise",
    limit_linhas: null,
    limit_ferramentas: ["custom"],
    watermark: false,
    preco: "custom",
  },
};
```

### Ferramentas (tools.ts)

```typescript
export const TOOLS = {
  consolidador: {
    id: "consolidador",
    name: "Consolidador",
    description: "Une múltiplas planilhas em uma estrutura única",
    icon: "merge",
    minPlano: "gratis",
  },
  categorizador: {
    id: "categorizador",
    name: "Categorizador",
    description: "Classifica transações por palavras-chave",
    icon: "tag",
    minPlano: "gratis",
  },
  // ... mais ferramentas
};
```

### Cores (colors.ts)

```typescript
export const COLORS = {
  background: "#0F172A",
  card: "#1E293B",
  border: "#334155",
  primary: "#10B981",
  alert: "#F59E0B",
  text_primary: "#F1F5F9",
  text_secondary: "#94A3B8",
};
```

## Types TypeScript

### user.ts

```typescript
interface User {
  id: string;
  email: string;
  nome: string;
  plano_tipo: "gratis" | "pro" | "enterprise";
  data_expiracao: Date;
  created_at: Date;
  updated_at: Date;
}
```

### execution.ts

```typescript
interface Execution {
  id: string;
  usuario_id: string;
  ferramenta: string;
  linhas_processadas: number;
  tempo_execucao_ms: number;
  tempo_economizado_minutos: number;
  resultado_arquivo: string;
  created_at: Date;
}
```

## Como Usar

### No Desktop (Python)

```python
# Importar constants
from shared.constants import PLANOS, TOOLS

if user_plan == PLANOS['pro']['id']:
    # Libera todas as ferramentas
```

### Na Web (TypeScript)

```typescript
import { PLANOS, TOOLS } from "@shared/constants";

const ferramantasDisponiveis = TOOLS.filter((t) =>
  PLANOS[userPlan].limit_ferramentas.includes(t.id),
);
```

## Next Steps

- [ ] Definir schema SQL completo
- [ ] Criar tipos TypeScript
- [ ] Documentar APIs de integração
