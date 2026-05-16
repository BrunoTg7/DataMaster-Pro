"""
Exemplos de Integração - DataMaster Pro

Como chamar as Supabase Functions e Queries do seu código Python (Desktop) e TypeScript (Web)
"""

# ==================== PYTHON (Desktop) ====================

# Exemplo 1: Validar Acesso a Ferramenta (antes de usar)

from supabase import create_client
import json

supabase = create_client(
"https://your-project.supabase.co",
"your-anon-key"
)

def pode_usar_ferramenta(usuario_id: str, ferramenta: str, linhas: int) -> bool:
"""Verifica se usuário pode usar a ferramenta"""
result = supabase.rpc("validar_acesso_ferramenta", {
"p_usuario_id": usuario_id,
"p_ferramenta": ferramenta,
"p_linhas": linhas
}).execute()

    if result.data:
        return result.data['tem_acesso']
    return False

# Uso:

if pode_usar_ferramenta(user_id, "orcamentos", 100):
print("✅ Pode usar a ferramenta")
else:
print("❌ Acesso negado")

# Exemplo 2: Registrar Execução após processar

def registrar_uso_ferramenta(
usuario_id: str,
ferramenta: str,
linhas_processadas: int,
tempo_ms: int,
arquivo_resultado: str
):
"""Registra execução e calcula ROI"""
result = supabase.rpc("registrar_execucao", {
"p_usuario_id": usuario_id,
"p_ferramenta": ferramenta,
"p_linhas": linhas_processadas,
"p_tempo_ms": tempo_ms,
"p_arquivo": arquivo_resultado
}).execute()

    if result.data:
        tempo_economizado = result.data['tempo_economizado_horas']
        print(f"⏰ Você economizou {tempo_economizado:.1f} horas!")
        return result.data
    return None

# Uso após usar ferramenta:

registrar_uso_ferramenta(
user_id,
"consolidador",
5000,
2500,
"/Users/usuario/Downloads/resultado.xlsx"
)

# Exemplo 3: Sincronizar dados (quando reconecta online)

def sincronizar_usuario_online(usuario_id: str):
"""Marca como sincronizado e processa fila""" # 1. Marca como sincronizado
result = supabase.rpc("sincronizar_usuario", {
"p_usuario_id": usuario_id
}).execute()

    print("✅ Usuário marcado como sincronizado")

    # 2. Chama edge function para processar async
    response = supabase.functions.invoke(
        'sync-background',
        {
            'usuario_id': usuario_id
        }
    )

    print(f"Syncs processadas: {response.json()['syncs_processadas']}")

# Uso no app ao detectar internet:

if internet_conectada():
sincronizar_usuario_online(user_id)

# Exemplo 4: Obter ROI do usuário

def obter_roi(usuario_id: str, dias: int = 30) -> dict:
"""Retorna estatísticas de ROI"""
result = supabase.rpc("calcular_roi", {
"p_usuario_id": usuario_id,
"p_dias": dias
}).execute()

    return result.data

# Uso no dashboard:

roi = obter_roi(user_id, 30)
print(f"""
📊 Seu ROI - Últimos 30 dias:

- Linhas processadas: {roi['total_linhas']}
- Tempo economizado: {roi['total_tempo_economizado_horas']:.1f} horas
- Execuções: {roi['execucoes']}
  """)

# Exemplo 5: Obter histórico de execuções

def obter_historico(usuario_id: str, limite: int = 10):
"""Retorna últimas execuções"""
result = supabase.table("execucoes").select(
"\*"
).eq("usuario_id", usuario_id).order(
"created_at", desc=True
).limit(limite).execute()

    return result.data

# Uso:

historico = obter_historico(user_id, 5)
for exec in historico:
print(f"- {exec['ferramenta']}: {exec['linhas_processadas']} linhas")

# Exemplo 6: Obter ferramentas favoritas

def obter_favoritos(usuario_id: str):
"""Retorna ferramentas favoritas"""
result = supabase.table("favoritos").select(
"\*"
).eq("usuario_id", usuario_id).order(
"ordem"
).execute()

    return [f['ferramenta'] for f in result.data]

# Uso no dashboard:

favoritos = obter_favoritos(user_id)
print(f"Seus favoritos: {', '.join(favoritos)}")

