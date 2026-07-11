'use client'

import { supabase } from '@/lib/supabase/client'
import { useSession } from '@/lib/contexts/SessionContext'
import { LayoutDashboard, LogOut, Menu, X, Settings, CreditCard, Clock } from 'lucide-react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { memo, useState, useEffect } from 'react'

const navLinks = [
  { href: '/', label: 'Home' },
  { href: '/planos', label: 'Planos' },
  { href: '/downloads', label: 'Downloads' },
]

function HeaderComponent() {
  const pathname = usePathname()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const { user, loading } = useSession()
  const [profile, setProfile] = useState<{ plano_tipo: string; data_expiracao?: string; created_at?: string } | null>(null)

  const isDashboard = pathname === '/dashboard' || pathname.startsWith('/dashboard/')

  useEffect(() => {
    if (!user || !isDashboard) {
      setProfile(null)
      return
    }
    supabase.from('usuarios').select('plano_tipo, data_expiracao, created_at').eq('id', user.id).single()
      .then(({ data }) => {
        if (data) setProfile(data)
      })
  }, [user, isDashboard])

  const calculateRenewalDate = (createdAt?: string, dataExpiracao?: string) => {
    const planType = profile?.plano_tipo || 'gratis'
    if (planType !== 'gratis' && dataExpiracao) {
      return new Date(dataExpiracao)
    }
    if (!createdAt) return null
    const created = new Date(createdAt)
    const now = new Date()
    let renewal = new Date(now.getFullYear(), now.getMonth(), created.getDate())
    const lastDayOfMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate()
    if (created.getDate() > lastDayOfMonth) renewal.setDate(lastDayOfMonth)
    if (renewal <= now) {
      renewal = new Date(now.getFullYear(), now.getMonth() + 1, created.getDate())
      const nextMonthLastDay = new Date(now.getFullYear(), now.getMonth() + 2, 0).getDate()
      if (created.getDate() > nextMonthLastDay) renewal.setDate(nextMonthLastDay)
    }
    return renewal
  }

  const handleLogout = async () => {
    await supabase.auth.signOut()
    window.location.href = '/'
  }

  return (
    <header role="banner" className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-xl border-b border-surface-200/50">
      <div className="max-w-full mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 lg:h-20">
          <Link href="/" className="flex items-center gap-2 group">
            <img
              src="/favicon.ico"
              alt="DataMaster Pro"
              className="w-10 h-10 rounded-xl shadow-lg shadow-primary-500/20 group-hover:scale-105 transition-transform object-cover"
            />
            <span className="text-xl font-bold text-surface-900">
              DataMaster<span className="text-primary-600">Pro</span>
            </span>
          </Link>

          <nav aria-label="Menu principal" className="hidden md:flex items-center gap-8">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className={`text-sm font-medium transition-colors hover:text-primary-600 ${
                  pathname === link.href 
                    ? 'text-primary-600' 
                    : 'text-surface-600'
                }`}
              >
                {link.label}
              </Link>
            ))}
          </nav>

          <div className="hidden md:flex items-center gap-4">
            {!loading && (
              <>
                {user ? (
                  <>
                    <Link 
                      href="/dashboard"
                      className="btn-ghost flex items-center gap-2"
                    >
                      <LayoutDashboard className="w-4 h-4" />
                      Painel
                    </Link>
                    <button 
                      onClick={handleLogout}
                      className="text-surface-500 hover:text-red-600 transition-colors"
                      aria-label="Sair da conta"
                    >
                      <LogOut className="w-5 h-5" />
                    </button>
                  </>
                ) : (
                  <>
                    <Link 
                      href="/auth/login"
                      className="btn-ghost"
                    >
                      Entrar
                    </Link>
                    <Link 
                      href="/auth/registro"
                      className="btn-primary"
                    >
                      Começar Agora
                    </Link>
                  </>
                )}
              </>
            )}
          </div>

          <button
            className="md:hidden p-2 text-surface-600 hover:text-surface-900"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label={mobileMenuOpen ? "Fechar menu" : "Abrir menu"}
            aria-expanded={mobileMenuOpen}
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {mobileMenuOpen && (
        <div className="md:hidden bg-white border-t border-surface-200">
          <nav className="flex flex-col p-4 gap-2">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className={`px-4 py-2 rounded-lg font-medium ${
                  pathname === link.href 
                    ? 'bg-primary-50 text-primary-600' 
                    : 'text-surface-600 hover:bg-surface-100'
                }`}
                onClick={() => setMobileMenuOpen(false)}
              >
                {link.label}
              </Link>
            ))}
            <hr className="my-2 border-surface-200" />
            
            {!loading && (
              <>
                {user ? (
                  <>
                    <Link
                      href="/dashboard"
                      className="px-4 py-2 flex items-center gap-2 text-surface-600 font-medium"
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      <LayoutDashboard className="w-4 h-4" />
                      Meu Painel
                    </Link>
                    {pathname === '/dashboard' && (
                      <>
                        <Link
                          href="/dashboard/configuracoes"
                          className="px-4 py-2 flex items-center gap-2 text-surface-600 font-medium"
                          onClick={() => setMobileMenuOpen(false)}
                        >
                          <Settings className="w-4 h-4" />
                          Configurações
                        </Link>
                        <Link
                          href="/planos"
                          className="px-4 py-2 flex items-center gap-2 text-surface-600 font-medium"
                          onClick={() => setMobileMenuOpen(false)}
                        >
                          <CreditCard className="w-4 h-4" />
                          Plano e Faturas
                        </Link>
                        {(profile?.created_at || profile?.data_expiracao) && (
                          <div className="px-4 py-2 flex items-center gap-2 text-primary-700 font-medium bg-primary-50 rounded-lg mx-0">
                            <Clock className="w-4 h-4" />
                            <div className="flex flex-col">
                              <span className="text-[10px] uppercase tracking-wider font-bold text-primary-600">
                                {profile?.plano_tipo === 'gratis' ? 'Renovação do Limite' : 'Vencimento do Plano'}
                              </span>
                              <span className="text-sm font-bold">
                                {calculateRenewalDate(profile?.created_at, profile?.data_expiracao)?.toLocaleDateString('pt-BR')}
                              </span>
                            </div>
                          </div>
                        )}
                      </>
                    )}
                    <button
                      onClick={handleLogout}
                      className="px-4 py-2 text-left text-red-600 font-medium flex items-center gap-2"
                      aria-label="Sair da conta"
                    >
                      <LogOut className="w-4 h-4" />
                      Sair da conta
                    </button>
                  </>
                ) : (
                  <>
                    <Link
                      href="/auth/login"
                      className="px-4 py-2 text-center text-surface-600 font-medium"
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      Entrar
                    </Link>
                    <Link
                      href="/auth/registro"
                      className="px-4 py-2 text-center btn-primary"
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      Começar Agora
                    </Link>
                  </>
                )}
              </>
            )}
          </nav>
        </div>
      )}
    </header>
  )
}

export const Header = memo(HeaderComponent)