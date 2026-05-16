import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.39.0"

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
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

    console.log(`Evento recebido: ${payload.event}`)

    switch (payload.event) {
      case "subscription_created":
      case "purchase.completed":
        // Captura os dados conforme a estrutura real do log
        const email = payload.data.customer?.email || payload.data.email
        const planName = payload.data.offer?.name || "Premium"
        const expiration = payload.data.subscription?.next_payment_date || payload.data.expiration_date

        console.log(`Processando upgrade para: ${email}`)

        const { data, error } = await supabase.rpc("processar_upgrade_cakto", {
          p_email: email,
          p_plano_novo: planName,
          p_data_expiracao: expiration,
        })

        if (error) throw error

        return new Response(JSON.stringify({ success: true, message: "Upgrade concluído" }), {
          status: 200,
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        })

      case "subscription.expired":
        const expiredEmail = payload.data.customer?.email || payload.data.expired_email

        await supabase
          .from("usuarios")
          .update({ plano_tipo: "gratis" })
          .eq("email", expiredEmail)

        return new Response(JSON.stringify({ success: true, message: "Assinatura expirada" }), {
          status: 200,
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        })

      default:
        console.log(`Evento ignorado: ${payload.event}`)
        return new Response(JSON.stringify({ message: "Evento recebido mas não processado" }), {
          status: 200, // Retornamos 200 para a Cakto não ficar tentando reenviar
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        })
    }
  } catch (error) {
    console.error("Erro no Webhook:", error.message)
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    })
  }
})