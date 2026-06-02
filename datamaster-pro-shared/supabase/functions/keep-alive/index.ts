import { serve } from "https://deno.land/std@0.168.0/http/server.ts"

const INTERNAL_URLS = [
  Deno.env.get("SUPABASE_URL")!,
  `${Deno.env.get("SUPABASE_URL")!}/auth/v1/health`,
]

serve(async () => {
  const results: { url: string; status: number }[] = []

  for (const url of INTERNAL_URLS) {
    try {
      const res = await fetch(url, { method: "GET", signal: AbortSignal.timeout(10_000) })
      results.push({ url, status: res.status })
    } catch (e) {
      results.push({ url, status: 0 })
    }
  }

  console.log("Keep-alive executado:", JSON.stringify(results))

  return new Response(JSON.stringify({ status: "ok", ts: new Date().toISOString(), results }), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  })
})
