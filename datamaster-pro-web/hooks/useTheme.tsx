'use client'

import { useEffect, useState } from 'react'
import { supabase } from '@/lib/supabase/client'

export function useTheme() {
  const [theme, setTheme] = useState<string>('system')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function loadTheme() {
      console.log('[Theme] Carregando tema...')
      const { data: { session } } = await supabase.auth.getSession()
      console.log('[Theme] Session:', session?.user?.id)
      
      if (session?.user) {
        const { data: profile, error } = await supabase
          .from('usuarios')
          .select('preferencias_tema')
          .eq('id', session.user.id)
          .single()
        
        console.log('[Theme] Profile:', profile, 'Error:', error)
        
        if (profile?.preferencias_tema) {
          setTheme(profile.preferencias_tema)
          applyTheme(profile.preferencias_tema)
        } else {
          applyTheme('system')
        }
      } else {
        applyTheme('system')
      }
      setLoading(false)
    }

    loadTheme()
  }, [])

  const applyTheme = (themeName: string) => {
    console.log('[Theme] Aplicando tema:', themeName)
    const root = window.document.documentElement
    root.classList.remove('light', 'dark')

    if (themeName === 'system') {
      const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
      console.log('[Theme] Sistema detected:', systemTheme)
      root.classList.add(systemTheme)
    } else {
      root.classList.add(themeName)
    }
    console.log('[Theme] Classes no HTML:', root.className)
  }

  const updateTheme = async (newTheme: string) => {
    console.log('[Theme] Atualizando para:', newTheme)
    setTheme(newTheme)
    applyTheme(newTheme)
    
    const { data: { session } } = await supabase.auth.getSession()
    if (session?.user) {
      console.log('[Theme] Salvando no Supabase...')
      const { error } = await supabase
        .from('usuarios')
        .update({ preferencias_tema: newTheme, updated_at: new Date().toISOString() })
        .eq('id', session.user.id)
      console.log('[Theme] Salvo, error:', error)
    }
  }

  return { theme, updateTheme, loading }
}