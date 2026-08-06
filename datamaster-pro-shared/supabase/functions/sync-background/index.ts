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

  const supabase = createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SUPABASE_ANON_KEY")!
  )

  // Validar JWT e obter usuario
  const { data: { user }, error: authError } = await supabase.auth.getUser(token)

  if (authError || !user) {
    return new Response(JSON.stringify({ error: "Token invalido ou expirado" }), {
      status: 401,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    })
  }

  try {
    // Usar service role para operacoes no banco
    const supabaseAdmin = createClient(
      Deno.env.get("SUPABASE_URL")!,
      Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!
    )

    const { usuario_id } = await req.json()

    // Verificar que o usuario so acessa seus proprios dados
    if (usuario_id !== user.id) {
      return new Response(JSON.stringify({ error: "Acesso negado" }), {
        status: 403,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      })
    }

    // Buscar syncs pendentes do usuario
    const { data: syncsPending, error: syncError } = await supabaseAdmin
      .from("sync_logs")
      .select("*")
      .eq("usuario_id", usuario_id)
      .eq("status", "pending")
      .limit(50)

    if (syncError) throw syncError

    console.log(`Processando ${syncsPending.length} syncs pendentes para ${usuario_id}`)

    const startTime = Date.now()

    // Processar cada sync
    for (const sync of syncsPending) {
      try {
        const dadosSincronizados = sync.dados_sincronizados

        // Marca como syncing
        await supabaseAdmin
          .from("sync_logs")
          .update({ status: "syncing" })
          .eq("id", sync.id)

        // Se tem execucao_id, verificar se existe
        if (dadosSincronizados?.execucao_id) {
          const { data: exec } = await supabaseAdmin
            .from("execucoes")
            .select("*")
            .eq("id", dadosSincronizados.execucao_id)
            .single()

          if (exec) {
            console.log(`Executando sincronizacao de ${dadosSincronizados.ferramenta}`)
            // Aqui voce faria a sincronizacao real
          }
        }

        // Marca como synced
        await supabaseAdmin
          .from("sync_logs")
          .update({ status: "synced" })
          .eq("id", sync.id)
      } catch (error) {
        console.error(`Erro ao sincronizar ${sync.id}:`, error)

        // Marca como failed
        await supabaseAdmin
          .from("sync_logs")
          .update({
            status: "failed",
            erro_mensagem: error.message,
          })
          .eq("id", sync.id)
      }
    }

    // Atualizar ultima_sincronizacao do usuario
    await supabaseAdmin
      .from("usuarios")
      .update({ ultima_sincronizacao: new Date().toISOString() })
      .eq("id", usuario_id)

    const duracao = Date.now() - startTime

    return new Response(
      JSON.stringify({
        success: true,
        syncs_processadas: syncsPending.length,
        duracao_ms: duracao,
      }),
      {
        status: 200,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      }
    )
  } catch (error) {
    console.error("Erro na sincronizacao:", error)
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    })
  }
})
