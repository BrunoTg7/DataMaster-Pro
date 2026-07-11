"use client"

import { useState } from 'react'
import { motion } from 'framer-motion'
import { Send, MessageSquare, Mail, MapPin, Loader2 } from 'lucide-react'
import { ConsentCheckbox } from '@/components/shared/ConsentCheckbox'

export default function ContatoPage() {
  const [enviado, setEnviado] = useState(false)
  const [erro, setErro] = useState<string | null>(null)
  const [consentChecked, setConsentChecked] = useState(false)
  const [consentError, setConsentError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [nome, setNome] = useState('')
  const [email, setEmail] = useState('')
  const [mensagem, setMensagem] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!consentChecked) {
      setConsentError('Voce precisa autorizar o tratamento dos seus dados para enviar a mensagem.')
      return
    }
    
    setConsentError(null)
    setErro(null)
    setLoading(true)

    try {
      const res = await fetch('/api/contact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          nome: nome.trim(),
          email: email.trim(),
          mensagem: mensagem.trim(),
          honeypot: '',
        }),
      })

      const data = await res.json()

      if (!res.ok) {
        setErro(data.error || 'Erro ao enviar mensagem. Tente novamente.')
        return
      }

      setEnviado(true)
      setNome('')
      setEmail('')
      setMensagem('')
      setTimeout(() => setEnviado(false), 5000)
    } catch {
      setErro('Erro de conexao. Verifique sua internet e tente novamente.')
    } finally {
      setLoading(false)
    }
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
                  <p className="text-surface-600 mt-1">Nossa equipe responde em até 24h úteis para usuários Free e Starter, e até 4h úteis para usuários Pro.</p>
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
              {erro && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl text-sm">
                  {erro}
                </div>
              )}
              <div>
                <label className="block text-sm font-medium text-surface-700 mb-2">Nome</label>
                <input 
                  type="text" 
                  required 
                  maxLength={100}
                  value={nome}
                  onChange={(e) => setNome(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl border border-surface-200 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all" 
                  placeholder="Seu nome completo" 
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-surface-700 mb-2">Email</label>
                <input 
                  type="email" 
                  required 
                  maxLength={254}
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl border border-surface-200 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all" 
                  placeholder="seu@email.com" 
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-surface-700 mb-2">Mensagem</label>
                <textarea 
                  required 
                  rows={4} 
                  maxLength={2000}
                  value={mensagem}
                  onChange={(e) => setMensagem(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl border border-surface-200 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all resize-none" 
                  placeholder="Como podemos ajudar? Duvidas tecnicas, financeiras ou parcerias."
                ></textarea>
                <p className="text-xs text-surface-400 mt-1">{mensagem.length}/2000</p>
              </div>
              <ConsentCheckbox
                onChange={setConsentChecked}
                error={consentError || undefined}
              />
              <p className="text-xs text-surface-400 -mt-2">
                Seus dados serao usados apenas para responder esta mensagem. Consulte nossa{' '}
                <a href="/privacidade" className="underline hover:text-surface-600">Politica de Privacidade</a>.
              </p>
              <button 
                type="submit" 
                disabled={loading}
                className="w-full btn-primary py-4 text-lg group disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-5 h-5 ml-2 animate-spin" />
                    Enviando...
                  </>
                ) : (
                  <>
                    Enviar Mensagem
                    <Send className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
                  </>
                )}
              </button>
            </form>
          </motion.div>
        </div>
      </div>
    </div>
  )
}
