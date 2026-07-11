"use client"

import { useThemeContext } from '@/hooks/ThemeProvider'
import { supabase } from '@/lib/supabase/client'
import { AnimatePresence, motion } from 'framer-motion'
import { AlertTriangle, Bell, Check, Info, Loader2, Lock, Mail, Monitor, Moon, Shield, Sun, Trash2, User, X } from 'lucide-react'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'

type Tab = 'perfil' | 'seguranca' | 'notificacoes' | 'privacidade'
type ToastType = 'success' | 'error' | 'info'

interface Toast {
  message: string
  type: ToastType
}

export default function ConfiguracoesPage() {
  const router = useRouter()
  const { theme: currentTheme, updateTheme, loading: themeLoading } = useThemeContext()
  const [activeTab, setActiveTab] = useState<Tab>('perfil')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [toast, setToast] = useState<Toast | null>(null)

  const showToast = (message: string, type: ToastType = 'info') => {
    setToast({ message, type })
    setTimeout(() => setToast(null), 5000)
  }

  const [formData, setFormData] = useState({
    nome: '',
    email: '',
    empresa: '',
    tema: 'system',
    notificacoes_email: true,
    notificacoes_desktop: true
  })

  useEffect(() => {
    async function loadProfile() {
      const { data: { session }, error: sessionError } = await supabase.auth.getSession()
      if (sessionError || !session) {
        router.push('/auth/login')
        return
      }

      const { data: profile } = await supabase
        .from('usuarios')
        .select('*')
        .eq('id', session.user.id)
        .single()

      if (profile) {
        setFormData({
          nome: profile.nome || '',
          email: profile.email || '',
          empresa: profile.empresa || '',
          tema: profile.preferencias_tema || 'system',
          notificacoes_email: profile.notificacoes_email ?? true,
          notificacoes_desktop: profile.notificacoes_desktop ?? true
        })
      }
      setLoading(false)
    }
    loadProfile()
  }, [router])

  const handleSave = async () => {
    setSaving(true)
    try {
      const { data: { session }, error: sessionError } = await supabase.auth.getSession()
      if (sessionError || !session) return

      // Sanitizar inputs
      const nomeSanitizado = formData.nome.trim().slice(0, 100)
      const empresaSanitizada = formData.empresa.trim().slice(0, 100)

      if (nomeSanitizado.length < 2) {
        alert('Nome deve ter pelo menos 2 caracteres.')
        setSaving(false)
        return
      }

      const { error } = await supabase
        .from('usuarios')
        .update({
          nome: nomeSanitizado,
          empresa: empresaSanitizada,
          preferencias_tema: formData.tema,
          notificacoes_email: formData.notificacoes_email,
          notificacoes_desktop: formData.notificacoes_desktop,
          updated_at: new Date().toISOString()
        })
        .eq('id', session.user.id)

      if (error) throw error

      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } catch (err) {
      console.error('Erro ao salvar:', err)
      showToast('Erro ao salvar as configuracoes.', 'error')
    } finally {
      setSaving(false)
    }
  }

  const handleResetPassword = async () => {
    const { error } = await supabase.auth.resetPasswordForEmail(formData.email, {
      redirectTo: `${window.location.origin}/auth/reset-password`,
    })
    if (error) showToast(error.message, 'error')
    else showToast('Email de redefinicao de senha enviado!', 'success')
  }

  const handleDeleteAccount = async () => {
    if (!confirmDelete) return
    
    setDeleting(true)
    try {
      const response = await fetch('/api/account/delete', {
        method: 'DELETE',
      })
      
      const result = await response.json()
      
      if (response.ok) {
        showToast('Conta excluida com sucesso. Redirecionando...', 'success')
        setTimeout(() => { window.location.href = '/' }, 2000)
      } else {
        throw new Error(result.error || 'Erro desconhecido')
      }
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Erro desconhecido'
      console.error('Erro ao deletar conta:', err)
      showToast(`Falha ao excluir conta: ${errorMessage}`, 'error')
    } finally {
      setDeleting(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-surface-50 dark:bg-surface-950">
        <Loader2 className="w-10 h-10 animate-spin text-primary-500" />
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto p-3 sm:p-4 md:p-8 mt-14 sm:mt-16 mb-16 relative">
      {/* Toast notification */}
      <AnimatePresence>
        {toast && (
          <motion.div
            initial={{ opacity: 0, y: -20, x: '-50%' }}
            animate={{ opacity: 1, y: 0, x: '-50%' }}
            exit={{ opacity: 0, y: -20, x: '-50%' }}
            className={`fixed top-4 sm:top-6 left-1/2 z-50 flex items-center gap-2 sm:gap-3 px-3 sm:px-5 py-2 sm:py-3 rounded-lg sm:rounded-xl shadow-lg border ${
              toast.type === 'success' ? 'bg-green-50 border-green-200 text-green-700' :
              toast.type === 'error' ? 'bg-red-50 border-red-200 text-red-700' :
              'bg-blue-50 border-blue-200 text-blue-700'
            }`}
          >
            {toast.type === 'success' && <Check className="w-4 h-4 sm:w-5 sm:h-5" />}
            {toast.type === 'error' && <AlertTriangle className="w-4 h-4 sm:w-5 sm:h-5" />}
            {toast.type === 'info' && <Info className="w-4 h-4 sm:w-5 sm:h-5" />}
            <span className="text-xs sm:text-sm font-medium">{toast.message}</span>
            <button onClick={() => setToast(null)} className="ml-1 sm:ml-2 opacity-70 hover:opacity-100">
              <X className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between m-6 sm:mb-10 gap-3 sm:gap-4">
        <div>
          <h1 className="text-2xl sm:text-4xl font-bold text-surface-900 dark:text-surface-50 font-display">Configurações</h1>
          <p className="text-surface-600 dark:text-surface-400 mt-1 sm:mt-2 text-sm sm:text-lg">Gerencie sua conta e preferências do DataMaster Pro.</p>
        </div>

      </div>

      <div className="grid lg:grid-cols-12 gap-4 sm:gap-8">
        {/* Sidebar Navigation */}
        <div className="lg:col-span-3">
          <div className="grid grid-cols-4 lg:grid-cols-1 gap-1.5 sm:gap-2">
            <button
              onClick={() => setActiveTab('perfil')}
              className={`flex flex-col items-center gap-1 sm:gap-2 p-2.5 sm:p-4 rounded-xl sm:rounded-2xl font-bold transition-all text-[10px] sm:text-base ${activeTab === 'perfil' ? 'bg-primary-500 text-white shadow-lg shadow-primary-500/25' : 'bg-white dark:bg-surface-900 text-surface-600 dark:text-surface-400 hover:bg-surface-50 dark:hover:bg-surface-800 border border-surface-100 dark:border-surface-800'}`}
            >
              <User className="w-4 h-4 sm:w-5 sm:h-5" /> 
              <span className="hidden sm:inline">Perfil Geral</span>
              <span className="sm:hidden">Perfil</span>
            </button>
            <button
              onClick={() => setActiveTab('seguranca')}
              className={`flex flex-col items-center gap-1 sm:gap-2 p-2.5 sm:p-4 rounded-xl sm:rounded-2xl font-bold transition-all text-[10px] sm:text-base ${activeTab === 'seguranca' ? 'bg-primary-500 text-white shadow-lg shadow-primary-500/25' : 'bg-white dark:bg-surface-900 text-surface-600 dark:text-surface-400 hover:bg-surface-50 dark:hover:bg-surface-800 border border-surface-100 dark:border-surface-800'}`}
            >
              <Shield className="w-4 h-4 sm:w-5 sm:h-5" /> 
              <span>Segurança</span>
            </button>
            <button
              onClick={() => setActiveTab('notificacoes')}
              className={`flex flex-col items-center gap-1 sm:gap-2 p-2.5 sm:p-4 rounded-xl sm:rounded-2xl font-bold transition-all text-[10px] sm:text-base ${activeTab === 'notificacoes' ? 'bg-primary-500 text-white shadow-lg shadow-primary-500/25' : 'bg-white dark:bg-surface-900 text-surface-600 dark:text-surface-400 hover:bg-surface-50 dark:hover:bg-surface-800 border border-surface-100 dark:border-surface-800'}`}
            >
              <Bell className="w-4 h-4 sm:w-5 sm:h-5" /> 
              <span className="hidden sm:inline">Notificações</span>
              <span className="sm:hidden">Alertas</span>
            </button>
            <button
              onClick={() => setActiveTab('privacidade')}
              className={`flex flex-col items-center gap-1 sm:gap-2 p-2.5 sm:p-4 rounded-xl sm:rounded-2xl font-bold transition-all text-[10px] sm:text-base ${activeTab === 'privacidade' ? 'bg-primary-500 text-white shadow-lg shadow-primary-500/25' : 'bg-white dark:bg-surface-900 text-surface-600 dark:text-surface-400 hover:bg-surface-50 dark:hover:bg-surface-800 border border-surface-100 dark:border-surface-800'}`}
            >
              <Shield className="w-4 h-4 sm:w-5 sm:h-5" /> 
              <span>Privacidade</span>
            </button>
          </div>
        </div>

        {/* Content Area */}
        <div className="lg:col-span-9 space-y-4 sm:space-y-6">
          {activeTab === 'perfil' && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-4 sm:space-y-6">
              <div className="bg-white dark:bg-surface-900 rounded-2xl sm:rounded-[2.5rem] p-5 sm:p-8 shadow-xl shadow-surface-200/50 dark:shadow-none border border-surface-100 dark:border-surface-800">
                <h2 className="text-lg sm:text-2xl font-bold text-surface-900 dark:text-surface-50 mb-5 sm:mb-8 border-b border-surface-50 dark:border-surface-800 pb-3 sm:pb-4 font-display">Informações Pessoais</h2>
                <div className="space-y-4 sm:space-y-6">
                  <div className="grid md:grid-cols-2 gap-4 sm:gap-6">
                    <div>
                      <label className="block text-xs sm:text-sm font-bold text-surface-700 dark:text-surface-300 mb-1.5 sm:mb-2">Nome </label>
                      <input
                        type="text"
                        value={formData.nome}
                        onChange={(e) => setFormData({ ...formData, nome: e.target.value })}
                        className="w-full px-3.5 sm:px-5 py-3 sm:py-4 rounded-xl sm:rounded-2xl border border-surface-200 dark:border-surface-700 focus:outline-none focus:ring-2 focus:ring-primary-500 transition-all bg-surface-50/50 dark:bg-surface-800 dark:text-surface-50 text-sm sm:text-base"
                        maxLength={100}
                        minLength={2}
                      />
                    </div>
                    <div>
                      <label className="block text-xs sm:text-sm font-bold text-surface-700 dark:text-surface-300 mb-1.5 sm:mb-2">Email de Login</label>
                      <div className="relative">
                        <input
                          type="email"
                          value={formData.email}
                          disabled
                          className="w-full px-3.5 sm:px-5 py-3 sm:py-4 rounded-xl sm:rounded-2xl border border-surface-200 dark:border-surface-700 bg-surface-100 dark:bg-surface-800 text-surface-500 dark:text-surface-400 cursor-not-allowed pr-10 sm:pr-12 text-sm sm:text-base"
                        />
                        <Lock className="absolute right-3 sm:right-4 top-1/2 -translate-y-1/2 w-4 h-4 sm:w-5 sm:h-5 text-surface-400" />
                      </div>
                    </div>
                  </div>
                  <div>
                    <label className="block text-xs sm:text-sm font-bold text-surface-700 dark:text-surface-300 mb-1.5 sm:mb-2">Organização / Empresa (Opcional)</label>
                    <input
                      type="text"
                      placeholder="Nome da sua empresa"
                      value={formData.empresa}
                      onChange={(e) => setFormData({ ...formData, empresa: e.target.value })}
                      className="w-full px-3.5 sm:px-5 py-3 sm:py-4 rounded-xl sm:rounded-2xl border border-surface-200 dark:border-surface-700 focus:outline-none focus:ring-2 focus:ring-primary-500 transition-all dark:bg-surface-800 dark:text-surface-50 text-sm sm:text-base"
                      maxLength={100}
                    />
                  </div>
                </div>
              </div>

              <div className="bg-white dark:bg-surface-900 rounded-2xl sm:rounded-[2.5rem] p-5 sm:p-8 shadow-xl shadow-surface-200/50 dark:shadow-none border border-surface-100 dark:border-surface-800">
                <h2 className="text-lg sm:text-2xl font-bold text-surface-900 dark:text-surface-50 mb-1 sm:mb-2 font-display">Aparência Padrão do Desktop</h2>
                <p className="text-surface-500 dark:text-surface-400 text-xs sm:text-sm mb-5 sm:mb-8">Escolha como o software deve se comportar visualmente.</p>
                <div className="grid grid-cols-3 gap-2.5 sm:gap-4 max-w-2xl">
                  {[
                    { id: 'light', icon: Sun, label: 'Claro' },
                    { id: 'dark', icon: Moon, label: 'Escuro' },
                    { id: 'system', icon: Monitor, label: 'Sistema' }
                  ].map((t) => (
                    <button
                      key={t.id}
                      onClick={() => { setFormData({ ...formData, tema: t.id }); updateTheme(t.id); }}
                      className={`p-4 sm:p-6 rounded-2xl sm:rounded-3xl border-2 flex flex-col items-center gap-2.5 sm:gap-4 transition-all ${formData.tema === t.id ? 'border-primary-500 bg-primary-50 dark:bg-primary-500/10 text-primary-700 dark:text-primary-400' : 'border-surface-100 dark:border-surface-800 text-surface-500 dark:text-surface-400 hover:border-surface-200 dark:hover:border-surface-700 bg-surface-50/30 dark:bg-surface-800/50'}`}
                    >
                      <t.icon className="w-6 h-6 sm:w-8 sm:h-8" />
                      <span className="font-bold text-xs sm:text-base">{t.label}</span>
                    </button>
                  ))}
                </div>
              </div>
            </motion.div>
          )}

          {activeTab === 'seguranca' && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="bg-white rounded-2xl sm:rounded-[2.5rem] p-5 sm:p-8 shadow-xl shadow-surface-200/50 border border-surface-100">
              <h2 className="text-lg sm:text-2xl font-bold text-surface-900 mb-5 sm:mb-8 border-b border-surface-50 pb-3 sm:pb-4 font-display">Segurança da Conta</h2>
              <div className="space-y-5 sm:space-y-8">
                <div className="flex items-start gap-3 sm:gap-4 p-4 sm:p-6 rounded-2xl sm:rounded-3xl bg-surface-50 border border-surface-100">
                  <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-xl sm:rounded-2xl bg-white border border-surface-200 flex items-center justify-center flex-shrink-0">
                    <Mail className="w-5 h-5 sm:w-6 sm:h-6 text-primary-600" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-bold text-surface-900 text-sm sm:text-base">Redefinir Senha</h3>
                    <p className="text-xs sm:text-sm text-surface-500 mt-0.5 sm:mt-1">Enviaremos um link de recuperação para o email: <strong>{formData.email}</strong></p>
                    <button
                      onClick={handleResetPassword}
                      className="mt-3 sm:mt-4 px-4 sm:px-6 py-2 sm:py-2.5 rounded-lg sm:rounded-xl bg-white border border-surface-200 hover:bg-surface-50 text-surface-700 font-bold transition-all text-xs sm:text-sm"
                    >
                      Enviar Email de Recuperação
                    </button>
                  </div>
                </div>

                <div className="flex items-start gap-3 sm:gap-4 p-4 sm:p-6 rounded-2xl sm:rounded-3xl bg-surface-50 border border-surface-100">
                  <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-xl sm:rounded-2xl bg-white border border-surface-200 flex items-center justify-center flex-shrink-0">
                    <Shield className="w-5 h-5 sm:w-6 sm:h-6 text-primary-600" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-bold text-surface-900 text-sm sm:text-base">Autenticação em Duas Etapas</h3>
                    <p className="text-xs sm:text-sm text-surface-500 mt-0.5 sm:mt-1">Em breve disponível. O Supabase já suporta 2FA nativo.</p>
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {activeTab === 'notificacoes' && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="bg-white rounded-2xl sm:rounded-[2.5rem] p-5 sm:p-8 shadow-xl shadow-surface-200/50 border border-surface-100">
              <h2 className="text-lg sm:text-2xl font-bold text-surface-900 mb-5 sm:mb-8 border-b border-surface-50 pb-3 sm:pb-4 font-display">Notificações</h2>
              <div className="space-y-3 sm:space-y-4">
                {[
                  { id: 'notificacoes_email', title: 'Alertas por Email', desc: 'Receba relatórios mensais e avisos de limite no seu email.' },
                  { id: 'notificacoes_desktop', title: 'Notificações Desktop', desc: 'Alertas em tempo real direto no seu computador ao finalizar tarefas.' }
                ].map((n) => (
                  <div key={n.id} className="flex items-center justify-between p-4 sm:p-6 rounded-2xl sm:rounded-3xl bg-surface-50 border border-surface-100 gap-3">
                    <div className="flex-1 min-w-0">
                      <h3 className="font-bold text-surface-900 text-sm sm:text-base">{n.title}</h3>
                      <p className="text-xs sm:text-sm text-surface-500 mt-0.5">{n.desc}</p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer flex-shrink-0">
                      <input
                        type="checkbox"
                        checked={(formData as any)[n.id]}
                        onChange={(e) => setFormData({ ...formData, [n.id]: e.target.checked })}
                        className="sr-only peer"
                      />
                      <div className="w-11 sm:w-14 h-6 sm:h-8 bg-surface-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[3px] sm:after:top-[4px] after:left-[3px] sm:after:left-[4px] after:bg-white after:border-surface-300 after:border after:rounded-full after:h-5 after:w-5 sm:after:h-6 sm:after:w-6 after:transition-all peer-checked:bg-primary-500"></div>
                    </label>
                  </div>
                ))}
              </div>
            </motion.div>
          )}
          {activeTab === 'privacidade' && (
            <motion.div 
              initial={{ opacity: 0, y: 10 }} 
              animate={{ opacity: 1, y: 0 }} 
              className="bg-white dark:bg-surface-900 rounded-2xl sm:rounded-[2.5rem] p-5 sm:p-8 shadow-xl shadow-surface-200/50 dark:shadow-none border border-surface-100 dark:border-surface-800 space-y-5 sm:space-y-8"
            >
              <div>
                <h2 className="text-lg sm:text-2xl font-bold text-surface-900 dark:text-surface-50 border-b border-surface-50 dark:border-surface-800 pb-3 sm:pb-4 font-display">Privacidade e Direitos (LGPD)</h2>
                <p className="text-xs sm:text-sm text-surface-500 mt-1.5 sm:mt-2">
                  Em conformidade com a Lei Geral de Proteção de Dados (LGPD - Lei nº 13.709/2018), garantimos o controle total dos seus dados pessoais.
                </p>
              </div>

              <div className="flex items-start gap-3 sm:gap-4 p-4 sm:p-6 rounded-2xl sm:rounded-3xl bg-red-50 dark:bg-red-950/20 border border-red-100 dark:border-red-900/30 text-red-700 dark:text-red-300">
                <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-xl sm:rounded-2xl bg-white dark:bg-surface-800 border border-red-200 dark:border-red-900 flex items-center justify-center flex-shrink-0">
                  <Trash2 className="w-5 h-5 sm:w-6 sm:h-6 text-red-600 dark:text-red-400" />
                </div>
                <div className="flex-1">
                  <h3 className="font-bold text-red-900 dark:text-red-400 text-sm sm:text-base">Exclusão de Conta e Dados Pessoais</h3>
                  <p className="text-xs sm:text-sm mt-1 text-red-700 dark:text-red-300">
                    Ao confirmar a exclusão, todos os seus dados pessoais, históricos de execução, preferências de temas, tarefas agendadas e registros de ROI serão **excluídos de forma definitiva e permanente** de nossos bancos de dados e servidores, sem possibilidade de recuperação.
                  </p>
                  
                  <div className="mt-3 sm:mt-4 flex items-center gap-2">
                    <input 
                      type="checkbox" 
                      id="confirm-delete-checkbox"
                      checked={confirmDelete}
                      onChange={(e) => setConfirmDelete(e.target.checked)}
                      className="rounded border-red-300 text-red-600 focus:ring-red-500 h-3.5 w-3.5 sm:h-4 sm:w-4"
                    />
                    <label htmlFor="confirm-delete-checkbox" className="text-[10px] sm:text-xs font-medium text-red-800 dark:text-red-400 cursor-pointer select-none">
                      Estou ciente de que esta ação é permanente e irreversível.
                    </label>
                  </div>

                  <button
                    onClick={handleDeleteAccount}
                    disabled={!confirmDelete || deleting}
                    className={`mt-3 sm:mt-4 px-4 sm:px-6 py-2.5 sm:py-3 rounded-lg sm:rounded-xl font-bold transition-all text-xs sm:text-sm flex items-center gap-2 shadow-lg ${
                      confirmDelete && !deleting 
                        ? 'bg-red-600 text-white hover:bg-red-700 shadow-red-500/20 active:scale-95' 
                        : 'bg-surface-200 dark:bg-surface-800 text-surface-400 dark:text-surface-600 cursor-not-allowed'
                    }`}
                  >
                    {deleting ? (
                      <>
                        <Loader2 className="w-3.5 h-3.5 sm:w-4 sm:h-4 animate-spin" /> Excluindo...
                      </>
                    ) : (
                      <>
                        <Trash2 className="w-3.5 h-3.5 sm:w-4 sm:h-4" /> Confirmar Exclusão de Conta
                      </>
                    )}
                  </button>
                </div>
              </div>
            </motion.div>
          )}

          {/* Save Button Bar (Fixed at bottom or after content) */}
          {(activeTab === 'perfil' || activeTab === 'notificacoes') && (
            <div className="flex justify-end pt-4 sm:pt-6">
              <button
                onClick={handleSave}
                disabled={saving}
                className="btn-primary relative overflow-hidden group px-6 sm:px-12 py-3 sm:py-4 text-sm sm:text-lg rounded-xl sm:rounded-2xl shadow-xl shadow-primary-500/25 min-w-[200px] sm:min-w-[260px]"
              >
                {saving ? (
                  <Loader2 className="w-5 h-5 sm:w-6 sm:h-6 animate-spin mx-auto" />
                ) : (
                  <>
                    <span className={`flex items-center justify-center gap-2 transition-all duration-500 ${saved ? '-translate-y-16 opacity-0' : 'translate-y-0 opacity-100'}`}>
                      Salvar Alterações
                    </span>
                    <span className={`absolute inset-0 flex items-center justify-center text-white bg-green-600 transition-all duration-500 ${saved ? 'translate-y-0 opacity-100' : 'translate-y-16 opacity-0'}`}>
                      <Check className="w-5 h-5 sm:w-6 sm:h-6 mr-2" /> Salvo!
                    </span>
                  </>
                )}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
