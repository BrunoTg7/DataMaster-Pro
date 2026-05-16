"use client"

import { useState, useEffect } from 'react'
import { User, Bell, Shield, Check, Monitor, Moon, Sun, Lock, Loader2, Mail, Key } from 'lucide-react'
import Link from 'next/link'
import { supabase } from '@/lib/supabase/client'
import { useRouter } from 'next/navigation'
import { useThemeContext } from '@/hooks/ThemeProvider'

type Tab = 'perfil' | 'seguranca' | 'notificacoes'

export default function ConfiguracoesPage() {
  const router = useRouter()
  const { theme: currentTheme, updateTheme, loading: themeLoading } = useThemeContext()
  const [activeTab, setActiveTab] = useState<Tab>('perfil')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

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
      const { data: { session } } = await supabase.auth.getSession()
      if (!session) {
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
      const { data: { session } } = await supabase.auth.getSession()
      if (!session) return

      const { error } = await supabase
        .from('usuarios')
        .update({
          nome: formData.nome,
          empresa: formData.empresa,
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
      alert('Erro ao salvar as configurações.')
    } finally {
      setSaving(false)
    }
  }

  const handleResetPassword = async () => {
    const { error } = await supabase.auth.resetPasswordForEmail(formData.email, {
      redirectTo: `${window.location.origin}/auth/reset-password`,
    })
    if (error) alert(error.message)
    else alert('Email de redefinição de senha enviado!')
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-surface-50 dark:bg-surface-950">
        <Loader2 className="w-10 h-10 animate-spin text-primary-500" />
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto p-4 md:p-8 mt-16">
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between mb-10 gap-4">
        <div>
          <h1 className="text-4xl font-bold text-surface-900 dark:text-surface-50 font-display">Configurações</h1>
          <p className="text-surface-600 dark:text-surface-400 mt-2 text-lg">Gerencie sua conta e preferências do DataMaster Pro.</p>
        </div>

      </div>

      <div className="grid lg:grid-cols-12 gap-8">
        {/* Sidebar Navigation */}
        <div className="lg:col-span-3 space-y-2">
          <button
            onClick={() => setActiveTab('perfil')}
            className={`w-full flex items-center gap-3 p-4 rounded-2xl font-bold transition-all ${activeTab === 'perfil' ? 'bg-primary-500 text-white shadow-lg shadow-primary-500/25' : 'bg-white dark:bg-surface-900 text-surface-600 dark:text-surface-400 hover:bg-surface-50 dark:hover:bg-surface-800 border border-surface-100 dark:border-surface-800'}`}
          >
            <User className="w-5 h-5" /> Perfil Geral
          </button>
          <button
            onClick={() => setActiveTab('seguranca')}
            className={`w-full flex items-center gap-3 p-4 rounded-2xl font-bold transition-all ${activeTab === 'seguranca' ? 'bg-primary-500 text-white shadow-lg shadow-primary-500/25' : 'bg-white dark:bg-surface-900 text-surface-600 dark:text-surface-400 hover:bg-surface-50 dark:hover:bg-surface-800 border border-surface-100 dark:border-surface-800'}`}
          >
            <Shield className="w-5 h-5" /> Segurança
          </button>
          <button
            onClick={() => setActiveTab('notificacoes')}
            className={`w-full flex items-center gap-3 p-4 rounded-2xl font-bold transition-all ${activeTab === 'notificacoes' ? 'bg-primary-500 text-white shadow-lg shadow-primary-500/25' : 'bg-white dark:bg-surface-900 text-surface-600 dark:text-surface-400 hover:bg-surface-50 dark:hover:bg-surface-800 border border-surface-100 dark:border-surface-800'}`}
          >
            <Bell className="w-5 h-5" /> Notificações
          </button>
        </div>

        {/* Content Area */}
        <div className="lg:col-span-9 space-y-6">
          {activeTab === 'perfil' && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
              <div className="bg-white dark:bg-surface-900 rounded-[2.5rem] p-8 shadow-xl shadow-surface-200/50 dark:shadow-none border border-surface-100 dark:border-surface-800">
                <h2 className="text-2xl font-bold text-surface-900 dark:text-surface-50 mb-8 border-b border-surface-50 dark:border-surface-800 pb-4 font-display">Informações Pessoais</h2>
                <div className="space-y-6">
                  <div className="grid md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-bold text-surface-700 dark:text-surface-300 mb-2">Nome Completo</label>
                      <input
                        type="text"
                        value={formData.nome}
                        onChange={(e) => setFormData({ ...formData, nome: e.target.value })}
                        className="w-full px-5 py-4 rounded-2xl border border-surface-200 dark:border-surface-700 focus:outline-none focus:ring-2 focus:ring-primary-500 transition-all bg-surface-50/50 dark:bg-surface-800 dark:text-surface-50"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-bold text-surface-700 dark:text-surface-300 mb-2">Email de Login</label>
                      <div className="relative">
                        <input
                          type="email"
                          value={formData.email}
                          disabled
                          className="w-full px-5 py-4 rounded-2xl border border-surface-200 dark:border-surface-700 bg-surface-100 dark:bg-surface-800 text-surface-500 dark:text-surface-400 cursor-not-allowed pr-12"
                        />
                        <Lock className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 text-surface-400" />
                      </div>
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-bold text-surface-700 dark:text-surface-300 mb-2">Organização / Empresa (Opcional)</label>
                    <input
                      type="text"
                      placeholder="Nome da sua empresa"
                      value={formData.empresa}
                      onChange={(e) => setFormData({ ...formData, empresa: e.target.value })}
                      className="w-full px-5 py-4 rounded-2xl border border-surface-200 dark:border-surface-700 focus:outline-none focus:ring-2 focus:ring-primary-500 transition-all dark:bg-surface-800 dark:text-surface-50"
                    />
                  </div>
                </div>
              </div>

              <div className="bg-white dark:bg-surface-900 rounded-[2.5rem] p-8 shadow-xl shadow-surface-200/50 dark:shadow-none border border-surface-100 dark:border-surface-800">
                <h2 className="text-2xl font-bold text-surface-900 dark:text-surface-50 mb-2 font-display">Aparência Padrão do Desktop</h2>
                <p className="text-surface-500 dark:text-surface-400 text-sm mb-8">Escolha como o software deve se comportar visualmente.</p>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 max-w-2xl">
                  {[
                    { id: 'light', icon: Sun, label: 'Claro' },
                    { id: 'dark', icon: Moon, label: 'Escuro' },
                    { id: 'system', icon: Monitor, label: 'Sistema' }
                  ].map((t) => (
                    <button
                      key={t.id}
                      onClick={() => { console.log('[Config] Mudando tema para:', t.id); setFormData({ ...formData, tema: t.id }); updateTheme(t.id); }}
                      className={`p-6 rounded-3xl border-2 flex flex-col items-center gap-4 transition-all ${formData.tema === t.id ? 'border-primary-500 bg-primary-50 dark:bg-primary-500/10 text-primary-700 dark:text-primary-400' : 'border-surface-100 dark:border-surface-800 text-surface-500 dark:text-surface-400 hover:border-surface-200 dark:hover:border-surface-700 bg-surface-50/30 dark:bg-surface-800/50'}`}
                    >
                      <t.icon className="w-8 h-8" />
                      <span className="font-bold">{t.label}</span>
                    </button>
                  ))}
                </div>
              </div>
            </motion.div>
          )}

          {activeTab === 'seguranca' && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="bg-white rounded-[2.5rem] p-8 shadow-xl shadow-surface-200/50 border border-surface-100">
              <h2 className="text-2xl font-bold text-surface-900 mb-8 border-b border-surface-50 pb-4 font-display">Segurança da Conta</h2>
              <div className="space-y-8">
                <div className="flex items-start gap-4 p-6 rounded-3xl bg-surface-50 border border-surface-100">
                  <div className="w-12 h-12 rounded-2xl bg-white border border-surface-200 flex items-center justify-center flex-shrink-0">
                    <Mail className="w-6 h-6 text-primary-600" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-bold text-surface-900">Redefinir Senha</h3>
                    <p className="text-sm text-surface-500 mt-1">Enviaremos um link de recuperação para o email: <strong>{formData.email}</strong></p>
                    <button
                      onClick={handleResetPassword}
                      className="mt-4 px-6 py-2.5 rounded-xl bg-white border border-surface-200 hover:bg-surface-50 text-surface-700 font-bold transition-all text-sm"
                    >
                      Enviar Email de Recuperação
                    </button>
                  </div>
                </div>

                <div className="flex items-start gap-4 p-6 rounded-3xl bg-red-50 border border-red-100">
                  <div className="w-12 h-12 rounded-2xl bg-white border border-red-200 flex items-center justify-center flex-shrink-0">
                    <Shield className="w-6 h-6 text-red-600" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-bold text-red-900">Autenticação em Duas Etapas</h3>
                    <p className="text-sm text-red-600/80 mt-1">Adicione uma camada extra de segurança à sua conta DataMaster.</p>
                    <button className="mt-4 px-6 py-2.5 rounded-xl bg-red-600 text-white font-bold transition-all text-sm hover:bg-red-700">
                      Configurar 2FA
                    </button>
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {activeTab === 'notificacoes' && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="bg-white rounded-[2.5rem] p-8 shadow-xl shadow-surface-200/50 border border-surface-100">
              <h2 className="text-2xl font-bold text-surface-900 mb-8 border-b border-surface-50 pb-4 font-display">Notificações</h2>
              <div className="space-y-4">
                {[
                  { id: 'notificacoes_email', title: 'Alertas por Email', desc: 'Receba relatórios mensais e avisos de limite no seu email.' },
                  { id: 'notificacoes_desktop', title: 'Notificações Desktop', desc: 'Alertas em tempo real direto no seu computador ao finalizar tarefas.' }
                ].map((n) => (
                  <div key={n.id} className="flex items-center justify-between p-6 rounded-3xl bg-surface-50 border border-surface-100">
                    <div>
                      <h3 className="font-bold text-surface-900">{n.title}</h3>
                      <p className="text-sm text-surface-500 mt-0.5">{n.desc}</p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={(formData as any)[n.id]}
                        onChange={(e) => setFormData({ ...formData, [n.id]: e.target.checked })}
                        className="sr-only peer"
                      />
                      <div className="w-14 h-8 bg-surface-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[4px] after:left-[4px] after:bg-white after:border-surface-300 after:border after:rounded-full after:h-6 after:w-6 after:transition-all peer-checked:bg-primary-500"></div>
                    </label>
                  </div>
                ))}
              </div>
            </motion.div>
          )}

          {/* Save Button Bar (Fixed at bottom or after content) */}
          <div className="flex justify-end pt-6">
            <button
              onClick={handleSave}
              disabled={saving}
              className="btn-primary relative overflow-hidden group px-12 py-4 text-lg rounded-2xl shadow-xl shadow-primary-500/25 min-w-[260px]"
            >
              {saving ? (
                <Loader2 className="w-6 h-6 animate-spin mx-auto" />
              ) : (
                <>
                  <span className={`flex items-center justify-center gap-2 transition-all duration-500 ${saved ? '-translate-y-16 opacity-0' : 'translate-y-0 opacity-100'}`}>
                    Salvar Todas as Alterações
                  </span>
                  <span className={`absolute inset-0 flex items-center justify-center text-white bg-green-600 transition-all duration-500 ${saved ? 'translate-y-0 opacity-100' : 'translate-y-16 opacity-0'}`}>
                    <Check className="w-6 h-6 mr-2" /> Configurações Salvas!
                  </span >
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

// Helper para animações simples (opcional, se não tiver framer-motion instalado, remova o <motion.div>)
const motion = {
  div: ({ children, initial, animate, className }: any) => <div className={className}>{children}</div>
}
