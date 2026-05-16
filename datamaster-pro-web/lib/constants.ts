export const TOOLS = [
  {
    id: 'consolidador',
    name: 'Consolidador',
    description: 'Une múltiplas planilhas em uma estrutura única, eliminando duplicatas e organizando seus dados.',
    icon: 'git-merge',
    minPlan: 'free',
    features: ['Merge automático', 'Elimina duplicatas', 'Organização inteligente']
  },
  {
    id: 'categorizador',
    name: 'Categorizador',
    description: 'Classifica transações por palavras-chave com regras personalizáveis.',
    icon: 'tags',
    minPlan: 'free',
    features: ['Regras personalizadas', 'Categorização automática', 'Relatórios detalhados']
  },
  {
    id: 'orcamentos',
    name: 'Orçamentos',
    description: 'Preenche templates de PDF em massa com dados da sua planilha.',
    icon: 'file-text',
    minPlan: 'pro',
    features: ['Preenchimento em massa', 'Templates customizáveis', 'Baixa automática']
  },
  {
    id: 'minerador',
    name: 'Minerador',
    description: 'Captura preços de sites concorrentes e monitora tendências do mercado.',
    icon: 'globe',
    minPlan: 'pro',
    features: ['Web scraping', 'Monitoramento contínuo', 'Relatórios de mercado']
  },
  {
    id: 'conciliador',
    name: 'Conciliador',
    description: 'Cruza extratos bancários com planilhas de vendas para identificar divergências.',
    icon: 'check-circle',
    minPlan: 'pro',
    features: ['conciliação automática', 'Detecção de divergências', 'Exportação detalhada']
  }
] as const

export type Tool = typeof TOOLS[number]['id']

export const PLANS = [
  {
    id: 'free',
    name: 'Grátis',
    price: 0,
    description: 'Perfeito para validar a potência das ferramentas.',
    features: [
      'Consolidador: Até 200 linhas (3 execs)',
      'Categorizador: Até 200 linhas (3 execs)',
      'Orçamentos: Até 10 documentos',
      'Conciliador: Até 3 conciliações',
      'Minerador: Até 5 links (2 execs)',
      'Marca d\'água em todos os relatórios',
      'Suporte via documentação'
    ],
    notIncluded: ['Suporte prioritário', 'Uso ilimitado'],
    cta: 'Começar Grátis',
    highlighted: false
  },
  {
    id: 'pro',
    name: 'Pro',
    price: 49.99,
    description: 'Para profissionais que buscam performance máxima e zero limites.',
    features: [
      'Todas as 5 ferramentas liberadas',
      'Arquivos e linhas ilimitados',
      'Sem marca d\'água',
      'Categorias Customizadas',
      'Logs de ROI (Dashboard)',
      'Suporte Prioritário (E-mail/WhatsApp)',
      'Atualizações antecipadas'
    ],
    notIncluded: [],
    cta: 'Assinar Plano Pro',
    highlighted: true,
    savings: 'Economize 40% no anual'
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    price: null,
    description: 'Solução sob medida para departamentos e grandes empresas.',
    features: [
      'Tudo do plano Pro',
      'Licenças em Volume (+5 usuários)',
      'Instalação Assistida',
      'Treinamento VIP (1h de Call)',
      'Customização de Código',
      'Suporte 24/7 Direto'
    ],
    notIncluded: [],
    cta: 'Falar com um Consultor',
    highlighted: false
  }
] as const

export type Plan = typeof PLANS[number]['id']

export const PLAN_LIMITS = {
  free: { 
    maxLinesMonth: 1200,
    maxExecsMonth: 15,
    tools_limit: {
        consolidador: { max_per_exec: 600, max_execs: 3 },
        categorizador: { max_per_exec: 600, max_execs: 3 },
        orcamentos: { max_per_exec: 15, max_execs: 5 },
        conciliador: { max_per_exec: null, max_execs: 3 },
        minerador: { max_per_exec: 10, max_execs: 2 },
    },
    tools: ['consolidador', 'categorizador', 'orcamentos', 'minerador', 'conciliador'] 
  },
  pro: { maxLinesMonth: null, tools_limit: null, tools: ['all'] },
  enterprise: { maxLinesMonth: null, tools_limit: null, tools: ['all'] }
}