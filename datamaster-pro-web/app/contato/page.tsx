"use client"

import { useState } from 'react'
import { motion } from 'framer-motion'
import { Send, MessageSquare, Mail, MapPin } from 'lucide-react'

export default function ContatoPage() {
  const [enviado, setEnviado] = useState(false)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setEnviado(true)
    setTimeout(() => setEnviado(false), 3000)
  }

  return (
    <div className="min-h-screen bg-surface-50 pt-24 pb-12 px-4">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <h1 className="text-4xl font-bold text-surface-900 mb-4">Fale Conosco</h1>
          <p className="text-xl text-surface-600">Estamos aqui para ajudar você a automatizar sua rotina.</p>
        </div>
        
        <div className="grid lg:grid-cols-2 gap-12 items-start">
          <motion.div 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="space-y-8"
          >
            <div className="bg-white p-8 rounded-3xl shadow-sm border border-surface-200 hover:shadow-md transition-shadow">
              <div className="flex items-start gap-4 mb-6">
                <div className="w-12 h-12 bg-primary-50 text-primary-600 rounded-xl flex items-center justify-center shrink-0">
                  <Mail className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-surface-900">Suporte por Email</h3>
                  <p className="text-surface-600 mt-1">Nossa equipe responde em até 24h úteis para usuários Standard, e até 4h úteis para usuários Premium e Enterprise.</p>
                  <a href="mailto:suporte@datamasterpro.com" className="text-primary-600 font-semibold mt-2 inline-block hover:underline">suporte@datamasterpro.com</a>
                </div>
              </div>
            </div>
            
            <div className="bg-white p-8 rounded-3xl shadow-sm border border-surface-200 hover:shadow-md transition-shadow">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 bg-primary-50 text-primary-600 rounded-xl flex items-center justify-center shrink-0">
                  <MapPin className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-surface-900">Nossa Base</h3>
                  <p className="text-surface-600 mt-1">Operamos de forma 100% remota no Brasil, atendendo empresas em todo o território nacional.</p>
                </div>
              </div>
            </div>
          </motion.div>

          <motion.div 
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="bg-white p-8 md:p-10 rounded-3xl shadow-xl shadow-surface-200/50 border border-surface-200 relative overflow-hidden"
          >
            {enviado ? (
              <motion.div 
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="absolute inset-0 flex flex-col items-center justify-center bg-white z-10"
              >
                <div className="w-20 h-20 bg-green-100 text-green-500 rounded-full flex items-center justify-center mb-6">
                  <Send className="w-10 h-10" />
                </div>
                <h3 className="text-2xl font-bold text-surface-900">Mensagem Enviada!</h3>
                <p className="text-surface-600 mt-2">Retornaremos o mais breve possível.</p>
              </motion.div>
            ) : null}

            <h2 className="text-2xl font-bold text-surface-900 mb-6 flex items-center gap-2">
              <MessageSquare className="text-primary-600" />
              Envie uma mensagem
            </h2>
            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-surface-700 mb-2">Nome</label>
                <input type="text" required className="w-full px-4 py-3 rounded-xl border border-surface-200 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all" placeholder="Seu nome completo" />
              </div>
              <div>
                <label className="block text-sm font-medium text-surface-700 mb-2">Email</label>
                <input type="email" required className="w-full px-4 py-3 rounded-xl border border-surface-200 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all" placeholder="seu@email.com" />
              </div>
              <div>
                <label className="block text-sm font-medium text-surface-700 mb-2">Mensagem</label>
                <textarea required rows={4} className="w-full px-4 py-3 rounded-xl border border-surface-200 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all resize-none" placeholder="Como podemos ajudar? Dúvidas técnicas, financeiras ou parcerias."></textarea>
              </div>
              <button type="submit" className="w-full btn-primary py-4 text-lg group">
                Enviar Mensagem
                <Send className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
              </button>
            </form>
          </motion.div>
        </div>
      </div>
    </div>
  )
}
