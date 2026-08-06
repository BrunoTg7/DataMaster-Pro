import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.39.0"

const ALLOWED_ORIGINS = [
  "https://datamaster.pro",
  "https://www.datamaster.pro",
  "http://localhost:3000",
]

function getAllowedOrigin(req: Request): string | null {
  const origin = req.headers.get("origin")
  if (origin && ALLOWED_ORIGINS.includes(origin)) {
    return origin
  }
  return null
}

function getCorsHeaders(req: Request): Record<string, string> {
  const allowedOrigin = getAllowedOrigin(req)
  return {
    "Access-Control-Allow-Origin": allowedOrigin || ALLOWED_ORIGINS[0],
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  }
}

// Templates de Email
const emailTemplates: Record<string, { subject: string; html: string }> = {
  welcome: {
    subject: "Bem-vindo ao DataMaster Pro!",
    html: `
      <h1>Bem-vindo ao DataMaster Pro!</h1>
      <p>Sua conta foi criada com sucesso.</p>
      <p>Voce comecar a usar nossas ferramentas gratuitas agora:</p>
      <ul>
        <li>Consolidador</li>
        <li>Categorizador</li>
      </ul>
      <p><a href="https://datamaster.pro/downloads">Baixe agora</a></p>
    `,
  },
  upgrade_pro: {
    subject: "Parabens! Seu plano foi atualizado para Pro",
    html: `
      <h1>Bem-vindo ao DataMaster Pro!</h1>
      <p>Seu plano foi atualizado com sucesso para <strong>Pro</strong>.</p>
      <p>Voce agora tem acesso a:</p>
      <ul>
        <li>Consolidador</li>
        <li>Categorizador</li>
        <li>Orcamentos</li>
        <li>Minerador</li>
        <li>Conciliador</li>
      </ul>
      <p>Sem limite de linhas! Baixe a versao atualizada:</p>
      <p><a href="https://datamaster.pro/downloads">Baixar app atualizado</a></p>
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
    subject: "Seu relatorio de ROI do mes",
    html: `
      <h1>Relatorio de ROI - {{month}}</h1>
      <p>Parabens! Aqui esta o resumo do seu uso:</p>
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
    throw new Error(`Template de email nao encontrado: ${tipoEmail}`)
  }

  let html = template.html

  // Substituir variaveis
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
  const corsHeaders = getCorsHeaders(req)

  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders })
  }

  // Verificar JWT do Supabase
  const authHeader = req.headers.get("Authorization")
  if (!authHeader) {
    return new Response(JSON.stringify({ error: "Token de autenticacao necessario" }), {
      status: 401,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    })
  }

  const token = authHeader.replace("Bearer ", "")

  const supabaseAnon = createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SUPABASE_ANON_KEY")!
  )

  // Validar JWT e obter usuario
  const { data: { user }, error: authError } = await supabaseAnon.auth.getUser(token)

  if (authError || !user) {
    return new Response(JSON.stringify({ error: "Token invalido ou expirado" }), {
      status: 401,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    })
  }

  try {
    // Usar service role para operacoes no banco
    const supabase = createClient(
      Deno.env.get("SUPABASE_URL")!,
      Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!
    )

    const { email_id, tipo_email, destinatario, variaveisTemplate } = await req.json()

    // Validar campos obrigatorios
    if (!tipo_email || !destinatario) {
      return new Response(JSON.stringify({ error: "tipo_email e destinatario sao obrigatorios" }), {
        status: 400,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      })
    }

    // Validar formato do email
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(destinatario)) {
      return new Response(JSON.stringify({ error: "Email destinatario invalido" }), {
        status: 400,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      })
    }

    // Validar template
    if (!emailTemplates[tipo_email]) {
      return new Response(JSON.stringify({ error: "Template de email invalido" }), {
        status: 400,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      })
    }

    console.log(`Enviando email ${tipo_email} para ${destinatario}`)

    // Enviar email
    await enviarEmail(supabase, destinatario, tipo_email, variaveisTemplate || {})

    // Atualizar status
    if (email_id) {
      await supabase
        .from("email_logs")
        .update({
          status: "enviado",
          ultima_tentativa: new Date().toISOString(),
        })
        .eq("id", email_id)
    }

    return new Response(JSON.stringify({ success: true }), {
      status: 200,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    })
  } catch (error) {
    console.error("Erro enviando email:", error)

    // Registrar falha
    if (req.body) {
      try {
        const payload = await req.json()
        const supabase = createClient(
          Deno.env.get("SUPABASE_URL")!,
          Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!
        )
        if (payload.email_id) {
          await supabase
            .from("email_logs")
            .update({
              status: "falha",
              ultima_tentativa: new Date().toISOString(),
            })
            .eq("id", payload.email_id)
        }
      } catch {
        // Ignorar erro no registro de falha
      }
    }

    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    })
  }
})
