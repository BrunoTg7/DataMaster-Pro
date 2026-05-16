'use client'

import { createContext, useContext, ReactNode } from 'react'
import { useTheme } from './useTheme'

const ThemeContext = createContext<{
  theme: string
  updateTheme: (theme: string) => Promise<void>
  loading: boolean
} | null>(null)

export function useThemeContext() {
  const context = useContext(ThemeContext)
  if (!context) {
    throw new Error('useThemeContext must be used within ThemeProvider')
  }
  return context
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  console.log('[ThemeProvider] Renderizando...')
  const themeValues = useTheme()
  console.log('[ThemeProvider] Theme values:', themeValues)
  
  return (
    <ThemeContext.Provider value={themeValues}>
      {children}
    </ThemeContext.Provider>
  )
}