'use client'

import { useEffect, useState } from 'react'
import { supabase } from '@/lib/supabase/client'

export function useTheme() {
  const [theme, setTheme] = useState<string>('system')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function loadTheme() {
      const { data: { session }, error: sessionError } = await supabase.auth.getSession()
      
      if (sessionError || !session?.user) {
        applyTheme('system')
        setLoading(false)
        return
      }

      const { data: profile } = await supabase
        .from('usuarios')
        .select('preferencias_tema')
        .eq('id', session.user.id)
        .single()
      
      if (profile?.preferencias_tema) {
        setTheme(profile.preferencias_tema)
        applyTheme(profile.preferencias_tema)
      } else {
        applyTheme('system')
      }
      setLoading(false)
    }

    loadTheme()
  }, [])

  const applyTheme = (themeName: string) => {
    const root = window.document.documentElement
    root.classList.remove('light', 'dark')

    if (themeName === 'system') {
      const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
      root.classList.add(systemTheme)
    } else {
      root.classList.add(themeName)
    }
  }

  const updateTheme = async (newTheme: string) => {
    setTheme(newTheme)
    applyTheme(newTheme)
    
    const { data: { session }, error: sessionError } = await supabase.auth.getSession()
    if (sessionError || !session?.user) return

    await supabase
      .from('usuarios')
      .update({ preferencias_tema: newTheme, updated_at: new Date().toISOString() })
      .eq('id', session.user.id)
  }

  return { theme, updateTheme, loading }
}
