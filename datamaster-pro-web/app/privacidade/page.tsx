import { Metadata } from 'next'
import { ShieldCheck } from 'lucide-react'

export const metadata: Metadata = {
  title: 'Política de Privacidade - DataMaster Pro',
}

export default function PrivacidadePage() {
  return (
    <div className="min-h-screen bg-surface-50 pt-24 pb-12 px-4">
      <div className="max-w-4xl mx-auto bg-white rounded-3xl shadow-sm border border-surface-200 p-8 md:p-12">
        <div className="flex items-center gap-4 mb-8 pb-8 border-b border-surface-100">
          <div className="w-16 h-16 bg-primary-50 rounded-2xl flex items-center justify-center text-primary-600">
            <ShieldCheck className="w-8 h-8" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-surface-900">Política de Privacidade</h1>
            <p className="text-surface-500 mt-2">Sua privacidade e segurança em primeiro lugar.</p>
          </div>
        </div>
        <div className="prose prose-surface max-w-none prose-headings:text-surface-900 prose-a:text-primary-600">
          <h2>Coleta de Dados</h2>
          <p>O DataMaster Pro preza pela segurança dos seus arquivos. Todo o processamento de planilhas, orçamentos, e conciliações ocorre <strong>estritamente de forma local</strong> no seu computador (via aplicativo Desktop).</p>
          <p>Coletamos apenas:</p>
          <ul>
            <li>Dados básicos de cadastro (Nome, Email) para a gestão de contas web.</li>
            <li>Telemetria básica de uso (Quais ferramentas foram utilizadas e quantas linhas foram processadas) para cálculo de ROI do plano.</li>
          </ul>
          
          <h2>Armazenamento Local</h2>
          <p>Seus tokens de autenticação da sessão web são criptografados localmente. Isso possibilita que você trabalhe offline nas ferramentas Desktop com segurança.</p>
          
          <h2>Compartilhamento</h2>
          <p>Nós NÃO vendemos ou compartilhamos suas informações pessoais com terceiros sob nenhuma circunstância, exceto para intermediários de pagamentos devidamente regulamentados (ex: Stripe, Cakto) necessários para a manutenção de sua assinatura.</p>

          <h2>Exclusão de Conta</h2>
          <p>Você tem o direito de solicitar a exclusão da sua conta e de todos os dados atrelados a ela a qualquer momento no seu Painel de Controle, ou entrando em contato com nosso suporte.</p>
        </div>
      </div>
    </div>
  )
}
