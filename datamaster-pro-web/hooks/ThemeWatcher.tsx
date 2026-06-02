'use client'

import { useEffect } from 'react'
import { useThemeContext } from './ThemeProvider'

export function ThemeWatcher() {
  const { theme } = useThemeContext()

  useEffect(() => {
    const root = window.document.documentElement
    root.classList.remove('light', 'dark')

    if (theme === 'system') {
      const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
      root.classList.add(systemTheme)
    } else {
      root.classList.add(theme)
    }
  }, [theme])

  return null
}
