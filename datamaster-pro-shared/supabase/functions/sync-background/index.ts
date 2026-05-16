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

    const { usuario_id } = await req.json()

    // Buscar all pending syncs do usuário
    const { data: syncsPending, error: syncError } = await supabase
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
        await supabase
          .from("sync_logs")
          .update({ status: "syncing" })
          .eq("id", sync.id)

        // Se tem execução_id, verificar se existe
        if (dadosSincronizados?.execucao_id) {
          const { data: exec } = await supabase
            .from("execucoes")
            .select("*")
            .eq("id", dadosSincronizados.execucao_id)
            .single()

          if (exec) {
            console.log(`Executando sincronização de ${dadosSincronizados.ferramenta}`)
            // Aqui você faria a sincronização real
          }
        }

        // Marca como synced
        await supabase
          .from("sync_logs")
          .update({ status: "synced" })
          .eq("id", sync.id)
      } catch (error) {
        console.error(`Erro ao sincronizar ${sync.id}:`, error)

        // Marca como failed
        await supabase
          .from("sync_logs")
          .update({
            status: "failed",
            erro_mensagem: error.message,
          })
          .eq("id", sync.id)
      }
    }

    // Atualizar ultima_sincronizacao do usuário
    await supabase
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
    console.error("Erro na sincronização:", error)
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    })
  }
})
