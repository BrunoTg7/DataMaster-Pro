import { NextResponse } from 'next/server'
import { timingSafeEqual } from 'crypto'

function safeCompare(a: string, b: string): boolean {
  const bufA = Buffer.from(a)
  const bufB = Buffer.from(b)
  if (bufA.length !== bufB.length) return false
  return timingSafeEqual(bufA, bufB)
}

function sanitizeString(value: unknown, maxLength: number): string {
  if (typeof value !== 'string') return ''
  return value.trim().slice(0, maxLength)
}

function sanitizeEmail(value: unknown): string {
  if (typeof value !== 'string') return ''
  return value.trim().toLowerCase().slice(0, 254)
}

export async function POST(request: Request) {
  try {
    const expectedSecret = process.env.CAKTO_WEBHOOK_SECRET

    if (!expectedSecret || expectedSecret === 'your-webhook-secret') {
      return NextResponse.json({ error: 'Server misconfiguration' }, { status: 500 })
    }

    const authHeader = request.headers.get('authorization') || request.headers.get('x-cakto-signature')

    if (!authHeader || (!safeCompare(authHeader, expectedSecret) && !safeCompare(authHeader, `Bearer ${expectedSecret}`))) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    const payload = await request.json()

    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
    const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY!
    
    const { createClient } = await import('@supabase/supabase-js')
    const supabase = createClient(supabaseUrl, supabaseServiceKey)

    const eventType = payload.event || ''
    
    let action = 'unknown'
    if (eventType === 'purchase_approved' || eventType === 'subscription_created') {
      action = 'activate'
    } else if (eventType === 'subscription_canceled' || eventType === 'purchase_refused') {
      action = 'cancel'
    } else if (eventType === 'refund' || eventType === 'chargeback') {
      action = 'refund'
    } else if (eventType === 'subscription_renewed') {
      action = 'renew'
    }

    const email = sanitizeEmail(payload.data?.email || payload.data?.customer_email || '')
    const planName = sanitizeString(payload.data?.plan || payload.data?.plan_name || 'pro', 50)
    const price = typeof payload.data?.price === 'number' ? payload.data.price : 0
    const expirationDate = sanitizeString(payload.data?.expiration_date || payload.data?.next_billing_date || '', 30) || null
    const transactionId = sanitizeString(payload.data?.transaction_id || payload.data?.subscription_id || '', 100)

    if (!email) {
      return NextResponse.json({ error: 'No email provided' }, { status: 400 })
    }

    // Check idempotency (avoid processing duplicate webhook events for the same transaction & status)
    if (transactionId) {
      const { data: existingPayment } = await supabase
        .from('pagamentos')
        .select('id')
        .eq('transacao_id', transactionId)
        .eq('status', action)
        .maybeSingle()

      if (existingPayment) {
        return NextResponse.json({ message: 'Processed (duplicate)' }, { status: 200 })
      }
    }

    const { data: userData, error: userError } = await supabase
      .from('usuarios')
      .select('id')
      .eq('email', email)
      .single()

    if (userError || !userData) {
      return NextResponse.json({ message: 'Processed' }, { status: 200 })
    }

    let planType = 'gratis'
    if (action === 'cancel' || action === 'refund') {
      planType = 'gratis'
    } else if (planName.toLowerCase().includes('pro') || price >= 49.90) {
      planType = 'pro'
    } else if (planName.toLowerCase().includes('starter') || price >= 29.90) {
      planType = 'starter'
    }

    let updateData: any = {
      plano_tipo: planType,
      updated_at: new Date().toISOString()
    }
    
    if (action === 'activate' || action === 'renew') {
      updateData.data_expiracao = expirationDate
    } else if (action === 'cancel' || action === 'refund') {
      updateData.data_expiracao = null
    }

    const { error: updateError } = await supabase
      .from('usuarios')
      .update(updateData)
      .eq('id', userData.id)

    if (updateError) {
      return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 })
    }

    // Sanitizar metadata - apenas campos essenciais
    const safeMetadata = {
      event: sanitizeString(payload.event, 50),
      plan: planName,
      price: price,
    }

    await supabase
      .from('pagamentos')
      .insert({
        usuario_id: userData.id,
        plano: planType,
        valor: price,
        status: action,
        transacao_id: transactionId,
        gateway: 'cakto',
        metadata: JSON.stringify(safeMetadata)
      })

    return NextResponse.json({ message: 'Processed' }, { status: 200 })

  } catch {
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 })
  }
}
