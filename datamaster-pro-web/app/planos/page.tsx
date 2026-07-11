'use client'

import { useState } from 'react'
import { Check, X } from 'lucide-react'
import Link from 'next/link'
import { PaymentLink } from '@/components/shared/PaymentLink'
import { PLANS } from '@/lib/constants'

export default function PlanosPage() {
  const [isAnnual, setIsAnnual] = useState(false)

  return (
    <div className="min-h-screen bg-surface-50 pt-20 sm:pt-24 pb-12 sm:pb-16 relative overflow-hidden">
      <div className="absolute inset-0">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-primary-500/[0.05] rounded-full blur-3xl" />
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
        <div className="text-center mb-8 sm:mb-12">
          <span className="inline-block px-3 sm:px-4 py-1 sm:py-1.5 bg-primary-100 text-primary-700 rounded-full text-xs sm:text-sm font-semibold mb-3 sm:mb-4">
            Planos e Preços
          </span>
          <h1 className="text-3xl sm:text-4xl lg:text-6xl font-bold text-surface-900 mb-4 sm:mb-6 font-display tracking-tight">
            Planos que{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary-600 to-primary-400">
              cabem no seu bolso
            </span>
          </h1>
          <p className="text-base sm:text-lg text-surface-600 max-w-2xl mx-auto leading-relaxed mb-6 sm:mb-8">
            Escolha o plano ideal para sua necessidade. Todos os planos incluem suporte
            e atualizações gratuitas.
          </p>

          {/* Toggle Mensal/Anual */}
          <div className="inline-flex items-center gap-2 sm:gap-3 bg-white rounded-full p-1 sm:p-1.5 border border-surface-200 shadow-sm">
            <button
              onClick={() => setIsAnnual(false)}
              className={`px-4 sm:px-5 py-2 sm:py-2.5 rounded-full text-xs sm:text-sm font-semibold transition-all ${
                !isAnnual
                  ? 'bg-primary-600 text-white shadow-md'
                  : 'text-surface-600 hover:text-surface-900'
              }`}
            >
              Mensal
            </button>
            <button
              onClick={() => setIsAnnual(true)}
              className={`px-4 sm:px-5 py-2 sm:py-2.5 rounded-full text-xs sm:text-sm font-semibold transition-all ${
                isAnnual
                  ? 'bg-primary-600 text-white shadow-md'
                  : 'text-surface-600 hover:text-surface-900'
              }`}
            >
              Anual
              <span className="ml-1 sm:ml-1.5 text-[10px] sm:text-xs font-bold text-green-600">-10%</span>
            </button>
          </div>
        </div>

        <div className="grid md:grid-cols-3 gap-4 sm:gap-6 lg:gap-8 max-w-5xl mx-auto items-start">
          {PLANS.map((plan, index) => {
            const price = isAnnual && plan.annualPrice ? plan.annualPrice : plan.price
            const isPro = plan.id === 'pro'

            return (
              <div
                key={plan.id}
                className={`relative bg-white rounded-2xl sm:rounded-3xl p-5 sm:p-8 ${
                  isPro
                    ? 'ring-2 ring-primary-500 shadow-2xl shadow-primary-500/15 sm:scale-105 lg:scale-110 z-10'
                    : 'border border-surface-200 shadow-lg shadow-surface-200/50 hover:shadow-xl hover:border-primary-200/50 transition-all duration-300'
                }`}
                style={{ animationDelay: `${index * 0.1}s` }}
              >
                {isPro && (
                  <div className="absolute -top-2 sm:-top-3 right-3 sm:right-4">
                    <span className="inline-flex items-center px-2 sm:px-3 py-0.5 sm:py-1 bg-primary-500 text-white text-[10px] sm:text-xs font-bold rounded-full">
                      Mais Popular
                    </span>
                  </div>
                )}

                <div className="text-center mb-5 sm:mb-8">
                  <h3 className="text-xl sm:text-2xl font-bold text-surface-900 mb-2 sm:mb-3 font-display">{plan.name}</h3>
                  <p className="text-surface-500 text-xs sm:text-sm leading-relaxed">{plan.description}</p>
                </div>

                <div className="text-center mb-5 sm:mb-8">
                  {plan.price === 0 ? (
                    <div className="text-3xl sm:text-5xl font-bold text-surface-900 font-display">
                      R$ 0
                      <span className="text-sm sm:text-lg text-surface-500 font-normal">/mês</span>
                    </div>
                  ) : (
                    <>
                      {isAnnual && plan.annualPrice && (
                        <div className="flex items-center justify-center gap-2 mb-1">
                          <span className="text-sm sm:text-lg text-surface-400 line-through font-medium">
                            R$ {plan.price.toFixed(2).replace('.', ',')}
                          </span>
                          <span className="inline-flex items-center px-1.5 sm:px-2 py-0.5 bg-green-100 text-green-700 text-[10px] sm:text-xs font-bold rounded-full">
                            -10%
                          </span>
                        </div>
                      )}
                      <div className="text-3xl sm:text-5xl font-bold text-surface-900 font-display">
                        R$ {price.toFixed(2).replace('.', ',')}
                        <span className="text-sm sm:text-lg text-surface-500 font-normal">/mês</span>
                      </div>
                      {isAnnual && plan.annualPrice && (
                        <div className="mt-1 text-[10px] sm:text-xs text-surface-400">
                          R$ {(plan.annualPrice * 12).toFixed(2).replace('.', ',')}/ano
                        </div>
                      )}
                      <div className="mt-1 text-[10px] sm:text-xs text-surface-400">+ taxa de pagamento</div>
                    </>
                  )}
                </div>

                <ul className="space-y-2.5 sm:space-y-4 mb-5 sm:mb-8">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex items-start gap-2 sm:gap-3">
                      <div className="w-4 h-4 sm:w-5 sm:h-5 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                        <Check className="w-2.5 h-2.5 sm:w-3 sm:h-3 text-green-600" />
                      </div>
                      <span className="text-surface-700 text-xs sm:text-sm">{feature}</span>
                    </li>
                  ))}
                  {plan.notIncluded.map((feature) => (
                    <li key={feature} className="flex items-start gap-2 sm:gap-3 opacity-50">
                      <div className="w-4 h-4 sm:w-5 sm:h-5 rounded-full bg-surface-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                        <X className="w-2.5 h-2.5 sm:w-3 sm:h-3 text-surface-400" />
                      </div>
                      <span className="text-surface-500 text-xs sm:text-sm">{feature}</span>
                    </li>
                  ))}
                </ul>

                <PaymentLink
                  planId={plan.id}
                  isAnnual={isAnnual}
                  className={`block text-center py-3 sm:py-4 rounded-xl font-bold transition-all text-sm sm:text-base ${
                    isPro
                      ? 'bg-primary-600 text-white hover:bg-primary-700 hover:shadow-lg hover:shadow-primary-500/25'
                      : 'bg-surface-100 text-surface-900 hover:bg-surface-200'
                  }`}
                >
                  {plan.cta}
                </PaymentLink>
              </div>
            )
          })}
        </div>

        <div className="mt-10 sm:mt-16 text-center">
          <p className="text-surface-600 text-sm sm:text-base">
            Precisa de algo personalizado?{' '}
            <Link href="/contato" className="text-primary-600 font-bold hover:underline">
              Fale com nossa equipe
            </Link>
          </p>
        </div>

        <div className="mt-12 sm:mt-20 max-w-3xl mx-auto">
          <h2 className="text-xl sm:text-3xl font-bold text-surface-900 text-center mb-6 sm:mb-10 font-display">
            Perguntas Frequentes
          </h2>
          <div className="space-y-3 sm:space-y-4">
            {faqItems.map((faq, index) => (
              <div
                key={index}
                className="bg-white rounded-xl sm:rounded-2xl p-4 sm:p-6 border border-surface-200 hover:border-primary-200 hover:shadow-lg hover:shadow-primary-500/5 transition-all duration-300"
              >
                <h3 className="font-bold text-surface-900 mb-2 sm:mb-3 text-base sm:text-lg">{faq.question}</h3>
                <p className="text-surface-600 leading-relaxed text-sm sm:text-base">{faq.answer}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

const faqItems = [
  {
    question: 'Posso cancelar a qualquer momento?',
    answer: 'Sim! Você pode cancelar sua assinatura a qualquer momento. Não há penalidades ou taxas adicionais. O acesso permanece até o fim do período pago.'
  },
  {
    question: 'O plano grátis tem limitações?',
    answer: 'Sim, o plano grátis possui limites por ferramenta (ex: Consolidador até 600 linhas, Minerador até 15 links), total de 1.200 linhas e 15 execuções por mês, além de 1 tarefa por vez e marca d\'água nos relatórios. Para uso ilimitado e 2 tarefas simultâneas, assine o Pro.'
  },
  {
    question: 'Quais formas de pagamento aceitam?',
    answer: 'Aceitamos todos os cartões de crédito principais (Visa, Mastercard, Elo, Amex), PIX para todos os planos e Boleto Bancário para planos anuais.'
  },
  {
    question: 'Posso fazer upgrade de plano depois?',
    answer: 'Claro! Você pode fazer upgrade para um plano superior a qualquer momento. O valor adicional será rateado proporcionalmente.'
  },
  {
    question: 'As ferramentas funcionam offline?',
    answer: 'Sim! O aplicativo desktop funciona 100% offline. As alterações são sincronizadas automaticamente quando você reconectar à internet.'
  }
]
