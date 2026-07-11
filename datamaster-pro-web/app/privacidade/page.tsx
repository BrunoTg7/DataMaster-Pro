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
            <h1 className="text-3xl font-bold text-surface-900">Politica de Privacidade</h1>
            <p className="text-surface-500 mt-2">Sua privacidade e seguranca em primeiro lugar.</p>
            <p className="text-surface-400 text-sm mt-1">Ultima atualizacao: 21 de junho de 2026</p>
          </div>
        </div>
        <div className="prose prose-surface max-w-none prose-headings:text-surface-900 prose-a:text-primary-600">
          <h2>1. Dados Coletados</h2>
          <p>O DataMaster Pro preza pela seguranca dos seus arquivos. Todo o processamento de planilhas, orcamentos, e conciliacoes ocorre <strong>estritamente de forma local</strong> no seu computador (via aplicativo Desktop).</p>
          <p>Coletamos apenas:</p>
          <ul>
            <li><strong>Dados de cadastro:</strong> Nome e email para gestao de contas web.</li>
            <li><strong>Telemetria de uso:</strong> Quais ferramentas foram utilizadas e quantas linhas processadas para calculo de ROI do plano.</li>
            <li><strong>Dados de consentimento:</strong> Registro do seu consentimento com esta politica e termos de uso.</li>
          </ul>

          <h2>2. Finalidade do Tratamento</h2>
          <p>Seus dados sao utilizados para:</p>
          <ul>
            <li>Autenticacao e gestao da sua conta;</li>
            <li>Processamento de tarefas solicitadas por voce;</li>
            <li>Envio de notificacoes relacionadas ao servico;</li>
            <li>Calculo de estatisticas de uso e melhoria do produto;</li>
            <li>Cumprimento de obrigacoes legais (LGPD).</li>
          </ul>

          <h2>3. Cookies e Tecnologias de Rastreamento</h2>
          <p>Utilizamos os seguintes tipos de cookies:</p>
          <ul>
            <li><strong>Necessarios:</strong> Sessao de autenticacao e preferencias. Nao podem ser desabilitados.</li>
            <li><strong>Analiticos:</strong> Google Analytics para entender como o site e utilizado. Opcional.</li>
            <li><strong>Marketing:</strong> Facebook Pixel para campanhas de aquisicao. Opcional.</li>
          </ul>
          <p>Voce pode gerenciar suas preferencias a qualquer momento pelo banner de cookies ou pela pagina <a href="/cookies">Politica de Cookies</a>.</p>

          <h2>4. Servicos de Terceiros</h2>
          <p>Compartilhamos dados apenas com:</p>
          <ul>
            <li><strong>Supabase:</strong> Hospedagem do banco de dados e autenticacao;</li>
            <li><strong>Stripe / Cakto:</strong> Processamento de pagamentos de assinaturas;</li>
            <li><strong>Vercel:</strong> Hospedagem do site e API.</li>
          </ul>
          <p>Nenhum dado e vendido ou compartilhado para fins de marketing com terceiros.</p>

          <h2>5. Retencao de Dados</h2>
          <ul>
            <li><strong>Dados de conta:</strong> Mantidos enquanto a conta estiver ativa, ou ate 30 dias apos solicitacao de exclusao;</li>
            <li><strong>Dados locais (Desktop):</strong> Armazenados apenas no seu computador, voce tem controle total;</li>
            <li><strong>Logs de auditoria:</strong> Mantidos por 12 meses para fins de seguranca e compliance;</li>
            <li><strong>Registros de consentimento:</strong> Mantidos por 5 anos conforme exigencia legal.</li>
          </ul>

          <h2>6. Seus Direitos (Art. 18 LGPD)</h2>
          <p>Voce tem direito a:</p>
          <ul>
            <li>Confirmacao da existencia de tratamento;</li>
            <li>Acesso aos seus dados;</li>
            <li>Correcao de dados incompletos ou desatualizados;</li>
            <li>Anonimizacao, bloqueio ou eliminacao de dados desnecessarios;</li>
            <li>Portabilidade dos dados;</li>
            <li>Eliminacao dos dados tratados com consentimento;</li>
            <li>Informacao sobre compartilhamento de dados;</li>
            <li>Revogacao do consentimento.</li>
          </ul>

          <h2>7. Responsavel de Protecao de Dados (DPO)</h2>
          <p>Em caso de duvidas ou solicitacoes relativas a seus dados pessoais, entre em contato:</p>
          <ul>
            <li><strong>Email:</strong> dpo@datamaster.pro</li>
            <li><strong>Canal:</strong> <a href="/contato">Pagina de Contato</a></li>
          </ul>

          <h2>8. Seguranca dos Dados</h2>
          <p>Adotamos medidas tecnicas e administrativas para proteger seus dados, incluindo criptografia de tokens, autenticacao segura e acesso restrito. Apesar disso, nenhum sistema e 100% seguro.</p>

          <h2>9. Alteracoes nesta Politica</h2>
          <p>Podemos atualizar esta politica periodicamente. Notificaremos sobre alteracoes significativas por email ou aviso no site.</p>
        </div>
      </div>
    </div>
  )
}
