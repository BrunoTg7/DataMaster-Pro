import { Metadata } from 'next'
import { Shield, Eye, Lock, FileCheck } from 'lucide-react'
import { LgpdActions } from './LgpdActions'

export const metadata: Metadata = {
  title: 'LGPD & Segurança - DataMaster Pro',
  description: 'Como estamos em conformidade com a Lei Geral de Proteção de Dados.',
}

export default function LGPDPage() {
  return (
    <div className="min-h-screen bg-surface-50 pt-24 pb-12 px-4">
      <div className="max-w-4xl mx-auto bg-white rounded-3xl shadow-sm border border-surface-200 p-8 md:p-12">
        <div className="flex items-center gap-4 mb-8 pb-8 border-b border-surface-100">
          <div className="w-16 h-16 bg-primary-50 rounded-2xl flex items-center justify-center text-primary-600">
            <Shield className="w-8 h-8" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-surface-900">LGPD & Segurança</h1>
            <p className="text-surface-500 mt-2">Conformidade e respeito total aos seus dados.</p>
          </div>
        </div>

        <div className="prose prose-surface max-w-none prose-headings:text-surface-900 prose-a:text-primary-600 space-y-12">
          <section>
            <div className="flex items-center gap-2 text-primary-600 font-bold mb-4 uppercase tracking-wider text-sm">
              <FileCheck className="w-5 h-5" /> Nosso Compromisso
            </div>
            <p>
              O DataMaster Pro atua como <strong>Operador de Dados</strong> em conformidade com a Lei nº 13.709/2018 (LGPD). 
              Diferente de outras soluções em nuvem, nossa arquitetura foi desenhada para que o tratamento de dados pessoais 
              críticos ocorra localmente no seu computador.
            </p>
          </section>

          <div className="grid md:grid-cols-2 gap-8 not-prose">
            <div className="p-6 bg-surface-50 rounded-2xl border border-surface-100">
              <Eye className="w-6 h-6 text-primary-600 mb-4" />
              <h3 className="font-bold text-surface-900 mb-2">Transparência</h3>
              <p className="text-sm text-surface-600">Não realizamos coletas ocultas. Cada dado coletado (telemetria de uso) é informado e serve para validação da licença.</p>
            </div>
            <div className="p-6 bg-surface-50 rounded-2xl border border-surface-100">
              <Lock className="w-6 h-6 text-primary-600 mb-4" />
              <h3 className="font-bold text-surface-900 mb-2">Criptografia</h3>
              <p className="text-sm text-surface-600">Os dados de acesso e sessão são criptografados com algoritmos de nível militar antes de serem armazenados localmente.</p>
            </div>
          </div>

          <section>
            <h2 className="text-xl font-bold mb-4">Direitos do Titular</h2>
            <p>Em conformidade com a LGPD, garantimos a você:</p>
            <ul className="list-disc pl-5 space-y-2 text-surface-600 mb-6">
              <li>Confirmação da existência de tratamento.</li>
              <li>Acesso e correção de dados incompletos ou inexatos.</li>
              <li>Eliminação de dados tratados com consentimento.</li>
              <li>Revogação do consentimento a qualquer momento.</li>
            </ul>

            <div className="not-prose mt-8">
              <LgpdActions />
            </div>
          </section>

          <div className="p-8 bg-surface-900 rounded-3xl text-white">
            <h3 className="text-lg font-bold mb-4">Dúvidas sobre Privacidade?</h3>
            <p className="text-surface-400 text-sm mb-6 leading-relaxed">
              Nosso encarregado de proteção de dados (DPO) está à disposição para esclarecimentos sobre como tratamos suas informações.
            </p>
            <a href="mailto:dpo@datamaster.pro" className="text-primary-500 font-bold hover:underline">dpo@datamaster.pro</a>
          </div>
        </div>
      </div>
    </div>
  )
}
