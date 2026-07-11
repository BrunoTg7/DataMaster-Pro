'use client'

import { AlertTriangle } from 'lucide-react'
import Link from 'next/link'

export default function ConfiguracoesError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <div className="min-h-screen bg-surface-50 dark:bg-surface-950 flex items-center justify-center px-4">
      <div className="text-center max-w-md">
        <div className="w-16 h-16 bg-red-50 dark:bg-red-950/30 rounded-2xl flex items-center justify-center mx-auto mb-6 border border-red-100 dark:border-red-900/50">
          <AlertTriangle className="w-8 h-8 text-red-500" />
        </div>
        <h1 className="text-2xl font-bold text-surface-900 dark:text-surface-50 mb-2">
          Erro nas Configuracoes
        </h1>
        <p className="text-surface-600 dark:text-surface-400 mb-8">
          Ocorreu um erro ao carregar suas configuracoes. Por favor, tente novamente.
        </p>
        <div className="flex gap-4 justify-center">
          <button onClick={reset} className="btn-primary">
            Tentar novamente
          </button>
          <Link href="/dashboard" className="px-6 py-3 rounded-xl border border-surface-200 dark:border-surface-700 text-surface-700 dark:text-surface-300 hover:bg-surface-50 dark:hover:bg-surface-800 transition-colors font-medium">
            Voltar ao Dashboard
          </Link>
        </div>
      </div>
    </div>
  )
}
