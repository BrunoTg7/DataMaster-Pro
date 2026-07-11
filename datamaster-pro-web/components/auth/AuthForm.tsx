'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { Eye, EyeOff, Loader2 } from 'lucide-react'
import { supabase } from '@/lib/supabase/client'
import { ConsentCheckbox } from '@/components/shared/ConsentCheckbox'

interface AuthFormProps {
  mode: 'login' | 'register'
}

export function AuthForm({ mode }: AuthFormProps) {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [consentChecked, setConsentChecked] = useState(false)
  const [consentError, setConsentError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      if (mode === 'register') {
        if (!consentChecked) {
          setConsentError('Voce precisa aceitar os Termos de Uso e a Politica de Privacidade para criar sua conta.')
          setLoading(false)
          return
        }
        setConsentError(null)
        const passwordError = validatePassword(password)
        if (passwordError) {
          setError(passwordError)
          setLoading(false)
          return
        }
      }

      // Sanitizar inputs
      const emailSanitizado = email.trim().toLowerCase()
      const nomeSanitizado = name.trim().slice(0, 100)

      if (mode === 'login') {
        const { error } = await supabase.auth.signInWithPassword({
          email: emailSanitizado,
          password,
        })
        if (error) throw error
        router.push('/dashboard')
      } else {
        const { data, error } = await supabase.auth.signUp({
          email: emailSanitizado,
          password,
          options: {
            data: {
              nome: nomeSanitizado,
            },
          },
        })
        if (error) throw error

        // Manually ensure user profile exists in 'usuarios' table
        if (data.user) {
          await supabase.from('usuarios').upsert({
            id: data.user.id,
            email: data.user.email!,
            nome: nomeSanitizado,
            plano_tipo: 'gratis'
          })
        }

        router.push('/dashboard')
      }
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Erro desconhecido'
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const handleGoogleLogin = async () => {
    setLoading(true)
    setError(null)
    try {
      const { error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: `${window.location.origin}/auth/callback`,
        },
      })
      if (error) throw error
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Erro ao autenticar com Google'
      setError(errorMessage)
      setLoading(false)
    }
  }

  const validatePassword = (pwd: string): string | null => {
    if (pwd.length < 8) return 'Senha deve ter pelo menos 8 caracteres'
    if (!/[A-Z]/.test(pwd)) return 'Senha deve conter pelo menos 1 letra maiúscula'
    if (!/[a-z]/.test(pwd)) return 'Senha deve conter pelo menos 1 letra minúscula'
    if (!/[0-9]/.test(pwd)) return 'Senha deve conter pelo menos 1 número'
    return null
  }

  const isLogin = mode === 'login'

  return (
    <div className="min-h-screen bg-surface-50 flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        <div className="text-center mb-8 mt-12">

          <h1 className="text-2xl font-bold text-surface-900">
            {isLogin ? 'Bem-vindo de volta' : 'Criar sua conta'}
          </h1>
          <p className="text-surface-600 mt-2">
            {isLogin
              ? 'Entre com seu email e senha para continuar'
              : 'Comece gratuitamente a usar todas as ferramentas'}
          </p>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-surface-200 p-6">
          <div className="space-y-4">
            <button
              type="button"
              onClick={handleGoogleLogin}
              disabled={loading}
              className="w-full flex items-center justify-center gap-3 px-4 py-3 border border-surface-300 rounded-lg hover:bg-surface-50 transition-colors disabled:opacity-50"
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24">
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4"/>
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
              </svg>
              Continuar com Google
            </button>

            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-surface-200" />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white text-surface-500">ou</span>
              </div>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {!isLogin && (
              <div>
                <label className="block text-sm font-medium text-surface-700 mb-1">
                  Nome completo
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="input-field"
                  placeholder="Seu nome"
                  required={!isLogin}
                  maxLength={100}
                  minLength={2}
                />
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-surface-700 mb-1">
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input-field"
                placeholder="seu@email.com"
                required
                autoComplete="email"
                maxLength={254}
              />
            </div>

            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="block text-sm font-medium text-surface-700">
                  Senha
                </label>
                {isLogin && (
                  <Link href="/auth/reset-password" className="text-xs font-medium text-primary-600 hover:text-primary-700 hover:underline">
                    Esqueceu a senha?
                  </Link>
                )}
              </div>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="input-field pr-10"
                  placeholder="••••••••"
                  required
                  minLength={8}
                  maxLength={128}
                  autoComplete={isLogin ? "current-password" : "new-password"}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-surface-400 hover:text-surface-600"
                  aria-label={showPassword ? "Ocultar senha" : "Mostrar senha"}
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            {error && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm" role="alert">
                {error}
              </div>
            )}

            {!isLogin && (
              <ConsentCheckbox
                onChange={setConsentChecked}
                error={consentError || undefined}
              />
            )}

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full"
            >
              {loading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : isLogin ? (
                'Entrar'
              ) : (
                'Criar conta'
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-surface-600 text-sm">
              {isLogin ? (
                <>
                  Não tem conta?{' '}
                  <Link href="/auth/registro" className="text-primary-600 font-semibold hover:underline">
                    Criar conta
                  </Link>
                </>
              ) : (
                <>
                  Já tem conta?{' '}
                  <Link href="/auth/login" className="text-primary-600 font-semibold hover:underline">
                    Entrar
                  </Link>
                </>
              )}
            </p>
          </div>
        </div>

        <p className="mt-6 text-center text-xs text-surface-500">
          Ao continuar, você aceita nossos{' '}
          <Link href="/termos" className="underline hover:text-surface-700">
            Termos de Uso
          </Link>{' '}
          e{' '}
          <Link href="/privacidade" className="underline hover:text-surface-700">
            Política de Privacidade
          </Link>
        </p>
      </div>
    </div>
  )
}