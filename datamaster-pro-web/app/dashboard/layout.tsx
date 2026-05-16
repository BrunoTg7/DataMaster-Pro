'use client'

import { ThemeProvider } from '@/hooks/ThemeProvider'
import { ThemeWatcher } from '@/hooks/ThemeWatcher'
import { ReactNode } from 'react'

export default function DashboardLayout({
  children,
}: {
  children: ReactNode
}) {
  return (
    <ThemeProvider>
      <ThemeWatcher />
      {children}
    </ThemeProvider>
  )
}