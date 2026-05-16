'use client'

import { useEffect, useState } from 'react'
import { supabase } from '@/lib/supabase/client'
import Link from 'next/link'

// Link do Cakto para pagamento
const CAKTO_CHECKOUT_URL = 'https://pay.cakto.com.br/zqno7nv_881188'

interface PaymentLinkProps {
  children: React.ReactNode
  className?: string
  planId?: string
}

export function PaymentLink({ children, className, planId }: PaymentLinkProps) {
  const [email, setEmail] = useState<string>('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function getUserEmail() {
      const { data: { session } } = await supabase.auth.getSession()
      if (session?.user?.email) {
        setEmail(session.user.email)
      }
      setLoading(false)
    }
    getUserEmail()
  }, [])

  if (loading) {
    return (
      <span className={className}>
        {children}
      </span>
    )
  }

  // Build URL com email pré-definido
  // Formatos comuns de plataformas de checkout:
  const params = new URLSearchParams()
  
  if (email) {
    // Tenta diferentes parâmetros (Cakto pode usar um desses)
    params.set('email', email)
    params.set('customer_email', email)
    params.set('pre_email', email)
  }
  
  if (planId) {
    params.set('plan', planId)
  }

  const queryString = params.toString()
  const checkoutUrl = queryString ? `${CAKTO_CHECKOUT_URL}?${queryString}` : CAKTO_CHECKOUT_URL

  return (
    <Link href={checkoutUrl} className={className} target="_blank" rel="noopener noreferrer">
      {children}
    </Link>
  )
}

// Hook para gerar URL de pagamento
export function usePaymentUrl(planId?: string) {
  const [paymentUrl, setPaymentUrl] = useState<string>(CAKTO_CHECKOUT_URL)

  useEffect(() => {
    async function getPaymentUrl() {
      const { data: { session } } = await supabase.auth.getSession()
      
      const params = new URLSearchParams()
      
      if (session?.user?.email) {
        params.set('email', session.user.email)
      }
      
      if (planId) {
        params.set('plan', planId)
      }

      const queryString = params.toString()
      setPaymentUrl(queryString ? `${CAKTO_CHECKOUT_URL}?${queryString}` : CAKTO_CHECKOUT_URL)
    }

    getPaymentUrl()
  }, [planId])

  return paymentUrl
}