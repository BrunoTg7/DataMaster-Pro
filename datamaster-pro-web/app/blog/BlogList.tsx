'use client'

import { useState } from 'react'
import { Calendar, User, ArrowRight, X, BookOpen } from 'lucide-react'
import Image from 'next/image'

interface Post {
  id: number
  title: string
  excerpt: string
  content: string
  author: string
  date: string
  category: string
  image: string
}

const POSTS: Post[] = [
  {
    id: 1,
    title: '5 Truques de Excel que você deveria saber em 2026',
    excerpt: 'Descubra como otimizar suas fórmulas e ganhar tempo com novas funções nativas.',
    content: `O Excel continua sendo a ferramenta de negócios mais importante do mundo. Em 2026, com o avanço de novos recursos, quem domina as técnicas modernas poupa dezenas de horas de trabalho. Aqui estão as 5 principais dicas:

1. Domine o PROCX (XLOOKUP)
O antigo PROCV ficou no passado. O PROCX é muito mais rápido, seguro e flexível. Ele busca dados tanto para a esquerda quanto para a direita e possui tratamento de erros embutido.

2. Filtros e Matrizes Dinâmicas
Use as fórmulas =FILTRAR() e =ORDENAR() para automatizar seus relatórios. Elas recalculam em tempo real à medida que novos dados são adicionados, eliminando a necessidade de atualizar planilhas manualmente.

3. Atalhos Avançados de Teclado
Ganhe velocidade de digitação aprendendo atalhos como Alt + Shift + F1 (criar nova planilha) e Ctrl + Shift + L (aplicar ou remover filtros).

4. Power Query para Importação
Evite copiar e colar dados. O Power Query permite que você se conecte a fontes externas (outras pastas de trabalho, PDFs, bancos de dados) e aplique etapas de tratamento automático.

5. Formatação Condicional Avançada
Use fórmulas personalizadas dentro da formatação condicional para realçar linhas inteiras com base no valor de uma única célula, gerando alertas visuais instantâneos.`,
    author: 'Equipe DataMaster',
    date: '02 de Maio, 2026',
    category: 'Tutoriais',
    image: 'https://images.unsplash.com/photo-1543286386-713bdd548da4?auto=format&fit=crop&q=80&w=800',
  },
  {
    id: 2,
    title: 'Automação Local vs Nuvem: Qual a melhor opção?',
    excerpt: 'Entenda por que manter o processamento de dados sensíveis na sua máquina é mais seguro.',
    content: `Muitas ferramentas modernas exigem que você faça upload de suas planilhas de trabalho para servidores web ou plataformas em nuvem de terceiros. Mas será que isso é seguro?

1. Vazamento de Dados e LGPD
Planilhas corporativas contêm salários, faturamento, CPFs, informações estratégicas e dados pessoais. Ao enviá-las para a nuvem, você está expondo dados sigilosos a possíveis vulnerabilidades.

2. Velocidade de Processamento
Processar arquivos pesados (com milhares de linhas) na nuvem depende de sua conexão de internet. Rodar o processamento localmente com os recursos da sua própria máquina é muitas vezes mais rápido e consistente.

3. O Modelo Híbrido do DataMaster Pro
Nossa arquitetura garante privacidade absoluta: todos os cálculos, mineração e consolidações ocorrem localmente no seu computador. Apenas estatísticas de ROI e autenticação são sincronizadas na nuvem, garantindo conformidade total à LGPD.`,
    author: 'Bruno Antonio',
    date: '28 de Abril, 2026',
    category: 'Segurança',
    image: 'https://images.unsplash.com/photo-1558494949-ef010cbdcc51?auto=format&fit=crop&q=80&w=800',
  },
  {
    id: 3,
    title: 'Como o DataMaster Pro reduziu custos em 30% na LogTech',
    excerpt: 'Um estudo de caso real sobre a implementação do nosso minerador de dados.',
    content: `A LogTech, uma startup brasileira de logística, enfrentava um gargalo operacional crítico: analistas financeiros passavam cerca de 35 horas por mês unindo e padronizando planilhas de frete de diferentes transportadoras.

A Solução:
Implementamos o Consolidador e o Minerador do DataMaster Pro. A equipe configurou regras automatizadas para capturar dados chave de arquivos XLS bagunçados e uni-los em um relatório mestre unificado.

Resultados:
- Tempo de consolidação reduzido de 35 horas para menos de 10 minutos.
- Erro humano na digitação reduzido a zero.
- Re-alocação dos analistas para atividades estratégicas, resultando em uma economia mensal de 30% nas despesas operacionais da área.`,
    author: 'Marketing DM',
    date: '15 de Abril, 2026',
    category: 'Cases',
    image: 'https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&q=80&w=800',
  },
]

