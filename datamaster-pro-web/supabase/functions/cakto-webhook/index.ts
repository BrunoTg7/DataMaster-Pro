// Cakto Webhook Handler
Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', {
      headers: { 'Access-Control-Allow-Origin': '*' }
    })
  }

  try {
    const payload = await req.json()
    console.log('Webhook Cakto recebido com sucesso:', JSON.stringify(payload))

    const supabaseUrl = Deno.env.get('SUPABASE_URL')!
    const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    
    const { createClient } = await import('https://esm.sh/@supabase/supabase-js@2')
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

    // Extract from Cakto payload structure
    const email = payload.data?.customer?.email || payload.data?.customer?.email || ''
    const price = parseFloat(payload.data?.offer?.price || payload.data?.amount || '0')
    const nextPaymentDate = payload.data?.subscription?.next_payment_date || null
    
    console.log(`Event: ${eventType}, action: ${action}, email: ${email}, price: ${price}`)

    if (!email) {
      return new Response(JSON.stringify({ error: 'No email provided' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' }
      })
    }

    // Find user by email
    const { data: userData, error: userError } = await supabase
      .from('usuarios')
      .select('id, email, plano_tipo')
      .eq('email', email)
      .single()

    if (userError || !userData) {
      console.log(`User not found for email: ${email}`)
      return new Response(JSON.stringify({ message: 'User not found, skipping', email }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' }
      })
    }

    // Determine plan type - only allow valid enum values
    let planType = 'gratis'
    if (action === 'cancel' || action === 'refund') {
      planType = 'gratis'
    } else if (action === 'activate' || action === 'renew') {
      // Detect annual vs monthly based on next_payment_date
      if (nextPaymentDate) {
        const nextDate = new Date(nextPaymentDate)
        const now = new Date()
        const monthsDiff = (nextDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24 * 30)
        // Annual if more than 6 months away
        planType = monthsDiff > 6 ? 'pro_anual' : 'pro'
      } else {
        planType = 'pro'
      }
    }

    console.log(`Plano definido: ${planType} (meses até próxima pagamento: ${nextPaymentDate ? Math.round((new Date(nextPaymentDate).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24 * 30)) : 'N/A'})`)

    // Update user plan
    const updateData: any = {
      plano_tipo: planType,
      updated_at: new Date().toISOString()
    }
    
    if (nextPaymentDate) {
      updateData.data_expiracao = nextPaymentDate.split('T')[0]
    }

    const { error: updateError } = await supabase
      .from('usuarios')
      .update(updateData)
      .eq('id', userData.id)

    if (updateError) {
      console.error('Error updating user:', updateError)
      return new Response(JSON.stringify({ error: updateError.message }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      })
    }

    // Log payment
    await supabase.from('pagamentos').insert({
      usuario_id: userData.id,
      plano: planType,
      valor: price,
      status: action,
      gateway: 'cakto',
      metadata: JSON.stringify(payload.data || {})
    })

    console.log(`Success! User ${userData.id} updated to ${planType}`)

    return new Response(JSON.stringify({ 
      success: true, 
      user_id: userData.id, 
      plan: planType 
    }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    })

  } catch (error) {
    console.error('Error:', error)
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    })
  }
})