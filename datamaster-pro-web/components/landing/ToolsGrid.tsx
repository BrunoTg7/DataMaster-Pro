'use client'

import { motion } from 'framer-motion'
import { 
  GitMerge, 
  Tags, 
  FileText, 
  Globe, 
  CheckCircle,
  Lock,
  ArrowUpRight
} from 'lucide-react'
import { TOOLS } from '@/lib/constants'
import Link from 'next/link'

const iconMap: Record<string, React.ComponentType<{ className?: string }>> = {
  'git-merge': GitMerge,
  'tags': Tags,
  'file-text': FileText,
  'globe': Globe,
  'check-circle': CheckCircle,
}

export function ToolsSection() {
  return (
    <section id="features" className="py-20 lg:py-32 bg-surface-50 relative overflow-hidden">
      <div className="absolute inset-0">
        <div className="absolute top-0 left-0 w-96 h-96 bg-primary-200/10 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-0 w-96 h-96 bg-primary-200/10 rounded-full blur-3xl" />
      </div>
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          viewport={{ once: true }}
          className="text-center mb-16 lg:mb-20"
        >
          <span className="inline-block px-4 py-1.5 bg-primary-100 text-primary-700 rounded-full text-sm font-semibold mb-4">
            Ferramentas
          </span>
          <h2 className="text-4xl sm:text-5xl font-bold text-surface-900 mb-6 font-display tracking-tight">
            Tudo que você precisa para{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary-600 to-primary-400">
              dominar seus dados
            </span>
          </h2>
          <p className="text-lg text-surface-600 max-w-2xl mx-auto leading-relaxed">
            5 ferramentas poderosas que transformam horas de trabalho manual em minutos de automação.
          </p>
        </motion.div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6 lg:gap-8">
          {TOOLS.map((tool, index) => {
            const Icon = iconMap[tool.icon] || FileText
            const isLocked = tool.minPlan !== 'free'
            
            return (
              <motion.div
                key={tool.id}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                viewport={{ once: true }}
                className={`relative group bg-white rounded-3xl p-8 transition-all duration-500 ${
                  isLocked 
                    ? 'border border-surface-200 hover:border-surface-300 hover:shadow-lg' 
                    : 'border-2 border-primary-200 shadow-xl shadow-primary-500/10 hover:shadow-2xl hover:shadow-primary-500/15 hover:-translate-y-2'
                }`}
              >
                {isLocked && (
                  <div className="absolute top-5 right-5">
                    <div className="flex items-center gap-1.5 px-3 py-1.5 bg-surface-100 rounded-full">
                      <Lock className="w-3.5 h-3.5 text-surface-500" />
                      <span className="text-xs text-surface-600 font-semibold uppercase">{tool.minPlan}</span>
                    </div>
                  </div>
                )}

                <div className={`w-14 h-14 rounded-2xl flex items-center justify-center mb-6 transition-all duration-300 ${
                  isLocked ? 'bg-surface-100 group-hover:bg-surface-200' : 'bg-gradient-to-br from-primary-100 to-primary-50 group-hover:scale-110'
                }`}>
                  <Icon className={`w-7 h-7 ${isLocked ? 'text-surface-400' : 'text-primary-600'}`} />
                </div>

                <h3 className="text-xl font-bold text-surface-900 mb-3 font-display">{tool.name}</h3>
                <p className="text-surface-600 text-sm mb-6 leading-relaxed">{tool.description}</p>

                <ul className="space-y-3 mb-6">
                  {tool.features.map((feature) => (
                    <li key={feature} className="flex items-center gap-3 text-sm text-surface-600">
                      <div className={`w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 ${
                        isLocked ? 'bg-surface-100' : 'bg-primary-100'
                      }`}>
                        <CheckCircle className={`w-3 h-3 ${isLocked ? 'text-surface-400' : 'text-primary-600'}`} />
                      </div>
                      {feature}
                    </li>
                  ))}
                </ul>

                <div className="pt-4 border-t border-surface-100">
                  {isLocked ? (
                    <Link 
                      href="/planos" 
                      className="inline-flex items-center text-sm font-semibold text-surface-500 hover:text-primary-600 transition-colors"
                    >
                      <span>Fazer upgrade</span>
                      <ArrowUpRight className="w-4 h-4 ml-1" />
                    </Link>
                  ) : (
                    <Link 
                      href="/auth/registro" 
                      className="inline-flex items-center text-sm font-semibold text-primary-600 hover:text-primary-700 transition-colors"
                    >
                      <span>Começar agora</span>
                      <ArrowUpRight className="w-4 h-4 ml-1" />
                    </Link>
                  )}
                </div>
              </motion.div>
            )
          })}
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.5 }}
          viewport={{ once: true }}
          className="text-center mt-16"
        >
          <p className="text-surface-600 mb-6 font-medium">
            Escolha o plano ideal para suas necessidades
          </p>
          <Link href="/planos" className="btn-primary inline-flex text-base px-8">
            Ver Todos os Planos
          </Link>
        </motion.div>
      </div>
    </section>
  )
}