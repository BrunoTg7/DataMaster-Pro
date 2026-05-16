'use client'

import { useEffect } from 'react'
import { useThemeContext } from './ThemeProvider'

export function ThemeWatcher() {
  const { theme } = useThemeContext()

  useEffect(() => {
    console.log('[ThemeWatcher] Tema mudou para:', theme)
    const root = window.document.documentElement
    root.classList.remove('light', 'dark')

    if (theme === 'system') {
      const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
      console.log('[ThemeWatcher] System theme:', systemTheme)
      root.classList.add(systemTheme)
    } else {
      root.classList.add(theme)
    }
    console.log('[ThemeWatcher] Classes no root:', root.className)
  }, [theme])

  return null
}