'use client'

import { TOOLS } from '@/lib/constants'
import { useSession } from '@/lib/contexts/SessionContext'
import { motion } from 'framer-motion'
import {
  ArrowUpRight,
  Calculator,
  CheckCircle,
  ClipboardList,
  FileText,
  GitMerge,
  Globe,
  LineChart,
  Link as LinkIcon,
  Lock,
  MessageSquare,
  Percent,
  Scan,
  Tags,
  Wand2
} from 'lucide-react'
import Link from 'next/link'

const iconMap: Record<string, React.ComponentType<{ className?: string }>> = {
  'git-merge': GitMerge,
  'tags': Tags,
  'file-text': FileText,
  'globe': Globe,
  'check-circle': CheckCircle,
  'scan': Scan,
  'link': LinkIcon,
  'line-chart': LineChart,
  'calculator': Calculator,
  'percent': Percent,
  'wand2': Wand2,
  'message-square': MessageSquare,
  'clipboard-list': ClipboardList,
}

export function ToolsSection() {
  const { user } = useSession()
  const isLoggedIn = !!user

  return (
    <section id="features" className="py-12 sm:py-20 lg:py-32 bg-surface-50 relative overflow-hidden">
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
          className="text-center mb-10 sm:mb-16 lg:mb-20"
        >
          <span className="inline-block px-3 sm:px-4 py-1 sm:py-1.5 bg-primary-100 text-primary-700 rounded-full text-xs sm:text-sm font-semibold mb-3 sm:mb-4">
            Ferramentas
          </span>
          <h2 className="text-2xl sm:text-4xl lg:text-5xl font-bold text-surface-900 mb-4 sm:mb-6 font-display tracking-tight">
            Tudo que você precisa para{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary-600 to-primary-400">
              dominar seus dados
            </span>
          </h2>
          <p className="text-sm sm:text-lg text-surface-600 max-w-2xl mx-auto leading-relaxed">
            5/15 ferramentas poderosas já disponíveis que transformam horas de trabalho manual em minutos de automação.
          </p>
        </motion.div>

        <div className="grid grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-6 lg:gap-8">
          {TOOLS.map((tool, index) => {
            const Icon = iconMap[tool.icon] || FileText
            const isLocked = tool.minPlan !== 'free'
            const isComingSoon = 'status' in tool
            const toolMinPlan = tool.minPlan
            const toolStatus = 'status' in tool ? tool.status : undefined

            return (
              <motion.div
                key={tool.id}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                viewport={{ once: true }}
                className={`relative group bg-white rounded-xl sm:rounded-3xl p-3.5 sm:p-8 transition-all duration-500 ${isComingSoon
                  ? 'border border-surface-200 opacity-80'
                  : isLocked
                    ? 'border border-surface-200 hover:border-surface-300 hover:shadow-lg'
                    : 'border-2 border-primary-200 shadow-xl shadow-primary-500/10 hover:shadow-2xl hover:shadow-primary-500/15 hover:-translate-y-2'
                  }`}
              >
                {isComingSoon ? (
                  <div className="absolute top-2 sm:top-5 right-2 sm:right-5">
                    <div className="flex items-center gap-0.5 sm:gap-1.5 px-1.5 sm:px-3 py-0.5 sm:py-1.5 bg-primary-100 text-primary-700 rounded-full">
                      <span className="text-[7px] sm:text-xs font-semibold uppercase">{toolStatus}</span>
                    </div>
                  </div>
                ) : isLocked && (
                  <div className="absolute top-2 sm:top-5 right-2 sm:right-5">
                    <div className="flex items-center gap-0.5 sm:gap-1.5 px-1.5 sm:px-3 py-0.5 sm:py-1.5 bg-surface-100 rounded-full">
                      <Lock className="w-2.5 h-2.5 sm:w-3.5 sm:h-3.5 text-surface-500" />
                      <span className="text-[7px] sm:text-xs text-surface-600 font-semibold uppercase">{toolMinPlan}</span>
                    </div>
                  </div>
                )}

                <div className={`w-8 h-8 sm:w-14 sm:h-14 rounded-lg sm:rounded-2xl flex items-center justify-center mb-2.5 sm:mb-6 transition-all duration-300 ${isLocked ? 'bg-surface-100 group-hover:bg-surface-200' : 'bg-gradient-to-br from-primary-100 to-primary-50 group-hover:scale-110'
                  }`}>
                  <Icon className={`w-4 h-4 sm:w-7 sm:h-7 ${isLocked ? 'text-surface-400' : 'text-primary-600'}`} />
                </div>

                <h3 className="text-xs sm:text-xl font-bold text-surface-900 mb-1 sm:mb-3 font-display">{tool.name}</h3>
                <p className="text-surface-600 text-[10px] sm:text-sm mb-2.5 sm:mb-6 leading-relaxed">{tool.description}</p>

                <ul className="space-y-1 sm:space-y-3 mb-2.5 sm:mb-6">
                  {tool.features.map((feature) => (
                    <li key={feature} className="flex items-center gap-1.5 sm:gap-3 text-[10px] sm:text-sm text-surface-600">
                      <div className={`w-3 h-3 sm:w-5 sm:h-5 rounded-full flex items-center justify-center flex-shrink-0 ${isLocked ? 'bg-surface-100' : 'bg-primary-100'
                        }`}>
                        <CheckCircle className={`w-2 h-2 sm:w-3 sm:h-3 ${isLocked ? 'text-surface-400' : 'text-primary-600'}`} />
                      </div>
                      <span>{feature}</span>
                    </li>
                  ))}
                </ul>

                <div className="pt-2 sm:pt-4 border-t border-surface-100">
                  {isComingSoon ? (
                    <span className="inline-flex items-center text-[9px] sm:text-sm font-semibold text-surface-400">
                      <span className="hidden sm:inline">Na próxima atualização do Desktop</span>
                      <span className="sm:hidden">Em breve</span>
                    </span>
                  ) : isLocked ? (
                    <Link
                      href="/planos"
                      className="inline-flex items-center text-[9px] sm:text-sm font-semibold text-surface-500 hover:text-primary-600 transition-colors"
                    >
                      <span>Upgrade</span>
                      <ArrowUpRight className="w-2.5 h-2.5 sm:w-4 sm:h-4 ml-0.5 sm:ml-1" />
                    </Link>
                  ) : (
                    <Link
                      href={isLoggedIn ? "/dashboard" : "/auth/registro"}
                      className="inline-flex items-center text-[9px] sm:text-sm font-semibold text-primary-600 hover:text-primary-700 transition-colors"
                    >
                      <span>{isLoggedIn ? "Acessar" : "Começar"}</span>
                      <ArrowUpRight className="w-2.5 h-2.5 sm:w-4 sm:h-4 ml-0.5 sm:ml-1" />
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
          <p className="text-surface-600 mb-4 sm:mb-6 font-medium text-sm sm:text-base">
            Escolha o plano ideal para suas necessidades
          </p>
          <Link href="/planos" className="btn-primary inline-flex text-sm sm:text-base px-6 sm:px-8">
            Ver Todos os Planos
          </Link>
        </motion.div>
      </div>
    </section>
  )
}