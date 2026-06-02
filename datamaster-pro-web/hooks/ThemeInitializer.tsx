'use client'

import { useEffect, useState } from 'react'
import { supabase } from '@/lib/supabase/client'

export function ThemeInitializer() {
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)

    async function initTheme() {
      const { data: { session }, error: sessionError } = await supabase.auth.getSession()

      if (sessionError || !session?.user) {
        applyTheme('light')
        return
      }

      const { data: profile } = await supabase
        .from('usuarios')
        .select('preferencias_tema')
        .eq('id', session.user.id)
        .single()

      const theme = profile?.preferencias_tema || 'system'
      applyTheme(theme)
    }

    const applyTheme = (themeName: string) => {
      const root = window.document.documentElement
      root.classList.remove('light', 'dark')

      if (themeName === 'system') {
        const systemTheme = window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark'
        root.classList.add(systemTheme)
      } else {
        root.classList.add(themeName)
      }
    }

    initTheme()
  }, [])

  if (!mounted) {
    return null
  }

  return null
}
