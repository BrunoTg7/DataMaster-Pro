'use client'

import { SessionProvider } from '@/lib/contexts/SessionContext'

export function ClientProviders({ children }: { children: React.ReactNode }) {
  return (
    <SessionProvider>
      {children}
    </SessionProvider>
  )
}
