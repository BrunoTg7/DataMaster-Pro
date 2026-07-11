import { Metadata } from 'next'
import { Cookie } from 'lucide-react'

export const metadata: Metadata = {
  title: 'Politica de Cookies - DataMaster Pro',
  description: 'Saiba como o DataMaster Pro utiliza cookies e tecnologias semelhantes para melhorar sua experiencia.',
}

export default function CookiesPage() {
  return (
    <div className="min-h-screen bg-surface-50 pt-24 pb-12 px-4">
      <div className="max-w-4xl mx-auto bg-white rounded-3xl shadow-sm border border-surface-200 p-8 md:p-12">
        <div className="flex items-center gap-4 mb-8 pb-8 border-b border-surface-100">
          <div className="w-16 h-16 bg-primary-50 rounded-2xl flex items-center justify-center text-primary-600">
            <Cookie className="w-8 h-8" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-surface-900">Politica de Cookies</h1>
            <p className="text-surface-500 mt-2">Ultima atualizacao: 21 de junho de 2026</p>
          </div>
        </div>

        <div className="prose prose-surface max-w-none prose-headings:text-surface-900 prose-a:text-primary-600">
          <h2>O que sao cookies?</h2>
          <p>
            Cookies sao pequenos arquivos de texto armazenados no seu dispositivo quando voce visita um site.
            Eles sao amplamente utilizados para fazer os sites funcionarem de forma mais eficiente e para fornecer
            informacoes aos proprietarios do site.
          </p>

          <h2>Como utilizamos cookies</h2>
          <p>Utilizamos cookies para os seguintes fins:</p>

          <h3>1. Cookies Necessarios (Sempre Ativos)</h3>
          <p>Essenciais para o funcionamento do site. Sem esses cookies, o site nao pode funcionar corretamente.</p>
          <ul>
            <li><strong>sb-access-token / sb-refresh-token</strong> — Gerenciamento de sessao do Supabase Auth. Duracao: Sessao.</li>
            <li><strong>datamaster_consent_v2</strong> — Armazena suas preferencias de cookies. Duracao: 1 ano.</li>
            <li><strong>theme</strong> — Preferencia de tema (claro/escuro). Duracao: Sessao.</li>
          </ul>

          <h3>2. Cookies de Analise (Opcionais)</h3>
          <p>Nos ajudam a entender como os visitantes interagem com o site, coletando informacoes de forma anonima.</p>
          <ul>
            <li><strong>Nenhum cookie de analise de terceiros atualmente.</strong> Se implementarmos Google Analytics ou similares, esta secao sera atualizada.</li>
          </ul>

          <h3>3. Cookies de Marketing (Opcionais)</h3>
          <p>Usados para rastrear visitantes entre sites e exibir anuncios relevantes.</p>
          <ul>
            <li><strong>Nenhum cookie de marketing atualmente.</strong> Esta secao sera atualizada se necessário.</li>
          </ul>

          <h2>Como gerenciar cookies</h2>
          <p>
            Voce pode gerenciar suas preferencias de cookies a qualquer momento clicando no botao
            &quot;Personalizar&quot; no banner de cookies que aparece na primeira visita. Tambem e possivel:
          </p>
          <ul>
            <li>Limpar os cookies diretamente pelo seu navegador</li>
            <li>Configurar seu navegador para recusar cookies</li>
            <li>Configurar alertas quando cookies forem enviados</li>
          </ul>

          <p className="text-sm text-surface-500">
            <strong>Importante:</strong> Desabilitar cookies necessarios pode afetar o funcionamento do site.
            A funcao de login, por exemplo, depende de cookies de sessao do Supabase.
          </p>

          <h2>Cookies de terceiros</h2>
          <p>
            O DataMaster Pro utiliza o <strong>Supabase</strong> como backend. O Supabase pode definir cookies
            proprios para autenticacao e gerenciamento de sessoes. Consulte a{' '}
            <a href="https://supabase.com/privacy" target="_blank" rel="noopener noreferrer">
              Politica de Privacidade do Supabase
            </a>{' '}
            para mais informacoes.
          </p>

          <h2>Contato</h2>
          <p>
            Em caso de duvidas sobre esta Politica de Cookies, entre em contato com nosso Encarregado de
            Protecao de Dados (DPO): <a href="mailto:dpo@datamaster.pro">dpo@datamaster.pro</a>
          </p>
        </div>
      </div>
    </div>
  )
}
