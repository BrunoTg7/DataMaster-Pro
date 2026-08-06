# Google Auth + Supabase - Configuração e Implementação

## Pré-requisitos (Configuração Manual)

### 1. Google Cloud Console

#### Passo 1: Criar projeto
1. Acesse [console.cloud.google.com](https://console.cloud.google.com/)
2. Clique no seletor de projetos no topo → **Novo Projeto**
3. Nome: `DataMaster Pro` (ou similar) → **Criar**

#### Passo 2: Configurar Tela de Consentimento
1. No menu lateral → **APIs e Serviços** → **Tela de consentimento OAuth**
2. Selecione **Externo** → **Criar**
3. Preencha:
   - **Nome do app**: `DataMaster Pro`
   - **E-mail do suporte**: seu e-mail
   - **E-mail de contato**: seu e-mail
4. Em **Escopos**, adicione:
   - `email`
   - `profile`
   - `openid`
5. Em **Telas de consentimento OAuth**, adicione seu e-mail como **usuário de teste** (enquanto o app estiver em modo "Teste")
6. **Salvar e Continuar**

#### Passo 3: Criar OAuth Client ID (único para Web + Desktop)
1. **APIs e Serviços** → **Credenciais** → **+ Criar Credenciais** → **ID do Cliente OAuth**
2. Tipo: **Aplicativo da Web**
3. Nome: `DataMaster Pro`
4. **URIs de redirecionamento autorizados**, adicione as duas:
   ```
   https://your-project.supabase.co/auth/v1/callback
   http://localhost:8765/callback
   ```
   - A primeira é para o **web** (Supabase redireciona para cá)
   - A segunda é para o **desktop** (app Python captura o code em localhost)
5. **Criar**
6. Anote o **ID do Cliente** e o **Segredo do Cliente**

> **Por que um único client?** O Supabase só permite um provider Google por projeto. Mesmo Client ID funciona para web e desktop porque cada um usa um redirect URI diferente.

---

### 2. Supabase Dashboard

1. Acesse [supabase.com/dashboard](https://supabase.com/dashboard) → seu projeto
2. **Authentication** → **Providers**
3. Busque **Google** → **Habilitar**
4. Cole:
   - **Client ID** (o do Passo 3 acima)
   - **Client Secret** (o do Passo 3 acima)
5. Em **Authentication** → **URL Configuration**:
   - **Site URL**: `https://seu-dominio.com` (se tiver) ou deixe como está
   - **Redirect URLs**: adicione as duas:
     ```
     http://localhost:3000/auth/callback
     http://localhost:8765/callback
     ```

---

### 3. Resumo

| Onde | Configuração |
|---|---|
| **Google Cloud Console** | 1 único Client ID (tipo Web) com 2 redirect URIs |
| **Supabase Dashboard** | 1 provider Google habilitado |
| **`.env` web** | Usa o Client ID e Secret do Google |
| **`.env` desktop** | Usa o **mesmo** Client ID e Secret |

---

## Variáveis de Ambiente

Ambos usam as **mesmas credenciais** do Google Cloud Console.

### Web (`datamaster-pro-web/.env`)
```env
GOOGLE_CLIENT_ID=seu-client-id
GOOGLE_CLIENT_SECRET=seu-client-secret
```

### Desktop (`datamaster-pro-desktop/.env`)
```env
GOOGLE_CLIENT_ID=seu-client-id
GOOGLE_CLIENT_SECRET=seu-client-secret
```

---

## Implementação

### Fluxo Visual

```
WEB:
Usuário clica "Google" → Supabase → Google → Callback → /auth/callback → Dashboard

DESKTOP:
Usuário clica "Google" → Navegador abre → Google → localhost:8765/callback → Supabase → App
```

### Arquivos a modificar/criar

| Arquivo | Ação |
|---|---|
| `datamaster-pro-web/app/auth/callback/route.ts` | **Criar** |
| `datamaster-pro-web/components/auth/AuthForm.tsx` | **Modificar** - adicionar botão Google |
| `supabase/config.toml` | **Modificar** - adicionar Google provider |
| `datamaster-pro-desktop/src/core/auth/auth_manager.py` | **Modificar** - adicionar `login_with_google()` |
| `datamaster-pro-desktop/src/gui/pages/login_page.py` | **Modificar** - adicionar botão Google |

---

### Parte 1: Web (Next.js)

#### 1. Criar callback route → `app/auth/callback/route.ts`

Rota que recebe o `code` do Google via Supabase e troca por sessão.

```typescript
import { NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/client'

export async function GET(request: Request) {
  const { searchParams, origin } = new URL(request.url)
  const code = searchParams.get('code')

  if (code) {
    const supabase = createClient()
    const { error } = await supabase.auth.exchangeCodeForSession(code)
    if (!error) {
      return NextResponse.redirect(`${origin}/dashboard`)
    }
  }

  return NextResponse.redirect(`${origin}/auth/login?error=auth_failed`)
}
```

#### 2. Adicionar botão Google → `components/auth/AuthForm.tsx`

Adicionar botão "Entrar com Google" acima do form, com linha divisória "ou".

```tsx
const handleGoogleLogin = async () => {
  const { error } = await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: {
      redirectTo: `${window.location.origin}/auth/callback`,
    },
  })
  if (error) setError(error.message)
}

// No JSX, adicionar antes do <form>:
<div className="space-y-4">
  <button
    type="button"
    onClick={handleGoogleLogin}
    className="w-full flex items-center justify-center gap-3 px-4 py-3 border border-surface-300 rounded-lg hover:bg-surface-50 transition-colors"
  >
    <svg className="w-5 h-5" viewBox="0 0 24 24">
      <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4"/>
      <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
      <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
      <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
    </svg>
    Continuar com Google
  </button>

  <div className="relative">
    <div className="absolute inset-0 flex items-center">
      <div className="w-full border-t border-surface-200" />
    </div>
    <div className="relative flex justify-center text-sm">
      <span className="px-2 bg-white text-surface-500">ou</span>
    </div>
  </div>
</div>
```

#### 3. Atualizar `supabase/config.toml` (para dev local)

```toml
[auth.external.google]
enabled = true
client_id = "env(SUPABASE_AUTH_GOOGLE_CLIENT_ID)"
secret = "env(SUPABASE_AUTH_GOOGLE_CLIENT_SECRET)"
```

---

### Parte 2: Desktop (Python/CustomTkinter)

#### 1. Adicionar `login_with_google()` → `auth_manager.py`

```python
import threading
import webbrowser
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

class GoogleAuthCallbackHandler(BaseHTTPRequestHandler):
    """Handler para capturar o callback do Google OAuth"""
    auth_code = None

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if "code" in params:
            GoogleAuthCallbackHandler.auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                b"<html><body style='font-family:Inter,sans-serif;text-align:center;padding:50px'>"
                b"<h2>Autenticação concluída!</h2>"
                b"<p>Pode fechar esta janela e voltar para o aplicativo.</p>"
                b"</body></html>"
            )
        elif "error" in params:
            self.send_response(400)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            error_msg = params.get("error_description", ["Erro desconhecido"])[0]
            self.wfile.write(f"<h1>Erro: {error_msg}</h1>".encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # Silenciar logs do servidor

# Método a adicionar na classe AuthManager:
def login_with_google(self) -> Dict:
    """
    Autenticar via Google OAuth usando loopback redirect.
    Abre o navegador do usuário e captura o callback em localhost.
    """
    try:
        from supabase import create_client, Client
        _c: Client = create_client(config._u0, config._r1())

        REDIRECT_PORT = 8765
        REDIRECT_URI = f"http://localhost:{REDIRECT_PORT}/callback"

        # 1. Obter URL do OAuth do Supabase
        response = _c.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {
                "redirect_to": REDIRECT_URI,
            }
        })

        if not response.url:
            return {"success": False, "error": "Falha ao gerar URL do Google"}

        # 2. Limpar code anterior
        GoogleAuthCallbackHandler.auth_code = None

        # 3. Iniciar servidor local em thread separada
        def run_server():
            server = HTTPServer(("localhost", REDIRECT_PORT), GoogleAuthCallbackHandler)
            server.handle_request()
            server.server_close()

        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()

        # 4. Abrir navegador
        webbrowser.open(response.url)

        # 5. Aguardar callback (timeout 120s)
        server_thread.join(timeout=120)

        if GoogleAuthCallbackHandler.auth_code is None:
            return {"success": False, "error": "Tempo esgotado ou autenticação cancelada"}

        # 6. Trocar code por sessão
        session_response = _c.auth.exchange_code_for_session(
            GoogleAuthCallbackHandler.auth_code
        )

        if session_response.user:
            profile = self._ensure_user_profile(
                session_response.user,
                session_response.session.access_token
            )
            user_data = {
                "id": session_response.user.id,
                "email": session_response.user.email,
                "nome": profile.get(
                    "nome",
                    (session_response.user.email or "usuario").split("@")[0]
                ),
                "plan": profile.get("plano_tipo", "gratis"),
                "created_at": profile.get("created_at"),
                "data_expiracao": profile.get("data_expiracao"),
                "notificacoes_email": profile.get("notificacoes_email", True),
                "notificacoes_desktop": profile.get("notificacoes_desktop", True),
                "expires_at": (datetime.now() + timedelta(days=90)).isoformat(),
                "session_token": session_response.session.access_token,
                "refresh_token": session_response.session.refresh_token,
            }
            self.current_user = user_data
            self._session_token = session_response.session.access_token
            self._stored_credentials = {
                "refresh_token": session_response.session.refresh_token
            }
            set_user_id(user_data["id"])
            audit_login(user_data["id"], success=True)
            return {"success": True, "user": user_data}

        return {"success": False, "error": "Falha ao obter sessão do Google"}

    except Exception as e:
        audit_login("google", success=False, error=str(e))
        return {"success": False, "error": str(e)}
```

#### 2. Adicionar botão Google → `login_page.py`

```python
# Adicionar botão após o login_button:
self.google_button = ctk.CTkButton(
    inner_frame,
    text="  Continuar com Google",
    width=320,
    height=45,
    fg_color="#ffffff",
    hover_color="#f5f5f5",
    text_color="#333333",
    font=ctk.CTkFont(family="Inter", size=14),
    corner_radius=8,
    border_width=1,
    border_color="#dadce0",
    command=self._on_google_login,
    image=self._load_google_icon()  # Opcional: ícone do Google
)
self.google_button.pack(pady=(0, 10))

# Separador "ou":
separator = ctk.CTkFrame(inner_frame, fg_color="transparent", height=20)
separator.pack()
or_label = ctk.CTkLabel(
    separator,
    text="ou",
    font=ctk.CTkFont(family="Inter", size=12),
    text_color=config.Colors.TEXT_SECONDARY
)
or_label.pack()

# Método a adicionar na classe LoginPage:
def _on_google_login(self):
    """Iniciar login com Google em thread separada"""
    self.google_button.configure(state="disabled", text="Abrindo navegador...")
    self.status_label.configure(text="")

    def google_auth_thread():
        try:
            result = self.auth_manager.login_with_google()
            if result.get("success"):
                user_data = result.get("user")
                self.storage_manager.save_user_session(user_data)
                self.after(100, lambda: self.on_login_success(user_data))
            else:
                error_msg = result.get("error", "Erro ao autenticar com Google")
                self.after(0, lambda: self.status_label.configure(text=error_msg))
        except Exception as e:
            self.after(0, lambda: self.status_label.configure(text=f"Erro: {str(e)}"))
        finally:
            if self.google_button.winfo_exists():
                self.after(0, lambda: self.google_button.configure(
                    state="normal", text="  Continuar com Google"
                ))

    threading.Thread(target=google_auth_thread, daemon=True).start()
```

---

## Checklist de Configuração

- [ ] Google Cloud Console: Projeto criado
- [ ] Google Cloud Console: Tela de consentimento configurada
- [ ] Google Cloud Console: OAuth Client "Web" criado
- [ ] Google Cloud Console: OAuth Client "Desktop" criado
- [ ] Supabase Dashboard: Provider Google habilitado
- [ ] Supabase Dashboard: Redirect URLs configuradas
- [ ] `.env` web: Variáveis adicionadas
- [ ] `.env` desktop: Variáveis adicionadas
- [ ] Web: `app/auth/callback/route.ts` criado
- [ ] Web: Botão Google adicionado ao AuthForm
- [ ] Desktop: `login_with_google()` adicionado ao AuthManager
- [ ] Desktop: Botão Google adicionado ao LoginPage
- [ ] Teste web: Login com Google funciona
- [ ] Teste desktop: Login com Google funciona