# Exemplo 7: Adicionar/Remover favorito

def adicionar_favorito(usuario_id: str, ferramenta: str, ordem: int = 0):
"""Adiciona ferramenta aos favoritos"""
supabase.table("favoritos").insert({
"usuario_id": usuario_id,
"ferramenta": ferramenta,
"ordem": ordem
}).execute()

def remover_favorito(usuario_id: str, ferramenta: str):
"""Remove favorito"""
supabase.table("favoritos").delete().eq(
"usuario_id", usuario_id
).eq("ferramenta", ferramenta).execute()

# Uso:

adicionar_favorito(user_id, "consolidador", 0)
remover_favorito(user_id, "minerador")

# ==================== TYPESCRIPT/JAVASCRIPT (Web) ====================

// Exemplo 1: Validar Acesso (antes de mostrar ferramenta)
async function podeUsarFerramenta(
usuarioId: string,
ferramenta: string,
linhas: number
): Promise<boolean> {
const supabase = useSupabaseClient()

const { data, error } = await supabase.rpc(
'validar_acesso_ferramenta',
{
p_usuario_id: usuarioId,
p_ferramenta: ferramenta,
p_linhas: linhas
}
)

if (error) console.error('Erro:', error)
return data?.tem_acesso ?? false
}

// Uso em componente:
const [temAcesso, setTemAcesso] = useState(false)

useEffect(() => {
podeUsarFerramenta(userId, 'orcamentos', 100)
.then(setTemAcesso)
}, [userId])

if (!temAcesso) {
return <UpgradePrompt plano="pro" />
}

// Exemplo 2: Registrar Execução (após processar no desktop)
async function registrarExecucao(
usuarioId: string,
ferramenta: string,
linhasProcessadas: number,
tempoMs: number,
arquivoResultado: string
) {
const supabase = useSupabaseClient()

const { data, error } = await supabase.rpc(
'registrar_execucao',
{
p_usuario_id: usuarioId,
p_ferramenta: ferramenta,
p_linhas: linhasProcessadas,
p_tempo_ms: tempoMs,
p_arquivo: arquivoResultado
}
)

if (data) {
// Mostrar notificação de sucesso
toast.success(
`Parabéns! Você economizou ${data.tempo_economizado_horas.toFixed(1)} horas!`
)
}

return data
}

// Uso (chamado pelo desktop via API):
const response = await fetch('/api/execucao', {
method: 'POST',
body: JSON.stringify({
usuarioId,
ferramenta,
linhasProcessadas,
tempoMs,
arquivoResultado
})
})

// Exemplo 3: Obter ROI para Dashboard
async function obterROI(
usuarioId: string,
dias: number = 30
): Promise<ROI> {
const supabase = useSupabaseClient()

const { data } = await supabase.rpc(
'calcular_roi',
{
p_usuario_id: usuarioId,
p_dias: dias
}
)

return data
}

// Uso em Dashboard:
export function DashboardROI() {
const { user } = useAuth()
const [roi, setRoi] = useState(null)

useEffect(() => {
obterROI(user.id)
.then(setRoi)
}, [user.id])

if (!roi) return <Skeleton />

return (
<div className="grid grid-cols-3 gap-4">
<Card>
<CardTitle>Linhas Processadas</CardTitle>
<CardValue>{roi.total_linhas}</CardValue>
</Card>
<Card>
<CardTitle>Tempo Economizado</CardTitle>
<CardValue>{roi.total_tempo_economizado_horas.toFixed(1)}h</CardValue>
</Card>
<Card>
<CardTitle>Execuções</CardTitle>
<CardValue>{roi.execucoes}</CardValue>
</Card>
</div>
)
}

// Exemplo 4: Obter Histórico de Execuções
async function obterHistorico(
usuarioId: string,
limite: number = 10
): Promise<Execution[]> {
const supabase = useSupabaseClient()

const { data } = await supabase
.from('execucoes')
.select('\*')
.eq('usuario_id', usuarioId)
.order('created_at', { ascending: false })
.limit(limite)

return data
}

