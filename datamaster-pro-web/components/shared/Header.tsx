'use client'

import { supabase } from '@/lib/supabase/client'
import { User } from '@supabase/supabase-js'
import { LayoutDashboard, LogOut, Menu, X } from 'lucide-react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { memo, useEffect, useState } from 'react'

const navLinks = [
  { href: '/', label: 'Home' },
  { href: '/planos', label: 'Planos' },
  { href: '/downloads', label: 'Downloads' },
]

function HeaderComponent() {
  const pathname = usePathname()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let mounted = true
    
    supabase.auth.getSession().then(({ data: { session }, error }) => {
      if (mounted) {
        if (error) {
          console.warn('Session error:', error.message)
          setUser(null)
        } else {
          setUser(session?.user ?? null)
        }
        setLoading(false)
      }
    }).catch(() => {
      if (mounted) {
        setUser(null)
        setLoading(false)
      }
    })

    const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
      if (mounted) {
        if (event === 'SIGNED_OUT' || event === 'TOKEN_REFRESHED') {
          setUser(session?.user ?? null)
        } else {
          setUser(session?.user ?? null)
        }
        setLoading(false)
      }
    })

    return () => {
      mounted = false
      subscription.unsubscribe()
    }
  }, [])

  const handleLogout = async () => {
    await supabase.auth.signOut()
    window.location.href = '/'
  }

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-xl border-b border-surface-200/50">
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

          <nav className="hidden md:flex items-center gap-8">
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
                      title="Sair"
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
                    <button
                      onClick={handleLogout}
                      className="px-4 py-2 text-left text-red-600 font-medium flex items-center gap-2"
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