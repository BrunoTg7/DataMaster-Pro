'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Loader2 } from 'lucide-react'
import { supabase } from '@/lib/supabase/client'

export function ResetPasswordForm() {
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const { error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${window.location.origin}/auth/update-password`,
      })
      
      if (error) throw error
      
      setSuccess(true)
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Erro ao solicitar redefinição de senha'
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-surface-50 flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        <div className="text-center mb-8 mt-12">
          <h1 className="text-2xl font-bold text-surface-900">
            Redefinir Senha
          </h1>
          <p className="text-surface-600 mt-2">
            Digite seu email e enviaremos um link para você redefinir sua senha
          </p>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-surface-200 p-6">
          {success ? (
            <div className="text-center space-y-4">
              <div className="p-3 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm">
                Verifique sua caixa de entrada! Enviamos um link de recuperação para o seu email.
              </div>
              <Link href="/auth/login" className="btn-primary w-full inline-block mt-4">
                Voltar para o Login
              </Link>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
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

              {error && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={loading || !email}
                className="btn-primary w-full"
              >
                {loading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  'Enviar link de recuperação'
                )}
              </button>
            </form>
          )}

          <div className="mt-6 text-center">
            <p className="text-surface-600 text-sm">
              Lembrou sua senha?{' '}
              <Link href="/auth/login" className="text-primary-600 font-semibold hover:underline">
                Voltar para o Login
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
