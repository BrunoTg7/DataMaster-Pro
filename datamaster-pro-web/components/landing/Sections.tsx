'use client'

import { useSession } from '@/lib/contexts/SessionContext'
import { motion } from 'framer-motion'
import { ArrowRight, Quote, Star } from 'lucide-react'
import Link from 'next/link'

const testimonials = [
  {
    name: 'Carlos Silva',
    role: 'Contador',
    company: 'Silva & Associados',
    avatar: 'CS',
    comment: 'O Consolidador economizou 4 horas por dia. Incrível como a ferramenta entende planilhas complexas e organiza tudo automaticamente.',
    rating: 5
  },
  {
    name: 'Mariana Costa',
    role: 'Gestora Financeira',
    company: 'Retail Brasil',
    avatar: 'MC',
    comment: 'Categorizador mudou completamente nosso fluxo de trabalho. Agora categorizamos 10mil transações em minutos, não dias.',
    rating: 5
  },
  {
    name: 'Roberto Alves',
    role: 'Analista de Dados',
    company: 'TechCorp',
    avatar: 'RA',
    comment: 'Minerador integra perfeitamente com nossos relatórios. A extração de dados de sites concorrentes é precisa e rápida.',
    rating: 5
  },
]

export function TestimonialsSection() {
  return (
    <section className="py-12 sm:py-20 lg:py-32 bg-white relative overflow-hidden">
      <div className="absolute top-20 left-0 w-72 h-72 bg-primary-100/30 rounded-full blur-3xl" />
      <div className="absolute bottom-20 right-0 w-72 h-72 bg-primary-100/20 rounded-full blur-3xl" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          viewport={{ once: true }}
          className="text-center mb-10 sm:mb-16 lg:mb-20"
        >
          <span className="inline-block px-3 sm:px-4 py-1 sm:py-1.5 bg-primary-100 text-primary-700 rounded-full text-xs sm:text-sm font-semibold mb-3 sm:mb-4">
            Depoimentos
          </span>
          <h2 className="text-2xl sm:text-4xl lg:text-5xl font-bold text-surface-900 mb-4 sm:mb-6 font-display tracking-tight">
            O que nossos{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary-600 to-primary-400">
              clientes dizem
            </span>
          </h2>
        </motion.div>

        <div className="grid grid-cols-2 md:grid-cols-3 gap-3 sm:gap-8 lg:gap-10">
          {testimonials.map((testimonial, index) => (
            <motion.div
              key={testimonial.name}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: index * 0.15 }}
              viewport={{ once: true }}
              className={`relative bg-surface-50 rounded-xl sm:rounded-3xl p-3.5 sm:p-8 border border-surface-100 hover:border-primary-100 hover:shadow-xl hover:shadow-primary-500/5 transition-all duration-300 ${index === 2 ? 'col-span-2 md:col-span-1' : ''}`}
            >
              <Quote className="absolute top-2.5 sm:top-6 right-2.5 sm:right-6 w-4 h-4 sm:w-8 sm:h-8 text-primary-200" />

              <div className="flex gap-0.5 sm:gap-1 mb-2 sm:mb-5">
                {[...Array(testimonial.rating)].map((_, i) => (
                  <Star key={i} className="w-3 h-3 sm:w-5 sm:h-5 text-yellow-400 fill-yellow-400" />
                ))}
              </div>
              <p className="text-[11px] sm:text-base text-surface-700 mb-2.5 sm:mb-6 leading-relaxed">"{testimonial.comment}"</p>
              <div className="flex items-center gap-2 sm:gap-4 pt-2 sm:pt-4 border-t border-surface-200">
                <div className="w-7 h-7 sm:w-12 sm:h-12 bg-gradient-to-br from-primary-500 to-primary-600 rounded-full flex items-center justify-center text-white font-bold text-[9px] sm:text-sm flex-shrink-0">
                  {testimonial.avatar}
                </div>
                <div className="min-w-0">
                  <div className="font-bold text-surface-900 text-[10px] sm:text-sm truncate">{testimonial.name}</div>
                  <div className="text-surface-500 text-[8px] sm:text-xs truncate">{testimonial.role}</div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}

export function CTASection() {
  const { user } = useSession()
  const isLoggedIn = !!user

  return (
    <section className="py-12 sm:py-20 lg:py-32 bg-surface-900 relative overflow-hidden">
      <div className="absolute inset-0">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiNmZmYiIGZpbGwtb3BhY2l0eT0iMC4wNSI+PGNpcmNsZSBjeD0iMzAiIGN5PSIzMCIgcj0iMiIvPjwvZz48L2c+PC9zdmc+')] opacity-30" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-primary-500/10 rounded-full blur-[120px]" />
      </div>

      <div className="relative max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          viewport={{ once: true }}
        >
          <h2 className="text-2xl sm:text-4xl lg:text-6xl font-bold text-white mb-6 sm:mb-8 font-display tracking-tight">
            Pronto para{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary-400 to-primary-300">
              transformar
            </span>{' '}
            seu trabalho?
          </h2>
          <p className="text-sm sm:text-xl text-surface-300 mb-8 sm:mb-10 max-w-2xl mx-auto leading-relaxed">
            Junte-se a milhares de profissionais que já economizam horas todos os dias
            com automação inteligente de planilhas.
          </p>

          <div className="flex flex-row items-center justify-center gap-2.5 sm:gap-5 mb-8 sm:mb-12">
            <Link href={isLoggedIn ? "/dashboard" : "/auth/registro"} className="btn-primary group text-xs sm:text-base px-4 sm:px-10 py-2.5 sm:py-4 flex-1 sm:flex-none">
              {isLoggedIn ? "Acessar Painel" : "Começar"}
              <ArrowRight className="w-3.5 h-3.5 sm:w-5 sm:h-5 ml-1.5 sm:ml-2 group-hover:translate-x-1 transition-transform" />
            </Link>
            <Link href="/planos" className="btn-secondary bg-transparent border-surface-600 text-white hover:bg-surface-800 text-xs sm:text-base px-4 sm:px-8 py-2.5 sm:py-4 flex-1 sm:flex-none">
              Ver Planos
            </Link>
          </div>


        </motion.div>
      </div>
    </section>
  )
}