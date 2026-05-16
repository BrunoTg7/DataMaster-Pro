"use client"

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Search, ChevronDown, HelpCircle, BookOpen } from 'lucide-react'

const FAQS = [
  { question: 'Como instalo o DataMaster Pro?', answer: 'Faça login no painel web, acesse a área de Downloads e baixe o instalador (.exe). Após instalado, basta logar com sua mesma conta web no aplicativo Desktop.' },
  { question: 'O software funciona sem internet?', answer: 'Sim! Após o primeiro login, seu token de segurança é salvo. Você pode usar as ferramentas totalmente offline (como em viagens) e o sistema validará a assinatura silenciosamente na sua próxima conexão.' },
  { question: 'Meus dados e planilhas vão para a nuvem?', answer: 'Não! Todo o processamento de planilhas pesadas, cruzamentos do Consolidador, e geração de PDFs do gerador de Orçamentos é feito 100% localmente no poder da sua máquina para garantir total privacidade e segurança. Nenhuma planilha sai do seu computador.' },
  { question: 'Posso usar em mais de um computador?', answer: 'O limite de licenças depende do seu plano contratado. Planos individuais suportam a ativação em até 1 dispositivo simultaneamente.' },
  { question: 'Como cancelar minha assinatura?', answer: 'Sem burocracia. Basta acessar a página de Planos no seu painel web e clicar em "Gerenciar Assinatura" -> "Cancelar Assinatura".' },
]

export default function AjudaPage() {
  const [openIndex, setOpenIndex] = useState<number | null>(0)
  const [search, setSearch] = useState('')

  const filteredFaqs = FAQS.filter(faq => 
    faq.question.toLowerCase().includes(search.toLowerCase()) || 
    faq.answer.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="min-h-screen bg-surface-50 pt-24 pb-12 px-4">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-12">
          <motion.div 
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="inline-flex items-center justify-center w-16 h-16 bg-primary-100 text-primary-600 rounded-2xl mb-6"
          >
            <HelpCircle className="w-8 h-8" />
          </motion.div>
          <h1 className="text-4xl font-bold text-surface-900 mb-4">Central de Ajuda</h1>
          <p className="text-xl text-surface-600 mb-8">Tire suas dúvidas ou busque soluções rápidas abaixo.</p>
          
          <div className="relative max-w-2xl mx-auto">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-surface-400 w-6 h-6" />
            <input 
              type="text" 
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Buscar por senhas, downloads, cancelamento..." 
              className="w-full pl-14 pr-6 py-5 rounded-2xl border border-surface-200 focus:border-primary-500 focus:ring-4 focus:ring-primary-500/10 shadow-sm text-lg outline-none transition-all"
            />
          </div>
        </div>

        <motion.div 
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.1 }}
          className="bg-white rounded-3xl shadow-sm border border-surface-200 p-8"
        >
          <h2 className="text-2xl font-bold text-surface-900 mb-6 flex items-center gap-2">
            <BookOpen className="text-primary-600" />
            Perguntas Frequentes
          </h2>
          
          <div className="space-y-4">
            {filteredFaqs.length > 0 ? filteredFaqs.map((faq, idx) => (
              <div key={idx} className="border border-surface-200 rounded-2xl overflow-hidden transition-all hover:border-primary-200 bg-white">
                <button
                  onClick={() => setOpenIndex(openIndex === idx ? null : idx)}
                  className="w-full flex items-center justify-between p-6 text-left hover:bg-surface-50 transition-colors"
                >
                  <span className="font-semibold text-surface-900 text-lg">{faq.question}</span>
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center transition-colors ${openIndex === idx ? 'bg-primary-50 text-primary-600' : 'bg-surface-100 text-surface-500'}`}>
                    <ChevronDown className={`w-5 h-5 transition-transform duration-300 ${openIndex === idx ? 'rotate-180' : ''}`} />
                  </div>
                </button>
                <AnimatePresence>
                  {openIndex === idx && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="overflow-hidden"
                    >
                      <div className="p-6 pt-0 text-surface-600 leading-relaxed border-t border-surface-100 mt-2">
                        {faq.answer}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            )) : (
              <div className="text-center py-12 text-surface-500">
                Nenhum resultado encontrado para "{search}". Tente buscar por outros termos!
              </div>
            )}
          </div>
        </motion.div>
      </div>
    </div>
  )
}
