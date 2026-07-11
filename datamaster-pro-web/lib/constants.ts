export const APP_VERSION = '1.0.0'

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
    minPlan: 'free',
    features: ['Preenchimento em massa', 'Templates customizáveis', 'Baixa automática']
  },
  {
    id: 'minerador',
    name: 'Minerador',
    description: 'Captura preços de sites concorrentes e monitora tendências do mercado.',
    icon: 'globe',
    minPlan: 'free',
    features: ['Web scraping', 'Monitoramento contínuo', 'Relatórios de mercado']
  },
  {
    id: 'conciliador',
    name: 'Conciliador',
    description: 'Cruza extratos bancários com planilhas de vendas para identificar divergências.',
    icon: 'check-circle',
    minPlan: 'free',
    features: ['conciliação automática', 'Detecção de divergências', 'Exportação detalhada']
  },
  {
    id: 'ocr',
    name: 'Conversor OCR',
    description: 'Extraia dados financeiros de faturas e recibos em PDF/Imagem direto para Excel.',
    icon: 'scan',
    minPlan: 'free',
    features: ['Extração Automática', 'Reconhecimento de Imagem', 'Exportação Estruturada'],
    status: 'Atualização 2.0'
  },
  {
    id: 'validador',
    name: 'Validador de Links',
    description: 'Verifique links quebrados e status HTTP de URLs em massa na sua planilha.',
    icon: 'link',
    minPlan: 'free',
    features: ['Verificação em Massa', 'Status HTTP', 'Identificação de Erros'],
    status: 'Em breve'
  },
  {
    id: 'tendencias',
    name: 'Analista de Tendências',
    description: 'Analise padrões históricos de vendas e preveja demandas futuras com IA.',
    icon: 'line-chart',
    minPlan: 'free',
    features: ['Previsão de Demanda', 'Análise Sazonal', 'Relatórios Preditivos'],
    status: 'Em breve'
  },
  {
    id: 'lucratividade',
    name: 'Calc. Lucratividade',
    description: 'Calcule a margem real de produtos incluindo taxas de marketplace e impostos.',
    icon: 'calculator',
    minPlan: 'free',
    features: ['Taxas de Marketplace', 'Cálculo de Impostos', 'Margem Líquida'],
    status: 'Atualização 2.0'
  },
  {
    id: 'comissoes',
    name: 'Gestor de Comissões',
    description: 'Calcule comissões complexas de vendedores baseado em regras e metas.',
    icon: 'percent',
    minPlan: 'free',
    features: ['Regras Dinâmicas', 'Metas por Vendedor', 'Extratos Individuais'],
    status: 'Em breve'
  },
  {
    id: 'sanitizer',
    name: 'Sanitizador de Dados',
    description: 'Limpe, padronize e corrija erros de digitação em massa nas suas planilhas.',
    icon: 'wand2',
    minPlan: 'pro',
    features: ['Padronização', 'Remoção de Anomalias', 'Limpeza Inteligente'],
    status: 'Atualização 2.0'
  },
  {
    id: 'reviews',
    name: 'Extrator de Reviews',
    description: 'Extraia e analise o sentimento de avaliações de produtos em e-commerces.',
    icon: 'message-square',
    minPlan: 'pro',
    features: ['Análise de Sentimento', 'Extração em Massa', 'Nuvem de Palavras'],
    status: 'Em breve'
  },
  {
    id: 'laudos',
    name: 'Gerador de Laudos',
    description: 'Crie documentos técnicos e laudos em lote a partir de dados estruturados.',
    icon: 'clipboard-list',
    minPlan: 'pro',
    features: ['Templates Customizáveis', 'Geração em Lote', 'Exportação PDF'],
    status: 'Atualização 2.0'
  },
  {
    id: 'classificador_ncm',
    name: 'Classificador NCM',
    description: 'Classifica produtos com códigos NCM e CEST corretos via fuzzy matching.',
    icon: 'tag',
    minPlan: 'pro',
    features: ['Fuzzy Matching NCM/CEST', 'Planilha em Massa', 'Sugestão Automática'],
    status: 'Atualização 2.0'
  },
  {
    id: 'precificador_canal',
    name: 'Precificador de Canal',
    description: 'Calcula preços por marketplace (ML, Shopee, Amazon, Magalu) garantindo margem líquida.',
    icon: 'calculator',
    minPlan: 'pro',
    features: ['Simulador Impostos', 'Cálculo Reverso', 'Margem Líquida'],
    status: 'Atualização 2.0'
  }
] as const

export type Tool = typeof TOOLS[number]['id']

