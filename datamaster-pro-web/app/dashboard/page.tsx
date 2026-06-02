'use client'

import { useEffect, useState, useCallback } from 'react'
import { motion } from 'framer-motion'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import {
  Download,
  CreditCard,
  Shield,
  Zap,
  User,
  Settings,
  LogOut,
  ExternalLink,
  ChevronRight,
  Package,
  TrendingUp,
  Clock,
  Loader2
} from 'lucide-react'
import { supabase } from '@/lib/supabase/client'
import { TOOLS, PLAN_LIMITS } from '@/lib/constants'

type UserData = {
  id: string
  email: string
  nome: string
  plano_tipo: 'gratis' | 'pro' | 'enterprise'
  created_at?: string
  data_expiracao?: string
}

type ROIStats = {
  total_linhas: number
  total_tempo_ms: number
  total_tempo_economizado_minutos: number
  total_tempo_economizado_horas: number
  execucoes: number
}

type Activity = {
  id: string
  ferramenta: string
  created_at: string
}

export default function DashboardPage() {
  const router = useRouter()
  const [user, setUser] = useState<UserData | null>(null)
  const [stats, setStats] = useState<ROIStats | null>(null)
  const [toolStats, setToolStats] = useState<Record<string, { lines: number, execs: number }>>({})
  const [activities, setActivities] = useState<Activity[]>([])
  const [loading, setLoading] = useState(true)

  const fetchData = useCallback(async () => {
    try {
      const { data: { session }, error: sessionError } = await supabase.auth.getSession()

      if (sessionError) {
        console.warn('Session error:', sessionError.message)
        await supabase.auth.signOut()
        router.push('/auth/login')
        return
      }

      if (!session) {
        router.push('/auth/login')
        return
      }

      const [profileRes, roiRes, toolRes, recentRes] = await Promise.all([
        supabase.from('usuarios').select('*').eq('id', session.user.id).single(),
        supabase.rpc('calcular_roi', { p_usuario_id: session.user.id, p_dias: 30 }),
        supabase
          .from('execucoes')
          .select('ferramenta, linhas_processadas')
          .eq('usuario_id', session.user.id)
          .gte('created_at', new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString()),
        supabase
          .from('execucoes')
          .select('id, ferramenta, created_at')
          .eq('usuario_id', session.user.id)
          .order('created_at', { ascending: false })
          .limit(5)
      ])

      if (profileRes.data) {
        setUser(profileRes.data as UserData)
      }

      if (!roiRes.error && roiRes.data) {
        setStats(roiRes.data as ROIStats)
      }

      if (toolRes.data) {
        const statsMap: Record<string, { lines: number, execs: number }> = {}
        let totalLinhasFerramentas = 0
        let totalExecs = 0

        toolRes.data.forEach((exec: { ferramenta: string; linhas_processadas: number }) => {
          if (!statsMap[exec.ferramenta]) {
            statsMap[exec.ferramenta] = { lines: 0, execs: 0 }
          }
          statsMap[exec.ferramenta].execs += 1
          statsMap[exec.ferramenta].lines += (exec.linhas_processadas || 0)

          if (exec.ferramenta === 'consolidador' || exec.ferramenta === 'categorizador') {
            totalLinhasFerramentas += (exec.linhas_processadas || 0)
          }
          totalExecs += 1
        })
        setToolStats(statsMap)

        setStats(prev => prev ? ({
          ...prev,
          total_linhas: totalLinhasFerramentas,
          execucoes: totalExecs
        }) : null)
      }

      if (recentRes.data) {
        setActivities(recentRes.data as Activity[])
      }

    } catch (err) {
      console.error('Erro ao carregar dados:', err)
    } finally {
      setLoading(false)
    }
  }, [router])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const calculateRenewalDate = (createdAt?: string, dataExpiracao?: string) => {
    if (currentPlan !== 'gratis' && dataExpiracao) {
      return new Date(dataExpiracao)
    }

    if (!createdAt) return null
    const created = new Date(createdAt)
    const now = new Date()

    let renewal = new Date(now.getFullYear(), now.getMonth(), created.getDate())

    const lastDayOfMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate()
    if (created.getDate() > lastDayOfMonth) {
      renewal.setDate(lastDayOfMonth)
    }

    if (renewal <= now) {
      renewal = new Date(now.getFullYear(), now.getMonth() + 1, created.getDate())
      const nextMonthLastDay = new Date(now.getFullYear(), now.getMonth() + 2, 0).getDate()
      if (created.getDate() > nextMonthLastDay) {
        renewal.setDate(nextMonthLastDay)
      }
    }

    return renewal
  }

  const handleLogout = async () => {
    await supabase.auth.signOut()
    router.push('/')
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-surface-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-10 h-10 text-primary-500 animate-spin mx-auto mb-4" />
          <p className="text-surface-600 font-medium">Carregando seu painel...</p>
        </div>
      </div>
    )
  }

  const currentPlan = user?.plano_tipo || 'gratis'
  const planLimits = PLAN_LIMITS[currentPlan === 'gratis' ? 'free' : currentPlan as 'pro' | 'enterprise']

  return (
    <div className="min-h-screen bg-surface-50 pt-24 pb-16 relative overflow-hidden">
      <div className="absolute inset-0">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[300px] bg-primary-500/[0.03] rounded-full blur-3xl" />
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
        <div className="flex flex-col md:flex-row md:items-center justify-between mb-8 gap-4">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
          >
            <h1 className="text-4xl font-bold text-surface-900 font-display">Dashboard</h1>
            <p className="text-surface-600 mt-2 text-lg">Bem-vindo de volta, {user?.nome}</p>
          </motion.div>

          <div className="flex items-center gap-3">
            <div className="text-right hidden sm:block">
              <div className="text-sm font-bold text-surface-900">{user?.nome}</div>
              <div className="text-xs text-surface-500 capitalize">Plano {currentPlan}</div>
            </div>
            <div className="w-12 h-12 rounded-2xl bg-white border border-surface-200 flex items-center justify-center shadow-sm">
              <User className="w-6 h-6 text-primary-600" />
            </div>
          </div>
        </div>

        <div className="grid lg:grid-cols-3 gap-6 lg:gap-8">
          <div className="lg:col-span-2 space-y-6">
            {/* Stats Card */}
            <div className="mb-12">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold text-surface-900 font-display flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-primary-500" />
                  Impacto e Uso (30 dias)
                </h2>
                <span className={`px-4 py-1.5 rounded-full text-xs font-bold ${currentPlan === 'pro' ? 'bg-primary-500 text-white' : 'bg-primary-100 text-primary-900'
                  }`}>
                  {currentPlan.toUpperCase()}
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
                <motion.div
                  whileHover={{ y: -5 }}
                  className="p-6 bg-white rounded-[2rem] border border-surface-100 shadow-xl shadow-surface-200/40 transition-all"
                >
                  <TrendingUp className="w-5 h-5 text-primary-500 mb-3" />
                  <div className="text-3xl font-bold text-surface-900 font-display">
                    {stats?.total_linhas || 0} {currentPlan === 'gratis' ? '/ 1200' : ''}
                  </div>
                  <div className="text-xs text-surface-500 font-bold mt-1">Linhas Processadas</div>
                </motion.div>

                <motion.div
                  whileHover={{ y: -5 }}
                  className="p-6 bg-white rounded-[2rem] border border-surface-100 shadow-xl shadow-surface-200/40 transition-all"
                >
                  <Zap className="w-5 h-5 text-primary-500 mb-3" />
                  <div className="text-3xl font-bold text-surface-900 font-display">
                    {stats?.execucoes || 0} {currentPlan === 'gratis' ? '/ 15' : ''}
                  </div>
                  <div className="text-xs text-surface-500 font-bold mt-1">Tarefas Realizadas</div>
                </motion.div>

                <motion.div
                  whileHover={{ y: -5 }}
                  className="p-6 bg-primary-600 rounded-[2rem] shadow-xl shadow-primary-500/20 transition-all text-white"
                >
                  <Clock className="w-5 h-5 text-primary-200 mb-3" />
                  <div className="text-3xl font-bold font-display">
                    {stats?.total_tempo_economizado_horas?.toFixed(1) || 0}h
                  </div>
                  <div className="text-xs text-primary-100 font-bold mt-1">Tempo Poupado</div>
                </motion.div>
              </div>
            </div>

            {/* Tools Grid */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="bg-white rounded-[2.5rem] p-8 shadow-xl shadow-surface-200/50 border border-surface-100"
            >
              <h2 className="text-xl font-bold text-surface-900 mb-6 font-display">Minhas Ferramentas</h2>
              <div className="grid sm:grid-cols-2 gap-4">
                {TOOLS.map(tool => {
                  const isAvailable = planLimits.tools.includes(tool.id as any) || planLimits.tools.includes('all' as any)
                  const isComingSoon = 'status' in tool

                  // Estatísticas reais desta ferramenta
                  const currentUsage = toolStats[tool.id] || { lines: 0, execs: 0 }
                  const toolLimit = planLimits.tools_limit?.[tool.id as keyof typeof planLimits.tools_limit]

                  const getUnit = () => {
                    if (tool.id === 'orcamentos' || tool.id === 'ocr') return 'Documentos'
                    if (tool.id === 'conciliador') return null  // Não mostra linhas
                    if (tool.id === 'minerador') return 'Links'
                    return 'Linhas'
                  }

                   const maxLines = (toolLimit && 'max_per_exec' in toolLimit) ? toolLimit.max_per_exec || null : null

                   const maxExecs = (toolLimit && 'max_execs' in toolLimit) ? toolLimit.max_execs || null : null

                  const isOrcamentos = tool.id === 'orcamentos'

                  return (
                    <div
                      key={tool.id}
                      onClick={() => {
                        if (isOrcamentos && isAvailable && !isComingSoon) {
                          router.push('/orcamentos-demo')
                        }
                      }}
                      className={`group p-6 rounded-[2.5rem] transition-all duration-300 border ${isComingSoon
                        ? 'bg-surface-50 border-transparent opacity-60'
                        : isAvailable
                          ? `bg-white border-surface-100 hover:border-primary-200 hover:shadow-xl ${isOrcamentos ? 'cursor-pointer' : ''}`
                          : 'bg-surface-50 border-transparent opacity-60 grayscale'
                        }`}
                    >
                      <div className="flex items-center gap-4 mb-4">
                        <div className={`w-12 h-12 rounded-2xl flex items-center justify-center transition-transform group-hover:scale-110 ${isAvailable ? 'bg-primary-50 text-primary-600' : 'bg-surface-200 text-surface-400'
                          }`}>
                          <Package className="w-6 h-6" />
                        </div>
                        <div>
                          <div className="font-bold text-surface-900">{tool.name}</div>
                          <div className="flex flex-col gap-0.5 mt-1">
                            {'status' in tool && (
                              <div className="text-[10px] font-bold text-primary-600 uppercase tracking-wider">
                                {tool.status}
                              </div>
                            )}
                            {(toolLimit && 'plano' in toolLimit && toolLimit.plano) && (
                              <div className="text-[10px] font-bold text-primary-600 uppercase tracking-wider">
                                {toolLimit.plano}
                              </div>
                            )}
                            {maxLines !== null && getUnit() !== null && (
                              <div className="text-[10px] font-bold text-primary-600 uppercase tracking-wider">
                                {currentPlan === 'gratis' ? `${currentUsage.lines} / ${maxLines} ${getUnit()}` : 'Ilimitado'}
                              </div>
                            )}
                            {maxExecs !== null && (
                              <div className="text-[10px] font-bold text-surface-400 uppercase tracking-wider">
                                {currentPlan === 'gratis' ? `${currentUsage.execs} / ${maxExecs} Execuções` : 'Ilimitado'}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                      <p className="text-sm text-surface-600 line-clamp-2 mb-4 leading-relaxed">
                        {tool.description}
                      </p>
                      {isComingSoon ? (
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-1.5 text-xs font-bold text-surface-500 bg-surface-100 px-3 py-1 rounded-full w-fit">
                            Em breve
                          </div>
                        </div>
                      ) : (toolLimit && 'plano' in toolLimit && toolLimit.plano) ? (
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-1.5 text-xs font-bold text-primary-600 bg-primary-50 px-3 py-1 rounded-full w-fit">
                            {toolLimit.plano}
                          </div>
                          <ChevronRight className="w-4 h-4 text-surface-300" />
                        </div>
                      ) : isAvailable ? (
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-1.5 text-xs font-bold text-green-600 bg-green-50 px-3 py-1 rounded-full w-fit">
                            <span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"></span>
                            Ativo
                          </div>
                          {tool.id === 'orcamentos' && (
                            <Link
                              href="/orcamentos-demo"
                              className="text-xs font-bold text-primary-600 hover:text-primary-700 flex items-center gap-1"
                            >
                              Ver Demo
                            </Link>
                          )}
                          <ChevronRight className="w-4 h-4 text-surface-300 group-hover:text-primary-500 transition-colors" />
                        </div>
                      ) : (
                        <Link href="/planos" className="text-primary-600 text-xs font-bold hover:underline flex items-center gap-1">
                          Liberar no Pro <ExternalLink className="w-3 h-3" />
                        </Link>
                      )}
                    </div>
                  )
                })}
              </div>
            </motion.div>
          </div>

          <div className="space-y-6">
            {/* User Profile Summary */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="bg-white rounded-[2.5rem] p-8 shadow-xl shadow-surface-200/50 border border-surface-100 overflow-hidden relative"
            >
              <div className="absolute top-0 right-0 w-24 h-24 bg-primary-50 rounded-full -mr-8 -mt-8" />

              <div className="relative z-10">
                <h3 className="font-bold text-surface-900 text-lg mb-6">Conta</h3>
                <div className="space-y-2">
                  <Link href="/dashboard/configuracoes" className="flex items-center justify-between p-4 rounded-2xl hover:bg-surface-50 text-surface-700 font-bold transition-all group">
                    <div className="flex items-center gap-3">
                      <Settings className="w-5 h-5 text-surface-400 group-hover:rotate-45 transition-transform" />
                      <span>Configurações</span>
                    </div>
                    <ChevronRight className="w-4 h-4" />
                  </Link>
                  <Link href="/planos" className="flex items-center justify-between p-4 rounded-2xl hover:bg-surface-50 text-surface-700 font-bold transition-all group">
                    <div className="flex items-center gap-3">
                      <CreditCard className="w-5 h-5 text-surface-400" />
                      <span>Plano e Faturas</span>
                    </div>
                    <ChevronRight className="w-4 h-4" />
                  </Link>

                  {(user?.created_at || user?.data_expiracao) && (
                    <div className="p-4 rounded-2xl bg-primary-100/100 border border-primary-100/50 mt-2">
                      <div className="text-[10px] uppercase tracking-widest text-primary-600 font-bold mb-1 flex items-center gap-2">
                        <Clock className="w-3 h-3" />
                        {currentPlan === 'gratis' ? 'Renovação do Limite' : 'Vencimento do Plano'}
                      </div>
                      <div className="text-sm font-bold text-primary-900">
                        {calculateRenewalDate(user.created_at, user.data_expiracao)?.toLocaleDateString('pt-BR')}
                      </div>
                    </div>
                  )}
                  <button
                    onClick={handleLogout}
                    className="w-full flex items-center gap-3 p-4 rounded-2xl hover:bg-red-50 text-red-600 font-bold transition-all group mt-2"
                  >
                    <LogOut className="w-5 h-5 group-hover:-translate-x-1 transition-transform" />
                    <span>Sair da Conta</span>
                  </button>
                </div>
              </div>
            </motion.div>

            {/* Download App */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="bg-surface-900 rounded-[2.5rem] p-8 text-white shadow-xl shadow-surface-900/20 relative overflow-hidden group"
            >
              <div className="absolute top-0 right-0 w-32 h-32 bg-primary-500/10 rounded-full -mr-16 -mt-16 blur-2xl group-hover:bg-primary-500/20 transition-all" />

              <h3 className="font-bold text-2xl mb-3 font-display">DataMaster Desktop</h3>
              <p className="text-surface-400 text-sm mb-8 leading-relaxed">
                Baixe a versão mais recente para processar seus arquivos localmente com máxima velocidade.
              </p>
              <Link
                href="/downloads"
                className="w-full bg-primary-500 hover:bg-primary-600 text-white font-bold py-4 rounded-2xl flex items-center justify-center gap-2 transition-all shadow-lg shadow-primary-500/25 active:scale-95"
              >
                <Download className="w-5 h-5" />
                Download Windows
              </Link>
              <div className="mt-4 flex items-center justify-center gap-4 text-[10px] uppercase tracking-widest text-surface-500 font-bold">
                <span>Versão 1.5.0</span>
                <span className="w-1 h-1 bg-surface-700 rounded-full"></span>
                <span>SHA-256 Verificado</span>
              </div>
            </motion.div>

            {/* Recent Activity */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="bg-white rounded-[2.5rem] p-8 shadow-xl shadow-surface-200/50 border border-surface-100"
            >
              <h3 className="font-bold text-surface-900 text-lg mb-6 font-display flex items-center gap-2">
                <Clock className="w-5 h-5 text-primary-500" />
                Atividade Recente
              </h3>
              <div className="space-y-6">
                {activities.length > 0 ? activities.map((activity) => (
                  <div key={activity.id} className="flex items-start gap-4">
                    <div className="w-10 h-10 rounded-xl bg-surface-50 flex items-center justify-center flex-shrink-0 mt-0.5 border border-surface-100">
                      <Package className="w-5 h-5 text-primary-600" />
                    </div>
                    <div>
                      <p className="text-sm text-surface-900 font-bold capitalize">
                        {activity.ferramenta}
                      </p>
                      <p className="text-xs text-surface-500">
                        {new Date(activity.created_at).toLocaleDateString('pt-BR', {
                          day: '2-digit',
                          month: 'short',
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </p>
                    </div>
                  </div>
                )) : (
                  <div className="text-center py-8">
                    <div className="w-12 h-12 bg-surface-50 rounded-2xl flex items-center justify-center mx-auto mb-4 border border-dashed border-surface-300">
                      <Clock className="w-6 h-6 text-surface-300" />
                    </div>
                    <p className="text-sm text-surface-500">Nenhuma tarefa executada ainda.</p>
                  </div>
                )}
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  )
}