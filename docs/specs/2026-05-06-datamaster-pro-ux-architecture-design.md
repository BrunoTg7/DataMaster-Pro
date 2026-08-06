# DataMaster Pro - UX Architecture & Navigation Design (Fase 1)

**Date:** 2026-05-06  
**Status:** Design Approved  
**Scope:** Navigation architecture, Dashboard UX, Online/Offline flows, User feedback

---

## 1. Executive Summary

DataMaster Pro adota uma **arquitetura de navegação Hybrid com Favoritos** que balanceia simplicidade (descoberta gradual) com poder (acesso rápido a múltiplas ferramentas). O design prioriza:

- **Descoberta por tentativa:** usuários veem todas as 5 ferramentas, descobrem limites de plano ao usar
- **Crescimento natural:** começam com 2-3 favoritos, adicionam conforme usam mais
- **Offline-first:** funcionalidade completa mesmo sem internet, sincronização silenciosa ao reconectar
- **Clareza de status:** LED visual + notificações em toast para manter usuário informado

---

## 2. Navigation Architecture

### 2.1 Fluxo Principal (Happy Path)

```
┌─────────────────┐
│  Tela de Login  │ (Supabase Auth)
└────────┬────────┘
         │
         ↓
┌──────────────────────────────┐
│   Dashboard Principal         │ (Hybrid com Favoritos)
│  ┌─ Favoritos (2-3)          │
│  └─ Tab: Todas Ferramentas   │
└────────┬─────────────────────┘
         │ (clica em uma ferramenta)
         ↓
┌──────────────────────────────┐
│  Página da Ferramenta        │
│  ┌─ Upload/Input de Dados    │
│  ├─ Configurações específicas│
│  └─ Botão "Executar"        │
└────────┬─────────────────────┘
         │ (executa)
         ↓
┌──────────────────────────────┐
│  Resultado & Histórico       │
│  ├─ Download resultado       │
│  ├─ Ver histórico de uso     │
│  └─ Botão "Voltar ao...      │
└──────────────────────────────┘
```

### 2.2 Fluxo Offline → Online

```
Usuario OFFLINE                Usuario ONLINE
├─ LED: Laranja              ├─ LED: Verde
├─ Badge "Offline"            ├─ Sem badge
├─ Dados do SQLite Local      ├─ Sincronização automática silenciosa
├─ Funcionalidade completa    │   (compara local vs Supabase)
│  (sem requisições)          │
└─ Fila local de execuções   └─ Toast: "Dados sincronizados"

Retorno à Conexão:
1. Sistema detecta internet
2. Sincroniza fila local → Supabase (background)
3. Toast curto: "Dados sincronizados" (não intrusivo)
4. LED muda para Verde
```

### 2.3 Estados de Acesso a Ferramentas

| Estado         | Plano Grátis                                       | Plano Pro    | Plano Enterprise     |
| -------------- | -------------------------------------------------- | ------------ | -------------------- |
| **Disponível** | Consolidador, Categorizador                        | Todas 5      | Todas + Customizadas |
| **Visual**     | Cards ativos                                       | Cards ativos | Cards ativos         |
| **Bloqueado**  | 3 ferramentas (Orçamentos, Minerador, Conciliador) | Nenhuma      | Nenhuma              |
| **Indicador**  | Lock icon + "Upgrade para usar"                    | -            | -                    |

**Descoberta:** Usuário vê todas, mas ao tentar usar ferramenta bloqueada, recebe modal "Essa ferramenta está disponível no plano Pro. Upgrade agora?" com botão direto para planos.

---

## 3. Dashboard Principal (Hybrid)

### 3.1 Layout Geral

```
┌────────────────────────────────────────────────┐
│ HEADER                                          │
│ Logo DataMaster Pro  │  User: João Silva       │
│                      │  Plano: Pro (até 15/12) │
│                      │  ⚙️ Settings             │
├────────────────────────────────────────────────┤
│ FAVORITOS (2-3 cards grandes)                  │
│ ┌──────────────────┐ ┌──────────────────┐      │
│ │ Consolidador    │ │ Categorizador    │      │
│ │ Última: Hoje 14h│ │ Última: Ontem 10h│      │
│ │ [Abrir]         │ │ [Abrir]          │      │
│ └──────────────────┘ └──────────────────┘      │
│ [+ Adicionar Favorito]                         │
├────────────────────────────────────────────────┤
│ TAB: Todas as Ferramentas (collapse/expand)   │
│ Orçamentos | Minerador | Conciliador | ...    │
├────────────────────────────────────────────────┤
│ FOOTER                                         │
│ 🟢 Conectado | Última sync: 5 min atrás        │
└────────────────────────────────────────────────┘
```