export function BlogList() {
  const [activePost, setActivePost] = useState<Post | null>(null)

  return (
    <>
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
        {POSTS.map((post) => (
          <article key={post.id} className="bg-white dark:bg-surface-900 rounded-[2rem] overflow-hidden shadow-sm border border-surface-100 dark:border-surface-800 hover:shadow-xl hover:-translate-y-1 transition-all duration-300 flex flex-col group">
            <div className="h-48 overflow-hidden relative">
              <Image 
                src={post.image} 
                alt={post.title}
                fill
                className="object-cover transition-transform duration-500 group-hover:scale-110"
                sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
              />
              <span className="absolute top-4 left-4 bg-primary-500 text-white text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wider">
                {post.category}
              </span>
            </div>
            <div className="p-8 flex-1 flex flex-col">
              <div className="flex items-center gap-4 text-xs text-surface-400 dark:text-surface-500 mb-4">
                <span className="flex items-center gap-1"><User className="w-3 h-3" /> {post.author}</span>
                <span className="flex items-center gap-1"><Calendar className="w-3 h-3" /> {post.date}</span>
              </div>
              <h2 className="text-xl font-bold text-surface-900 dark:text-white mb-3 group-hover:text-primary-600 transition-colors line-clamp-2">
                {post.title}
              </h2>
              <p className="text-surface-600 dark:text-surface-400 text-sm leading-relaxed mb-6 line-clamp-3">
                {post.excerpt}
              </p>
              <div className="mt-auto pt-6 border-t border-surface-50 dark:border-surface-800">
                <button 
                  onClick={() => setActivePost(post)}
                  className="text-primary-600 dark:text-primary-400 font-bold flex items-center gap-2 hover:gap-3 transition-all text-sm uppercase tracking-wide"
                >
                  Ler artigo <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          </article>
        ))}
      </div>

      {/* Article Modal */}
      {activePost && (
        <div className="fixed inset-0 bg-surface-950/60 backdrop-blur-md z-[100] flex items-center justify-center p-4">
          <div className="bg-white dark:bg-surface-900 w-full max-w-3xl rounded-[2.5rem] shadow-2xl border border-surface-100 dark:border-surface-800 max-h-[85vh] overflow-hidden flex flex-col">
            {/* Header */}
            <div className="relative h-64 shrink-0">
              <Image 
                src={activePost.image} 
                alt={activePost.title} 
                fill
                className="object-cover"
                sizes="(max-width: 768px) 100vw, 768px"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/40 to-transparent" />
              <button 
                onClick={() => setActivePost(null)}
                className="absolute top-6 right-6 w-10 h-10 bg-white/10 hover:bg-white/20 backdrop-blur-md text-white rounded-full flex items-center justify-center transition-all border border-white/20"
                aria-label="Fechar"
              >
                <X className="w-5 h-5" />
              </button>
              <div className="absolute bottom-6 left-6 right-6 text-white">
                <span className="bg-primary-500 text-white text-[10px] font-bold px-2.5 py-1 rounded-full uppercase tracking-wider mb-3 inline-block">
                  {activePost.category}
                </span>
                <h3 className="text-xl md:text-3xl font-bold font-display">{activePost.title}</h3>
              </div>
            </div>

            {/* Meta & Scrollable Content */}
            <div className="p-6 md:p-8 overflow-y-auto flex-1">
              <div className="flex items-center gap-6 text-sm text-surface-500 dark:text-surface-400 mb-6 pb-6 border-b border-surface-100 dark:border-surface-800">
                <span className="flex items-center gap-1.5"><User className="w-4 h-4 text-primary-500" /> {activePost.author}</span>
                <span className="flex items-center gap-1.5"><Calendar className="w-4 h-4 text-primary-500" /> {activePost.date}</span>
                <span className="flex items-center gap-1.5"><BookOpen className="w-4 h-4 text-primary-500" /> 3 min leitura</span>
              </div>
              <div className="text-surface-700 dark:text-surface-300 leading-relaxed text-base whitespace-pre-line space-y-4">
                {activePost.content}
              </div>
            </div>

            {/* Footer */}
            <div className="p-6 border-t border-surface-100 dark:border-surface-800 flex justify-end shrink-0 bg-surface-50 dark:bg-surface-900/50">
              <button
                onClick={() => setActivePost(null)}
                className="btn-primary py-2 px-6 rounded-xl text-sm"
              >
                Fechar Artigo
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
