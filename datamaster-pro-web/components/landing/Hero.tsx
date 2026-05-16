'use client'

import { motion } from 'framer-motion'
import { ArrowRight, CheckCircle, Zap, Shield, Clock, Play } from 'lucide-react'
import Link from 'next/link'

const stats = [
  { value: '50k+', label: 'Planilhas processadas' },
  { value: '10x', label: 'Mais rápido' },
  { value: '99.9%', label: 'Precisão' },
  { value: '4.9/5', label: 'Avaliação' },
]

const benefits = [
  {
    icon: Zap,
    title: 'Automação Inteligente',
    description: 'Processe milhares de linhas em segundos com algoritmos otimizados.'
  },
  {
    icon: Shield,
    title: 'Segurança de Dados',
    description: 'Seus dados criptografados e protegidos. Totalmente compatível com LGPD.'
  },
  {
    icon: Clock,
    title: 'Economize Tempo',
    description: 'Reduza horas de trabalho manual para minutos de automação.'
  },
]

export function HeroSection() {
  return (
    <section className="relative overflow-hidden bg-surface-50 pt-24 pb-16 lg:pt-32 lg:pb-24">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-primary-100/40 via-transparent to-transparent" />
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[600px] bg-primary-500/[0.03] rounded-full blur-[120px]" />
      <div className="absolute bottom-20 right-0 w-[500px] h-[500px] bg-primary-400/[0.05] rounded-full blur-[100px]" />

      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-40 left-10 w-72 h-72 border border-primary-200/20 rounded-full" />
        <div className="absolute top-60 right-20 w-96 h-96 border border-primary-200/10 rounded-full" />
        <div className="absolute bottom-40 left-1/4 w-48 h-48 border border-primary-200/15 rounded-full" />
      </div>

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-4xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="mb-6"
          >
            <span className="inline-flex items-center gap-2 px-5 py-2.5 bg-white/80 backdrop-blur-sm border border-primary-200/50 text-primary-700 rounded-full text-sm font-medium shadow-sm">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary-500 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-primary-500"></span>
              </span>
              Novo: Sistema Disponível!
            </span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="text-5xl sm:text-6xl lg:text-7xl font-bold text-surface-900 leading-[1.1] mb-8 tracking-tight font-display"
          >
            Transforme planilhas em{' '}
            <span className="relative">
              <span className="relative z-10 text-transparent bg-clip-text bg-gradient-to-r from-primary-600 via-primary-500 to-primary-400">
                potência produtiva
              </span>
              <svg className="absolute -bottom-2 left-0 w-full h-3 text-primary-300/30" viewBox="0 0 200 12" preserveAspectRatio="none">
                <path d="M0 9c30-8 70-8 100 0s70 8 100 0" fill="none" stroke="currentColor" strokeWidth="3" />
              </svg>
            </span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="text-lg sm:text-xl text-surface-600 mb-10 max-w-2xl mx-auto leading-relaxed"
          >
            5 ferramentas profissionais para automatizar tarefas repetitivas no Excel.{' '}
            Consolide, categorize, preencha orçamentos, miner dados e concilie em segundos.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-8"
          >
            <Link href="/auth/registro" className="btn-primary group text-base px-8 py-4">
              Começar Gratuitamente
              <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
            </Link>

          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.4 }}
            className="flex flex-wrap items-center justify-center gap-6 text-sm text-surface-500"
          >
            <span className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-green-500" />
              Sem cartão de crédito
            </span>
            <span className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-green-500" />
              Cancelamento anytime
            </span>

          </motion.div>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.5 }}
          className="mt-16 lg:mt-24"
        >
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 lg:gap-8">
            {stats.map((stat, index) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.6 + index * 0.1 }}
                className="text-center group"
              >
                <div className="text-4xl lg:text-5xl font-bold text-surface-900 mb-2 font-display tracking-tight group-hover:text-primary-600 transition-colors">
                  {stat.value}
                </div>
                <div className="text-sm text-surface-500 font-medium">{stat.label}</div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  )
}

export function BenefitsSection() {
  return (
    <section className="py-20 lg:py-28 bg-white relative">
      <div className="absolute inset-0 bg-gradient-to-b from-surface-50/50 to-transparent" />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
        <div className="grid md:grid-cols-3 gap-8 lg:gap-12">
          {benefits.map((benefit, index) => (
            <motion.div
              key={benefit.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              viewport={{ once: true }}
              className="flex flex-col items-center text-center p-8 rounded-3xl bg-surface-50/50 border border-surface-100 hover:border-primary-100 hover:shadow-xl hover:shadow-primary-500/5 transition-all duration-300 group"
            >
              <div className="w-16 h-16 bg-gradient-to-br from-primary-100 to-primary-50 rounded-2xl flex items-center justify-center mb-5 group-hover:scale-110 transition-transform duration-300">
                <benefit.icon className="w-8 h-8 text-primary-600" />
              </div>
              <h3 className="text-xl font-bold text-surface-900 mb-3 font-display">{benefit.title}</h3>
              <p className="text-surface-600 leading-relaxed">{benefit.description}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}