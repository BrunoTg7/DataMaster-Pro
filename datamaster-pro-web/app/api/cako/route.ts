import { NextResponse } from 'next/server'

export async function POST(request: Request) {
  try {
    const authHeader = request.headers.get('authorization') || request.headers.get('x-cakto-signature')
    const expectedSecret = process.env.CAKTO_WEBHOOK_SECRET

    if (expectedSecret && authHeader !== expectedSecret && authHeader !== `Bearer ${expectedSecret}`) {
      console.warn('Webhook Unauthorized: Invalid signature')
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    const payload = await request.json()
    console.log('Cakto webhook received:', JSON.stringify(payload))

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

    const email = payload.data?.email || payload.data?.customer_email || ''
    const planName = payload.data?.plan || payload.data?.plan_name || 'pro'
    const price = payload.data?.price || 0
    const expirationDate = payload.data?.expiration_date || payload.data?.next_billing_date || null
    const transactionId = payload.data?.transaction_id || payload.data?.subscription_id || ''

    if (!email) {
      return NextResponse.json({ error: 'No email provided' }, { status: 400 })
    }

    const { data: userData, error: userError } = await supabase
      .from('usuarios')
      .select('id, email, plano_tipo')
      .eq('email', email)
      .single()

    if (userError || !userData) {
      console.log(`User not found for email: ${email}`)
      return NextResponse.json({ message: 'User not found', email }, { status: 200 })
    }

    let planType = 'gratis'
    if (action === 'cancel' || action === 'refund') {
      planType = 'gratis'
    } else if (planName.toLowerCase().includes('pro') || price >= 49.90) {
      planType = 'pro'
    } else if (planName.toLowerCase().includes('enterprise')) {
      planType = 'enterprise'
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
      console.error('Error updating user plan:', updateError)
      return NextResponse.json({ error: updateError.message }, { status: 500 })
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
        metadata: JSON.stringify(payload.data || {})
      })

    return NextResponse.json({ success: true, user_id: userData.id, plan: planType }, { status: 200 })

  } catch (error: any) {
    console.error('Error processing webhook:', error)
    return NextResponse.json({ error: error.message || 'Internal Server Error' }, { status: 500 })
  }
}