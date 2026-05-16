import { Metadata } from 'next'
import { FileText } from 'lucide-react'

export const metadata: Metadata = {
  title: 'Termos de Uso - DataMaster Pro',
}

export default function TermosPage() {
  return (
    <div className="min-h-screen bg-surface-50 pt-24 pb-12 px-4">
      <div className="max-w-4xl mx-auto bg-white rounded-3xl shadow-sm border border-surface-200 p-8 md:p-12">
        <div className="flex items-center gap-4 mb-8 pb-8 border-b border-surface-100">
          <div className="w-16 h-16 bg-primary-50 rounded-2xl flex items-center justify-center text-primary-600">
            <FileText className="w-8 h-8" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-surface-900">Termos de Uso</h1>
            <p className="text-surface-500 mt-2">Última atualização: 08 de Maio de 2026</p>
          </div>
        </div>
        <div className="prose prose-surface max-w-none prose-headings:text-surface-900 prose-a:text-primary-600">
          <h2>1. Aceitação dos Termos</h2>
          <p>Ao acessar e usar o DataMaster Pro, você concorda em cumprir e estar vinculado a estes Termos de Uso. Se você não concordar com qualquer parte destes termos, não poderá usar nosso software.</p>
          
          <h2>2. Licença de Uso</h2>
          <p>Concedemos a você uma licença limitada, não exclusiva e intransferível para usar o DataMaster Pro de acordo com o plano contratado. O software Desktop foi desenhado para ser executado em ambiente Windows.</p>
          
          <h2>3. Responsabilidades do Usuário</h2>
          <p>Você é responsável por manter a confidencialidade de sua conta e senha. O DataMaster Pro não se responsabiliza por dados inseridos incorretamente nas ferramentas de consolidação, conciliação, ou uso indevido das rotinas geradas.</p>

          <h2>4. Privacidade e Proteção de Dados</h2>
          <p>Seus dados de uso são geridos conforme nossa Política de Privacidade. Lembramos que os arquivos locais (Excel, PDFs) manipulados no seu computador NÃO são enviados para nossos servidores, mantendo total privacidade de seus dados sensíveis.</p>
          
          <h2>5. Modificações dos Termos</h2>
          <p>Reservamo-nos o direito de modificar estes termos a qualquer momento. Alterações significativas serão notificadas através da plataforma web ou por email.</p>
        </div>
      </div>
    </div>
  )
}