### 3.2 Cards de Ferramentas

Cada card exibe:

- **Nome da ferramenta** (ex: "Consolidador")
- **Descrição curta** (ex: "Une múltiplas planilhas")
- **Timestamp da última execução** (ex: "Última: Hoje 14:30")
- **Status do plano** (verde = OK, laranja = Upgrade necessário, cinza = bloqueado)
- **Botão primário** ([Abrir] ou [Upgrade])

Exemplo card desabilitado:

```
┌────────────────────────────┐
│ 🔒 Minerador              │ (ícone lock)
│ Captura preços de sites   │
│ Sem acesso neste plano    │
│ [Upgrade Pro +R$ 29/mês]  │
└────────────────────────────┘
```

### 3.3 Modal de Favoritos

Ao clicar "[+ Adicionar Favorito]" ou botão "Customizar Favoritos":

```
┌──────────────────────────────────────┐
│ Selecione suas Ferramentas Favoritas │
│ (máx 3)                              │
├──────────────────────────────────────┤
│ ☑ Consolidador                       │
│ ☑ Categorizador                      │
│ ☐ Orçamentos                         │
│ ☐ Minerador                          │
│ ☐ Conciliador                        │
├──────────────────────────────────────┤
│ [Cancelar]  [Salvar Preferências]   │
└──────────────────────────────────────┘
```

Preferências salvas localmente (criptografadas no SQLite).

---

## 4. Header & Navigation

### 4.1 Header

**Left Side (Logo):**

- Logo DataMaster Pro (link para voltar ao dashboard)

**Right Side (User Info & Settings):**

- Nome do usuário + Avatar
- Plano ativo: "🟢 Pro | Válido até 15/12/2026"
- Botão ⚙️ Settings

**Dropdown Settings:**

- Preferências (tema, idioma, pasta padrão de download)
- Logs de uso & ROI
- Sobre & Versão
- Logout

### 4.2 Breadcrumb (em páginas de ferramentas)

Dashboard > [Nome da Ferramenta] | [Botão Voltar]

---

## 5. Footer Status Bar

### 5.1 Componentes

```
┌─────────────────────────────────────┐
│ 🟢 Conectado | Última sync: 5 min   │
└─────────────────────────────────────┘
```

**Online (Conectado):**

- LED: 🟢 Verde
- Texto: "Conectado"
- Timestamp: "Última sync: X min atrás"

**Offline (Dados Locais):**

- LED: 🟠 Laranja
- Badge: "⚠️ OFFLINE"
- Texto: "Usando dados locais"

### 5.2 Sincronização em Background

Quando volta à conexão:

1. Sistema detecta internet automaticamente
2. Compara fila local com estado no Supabase
3. Sincroniza dados (background, sem bloquear UI)
4. **Toast notification:** "✅ Dados sincronizados com sucesso"
   - Duração: 3 segundos
   - Posição: Bottom-right
   - Não intrusivo, não bloqueia interações

---

## 6. Data Flow & Persistence

### 6.1 Login & Credenciais

1. **Primeiro login:** Autenticação online no Supabase
2. **Local storage:** Token de sessão + data de expiração + nível de plano (criptografados com biblioteca `cryptography`)
3. **Revalidação silenciosa:** Quando online, sistema valida token periodicamente (a cada 15 min)
4. **Token expirado:** Se offline com token expirado, aviso ao reconectar

### 6.2 Dados de Uso & Histórico

Todas as execuções são registradas localmente:

- **Ferramenta usada**
- **Timestamp**
- **Linhas processadas**
- **Tempo de execução**
- **Resultado (arquivo processado)**

Armazenados em SQLite local + sincronizados com Supabase quando online para analytics.

