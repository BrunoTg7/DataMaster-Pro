import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'

function sanitizeString(value: unknown, maxLength: number): string {
  if (typeof value !== 'string') return ''
  return value.trim().slice(0, maxLength)
}

export async function POST(request: NextRequest) {
  const supabase = createClient()

  // Usar getUser() em vez de getSession() para verificacao server-side
  const { data: { user }, error: userError } = await supabase.auth.getUser()
  if (userError || !user) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  // CSRF: verificar Origin header
  const origin = request.headers.get('origin')
  const host = request.headers.get('host')
  if (origin && host && !origin.includes(host)) {
    return NextResponse.json({ error: 'Invalid origin' }, { status: 403 })
  }

  let body: Record<string, unknown>
  try {
    body = await request.json()
  } catch {
    return NextResponse.json({ error: 'Invalid JSON' }, { status: 400 })
  }

  const { necessary, analytics, marketing } = body

  if (typeof necessary !== 'boolean' || typeof analytics !== 'boolean' || typeof marketing !== 'boolean') {
    return NextResponse.json({ error: 'Invalid consent values' }, { status: 400 })
  }

  // Validar que pelo menos necessary esta presente (obrigatorio)
  if (necessary !== true) {
    return NextResponse.json({ error: 'Consentimento necessario e obrigatorio' }, { status: 400 })
  }

  const { error } = await supabase
    .from('consent_logs')
    .insert({
      user_id: user.id,
      necessary,
      analytics,
      marketing,
      ip_address: sanitizeString(request.headers.get('x-forwarded-for') || request.headers.get('x-real-ip'), 45),
      user_agent: sanitizeString(request.headers.get('user-agent'), 500),
    })

  if (error) {
    console.error('Error saving consent:', error)
    return NextResponse.json({ error: 'Failed to save consent' }, { status: 500 })
  }

  return NextResponse.json({ success: true })
}

export async function GET(request: NextRequest) {
  const supabase = createClient()

  // Usar getUser() em vez de getSession()
  const { data: { user }, error: userError } = await supabase.auth.getUser()
  if (userError || !user) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const { data, error } = await supabase
    .from('consent_logs')
    .select('*')
    .eq('user_id', user.id)
    .order('created_at', { ascending: false })
    .limit(1)
    .single()

  if (error && error.code !== 'PGRST116') {
    return NextResponse.json({ error: 'Failed to fetch consent' }, { status: 500 })
  }

  return NextResponse.json({ consent: data || null })
}
