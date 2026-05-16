import { Metadata } from 'next'
import { PLANS } from '@/lib/constants'
import { Check, X, Sparkles } from 'lucide-react'
import Link from 'next/link'
import { PaymentLink } from '@/components/shared/PaymentLink'

export const metadata: Metadata = {
  title: 'Planos e Preços - DataMaster Pro',
  description: 'Escolha o plano ideal para sua necessidade. Começe grátis ou upgrade para Pro.',
}

export default function PlanosPage() {
  return (
    <div className="min-h-screen bg-surface-50 pt-24 pb-16 relative overflow-hidden">
      <div className="absolute inset-0">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-primary-500/[0.05] rounded-full blur-3xl" />
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
        <div className="text-center mb-16 animate-fade-in">
          <span className="inline-block px-4 py-1.5 bg-primary-100 text-primary-700 rounded-full text-sm font-semibold mb-4">
            Planos e Preços
          </span>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-surface-900 mb-6 font-display tracking-tight">
            Planos que{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary-600 to-primary-400">
              cabem no seu bolso
            </span>
          </h1>
          <p className="text-lg text-surface-600 max-w-2xl mx-auto leading-relaxed">
            Escolha o plano ideal para sua necessidade. Todos os planos incluem suporte
            e atualizações gratuitas.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-6 lg:gap-8 max-w-5xl mx-auto">
          {PLANS.map((plan, index) => (
            <div
              key={plan.id}
              className={`relative bg-white rounded-3xl p-8 animate-slide-up ${plan.highlighted
                ? 'ring-2 ring-primary-500 shadow-2xl shadow-primary-500/15 scale-105 lg:scale-110 z-10'
                : 'border border-surface-200 shadow-lg shadow-surface-200/50 hover:shadow-xl hover:border-primary-200/50 transition-all duration-300'
                }`}
              style={{ animationDelay: `${index * 0.1}s` }}
            >
              {'savings' in plan && plan.savings && (
                <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                  <span className="inline-flex items-center gap-1 px-4 py-1.5 bg-gradient-to-r from-primary-500 to-primary-600 text-white text-xs font-bold rounded-full shadow-lg shadow-primary-500/30">
                    <Sparkles className="w-3 h-3" />
                    {plan.savings}
                  </span>
                </div>
              )}

              {plan.highlighted && (
                <div className="absolute -top-3 right-4">
                  <span className="inline-flex items-center px-3 py-1 bg-primary-500 text-white text-xs font-bold rounded-full">
                    Mais Popular
                  </span>
                </div>
              )}

              <div className="text-center mb-8">
                <h3 className="text-2xl font-bold text-surface-900 mb-3 font-display">{plan.name}</h3>
                <p className="text-surface-500 text-sm leading-relaxed">{plan.description}</p>
              </div>

              <div className="text-center mb-8">
                {plan.price === null ? (
                  <div className="text-4xl font-bold text-surface-900 font-display">Custom</div>
                ) : plan.price > 0 ? (
                  <>
                    <div className="flex items-center justify-center gap-2 mb-1">
                      <span className="text-lg text-surface-400 line-through font-medium">R$ 160,00</span>
                      <span className="inline-flex items-center px-2 py-0.5 bg-red-100 text-red-600 text-xs font-bold rounded-full animate-pulse">-60%</span>
                    </div>
                    <div className="text-5xl font-bold text-surface-900 font-display">
                      R$ {plan.price.toFixed(2).replace('.', ',')}
                      <span className="text-lg text-surface-500 font-normal">/mês</span>
                    </div>
                    <div className="mt-1 text-xs text-surface-400">+ taxa de pagamento</div>
                  </>
                ) : (
                  <div className="text-5xl font-bold text-surface-900 font-display">
                    R$ {plan.price.toFixed(2).replace('.', ',')}
                    <span className="text-lg text-surface-500 font-normal">/mês</span>
                  </div>
                )}
              </div>

              <ul className="space-y-4 mb-8">
                {plan.features.map((feature) => (
                  <li key={feature} className="flex items-start gap-3">
                    <div className="w-5 h-5 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                      <Check className="w-3 h-3 text-green-600" />
                    </div>
                    <span className="text-surface-700 text-sm">{feature}</span>
                  </li>
                ))}
                {plan.notIncluded.map((feature) => (
                  <li key={feature} className="flex items-start gap-3 opacity-50">
                    <div className="w-5 h-5 rounded-full bg-surface-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                      <X className="w-3 h-3 text-surface-400" />
                    </div>
                    <span className="text-surface-500 text-sm">{feature}</span>
                  </li>
                ))}
              </ul>

              {plan.id === 'enterprise' ? (
                <Link
                  href="/contato"
                  className={`block text-center py-4 rounded-xl font-bold transition-all ${plan.highlighted
                    ? 'bg-primary-600 text-white hover:bg-primary-700 hover:shadow-lg hover:shadow-primary-500/25'
                    : 'bg-surface-100 text-surface-900 hover:bg-surface-200'
                    }`}
                >
                  {plan.cta}
                </Link>
              ) : (
                <PaymentLink
                  planId={plan.id}
                  className={`block text-center py-4 rounded-xl font-bold transition-all ${plan.highlighted
                    ? 'bg-primary-600 text-white hover:bg-primary-700 hover:shadow-lg hover:shadow-primary-500/25'
                    : 'bg-surface-100 text-surface-900 hover:bg-surface-200'
                    }`}
                >
                  {plan.cta}
                </PaymentLink>
              )}
            </div>
          ))}
        </div>

        <div className="mt-16 text-center animate-fade-in" style={{ animationDelay: '0.5s' }}>
          <p className="text-surface-600">
            Precisa de algo personalizado?{' '}
            <Link href="/contato" className="text-primary-600 font-bold hover:underline">
              Fale com nossa equipe
            </Link>
          </p>
        </div>

        <div className="mt-20 max-w-3xl mx-auto">
          <h2 className="text-3xl font-bold text-surface-900 text-center mb-10 font-display animate-fade-in" style={{ animationDelay: '0.6s' }}>
            Perguntas Frequentes
          </h2>
          <div className="space-y-4">
            {faqItems.map((faq, index) => (
              <div
                key={index}
                className="bg-white rounded-2xl p-6 border border-surface-200 hover:border-primary-200 hover:shadow-lg hover:shadow-primary-500/5 transition-all duration-300 animate-slide-up"
                style={{ animationDelay: `${0.7 + index * 0.1}s` }}
              >
                <h3 className="font-bold text-surface-900 mb-3 text-lg">{faq.question}</h3>
                <p className="text-surface-600 leading-relaxed">{faq.answer}</p>
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
    answer: 'O plano grátis inclui as ferramentas Consolidador e Categorizador, com limite de 10 linhas por arquivo e marca d\'água nos relatórios.'
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