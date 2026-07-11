import { NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'
import { timingSafeEqual } from 'crypto'

function safeCompare(a: string, b: string): boolean {
  const bufA = Buffer.from(a)
  const bufB = Buffer.from(b)
  if (bufA.length !== bufB.length) return false
  return timingSafeEqual(bufA, bufB)
}

export async function GET(request: Request) {
  const authHeader = request.headers.get('Authorization')
  const secretToken = process.env.HEALTH_CHECK_SECRET

  // Unauthenticated: return static OK with no infra details
  if (!secretToken || !authHeader || !safeCompare(authHeader, `Bearer ${secretToken}`)) {
    return NextResponse.json({ status: 'ok' })
  }

  // Authenticated: full health check
  let dbStatus = 'unknown'
  let dbLatency = 0

  try {
    const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
    const supabase = createClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      supabaseKey
    )
    const dbStart = Date.now()
    const { error } = await supabase.from('usuarios').select('id').limit(1)
    dbLatency = Date.now() - dbStart
    dbStatus = error ? 'error' : 'ok'
  } catch {
    dbStatus = 'error'
  }

  return NextResponse.json({
    status: dbStatus === 'ok' ? 'ok' : 'unhealthy',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    database: {
      status: dbStatus,
      latency_ms: dbLatency,
    },
  })
}