export const PLANS = [
  {
    id: 'free',
    name: 'Grátis',
    price: 0,
    annualPrice: null,
    description: 'Perfeito para validar a potência das ferramentas.',
    features: [
      'Consolidador: Até 600 linhas (5 execs)',
      'Categorizador: Até 600 linhas (5 execs)',
      'Orçamentos: Até 15 documentos (3 execs)',
      'Conciliador: Até 2 conciliações',
      'Minerador: Até 15 links (2 execs)',
      'Marca d\'água em todos os relatórios',
      'Retenção de histórico: 1 hora',
      'Suporte via documentação'
    ],
    notIncluded: ['Suporte prioritário', 'Uso ilimitado', '2 tarefas simultâneas', 'Retenção de histórico configurável'],
    cta: 'Começar Grátis',
    highlighted: false
  },
  {
    id: 'starter',
    name: 'Starter',
    price: 34.00,
    annualPrice: 30.60,
    description: 'Para quem precisa de mais volume e sem marca d\'água.',
    features: [
      'Consolidador: Até 3.000 linhas (10 execs)',
      'Categorizador: Até 3.000 linhas (10 execs)',
      'Orçamentos: Até 60 documentos (6 execs)',
      'Conciliador: Até 8 conciliações',
      'Minerador: Até 80 links (8 execs)',
      'Sem marca d\'água',
      '2 tarefas simultâneas',
      'Retenção de histórico (7 dias, 15 dias, 1 mês ou 6 meses)',
      'Suporte por e-mail'
    ],
    notIncluded: ['Uso ilimitado', 'Suporte prioritário WhatsApp', 'Atualizações antecipadas'],
    cta: 'Assinar Starter',
    highlighted: false
  },
  {
    id: 'pro',
    name: 'Pro',
    price: 64.00,
    annualPrice: 57.60,
    description: 'Para profissionais que buscam performance máxima e zero limites.',
    features: [
      'Todas ferramentas liberadas',
      'Arquivos e linhas ilimitados',
      '2 tarefas simultâneas',
      'Retenção de histórico (7 dias, 15 dias, 1 mês ou 6 meses)',
      'Sem marca d\'água',
      'Categorias Customizadas',
      'Logs de ROI (Dashboard)',
      'Suporte Prioritário (E-mail/WhatsApp)',
      'Atualizações antecipadas'
    ],
    notIncluded: [],
    cta: 'Assinar Plano Pro',
    highlighted: true
  }
] as const

export type Plan = typeof PLANS[number]['id']

export const PLAN_LIMITS = {
  free: {
    maxLinesMonth: 1200,
    maxExecsMonth: 15,
    maxConcurrentTasks: 1,
    availableHistoryRetentions: ['1h'],
    tools_limit: {
      consolidador: { max_per_exec: 600, max_execs: 5 },
      categorizador: { max_per_exec: 600, max_execs: 5 },
      orcamentos: { max_per_exec: 15, max_execs: 3 },
      conciliador: { max_execs: 2 },
      minerador: { max_per_exec: 15, max_total: 15, max_execs: 2 },
      ocr: { max_per_exec: 10, max_execs: 3 },
      validador: { max_per_exec: 20, max_execs: 3 },
      lucratividade: { max_execs: 3 },
      tendencias: { max_per_exec: 5, max_execs: 3 },
      comissoes: { max_per_exec: 20, max_execs: 3 },
      classificador_ncm: { max_per_exec: 100, max_execs: 3 },
      precificador_canal: { max_per_exec: 100, max_execs: 3 },
    },
    tools: ['consolidador', 'categorizador', 'orcamentos', 'minerador', 'conciliador', 'ocr', 'validador', 'lucratividade', 'tendencias', 'comissoes', 'sanitizer', 'laudos', 'reviews']
  },
  starter: {
    maxLinesMonth: 10000,
    maxExecsMonth: 80,
    maxConcurrentTasks: 2,
    availableHistoryRetentions: ['7d', '15d', '1m', '6m'],
    tools_limit: {
      consolidador: { max_per_exec: 3000, max_execs: 10 },
      categorizador: { max_per_exec: 3000, max_execs: 10 },
      orcamentos: { max_per_exec: 60, max_execs: 6 },
      conciliador: { max_execs: 8 },
      minerador: { max_per_exec: 80, max_total: 80, max_execs: 8 },
      ocr: { max_per_exec: 20, max_execs: 6 },
      validador: { max_per_exec: 40, max_execs: 6 },
      lucratividade: { max_execs: 6 },
      tendencias: { max_per_exec: 10, max_execs: 6 },
      comissoes: { max_per_exec: 40, max_execs: 6 },
      classificador_ncm: { max_per_exec: 200, max_execs: 6 },
      precificador_canal: { max_per_exec: 200, max_execs: 6 },
    },
    tools: ['consolidador', 'categorizador', 'orcamentos', 'minerador', 'conciliador', 'ocr', 'validador', 'lucratividade', 'tendencias', 'comissoes', 'classificador_ncm', 'precificador_canal']
  },
  pro: { maxLinesMonth: null, maxConcurrentTasks: 2, availableHistoryRetentions: ['7d', '15d', '1m', '6m'], tools_limit: null, tools: ['all'] }
}