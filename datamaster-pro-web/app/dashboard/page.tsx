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
  plano_tipo: 'gratis' | 'starter' | 'pro'
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

function getCycleStart(createdAt?: string): Date {
  if (!createdAt) return new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)
  const created = new Date(createdAt)
  const now = new Date()
  let cycleStart = new Date(now.getFullYear(), now.getMonth(), created.getDate())
  const lastDay = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate()
  if (created.getDate() > lastDay) {
    cycleStart.setDate(lastDay)
  }
  if (cycleStart > now) {
    const prevMonth = now.getMonth() === 0 ? 11 : now.getMonth() - 1
    const prevYear = now.getMonth() === 0 ? now.getFullYear() - 1 : now.getFullYear()
    cycleStart = new Date(prevYear, prevMonth, created.getDate())
    const prevLastDay = new Date(prevYear, prevMonth + 1, 0).getDate()
    if (created.getDate() > prevLastDay) {
      cycleStart.setDate(prevLastDay)
    }
  }
  return cycleStart
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

      const profileRes = await supabase.from('usuarios').select('*').eq('id', session.user.id).single()

      if (profileRes.data) {
        setUser(profileRes.data as UserData)
      }

      const cycleStart = getCycleStart(profileRes.data?.created_at)
      const cycleDays = Math.max(1, Math.ceil((Date.now() - cycleStart.getTime()) / (1000 * 60 * 60 * 24)))

      const [roiRes, toolRes, recentRes] = await Promise.all([
        supabase.rpc('calcular_roi', { p_usuario_id: session.user.id, p_dias: cycleDays }),
        supabase
          .from('execucoes')
          .select('ferramenta, linhas_processadas')
          .eq('usuario_id', session.user.id)
          .gte('created_at', cycleStart.toISOString()),
        supabase
          .from('execucoes')
          .select('id, ferramenta, created_at')
          .eq('usuario_id', session.user.id)
          .order('created_at', { ascending: false })
          .limit(5)
      ])

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
  const planLimits = PLAN_LIMITS[currentPlan === 'gratis' ? 'free' : currentPlan as 'starter' | 'pro']

  return (
    <div className="min-h-screen bg-surface-50 pt-20 sm:pt-24 pb-10 sm:pb-16 relative overflow-hidden">
      <div className="absolute inset-0">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[300px] bg-primary-500/[0.03] rounded-full blur-3xl" />
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-6 sm:mb-8 gap-3 sm:gap-4">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
          >
            <h1 className="text-2xl sm:text-4xl font-bold text-surface-900 font-display">Dashboard</h1>
            <p className="text-surface-600 mt-1 sm:mt-2 text-sm sm:text-lg">Bem-vindo de volta, {user?.nome}</p>
          </motion.div>

          <div className="flex items-center gap-3">
            <div className="text-right hidden sm:block">
              <div className="text-sm font-bold text-surface-900">{user?.nome}</div>
              <div className="text-xs text-surface-500 capitalize">Plano {currentPlan}</div>
            </div>
            <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-xl sm:rounded-2xl bg-white border border-surface-200 flex items-center justify-center shadow-sm">
              <User className="w-5 h-5 sm:w-6 sm:h-6 text-primary-600" />
            </div>
          </div>
        </div>

        <div className="grid lg:grid-cols-3 gap-4 sm:gap-6 lg:gap-8">
          <div className="lg:col-span-2 space-y-4 sm:space-y-6">
            {/* Stats Card */}
            <div className="mb-6 sm:mb-12">
              <div className="flex items-center justify-between mb-4 sm:mb-6">
                <h2 className="text-base sm:text-xl font-bold text-surface-900 font-display flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 sm:w-5 sm:h-5 text-primary-500" />
                  Impacto e Uso (30 dias)
                </h2>
                <span className={`px-2.5 sm:px-4 py-1 sm:py-1.5 rounded-full text-[10px] sm:text-xs font-bold ${currentPlan === 'pro' ? 'bg-primary-500 text-white' : 'bg-primary-100 text-primary-900'
                  }`}>
                  {currentPlan.toUpperCase()}
                </span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5 sm:gap-6">
                <motion.div
                  whileHover={{ y: -5 }}
                  className="p-3 sm:p-6 bg-white rounded-xl sm:rounded-[2rem] border border-surface-100 shadow-xl shadow-surface-200/40 transition-all"
                >
                  <TrendingUp className="w-3.5 h-3.5 sm:w-5 sm:h-5 text-primary-500 mb-1.5 sm:mb-3" />
                  <div className="text-lg sm:text-3xl font-bold text-surface-900 font-display">
                    {stats?.total_linhas || 0} {currentPlan === 'gratis' ? '/ 1200' : ''}
                  </div>
                  <div className="text-[9px] sm:text-xs text-surface-500 font-bold mt-0.5 sm:mt-1">Linhas</div>
                </motion.div>

                <motion.div
                  whileHover={{ y: -5 }}
                  className="p-3 sm:p-6 bg-white rounded-xl sm:rounded-[2rem] border border-surface-100 shadow-xl shadow-surface-200/40 transition-all"
                >
                  <Zap className="w-3.5 h-3.5 sm:w-5 sm:h-5 text-primary-500 mb-1.5 sm:mb-3" />
                  <div className="text-lg sm:text-3xl font-bold text-surface-900 font-display">
                    {stats?.execucoes || 0} {currentPlan === 'gratis' ? '/ 15' : ''}
                  </div>
                  <div className="text-[9px] sm:text-xs text-surface-500 font-bold mt-0.5 sm:mt-1">Tarefas</div>
                </motion.div>

                <motion.div
                  whileHover={{ y: -5 }}
                  className="col-span-2 sm:col-span-1 p-3 sm:p-6 bg-primary-600 rounded-xl sm:rounded-[2rem] shadow-xl shadow-primary-500/20 transition-all text-white"
                >
                  <Clock className="w-3.5 h-3.5 sm:w-5 sm:h-5 text-primary-200 mb-1.5 sm:mb-3" />
                  <div className="text-lg sm:text-3xl font-bold font-display">
                    {(() => {
                      const h = stats?.total_tempo_economizado_horas || 0;
                      if (h <= 0) return '0 min';
                      const hours = Math.floor(h);
                      const mins = Math.round((h - hours) * 60);
                      if (hours > 0 && mins > 0) return `${hours}h ${mins}min`;
                      if (hours > 0) return `${hours}h`;
                      return `${mins} min`;
                    })()}
                  </div>
                  <div className="text-[9px] sm:text-xs text-primary-100 font-bold mt-0.5 sm:mt-1">Tempo Poupado</div>
                </motion.div>
              </div>
            </div>

            {/* Tools Grid */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="bg-white rounded-2xl sm:rounded-[2.5rem] p-5 sm:p-8 shadow-xl shadow-surface-200/50 border border-surface-100"
            >
              <h2 className="text-base sm:text-xl font-bold text-surface-900 mb-4 sm:mb-6 font-display">Minhas Ferramentas</h2>
              <div className="grid grid-cols-2 gap-2.5 sm:gap-4">
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
                      className={`group p-3 sm:p-6 rounded-xl sm:rounded-[2.5rem] transition-all duration-300 border ${isComingSoon
                        ? 'bg-surface-50 border-surface-200 opacity-70'
                        : isAvailable
                          ? `bg-white border-surface-100 hover:border-primary-200 hover:shadow-xl ${isOrcamentos ? 'cursor-pointer' : ''}`
                          : 'bg-surface-50 border-surface-200 opacity-60 grayscale'
                        }`}
                    >
                      <div className="flex items-center gap-2 sm:gap-4 mb-2 sm:mb-4">
                        <div className={`w-8 h-8 sm:w-12 sm:h-12 rounded-lg sm:rounded-2xl flex items-center justify-center transition-transform group-hover:scale-110 flex-shrink-0 ${isAvailable ? 'bg-primary-50 text-primary-600' : 'bg-surface-200 text-surface-400'
                          }`}>
                          <Package className="w-4 h-4 sm:w-6 sm:h-6" />
                        </div>
                        <div className="min-w-0">
                          <div className="font-bold text-surface-900 text-xs sm:text-base truncate">{tool.name}</div>
                          <div className="flex flex-col gap-0 mt-0.5">
                            {'status' in tool && (
                              <div className="text-[8px] sm:text-[10px] font-bold text-primary-600 uppercase tracking-wider">
                                {tool.status}
                              </div>
                            )}
                            {maxLines !== null && getUnit() !== null && (
                              <div className="text-[8px] sm:text-[10px] font-bold text-primary-600 uppercase tracking-wider">
                                {currentPlan === 'gratis' ? `${currentUsage.lines}/${maxLines}` : 'Ilimitado'}
                              </div>
                            )}
                            {maxExecs !== null && (
                              <div className="text-[8px] sm:text-[10px] font-bold text-surface-400 uppercase tracking-wider">
                                {currentPlan === 'gratis' ? `${currentUsage.execs}/${maxExecs}` : 'Ilimitado'}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                      <p className="text-surface-600 text-[10px] sm:text-sm mb-2 sm:mb-4 leading-relaxed">
                        {tool.description}
                      </p>
                      {isComingSoon ? (
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-1 sm:gap-1.5 text-[8px] sm:text-xs font-bold text-surface-500 bg-surface-100 px-2 sm:px-3 py-0.5 sm:py-1 rounded-full w-fit">
                            Em breve
                          </div>
                        </div>
                      ) : isAvailable ? (
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-1 sm:gap-1.5 text-[8px] sm:text-xs font-bold text-green-600 bg-green-50 px-2 sm:px-3 py-0.5 sm:py-1 rounded-full w-fit">
                            <span className="w-1 h-1 sm:w-1.5 sm:h-1.5 bg-green-500 rounded-full animate-pulse"></span>
                            <span className="hidden sm:inline">Ativo</span>
                            <span className="sm:hidden">OK</span>
                          </div>
                          {tool.id === 'orcamentos' && (
                            <Link
                              href="/orcamentos-demo"
                              className="text-[8px] sm:text-xs font-bold text-primary-600 hover:text-primary-700 flex items-center gap-0.5 sm:gap-1"
                            >
                              Demo
                            </Link>
                          )}
                          <ChevronRight className="w-3 h-3 sm:w-4 sm:h-4 text-surface-300 group-hover:text-primary-500 transition-colors" />
                        </div>
                      ) : (
                        <Link href="/planos" className="text-primary-600 text-[8px] sm:text-xs font-bold hover:underline flex items-center gap-0.5 sm:gap-1">
                          Upgrade <ExternalLink className="w-2 h-2 sm:w-3 sm:h-3" />
                        </Link>
                      )}
                    </div>
                  )
                })}
              </div>
            </motion.div>
          </div>

          <div className="space-y-4 sm:space-y-6">
            {/* User Profile Summary - apenas desktop */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="hidden lg:block bg-white rounded-2xl sm:rounded-[2.5rem] p-5 sm:p-8 shadow-xl shadow-surface-200/50 border border-surface-100 overflow-hidden relative"
            >
              <div className="absolute top-0 right-0 w-20 sm:w-24 h-20 sm:h-24 bg-primary-50 rounded-full -mr-6 sm:-mr-8 -mt-6 sm:-mt-8" />

              <div className="relative z-10">
                <h3 className="font-bold text-surface-900 text-base sm:text-lg mb-4 sm:mb-6">Conta</h3>
                <div className="space-y-1.5 sm:space-y-2">
                  <Link href="/dashboard/configuracoes" className="flex items-center justify-between p-3 sm:p-4 rounded-xl sm:rounded-2xl hover:bg-surface-50 text-surface-700 font-bold transition-all group">
                    <div className="flex items-center gap-2.5 sm:gap-3">
                      <Settings className="w-4 h-4 sm:w-5 sm:h-5 text-surface-400 group-hover:rotate-45 transition-transform" />
                      <span className="text-sm sm:text-base">Configurações</span>
                    </div>
                    <ChevronRight className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
                  </Link>
                  <Link href="/planos" className="flex items-center justify-between p-3 sm:p-4 rounded-xl sm:rounded-2xl hover:bg-surface-50 text-surface-700 font-bold transition-all group">
                    <div className="flex items-center gap-2.5 sm:gap-3">
                      <CreditCard className="w-4 h-4 sm:w-5 sm:h-5 text-surface-400" />
                      <span className="text-sm sm:text-base">Plano e Faturas</span>
                    </div>
                    <ChevronRight className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
                  </Link>

                  {(user?.created_at || user?.data_expiracao) && (
                    <div className="p-3 sm:p-4 rounded-xl sm:rounded-2xl bg-primary-100/100 border border-primary-100/50 mt-1.5 sm:mt-2">
                      <div className="text-[9px] sm:text-[10px] uppercase tracking-widest text-primary-600 font-bold mb-0.5 sm:mb-1 flex items-center gap-1.5 sm:gap-2">
                        <Clock className="w-2.5 h-2.5 sm:w-3 sm:h-3" />
                        {currentPlan === 'gratis' ? 'Renovação do Limite' : 'Vencimento do Plano'}
                      </div>
                      <div className="text-xs sm:text-sm font-bold text-primary-900">
                        {calculateRenewalDate(user.created_at, user.data_expiracao)?.toLocaleDateString('pt-BR')}
                      </div>
                    </div>
                  )}
                  <button
                    onClick={handleLogout}
                    className="w-full flex items-center gap-2.5 sm:gap-3 p-3 sm:p-4 rounded-xl sm:rounded-2xl hover:bg-red-50 text-red-600 font-bold transition-all group mt-1.5 sm:mt-2"
                  >
                    <LogOut className="w-4 h-4 sm:w-5 sm:h-5 group-hover:-translate-x-1 transition-transform" />
                    <span className="text-sm sm:text-base">Sair da Conta</span>
                  </button>
                </div>
              </div>
            </motion.div>

            {/* Download App e Atividade lado a lado no mobile */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-1 gap-4 sm:gap-6">
              {/* Download App */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="bg-surface-900 rounded-2xl sm:rounded-[2.5rem] p-4 sm:p-8 text-white shadow-xl shadow-surface-900/20 relative overflow-hidden group"
              >
                <div className="absolute top-0 right-0 w-20 sm:w-32 h-20 sm:h-32 bg-primary-500/10 rounded-full -mr-10 sm:-mr-16 -mt-10 sm:-mt-16 blur-2xl group-hover:bg-primary-500/20 transition-all" />

                <h3 className="font-bold text-base sm:text-2xl mb-1.5 sm:mb-3 font-display">DataMaster Desktop</h3>
                <p className="text-surface-400 text-[10px] sm:text-sm mb-3 sm:mb-8 leading-relaxed">
                  Baixe a versão mais recente para processar seus arquivos localmente com máxima velocidade.
                </p>
                <Link
                  href="/downloads"
                  className="w-full bg-primary-500 hover:bg-primary-600 text-white font-bold py-2.5 sm:py-4 rounded-lg sm:rounded-2xl flex items-center justify-center gap-2 transition-all shadow-lg shadow-primary-500/25 active:scale-95 text-xs sm:text-base"
                >
                  <Download className="w-3.5 h-3.5 sm:w-5 sm:h-5" />
                  Download
                </Link>
                <div className="mt-2 sm:mt-4 flex items-center justify-center gap-2 sm:gap-4 text-[8px] sm:text-[10px] uppercase tracking-widest text-surface-500 font-bold">
                  <span>v1.5.0</span>
                  <span className="w-0.5 h-0.5 sm:w-1 sm:h-1 bg-surface-700 rounded-full"></span>
                  <span className="hidden sm:inline">SHA-256 Verificado</span>
                </div>
              </motion.div>

              {/* Recent Activity */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                className="bg-white rounded-2xl sm:rounded-[2.5rem] p-4 sm:p-8 shadow-xl shadow-surface-200/50 border border-surface-100"
              >
                <h3 className="font-bold text-surface-900 text-sm sm:text-lg mb-3 sm:mb-6 font-display flex items-center gap-2">
                  <Clock className="w-3.5 h-3.5 sm:w-5 sm:h-5 text-primary-500" />
                  Atividade Recente
                </h3>
                <div className="space-y-2.5 sm:space-y-6">
                  {activities.length > 0 ? activities.slice(0, 3).map((activity) => (
                    <div key={activity.id} className="flex items-start gap-2.5 sm:gap-4">
                      <div className="w-7 h-7 sm:w-10 sm:h-10 rounded-lg sm:rounded-xl bg-surface-50 flex items-center justify-center flex-shrink-0 mt-0.5 border border-surface-100">
                        <Package className="w-3.5 h-3.5 sm:w-5 sm:h-5 text-primary-600" />
                      </div>
                      <div className="min-w-0">
                        <p className="text-xs sm:text-sm text-surface-900 font-bold capitalize truncate">
                          {activity.ferramenta}
                        </p>
                        <p className="text-[9px] sm:text-xs text-surface-500">
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
                    <div className="text-center py-4 sm:py-8">
                      <div className="w-8 h-8 sm:w-12 sm:h-12 bg-surface-50 rounded-lg sm:rounded-2xl flex items-center justify-center mx-auto mb-2 sm:mb-4 border border-dashed border-surface-300">
                        <Clock className="w-4 h-4 sm:w-6 sm:h-6 text-surface-300" />
                      </div>
                      <p className="text-[10px] sm:text-sm text-surface-500">Nenhuma tarefa ainda.</p>
                    </div>
                  )}
                </div>
              </motion.div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}