// Uso:
export function ExecutionHistory() {
const { user } = useAuth()
const { data: executions } = useQuery(
['executions', user.id],
() => obterHistorico(user.id)
)

return (
<table>
<tbody>
{executions?.map(exec => (
<tr key={exec.id}>
<td>{exec.ferramenta}</td>
<td>{exec.linhas_processadas} linhas</td>
<td>{exec.tempo_economizado_minutos} min</td>
<td>{new Date(exec.created_at).toLocaleDateString()}</td>
</tr>
))}
</tbody>
</table>
)
}

// Exemplo 5: Processar Upgrade (Webhook Cakto)
// Isso é chamado automaticamente pelo webhook
// Mas você pode testar com:

async function testarWebhookCakto() {
const response = await fetch(
'https://your-project.supabase.co/functions/v1/cakto-webhook',
{
method: 'POST',
headers: {
'x-cakto-token': process.env.CAKTO_WEBHOOK_SECRET,
'Content-Type': 'application/json'
},
body: JSON.stringify({
event: 'purchase.completed',
data: {
email: 'user@example.com',
plan: 'pro',
expiration_date: '2026-05-06'
}
})
}
)

return response.json()
}

// Exemplo 6: Enviar Email Customizado
async function enfileirarEmail(
usuarioId: string,
tipoEmail: string,
destinatario: string,
assunto: string
) {
const supabase = useSupabaseClient()

const { data } = await supabase.rpc(
'enfileirar_email',
{
p_usuario_id: usuarioId,
p_tipo_email: tipoEmail,
p_destinatario: destinatario,
p_assunto: assunto
}
)

// Chamar edge function para enviar
if (data?.email_id) {
await supabase.functions.invoke('send-email', {
body: {
email_id: data.email_id,
tipo_email: tipoEmail,
destinatario: destinatario,
variaveisTemplate: {
month: 'Maio 2026',
executions: '15',
lines: '5000',
time_saved: '42'
}
}
})
}
}

// Uso (admin):
await enfileirarEmail(
userId,
'roi_report',
'usuario@example.com',
'Seu Relatório de ROI'
)

// Exemplo 7: Real-time Updates (opcional, usando Realtime)
export function LiveExecutions() {
const { user } = useAuth()
const supabase = useSupabaseClient()
const [executions, setExecutions] = useState([])

useEffect(() => {
// Subscribe a mudanças em tempo real
const channel = supabase
.channel(`execucoes:${user.id}`)
.on(
'postgres_changes',
{
event: 'INSERT',
schema: 'public',
table: 'execucoes',
filter: `usuario_id=eq.${user.id}`
},
payload => {
setExecutions(prev => [payload.new, ...prev])
}
)
.subscribe()

    return () => {
      supabase.removeChannel(channel)
    }

}, [user.id])

return <ExecutionList executions={executions} />
}

// ==================== API ROUTE EXAMPLE (Next.js) ====================

// pages/api/execucao.ts
import type { NextApiRequest, NextApiResponse } from 'next'
import { createServerSupabaseClient } from '@supabase/auth-helpers-nextjs'

export default async function handler(
req: NextApiRequest,
res: NextApiResponse
) {
if (req.method !== 'POST') {
return res.status(405).json({ error: 'Method not allowed' })
}

const supabase = createServerSupabaseClient({ req, res })
const { data: { session } } = await supabase.auth.getSession()

if (!session) {
return res.status(401).json({ error: 'Not authenticated' })
}

const {
ferramenta,
linhasProcessadas,
tempoMs,
arquivoResultado
} = req.body

const { data, error } = await supabase.rpc(
'registrar_execucao',
{
p_usuario_id: session.user.id,
p_ferramenta: ferramenta,
p_linhas: linhasProcessadas,
p_tempo_ms: tempoMs,
p_arquivo: arquivoResultado
}
)

if (error) {
return res.status(400).json({ error: error.message })
}

return res.status(200).json({ data })
}

# ==================== RESUMO DE CHAMADAS ====================

"""
PYTHON (Desktop):

- supabase.rpc('função_name', params) → Chama SQL Function
- supabase.table('tabela').select() → Query
- supabase.functions.invoke('edge_function') → Chama Edge Function

TYPESCRIPT (Web):

- supabase.rpc('função_name', params) → Chama SQL Function
- supabase.from('tabela').select() → Query
- supabase.functions.invoke('edge_function') → Chama Edge Function

Ambos usam autenticação via JWT (gerado pelo Supabase Auth)
"""
