'use client'

import { useSession } from '@/lib/contexts/SessionContext'
import Link from 'next/link'

// Links do Cakto para pagamento (configurar via env ou atualizar com URLs reais)
const CAKTO_CHECKOUT_URLS: Record<string, { monthly: string; annual: string }> = {
  pro: {
    monthly: process.env.NEXT_PUBLIC_CAKTO_PRO_URL || '',
    annual: process.env.NEXT_PUBLIC_CAKTO_PRO_ANUAL_URL || '',
  },
  starter: {
    monthly: process.env.NEXT_PUBLIC_CAKTO_STARTER_URL || '',
    annual: process.env.NEXT_PUBLIC_CAKTO_STARTER_ANUAL_URL || '',
  },
}
const CAKTO_CHECKOUT_URL_DEFAULT = process.env.NEXT_PUBLIC_CAKTO_PRO_URL || ''

interface PaymentLinkProps {
  children: React.ReactNode
  className?: string
  planId?: string
  isAnnual?: boolean
}

export function PaymentLink({ children, className, planId, isAnnual }: PaymentLinkProps) {
  const { user, loading } = useSession()
  const isLoggedIn = !!user
  const email = user?.email || ''

  if (loading) {
    return (
      <span className={className}>
        {children}
      </span>
    )
  }

  if (planId === 'free') {
    return (
      <Link href={isLoggedIn ? '/dashboard' : '/auth/registro'} className={className}>
        {children}
      </Link>
    )
  }

  if (!isLoggedIn && planId === 'pro') {
    return (
      <Link href="/auth/registro" className={className}>
        {children}
      </Link>
    )
  }

  // Build URL com email pré-definido
  const params = new URLSearchParams()

  if (email) {
    params.set('email', email)
    params.set('customer_email', email)
    params.set('pre_email', email)
  }

  if (planId) {
    params.set('plan', planId)
  }

  const queryString = params.toString()
  const planUrls = planId ? CAKTO_CHECKOUT_URLS[planId] : undefined
  const baseUrl = planUrls
    ? (isAnnual ? planUrls.annual : planUrls.monthly) || CAKTO_CHECKOUT_URL_DEFAULT
    : CAKTO_CHECKOUT_URL_DEFAULT

  // Se a URL do plano não está configurada, redireciona para página de planos
  if (planId && planId !== 'pro' && !baseUrl) {
    return (
      <Link href="/planos" className={className}>
        {children}
      </Link>
    )
  }

  const checkoutUrl = queryString ? `${baseUrl}?${queryString}` : baseUrl

  return (
    <Link href={checkoutUrl} className={className} target="_blank" rel="noopener noreferrer">
      {children}
    </Link>
  )
}

// Hook para gerar URL de pagamento
export function usePaymentUrl(planId?: string, isAnnual?: boolean) {
  const { user } = useSession()

  const params = new URLSearchParams()

  if (user?.email) {
    params.set('email', user.email)
  }

  if (planId) {
    params.set('plan', planId)
  }

  const queryString = params.toString()
  const planUrls = planId ? CAKTO_CHECKOUT_URLS[planId] : undefined
  const baseUrl = planUrls
    ? (isAnnual ? planUrls.annual : planUrls.monthly) || CAKTO_CHECKOUT_URL_DEFAULT
    : CAKTO_CHECKOUT_URL_DEFAULT

  // Se a URL do plano não está configurada, redireciona para página de planos
  if (planId && planId !== 'pro' && !baseUrl) {
    return '/planos'
  }

  return queryString ? `${baseUrl}?${queryString}` : baseUrl
}