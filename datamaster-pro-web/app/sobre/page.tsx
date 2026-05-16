import { Metadata } from 'next'
import { Users, Target, Rocket, ShieldCheck } from 'lucide-react'

export const metadata: Metadata = {
  title: 'Sobre Nós - DataMaster Pro',
  description: 'Conheça a história e a missão por trás do DataMaster Pro.',
}

export default function SobrePage() {
  return (
    <div className="min-h-screen bg-surface-50 pt-24 pb-12 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Hero Section */}
        <div className="text-center mb-20">
          <h1 className="text-5xl font-extrabold text-surface-900 mb-6 bg-clip-text text-transparent bg-gradient-to-r from-primary-600 to-primary-800">
            Nossa Missão é Simplificar
          </h1>
          <p className="text-xl text-surface-600 max-w-3xl mx-auto leading-relaxed">
            Nascemos da frustração de lidar com planilhas complexas e processos manuais lentos. 
            O DataMaster Pro foi criado para devolver o tempo às pessoas, automatizando o que é repetitivo.
          </p>
        </div>

        {/* Values Grid */}
        <div className="grid md:grid-cols-3 gap-8 mb-20">
          <div className="bg-white p-8 rounded-3xl shadow-sm border border-surface-100 hover:shadow-md transition-shadow">
            <div className="w-14 h-14 bg-primary-50 rounded-2xl flex items-center justify-center text-primary-600 mb-6">
              <Target className="w-8 h-8" />
            </div>
            <h3 className="text-xl font-bold text-surface-900 mb-3">Foco no Cliente</h3>
            <p className="text-surface-600 leading-relaxed">
              Cada funcionalidade é desenhada ouvindo quem realmente usa o Excel no dia a dia corporativo.
            </p>
          </div>
          <div className="bg-white p-8 rounded-3xl shadow-sm border border-surface-100 hover:shadow-md transition-shadow">
            <div className="w-14 h-14 bg-primary-50 rounded-2xl flex items-center justify-center text-primary-600 mb-6">
              <Rocket className="w-8 h-8" />
            </div>
            <h3 className="text-xl font-bold text-surface-900 mb-3">Inovação Constante</h3>
            <p className="text-surface-600 leading-relaxed">
              Não paramos. Estamos sempre buscando novas formas de processar dados com mais velocidade e precisão.
            </p>
          </div>
          <div className="bg-white p-8 rounded-3xl shadow-sm border border-surface-100 hover:shadow-md transition-shadow">
            <div className="w-14 h-14 bg-primary-50 rounded-2xl flex items-center justify-center text-primary-600 mb-6">
              <ShieldCheck className="w-8 h-8" />
            </div>
            <h3 className="text-xl font-bold text-surface-900 mb-3">Ética e Dados</h3>
            <p className="text-surface-600 leading-relaxed">
              Seus dados nunca saem do seu computador. Processamento local é o nosso compromisso com sua segurança.
            </p>
          </div>
        </div>

        {/* Stats Section */}
        <div className="bg-surface-900 rounded-[3rem] p-12 md:p-20 text-white relative overflow-hidden">
          <div className="absolute top-0 right-0 w-64 h-64 bg-primary-500/10 blur-[100px] rounded-full" />
          <div className="absolute bottom-0 left-0 w-64 h-64 bg-primary-500/10 blur-[100px] rounded-full" />
          
          <div className="grid md:grid-cols-3 gap-12 text-center relative z-10">
            <div>
              <div className="text-5xl font-bold text-primary-500 mb-2">500+</div>
              <p className="text-surface-400 font-medium">Empresas Atendidas</p>
            </div>
            <div>
              <div className="text-5xl font-bold text-primary-500 mb-2">10M+</div>
              <p className="text-surface-400 font-medium">Linhas Processadas</p>
            </div>
            <div>
              <div className="text-5xl font-bold text-primary-500 mb-2">20h+</div>
              <p className="text-surface-400 font-medium">Poupadas por Mês/Usuário</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
