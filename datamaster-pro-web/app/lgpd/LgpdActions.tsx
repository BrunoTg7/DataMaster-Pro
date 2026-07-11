'use client'

import { useEffect, useState } from 'react'
import { supabase } from '@/lib/supabase/client'
import { Download, Trash2, Loader2, Key } from 'lucide-react'
import Link from 'next/link'

export function LgpdActions() {
  const [user, setUser] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null)
      setLoading(false)
    }).catch(() => {
      setLoading(false)
    })
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center p-6 bg-surface-50 dark:bg-surface-900/50 rounded-2xl border border-surface-100 dark:border-surface-800">
        <Loader2 className="w-6 h-6 animate-spin text-primary-500" />
      </div>
    )
  }

  if (!user) {
    return (
      <div className="p-6 bg-surface-50 dark:bg-surface-900/50 rounded-2xl border border-surface-100 dark:border-surface-800 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div>
          <h3 className="font-bold text-surface-900 dark:text-white text-sm">Painel de Direitos do Titular</h3>
          <p className="text-xs text-surface-500 dark:text-surface-400 mt-1">Faça login para baixar seus dados ou solicitar a exclusão de sua conta.</p>
        </div>
        <Link 
          href="/auth/login" 
          className="btn-primary flex items-center gap-2 text-xs py-2.5 px-4"
        >
          <Key className="w-4 h-4" /> Entrar na Minha Conta
        </Link>
      </div>
    )
  }

  return (
    <div className="p-6 bg-surface-50 dark:bg-surface-900/50 rounded-2xl border border-surface-100 dark:border-surface-800 space-y-4">
      <div>
        <h3 className="font-bold text-surface-900 dark:text-white text-sm">Painel de Direitos do Titular</h3>
        <p className="text-xs text-surface-500 dark:text-surface-400 mt-1">
          Conectado como: <strong className="text-surface-700 dark:text-surface-300">{user.email}</strong>
        </p>
      </div>
      <div className="flex flex-col sm:flex-row gap-3">
        <a 
          href="/api/account/export"
          download
          className="flex-1 flex items-center justify-center gap-2 p-3 bg-white dark:bg-surface-850 border border-surface-200 dark:border-surface-700 hover:bg-surface-50 dark:hover:bg-surface-800 text-surface-700 dark:text-surface-200 rounded-xl font-semibold transition-all text-xs"
        >
          <Download className="w-4 h-4 text-primary-500" /> Baixar Meus Dados (JSON)
        </a>
        <Link 
          href="/dashboard/configuracoes"
          className="flex-1 flex items-center justify-center gap-2 p-3 bg-red-50 dark:bg-red-950/20 border border-red-100 dark:border-red-900/30 hover:bg-red-100/50 dark:hover:bg-red-950/40 text-red-600 dark:text-red-400 rounded-xl font-semibold transition-all text-xs"
        >
          <Trash2 className="w-4 h-4 text-red-500" /> Solicitar Exclusão da Conta
        </Link>
      </div>
    </div>
  )
}
