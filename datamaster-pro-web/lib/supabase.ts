import { createBrowserClient } from '@supabase/ssr'

/**
 * Supabase Client - Web Application
 * 
 * Cliente configurado para uso no navegador (browser) com
 * suporte a autenticação de servidor (SSR).
 * 
 * Uso:
 * import { supabase } from '@/lib/supabase'
 * 
 * const { data, error } = await supabase
 *   .from('usuarios')
 *   .select('*')
 */

export const supabase = createBrowserClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)

/**
 * Funções auxiliares comuns
 */

/**
 * Fazer login com email e senha
 */
export async function signIn(email: string, password: string) {
  return await supabase.auth.signInWithPassword({
    email,
    password,
  })
}

/**
 * Fazer cadastro novo
 */
export async function signUp(email: string, password: string, nome: string) {
  const { data, error } = await supabase.auth.signUp({
    email,
    password,
    options: {
      data: {
        nome: nome,
      },
    },
  })
  
  if (error) return { data: null, error }
  
  // Criar registro do usuário na tabela usuarios
  if (data.user) {
    const { error: dbError } = await supabase
      .from('usuarios')
      .insert({
        id: data.user.id,
        email: data.user.email,
        nome: nome,
        plano_tipo: 'gratis',
      })
    
    if (dbError) return { data: null, error: dbError }
  }
  
  return { data, error: null }
}

/**
 * Fazer logout
 */
export async function signOut() {
  return await supabase.auth.signOut()
}

/**
 * Obter usuário atual
 */
export async function getCurrentUser() {
  const { data: { user } } = await supabase.auth.getUser()
  return user
}

/**
 * Obter sessão atual
 */
export async function getSession() {
  const { data: { session } } = await supabase.auth.getSession()
  return session
}

/**
 * Obter informações completas do usuário (profile + metadata)
 */
export async function getUserProfile(userId: string) {
  const { data, error } = await supabase
    .from('usuarios')
    .select('*')
    .eq('id', userId)
    .single()
  
  return { data, error }
}

/**
 * Atualizar plano do usuário
 */
export async function updateUserPlan(userId: string, newPlan: 'gratis' | 'pro' | 'enterprise') {
  return await supabase
    .from('usuarios')
    .update({ plano_tipo: newPlan })
    .eq('id', userId)
}

/**
 * Obter histórico de execuções do usuário
 */
export async function getUserExecutions(userId: string, limit: number = 50) {
  return await supabase
    .from('execucoes')
    .select('*')
    .eq('usuario_id', userId)
    .order('created_at', { ascending: false })
    .limit(limit)
}

/**
 * Registrar execução de ferramenta
 */
export async function logExecution(
  userId: string,
  ferramenta: string,
  linhas: number,
  tempo_ms: number
) {
  return await supabase
    .from('execucoes')
    .insert({
      usuario_id: userId,
      ferramenta,
      linhas_processadas: linhas,
      tempo_execucao_ms: tempo_ms,
      tempo_economizado_minutos: Math.round(tempo_ms / 60000), // Estimativa simples
    })
}

/**
 * Obter favoritos do usuário
 */
export async function getUserFavorites(userId: string) {
  return await supabase
    .from('favoritos')
    .select('*')
    .eq('usuario_id', userId)
    .order('posicao', { ascending: true })
}

/**
 * Adicionar ferramenta aos favoritos
 */
export async function addFavorite(userId: string, ferramenta: string, posicao: number) {
  return await supabase
    .from('favoritos')
    .insert({
      usuario_id: userId,
      ferramenta,
      posicao,
    })
}

/**
 * Remover ferramenta dos favoritos
 */
export async function removeFavorite(userId: string, ferramenta: string) {
  return await supabase
    .from('favoritos')
    .delete()
    .eq('usuario_id', userId)
    .eq('ferramenta', ferramenta)
}

/**
 * Obter configurações do usuário
 */
export async function getUserConfig(userId: string, chave: string) {
  const { data, error } = await supabase
    .from('configs_usuario')
    .select('valor')
    .eq('usuario_id', userId)
    .eq('chave', chave)
    .single()
  
  return { data: data?.valor, error }
}

/**
 * Atualizar configuração do usuário
 */
export async function updateUserConfig(userId: string, chave: string, valor: string) {
  // Tentar atualizar, se não existir, inserir
  const { data: existing } = await supabase
    .from('configs_usuario')
    .select('id')
    .eq('usuario_id', userId)
    .eq('chave', chave)
    .single()
  
  if (existing) {
    return await supabase
      .from('configs_usuario')
      .update({ valor })
      .eq('usuario_id', userId)
      .eq('chave', chave)
  } else {
    return await supabase
      .from('configs_usuario')
      .insert({
        usuario_id: userId,
        chave,
        valor,
      })
  }
}

/**
 * Stream (real-time) de mudanças nos dados do usuário
 */
export function subscribeToUserChanges(userId: string, callback: (data: any) => void) {
  return supabase
    .channel(`public:usuarios:id=eq.${userId}`)
    .on(
      'postgres_changes',
      { event: '*', schema: 'public', table: 'usuarios', filter: `id=eq.${userId}` },
      (payload) => {
        callback(payload.new)
      }
    )
    .subscribe()
}

/**
 * Cancelar subscription
 */
export async function unsubscribe(subscription: any) {
  if (subscription) {
    await supabase.removeSubscription(subscription)
  }
}

export default supabase
