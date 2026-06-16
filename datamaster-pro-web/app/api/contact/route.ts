import { NextResponse } from 'next/server'

const rateLimitMap = new Map<string, { count: number; resetTime: number }>()

function checkContactRateLimit(ip: string): boolean {
  const now = Date.now()
  const limit = 5
  const window = 60000

  const current = rateLimitMap.get(ip)
  if (!current || now > current.resetTime) {
    rateLimitMap.set(ip, { count: 1, resetTime: now + window })
    return true
  }
  if (current.count >= limit) return false
  current.count++
  return true
}

export async function POST(request: Request) {
  try {
    const ip = request.headers.get('x-forwarded-for') || request.headers.get('x-real-ip') || 'unknown'

    if (!checkContactRateLimit(ip)) {
      return NextResponse.json(
        { error: 'Muitas requisições. Tente novamente em 1 minuto.' },
        { status: 429 }
      )
    }

    const body = await request.json()
    const { nome, email, mensagem, honeypot } = body

    if (honeypot) {
      return NextResponse.json({ message: 'Enviado' }, { status: 200 })
    }

    if (!nome || !email || !mensagem) {
      return NextResponse.json(
        { error: 'Nome, email e mensagem são obrigatórios.' },
        { status: 400 }
      )
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(email)) {
      return NextResponse.json(
        { error: 'Email inválido.' },
        { status: 400 }
      )
    }

    if (mensagem.length > 2000) {
      return NextResponse.json(
        { error: 'Mensagem muito longa (máximo 2000 caracteres).' },
        { status: 400 }
      )
    }

    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
    const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY!

    if (supabaseUrl && supabaseServiceKey) {
      const { createClient } = await import('@supabase/supabase-js')
      const supabase = createClient(supabaseUrl, supabaseServiceKey)

      await supabase.from('webhooks_log').insert({
        fonte: 'contato',
        tipo_evento: 'contact_form',
        payload: {
          nome,
          email,
          mensagem,
          ip,
          user_agent: request.headers.get('user-agent'),
          created_at: new Date().toISOString(),
        },
        processado: false,
      })
    }

    return NextResponse.json(
      { message: 'Mensagem recebida com sucesso!' },
      { status: 200 }
    )
  } catch {
    return NextResponse.json(
      { error: 'Erro interno do servidor.' },
      { status: 500 }
    )
  }
}
