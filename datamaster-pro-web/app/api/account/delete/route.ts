import { createClient } from '@/lib/supabase/server'
import { createClient as createSupabaseClient } from '@supabase/supabase-js'
import { NextResponse } from 'next/server'

export async function DELETE(request: Request) {
  try {
    // CSRF protection: verify Origin/Referer headers
    const origin = request.headers.get('origin')
    const referer = request.headers.get('referer')
    const allowedHost = process.env.NEXT_PUBLIC_APP_URL || 'https://datamaster.pro'
    const isFromSameOrigin = (origin && origin.startsWith(allowedHost)) || (referer && referer.startsWith(allowedHost))

    if (!isFromSameOrigin) {
      return NextResponse.json({ error: 'Requisição inválida' }, { status: 403 })
    }

    const supabase = createClient()
    const { data: { user }, error: authError } = await supabase.auth.getUser()

    if (authError || !user) {
      return NextResponse.json({ error: 'Não autorizado' }, { status: 401 })
    }

    const userId = user.id

    // Instancia o cliente admin usando a service role key
    const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY
    if (!serviceRoleKey) {
      console.error('SUPABASE_SERVICE_ROLE_KEY não está configurada')
      // Fallback local se estiver em dev e sem service role configurada
      return NextResponse.json(
        { error: 'Erro de configuração do servidor. SUPABASE_SERVICE_ROLE_KEY ausente.' },
        { status: 500 }
      )
    }

    const supabaseAdmin = createSupabaseClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      serviceRoleKey
    )

    // 1. Deletar os dados das tabelas do usuário (cascade)
    // Deletar da tabela `usuarios`. Isso deve disparar o ON DELETE CASCADE nas tabelas relacionadas.
    const { error: dbError } = await supabaseAdmin
      .from('usuarios')
      .delete()
      .eq('id', userId)

    if (dbError) {
      console.error('Erro ao deletar dados do usuário:', dbError)
      return NextResponse.json({ error: 'Erro ao deletar dados do banco de dados' }, { status: 500 })
    }

    // 2. Deletar o usuário de auth.users no Supabase Auth
    const { error: deleteUserError } = await supabaseAdmin.auth.admin.deleteUser(userId)

    if (deleteUserError) {
      console.error('Erro ao deletar usuário de auth.users:', deleteUserError)
      return NextResponse.json({ error: 'Erro ao deletar conta' }, { status: 500 })
    }

    // Limpar cookies da sessão
    await supabase.auth.signOut()

    return NextResponse.json({ success: true, message: 'Conta excluída com sucesso' })
  } catch (error: any) {
    console.error('Erro na exclusão de conta:', error)
    return NextResponse.json({ error: 'Erro interno do servidor' }, { status: 500 })
  }
}
