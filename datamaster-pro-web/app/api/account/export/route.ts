import { createClient } from '@/lib/supabase/server'
import { createClient as createSupabaseClient } from '@supabase/supabase-js'
import { NextResponse } from 'next/server'

export async function GET(request: Request) {
  try {
    const supabase = createClient()
    const { data: { user }, error: authError } = await supabase.auth.getUser()

    if (authError || !user) {
      return NextResponse.json({ error: 'Não autorizado' }, { status: 401 })
    }

    const userId = user.id
    const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY
    if (!serviceRoleKey) {
      console.error('SUPABASE_SERVICE_ROLE_KEY não configurada')
      return NextResponse.json({ error: 'Erro de configuração do servidor' }, { status: 500 })
    }

    const supabaseAdmin = createSupabaseClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      serviceRoleKey
    )

    // Fetch all user records from relevant tables
    const [
      profileResult,
      execucoesResult,
      favoritosResult,
      logsResult
    ] = await Promise.all([
      supabaseAdmin.from('usuarios').select('*').eq('id', userId).maybeSingle(),
      supabaseAdmin.from('execucoes').select('*').eq('usuario_id', userId),
      supabaseAdmin.from('favoritos').select('*').eq('usuario_id', userId),
      supabaseAdmin.from('execution_logs').select('*').eq('user_id', userId),
    ])

    const exportData = {
      profile: profileResult.data || {},
      execucoes: execucoesResult.data || [],
      favoritos: favoritosResult.data || [],
      execution_logs: logsResult.data || [],
      exported_at: new Date().toISOString(),
      law_compliance: 'LGPD (Lei nº 13.709/2018) - Direito de Acesso e Portabilidade (Art. 18)'
    }

    return new Response(JSON.stringify(exportData, null, 2), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        'Content-Disposition': `attachment; filename=datamaster_dados_pessoais.json`,
      },
    })
  } catch (error: any) {
    console.error('Erro na exportação de dados:', error)
    return NextResponse.json({ error: 'Erro interno do servidor' }, { status: 500 })
  }
}
