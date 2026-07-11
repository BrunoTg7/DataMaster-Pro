'use client'

import { AlertTriangle } from 'lucide-react'
import Link from 'next/link'

export default function PlanosError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <div className="min-h-screen bg-surface-50 flex items-center justify-center px-4">
      <div className="text-center max-w-md">
        <div className="w-16 h-16 bg-red-50 rounded-2xl flex items-center justify-center mx-auto mb-6 border border-red-100">
          <AlertTriangle className="w-8 h-8 text-red-500" />
        </div>
        <h1 className="text-2xl font-bold text-surface-900 mb-2">
          Erro ao carregar planos
        </h1>
        <p className="text-surface-600 mb-8">
          Ocorreu um erro ao carregar informacoes dos planos. Por favor, tente novamente.
        </p>
        <div className="flex gap-4 justify-center">
          <button onClick={reset} className="btn-primary">
            Tentar novamente
          </button>
          <Link href="/" className="px-6 py-3 rounded-xl border border-surface-200 text-surface-700 hover:bg-surface-50 transition-colors font-medium">
            Voltar ao Inicio
          </Link>
        </div>
      </div>
    </div>
  )
}
