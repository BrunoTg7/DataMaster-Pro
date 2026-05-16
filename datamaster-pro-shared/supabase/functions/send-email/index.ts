import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.39.0"

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
}

// Templates de Email
const emailTemplates = {
  welcome: {
    subject: "Bem-vindo ao DataMaster Pro! 🎉",
    html: `
      <h1>Bem-vindo ao DataMaster Pro!</h1>
      <p>Sua conta foi criada com sucesso.</p>
      <p>Você pode começar a usar nossos 2 ferramentas gratuitas agora:</p>
      <ul>
        <li>Consolidador</li>
        <li>Categorizador</li>
      </ul>
      <p><a href="https://datamaster.pro/downloads">Baixe agora</a></p>
    `,
  },
  upgrade_pro: {
    subject: "Parabéns! Seu plano foi atualizado para Pro 🚀",
    html: `
      <h1>Bem-vindo ao DataMaster Pro!</h1>
      <p>Seu plano foi atualizado com sucesso para <strong>Pro</strong>.</p>
      <p>Você agora tem acesso a:</p>
      <ul>
        <li>✅ Consolidador</li>
        <li>✅ Categorizador</li>
        <li>✅ Orçamentos</li>
        <li>✅ Minerador</li>
        <li>✅ Conciliador</li>
      </ul>
      <p>Sem limite de linhas! Baixe a versão atualizada:</p>
      <p><a href="https://datamaster.pro/downloads">Baixar app atualizado</a></p>
    `,
  },
  upgrade_enterprise: {
    subject: "Bem-vindo Enterprise! Suporte prioritário 🏆",
    html: `
      <h1>Bem-vindo ao plano Enterprise!</h1>
      <p>Seu plano foi atualizado para <strong>Enterprise</strong>.</p>
      <p>Você tem acesso a todas as ferramentas + customizações.</p>
      <p>Nosso time de suporte prioritário está pronto para ajudar:</p>
      <p>Email: <strong>support@datamaster.pro</strong></p>
      <p>Resposta em até 12 horas!</p>
    `,
  },
  expiration_warning: {
    subject: "Seu plano expira em 3 dias",
    html: `
      <h1>Seu plano expira em breve</h1>
      <p>Sua assinatura <strong>Pro</strong> expira em 3 dias.</p>
      <p>Para continuar usando todas as ferramentas, renove sua assinatura:</p>
      <p><a href="https://datamaster.pro/planos">Renovar agora</a></p>
    `,
  },
  roi_report: {
    subject: "Seu relatório de ROI do mês 📊",
    html: `
      <h1>Relatório de ROI - {{month}}</h1>
      <p>Parabéns! Aqui está o resumo do seu uso:</p>
      <ul>
        <li>Arquivos processados: {{executions}}</li>
        <li>Linhas processadas: {{lines}}</li>
        <li>Tempo economizado: {{time_saved}} horas</li>
      </ul>
      <p><a href="https://datamaster.pro/dashboard">Ver detalhes</a></p>
    `,
  },
}

async function enviarEmail(
  supabase: any,
  destinatario: string,
  tipoEmail: string,
  variaveisTemplate: Record<string, string> = {}
) {
  const template = emailTemplates[tipoEmail]

  if (!template) {
    throw new Error(`Template de email não encontrado: ${tipoEmail}`)
  }

  let html = template.html

  // Substituir variáveis
  Object.entries(variaveisTemplate).forEach(([key, value]) => {
    html = html.replace(`{{${key}}}`, value)
  })

  // Enviar via Supabase Email
  const { data, error } = await supabase.auth.admin.sendEmail({
    email: destinatario,
    subject: template.subject,
    html: html,
  })

  if (error) {
    throw new Error(`Supabase Email error: ${error.message}`)
  }

  return data
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

    const { email_id, tipo_email, destinatario, variaveisTemplate } = await req.json()

    console.log(`Enviando email ${tipo_email} para ${destinatario}`)

    // Enviar email
    await enviarEmail(supabase, destinatario, tipo_email, variaveisTemplate || {})

    // Atualizar status
    await supabase
      .from("email_logs")
      .update({
        status: "enviado",
        ultima_tentativa: new Date().toISOString(),
      })
      .eq("id", email_id)

    return new Response(JSON.stringify({ success: true }), {
      status: 200,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    })
  } catch (error) {
    console.error("Erro enviando email:", error)

    // Registrar falha
    if (req.body) {
      const payload = await req.json()
      const supabase = createClient(
        Deno.env.get("SUPABASE_URL")!,
        Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!
      )
      await supabase
        .from("email_logs")
        .update({
          status: "falha",
          ultima_tentativa: new Date().toISOString(),
          tentativas: supabase.from("email_logs").select("tentativas").eq("id", payload.email_id),
        })
        .eq("id", payload.email_id)
    }

    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    })
  }
})