### 6.3 Sincronização Offline → Online

```
┌─ Fila Local (SQLite)        ┌─ Supabase
│ Execução 1                  │ Tabela: execucoes
│ Execução 2                  │ Tabela: usuarios
│ Execução 3                  │ Tabela: analytics
└─┬────────────────────────────└─┬──
  │ (ao reconectar)              │
  ├─ Compara estado local x remote
  ├─ Valida conflitos (unlikely mas handled)
  ├─ Upload de dados faltantes
  └─ LED muda para Verde
```

**Conflito hipotético:** Se usuário estava offline com Plano Grátis e fez execução de 100 linhas (que seria bloqueada em Grátis), ao sincronizar o sistema detecta e notifica ("Execução bloqueada por plano").

---

## 7. Error Handling & Edge Cases

### 7.1 Rede Intermitente

- Sistema tenta reconectar a cada 30 segundos
- LED permanece laranja até confirmar conexão estável
- Sem "connection lost" toast (muito intrusivo)
- Ao restaurar: notificação discreta

### 7.2 Token Expirado Offline

- Aviso ao reconectar: "Sua sessão expirou. Faça login novamente"
- Modal de re-login
- Dados locais preservados (não apagados)

### 7.3 Sincronização com Conflito

- **Muito raro:** sistema usa last-write-wins para execuções
- **Logs preservados:** todas as execuções registradas mesmo com conflito
- **Notificação:** Toast subtil: "⚠️ Detectamos sobreposição de dados. Verifique o histórico"

---

## 8. Visual Design System (Existing)

- **Fundo:** #0F172A (Escuro Moderno)
- **Cards:** #1E293B com bordas de 1px em #334155
- **Destaque:** #10B981 (Verde Esmeralda - ações primárias)
- **Alerta:** #F59E0B (Amarelo - avisos, limites de plano)
- **Texto primário:** #F1F5F9
- **Texto secundário:** #94A3B8
- **LED Online:** #10B981 (Verde)
- **LED Offline:** #F59E0B (Laranja)

---

## 9. Pages de Ferramentas (Individual)

Cada ferramenta segue este template:

```
┌─ Breadcrumb: Dashboard > [Nome] | [Voltar]
├─ Título & Descrição
├─ Área de Upload/Input (Drag & Drop)
├─ Configurações específicas por ferramenta
├─ Botão "Executar" (destaque verde)
│
│ (durante execução)
├─ Progresso visual (barra ou animação)
│
│ (após execução)
├─ Resultado
├─ Opção Download
├─ Histórico de execuções dessa ferramenta
└─ [Voltar ao Dashboard]
```

---

## 10. Página de Planos

Acessível via link no header/footer e também na landing page.

- Status atual do plano
- Data de renovação
- Contador de uso (ex: "3 de 100 execuções este mês")
- Botão "Upgrade para Pro" ou "Renovar"
- Histórico de pagamentos
- Suporte por e-mail

---

## 11. Success Criteria

✅ **Usuário consegue identificar:**

- Qual é o plano ativo
- Quais ferramentas estão disponíveis vs bloqueadas
- Status online/offline da aplicação

✅ **Experiência offline:**

- Funciona sem internet
- Sincroniza silenciosamente ao reconectar
- Histórico de uso está disponível

✅ **Onboarding:**

- Usuário novo consegue usar ao menos 1 ferramenta em < 2 minutos
- Crescimento natural: conforme usa mais, customiza favoritos

✅ **Feedback visual:**

- Toast de sincronização é discreto, não intrusivo
- LED de status é sempre visível
- Erros são claros (não genéricos)

---

## 12. Próximos Passos (Fase 2 & 3)

**Fase 2: Monetização & Estratégia de Planos**

- Refinar modelo de precificação
- Validar limites por plano (linhas, ferramentas)
- Estratégia de upsell dentro da app

**Fase 3: Desafios Técnicos**

- Implementação offline-first (SyncAdapter pattern)
- Segurança de dados criptografados
- Testes de sincronização

---

## Aprovação

- ✅ Design refinado aprovado pelo time
- ⏳ Aguardando aprovação final para início de Fase 2 (Monetização)
