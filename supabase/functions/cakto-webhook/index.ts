import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.39.0"

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
}

/**
 * Mapeia nome do plano da Cakto para o enum plan_type do banco.
 * Aceita variações como "Pro", "Premium", "Pro Anual", etc.
 */
function mapPlanType(planName: string): string {
  const lower = (planName || "").toLowerCase()
  if (lower.includes("enterprise") || lower.includes("empresas")) return "enterprise"
  if (lower.includes("pro") || lower.includes("premium")) return "pro"
  return "pro" // Default para planos pagos
}

/**
 * Calcula data de expiração (hoje + 30 dias) no formato YYYY-MM-DD.
 */
function calculateExpiration(nextPaymentDate?: string): string {
  if (nextPaymentDate) {
    try {
      const d = new Date(nextPaymentDate)
      if (!isNaN(d.getTime())) {
        return d.toISOString().split("T")[0]
      }
    } catch { /* ignore */ }
  }
  const now = new Date()
  now.setDate(now.getDate() + 30)
  return now.toISOString().split("T")[0]
}

serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders })
  }

  try {
    const supabase = createClient(
      Deno.env.get("SUPABASE_URL")!,
      Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!
    )

    const payload = await req.json()

    // --- SEGURANÇA BASEADA NO SECRET DA CAKTO ---
    if (payload.secret !== Deno.env.get("CAKTO_WEBHOOK_SECRET")) {
      console.error("Tentativa de acesso com secret inválido")
      return new Response(JSON.stringify({ error: "Unauthorized" }), {
        status: 401,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      })
    }

    const eventType = payload.event || ""
    console.log(`Evento recebido: ${eventType}`)

    // Extrair dados do payload (suporta variações de estrutura Cakto)
    const email = payload.data?.customer?.email
      || payload.data?.email
      || payload.data?.customer_email
      || ""

    const planName = payload.data?.offer?.name
      || payload.data?.plan
      || payload.data?.plan_name
      || "Pro"

    const nextPaymentDate = payload.data?.subscription?.next_payment_date
      || payload.data?.next_billing_date
      || ""

    const expirationDate = payload.data?.expiration_date || null

    if (!email) {
      console.error("Webhook sem email, ignorando")
      return new Response(JSON.stringify({ message: "No email" }), {
        status: 200,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      })
    }

    // Buscar usuário
    const { data: userData, error: userError } = await supabase
      .from("usuarios")
      .select("id, plano_tipo")
      .eq("email", email)
      .single()

    if (userError || !userData) {
      console.warn(`Usuário não encontrado: ${email}`)
      return new Response(JSON.stringify({ message: "User not found" }), {
        status: 200,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      })
    }

    let updateData: Record<string, unknown> = {
      updated_at: new Date().toISOString(),
    }

    let logAction = "unknown"

    switch (eventType) {
      // === ATIVAÇÃO / COMPRA ===
      case "subscription_created":
      case "purchase.completed":
      case "purchase_approved": {
        const planType = mapPlanType(planName)
        const expDate = expirationDate || calculateExpiration(nextPaymentDate)
        updateData.plano_tipo = planType
        updateData.data_expiracao = expDate
        logAction = "activate"
        console.log(`Ativando plano ${planType} para ${email}, expira em ${expDate}`)
        break
      }

      // === RENOVAÇÃO ===
      case "subscription_renewed": {
        const planType = mapPlanType(planName)
        const expDate = expirationDate || calculateExpiration(nextPaymentDate)
        updateData.plano_tipo = planType
        updateData.data_expiracao = expDate
        logAction = "renew"
        console.log(`Renovando plano ${planType} para ${email}, nova expiração ${expDate}`)
        break
      }

      // === EXPIRAÇÃO ===
      case "subscription.expired": {
        updateData.plano_tipo = "gratis"
        updateData.data_expiracao = null
        logAction = "expire"
        console.log(`Plano expirado para ${email}, revertendo para gratis`)
        break
      }

      // === CANCELAMENTO ===
      case "subscription_canceled":
      case "purchase_refused": {
        updateData.plano_tipo = "gratis"
        updateData.data_expiracao = null
        logAction = "cancel"
        console.log(`Plano cancelado/recusado para ${email}`)
        break
      }

      // === REEMBOLSO / CHARGEBACK ===
      case "refund":
      case "chargeback": {
        updateData.plano_tipo = "gratis"
        updateData.data_expiracao = null
        logAction = "refund"
        console.log(`Reembolso/chargeback para ${email}`)
        break
      }

      default:
        console.log(`Evento ignorado: ${eventType}`)
        return new Response(JSON.stringify({ message: "Evento não processado" }), {
          status: 200,
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        })
    }

    // Atualizar usuário
    const { error: updateError } = await supabase
      .from("usuarios")
      .update(updateData)
      .eq("id", userData.id)

    if (updateError) {
      console.error(`Erro ao atualizar usuário: ${updateError.message}`)
      throw updateError
    }

    // Registrar pagamento na tabela de logs
    await supabase.from("pagamentos").insert({
      usuario_id: userData.id,
      plano: updateData.plano_tipo || "gratis",
      valor: payload.data?.price || 0,
      status: logAction,
      transacao_id: payload.data?.transaction_id || payload.data?.subscription_id || "",
      gateway: "cakto",
      metadata: JSON.stringify(payload.data || {}),
    }).then(() => {}).catch((e) => console.warn("Erro ao logar pagamento:", e))

    // Enviar email de confirmação (apenas para ativação e renovação)
    if (logAction === "activate" || logAction === "renew") {
      try {
        const emailType = logAction === "activate" ? "upgrade_pro" : "renewal_pro"
        await supabase.rpc("enfileirar_email", {
          p_usuario_id: userData.id,
          p_tipo_email: emailType,
          p_destinatario: email,
          p_assunto: logAction === "activate"
            ? "Bem-vindo ao DataMaster Pro!"
            : "Sua assinatura foi renovada"
        })
      } catch (e) {
        console.warn("Erro ao enfileirar email:", e)
      }
    }

    return new Response(JSON.stringify({ success: true, action: logAction }), {
      status: 200,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    })

  } catch (error) {
    console.error("Erro no Webhook:", error.message)
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    })
  }
})
