'use client'

import { useEffect, useState } from 'react'
import { supabase } from '@/lib/supabase/client'

export function ThemeInitializer() {
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
    console.log('[ThemeInitializer] Inicializando...')

    async function initTheme() {
      const { data: { session } } = await supabase.auth.getSession()
      console.log('[ThemeInitializer] Session:', session?.user?.id)

      if (session?.user) {
        const { data: profile } = await supabase
          .from('usuarios')
          .select('preferencias_tema')
          .eq('id', session.user.id)
          .single()

        const theme = profile?.preferencias_tema || 'system'
        console.log('[ThemeInitializer] Tema do DB:', theme)
        applyTheme(theme)
      } else {
        console.log('[ThemeInitializer] Sem session, usando light')
        applyTheme('light')
      }
    }

    const applyTheme = (themeName: string) => {
      console.log('[ThemeInitializer] Aplicando:', themeName)
      const root = window.document.documentElement
      root.classList.remove('light', 'dark')

      if (themeName === 'system') {
        const systemTheme = window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark'
        console.log('[ThemeInitializer] System detected:', systemTheme)
        root.classList.add(systemTheme)
      } else {
        root.classList.add(themeName)
      }
      console.log('[ThemeInitializer] Classes finais:', root.className)
    }


    initTheme()
  }, [])

  if (!mounted) {
    return null
  }

  return null
}