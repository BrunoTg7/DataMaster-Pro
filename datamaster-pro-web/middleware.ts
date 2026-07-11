import { createServerClient } from '@supabase/ssr'
import { NextResponse, type NextRequest } from 'next/server'

// Rate limiter simples em memória (reseta a cada restart do server)
const rateLimitMap = new Map<string, { count: number; resetTime: number }>()

function getRateLimit(key: string, limit: number, windowMs: number): boolean {
  const now = Date.now()
  
  // Limpeza sob demanda para evitar vazamento de memória em serverless
  if (rateLimitMap.size > 500) {
    for (const [k, v] of Array.from(rateLimitMap.entries())) {
      if (now > v.resetTime) {
        rateLimitMap.delete(k)
      }
    }
  }

  const record = rateLimitMap.get(key)

  if (!record || now > record.resetTime) {
    rateLimitMap.set(key, { count: 1, resetTime: now + windowMs })
    return true
  }

  if (record.count >= limit) {
    return false
  }

  record.count++
  return true
}

async function isAllowed(key: string, limit: number, windowSeconds: number): Promise<boolean> {
  const url = process.env.UPSTASH_REDIS_REST_URL
  const token = process.env.UPSTASH_REDIS_REST_TOKEN

  if (url && token) {
    try {
      const cleanedUrl = url.endsWith('/') ? url : `${url}/`
      const evalUrl = `${cleanedUrl}eval`

      const luaScript = `
        local current = redis.call('incr', KEYS[1])
        if current == 1 then
          redis.call('expire', KEYS[1], ARGV[1])
        end
        return current
      `

      const res = await fetch(evalUrl, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          script: luaScript,
          args: [windowSeconds.toString()],
          keys: [key]
        }),
        signal: AbortSignal.timeout(2000)
      })

      if (res.ok) {
        const data = await res.json()
        const currentCount = Number(data.result)
        return currentCount <= limit
      }
    } catch (e) {
      console.warn('Erro ao conectar ao Upstash Redis. Fallback para in-memory rate limiting.', e)
    }
  }

  return getRateLimit(key, limit, windowSeconds * 1000)
}

export async function middleware(request: NextRequest) {
  const ip = request.headers.get('x-forwarded-for') || request.headers.get('x-real-ip') || 'unknown'
  const pathname = request.nextUrl.pathname

  // Rate limiting para endpoints de auth
  const authPaths = ['/auth/login', '/auth/registro', '/auth/reset-password', '/api/auth']
  if (authPaths.some(path => pathname.startsWith(path))) {
    const rateLimitKey = `auth:${ip}`
    const allowed = await isAllowed(rateLimitKey, 10, 60)
    if (!allowed) {
      return NextResponse.json(
        { error: 'Muitas tentativas. Tente novamente em 1 minuto.' },
        { status: 429 }
      )
    }
  }

  // Rate limiting para webhook
  if (pathname.startsWith('/api/cakto')) {
    const rateLimitKey = `webhook:${ip}`
    const allowed = await isAllowed(rateLimitKey, 30, 60)
    if (!allowed) {
      return NextResponse.json(
        { error: 'Rate limit exceeded' },
        { status: 429 }
      )
    }
  }

  // Rate limiting para account management
  if (pathname.startsWith('/api/account')) {
    const rateLimitKey = `account:${ip}`
    const allowed = await isAllowed(rateLimitKey, 20, 60)
    if (!allowed) {
      return NextResponse.json(
        { error: 'Muitas tentativas. Tente novamente em 1 minuto.' },
        { status: 429 }
      )
    }
  }

  let supabaseResponse = NextResponse.next({ request })

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll()
        },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value }) =>
            request.cookies.set(name, value)
          )
          supabaseResponse = NextResponse.next({ request })
          cookiesToSet.forEach(({ name, value, options }) =>
            supabaseResponse.cookies.set(name, value, options)
          )
        },
      },
    }
  )

  const {
    data: { user },
  } = await supabase.auth.getUser()

  if (
    !user &&
    (request.nextUrl.pathname.startsWith('/dashboard') ||
      request.nextUrl.pathname.startsWith('/configuracoes'))
  ) {
    const url = request.nextUrl.clone()
    url.pathname = '/auth/login'
    return NextResponse.redirect(url)
  }

  return supabaseResponse
}

export const config = {
  matcher: [
    '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
}
