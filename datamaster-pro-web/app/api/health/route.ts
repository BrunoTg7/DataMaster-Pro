import { NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

export async function GET() {
  const start = Date.now()

  let dbStatus = 'unknown'
  let dbLatency = 0

  try {
    const supabase = createClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.SUPABASE_SERVICE_ROLE_KEY!
    )
    const dbStart = Date.now()
    const { error } = await supabase.from('usuarios').select('id').limit(1)
    dbLatency = Date.now() - dbStart
    dbStatus = error ? 'error' : 'ok'
  } catch {
    dbStatus = 'error'
  }

  return NextResponse.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    database: {
      status: dbStatus,
      latency_ms: dbLatency,
    },
  })
}
