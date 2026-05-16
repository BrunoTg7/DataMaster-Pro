import { Metadata } from 'next'
import { Sparkles, Terminal, Activity, Zap, HardDrive } from 'lucide-react'

export const metadata: Metadata = {
  title: 'Changelog - DataMaster Pro',
}

const UPDATES = [
  {
    version: 'v1.5.0',
    date: '08 de Maio de 2026',
    title: 'Autenticação Robusta e Design Refresh',
    description: 'Implementação de persistência de sessão offline via Supabase. Seu token de acesso agora pode durar semanas sem necessidade de conexão. As telas de Login Web e Desktop foram totalmente reprojetadas com a estética Glassmorphism.',
    type: 'feature',
    icon: Sparkles,
    color: 'text-purple-600',
    bg: 'bg-purple-100',
    border: 'border-purple-200'
  },
  {
    version: 'v1.2.0',
    date: '12 de Março de 2026',
    title: 'Nova Ferramenta: Conciliador de Extratos',
    description: 'A ferramenta de conciliação foi lançada em beta, cruzando extratos bancários (OFX/CSV) com planilhas de vendas para encontrar aquelas divergências incômodas de centavos em segundos.',
    type: 'feature',
    icon: HardDrive,
    color: 'text-blue-600',
    bg: 'bg-blue-100',
    border: 'border-blue-200'
  },
  {
    version: 'v1.1.5',
    date: '05 de Fevereiro de 2026',
    title: 'Performance Turbo no Consolidador',
    description: 'Otimização violenta no script interno do Consolidador. Através da biblioteca interna atualizada, o Desktop agora consegue processar e mesclar 50.000 linhas em menos de 2 segundos.',
    type: 'improvement',
    icon: Zap,
    color: 'text-amber-500',
    bg: 'bg-amber-100',
    border: 'border-amber-200'
  },
  {
    version: 'v1.0.0',
    date: '10 de Janeiro de 2026',
    title: 'Lançamento Oficial',
    description: 'Nascimento do DataMaster Pro! Suite com 4 ferramentas fundamentais liberadas: Consolidador, Categorizador Inteligente, Preenchimento Mestre de Orçamentos (PDFs) e o Web Minerador.',
    type: 'release',
    icon: Terminal,
    color: 'text-primary-600',
    bg: 'bg-primary-100',
    border: 'border-primary-200'
  }
]

export default function ChangelogPage() {
  return (
    <div className="min-h-screen bg-surface-50 pt-24 pb-12 px-4">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-16">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-surface-900 text-white rounded-2xl mb-6 shadow-xl shadow-surface-900/20">
            <Activity className="w-8 h-8" />
          </div>
          <h1 className="text-4xl font-bold text-surface-900 mb-4">Changelog</h1>
          <p className="text-xl text-surface-600">Acompanhe as novidades e a evolução do DataMaster Pro.</p>
        </div>

        <div className="relative border-l-2 border-surface-200 ml-4 md:ml-0 md:space-y-12 space-y-8">
          {UPDATES.map((update, idx) => {
            const Icon = update.icon
            const isEven = idx % 2 === 0
            
            return (
              <div key={idx} className="relative pl-8 md:pl-0">
                <div className={`absolute -left-[21px] md:left-1/2 md:-ml-[25px] w-10 h-10 rounded-full border-4 border-surface-50 flex items-center justify-center ${update.bg} ${update.color} z-10`}>
                  <Icon className="w-4 h-4" />
                </div>
                
                <div className={`md:w-[45%] ${isEven ? 'md:ml-auto md:pl-12' : 'md:pr-12'}`}>
                  <div className={`bg-white p-8 rounded-3xl shadow-sm border ${update.border} hover:shadow-lg hover:-translate-y-1 transition-all duration-300`}>
                    <div className="flex items-center gap-3 mb-4">
                      <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${update.bg} ${update.color}`}>
                        {update.version}
                      </span>
                      <span className="text-surface-400 text-sm font-medium">{update.date}</span>
                    </div>
                    <h3 className="text-2xl font-bold text-surface-900 mb-3">{update.title}</h3>
                    <p className="text-surface-600 leading-relaxed">{update.description}</p>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
