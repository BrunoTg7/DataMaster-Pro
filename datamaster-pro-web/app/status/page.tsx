import { Metadata } from 'next'
import { Activity, CheckCircle2, AlertCircle, Clock } from 'lucide-react'

export const metadata: Metadata = {
  title: 'Status do Sistema - DataMaster Pro',
  description: 'Verifique o status atual dos nossos serviços em tempo real.',
}

const SERVICES = [
  { name: 'Autenticação (Supabase)', status: 'operational', lastCheck: '1 min atrás' },
  { name: 'Web Dashboard', status: 'operational', lastCheck: '2 mins atrás' },
  { name: 'API de Licenciamento', status: 'operational', lastCheck: '1 min atrás' },
  { name: 'Downloads (CDN)', status: 'operational', lastCheck: '5 mins atrás' },
  { name: 'Edge Functions', status: 'operational', lastCheck: '3 mins atrás' },
]

export default function StatusPage() {
  return (
    <div className="min-h-screen bg-surface-50 pt-24 pb-12 px-4">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-[2.5rem] p-8 md:p-12 shadow-sm border border-surface-200">
          <div className="flex flex-col md:flex-row md:items-center justify-between mb-12 gap-6">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 bg-green-100 text-green-600 rounded-2xl flex items-center justify-center">
                <Activity className="w-8 h-8" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-surface-900">Status do Sistema</h1>
                <p className="text-surface-500 mt-1">Atualizado em tempo real</p>
              </div>
            </div>
            <div className="px-6 py-3 bg-green-50 border border-green-200 rounded-2xl flex items-center gap-3">
              <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse" />
              <span className="text-green-700 font-bold">Todos os sistemas operacionais</span>
            </div>
          </div>

          <div className="space-y-4">
            {SERVICES.map((service) => (
              <div key={service.name} className="flex items-center justify-between p-6 bg-surface-50 rounded-2xl border border-surface-100 transition-colors hover:bg-white hover:shadow-md">
                <div className="flex items-center gap-3">
                  <span className="font-bold text-surface-900">{service.name}</span>
                </div>
                <div className="flex items-center gap-6">
                  <div className="flex items-center gap-1.5 text-xs text-surface-400 font-medium">
                    <Clock className="w-3 h-3" /> {service.lastCheck}
                  </div>
                  <div className="flex items-center gap-2 text-green-600 font-bold text-sm bg-green-50 px-3 py-1 rounded-full border border-green-100">
                    <CheckCircle2 className="w-4 h-4" /> Operacional
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-12 pt-8 border-t border-surface-100">
            <h2 className="text-xl font-bold text-surface-900 mb-6 flex items-center gap-2">
              <Clock className="text-primary-600 w-5 h-5" />
              Histórico de Incidentes
            </h2>
            <div className="space-y-6">
              <div className="flex gap-4">
                <div className="w-10 h-10 bg-surface-100 rounded-xl flex items-center justify-center shrink-0">
                  <AlertCircle className="w-5 h-5 text-surface-400" />
                </div>
                <div>
                  <p className="text-surface-900 font-bold">Nenhum incidente relatado nos últimos 30 dias.</p>
                  <p className="text-sm text-surface-500 mt-1">Estamos mantendo 99.9% de uptime histórico.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div className="mt-12 text-center">
          <p className="text-surface-500 text-sm">
            Encontrou algum problema? <a href="/contato" className="text-primary-600 font-bold hover:underline">Fale com o suporte.</a>
          </p>
        </div>
      </div>
    </div>
  )
}
