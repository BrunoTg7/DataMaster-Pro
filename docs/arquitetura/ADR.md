# Decisoes Arquiteturais (ADRs) — DataMaster Pro

Registro das decisoes tecnicas mais importantes e seus contextos.

---

## ADR-001: Python + CustomTkinter para Desktop

**Status:** Aceito  
**Data:** 2024  
**Decisor:** Equipe DataMaster  

### Contexto

Precisavamos de uma tecnologia para criar aplicacao desktop com interface moderna, distribuivel como .exe, sem necessidade de instalacao complexa.

### Decisao

Usar **Python 3.10+** com **CustomTkinter** para a interface GUI.

### Alternativas Consideradas

| Alternativa   | Pro                          | Contra                        |
|---------------|------------------------------|-------------------------------|
| Electron      | Web tech, rica               | 200MB+, memoria alta          |
| PyQt6         | Madura, documentada          | Licenca comercial (GPL/comercial) |
| **CustomTkinter** | leve, sem deps, MIT    | Menos widgets, comunidade menor |
| Tkinter natia | Built-in Python              | UI datada, sem temas modernos |

### Consequencias

- Distribuicao via PyInstaller (~300-500MB com deps)
- Interface moderna com temas dark/light
- Sem custo de licenca
- Comunidade menor que Qt, mas suficiente para o escopo

---

## ADR-002: Next.js 14 + TypeScript para Web

**Status:** Aceito  
**Data:** 2024  
**Decisor:** Equipe DataMaster  

### Contexto

Precisavamos de uma plataforma web para landing page, autenticacao, area de membros e gerenciamento de assinaturas.

### Decisao

Usar **Next.js 14 (App Router)** com **TypeScript** e **Tailwind CSS**.

### Alternativas Consideradas

| Alternativa    | Pro                          | Contra                        |
|----------------|------------------------------|-------------------------------|
| React SPA      | Simples, flexivel            | Sem SSR, SEO limitado         |
| **Next.js 14** | SSR/SSG, SEO, App Router     | Curva de aprendizado          |
| Nuxt.js        | Vue ecosystem                | Menor ecossistema que React   |
| Astro          | Performance extrema          | Menos maduro para apps complexas |

### Consequencias

- Deploy trivial na Vercel
- Server Components + Client Components
- SEO nativo (OpenGraph, sitemap, robots)
- Supabase SSR integration nativa

---

## ADR-003: Supabase como BaaS (Backend as a Service)

**Status:** Aceito  
**Data:** 2024  
**Decisor:** Equipe DataMaster  

### Contexto

Precisavamos de autenticacao, banco de dados relacional, storage e functions server-side sem gerenciar infraestrutura propria.

### Decisao

Usar **Supabase** como backend completo (PostgreSQL + Auth + Edge Functions + Realtime).

### Alternativas Consideradas

| Alternativa    | Pro                          | Contra                        |
|----------------|------------------------------|-------------------------------|
| Firebase       | Madura, Google backing       | NoSQL, vendor lock-in alto    |
| **Supabase**   | PostgreSQL real, open-source | Jovem, features em beta       |
| AWS Amplify     | Escalavel, AWS integration   | Complexidade, custos variaveis |
| Parse Server   | Self-hosted, flexivel        | Manutencao propria            |

### Consequencias

- PostgreSQL real com RLS (Row Level Security)
- Auth com OAuth (Google, email/senha)
- Edge Functions em Deno
- Realtime para sincronizacao
- Risco: dependencia de servico terceiro

---

## ADR-004: SQLite Local + Sync Offline-First

**Status:** Aceito  
**Data:** 2024  
**Decisor:** Equipe DataMaster  

### Contexto

O app desktop precisava funcionar offline, salvando dados localmente e sincronizando quando online.

### Decisao

Usar **SQLite** como banco local com padrao **offline-first**: opera完全 offline, sincroniza quando conectado.

### Alternativas Consideradas

| Alternativa       | Pro                          | Contra                        |
|-------------------|------------------------------|-------------------------------|
| **SQLite**        | Leve, serverless, rapido     | Sem concorrência multi-user   |
| IndexedDB         | Native no browser            | Nao disponivel em desktop     |
| Realm             | Rapido, mobile-ready         | Licenca MongoDB, complexidade |
| PostgreSQL local  | Poderoso                     | Overhead para desktop         |

### Consequencias

- App funciona 100% offline
- Sync queue com retry/backoff
- WAL mode para concorrência leitura
- Backups automaticos com rotação
- Limite: concorrência single-process

---

## ADR-005: PyInstaller para Distribuicao

**Status:** Aceito  
**Data:** 2024  
**Decisor:** Equipe DataMaster  

### Contexto

Precisavamos distribuir o app desktop para usuarios finais sem exigir instalacao de Python ou dependencias.

### Decisao

Usar **PyInstaller** para gerar executavel standalone (.exe).

### Alternativas Consideradas

| Alternativa    | Pro                          | Contra                        |
|----------------|------------------------------|-------------------------------|
| **PyInstaller**| Madura, bem suportada        | Tamanho grande (~300-500MB)   |
| cx_Freeze      | Multiplataforma              | Configuracao mais complexa    |
| Nuitka         | Compilador real, otimizado   | Build lento, bugs ocasionais  |
| py2exe         | Leve                         | Desatualizado, so Windows     |

### Consequencias

- Distribuicao simples: 1 arquivo .exe
- Todas as deps empacotadas (pandas, customtkinter, etc.)
- Tamanho de ~300-500MB aceitavel para desktop
- Instalador customizado com Tkinter + NSIS

---

## ADR-006: Clean Architecture (Domínio/Aplicação/Infraestrutura)

**Status:** Aceito  
**Data:** 2026-06-02  
**Decisor:** Auditoria de Arquitetura  

### Contexto

A arquitetura original tinha GUI acoplada diretamente a logica de negocio, StorageManager como God Class (1177 linhas), e impossibilidade de testar sem GUI.

### Decisao

Implementar **Clean Architecture** com 3 camadas:

```
Domínio (entities, interfaces)
    ↓
Aplicação (use cases, services)
    ↓
Infraestrutura (adapters, container)
```

### Alternativas Consideradas

| Alternativa      | Pro                          | Contra                        |
|------------------|------------------------------|-------------------------------|
| MVC classico     | Simples, maduro              | Acoplamento alto              |
| Hexagonal        | Flexivel                     | Over-engineering para desktop |
| **Clean Arch**   | Testavel, desacoplada        | Mais arquivos, curvalearn     |
| Onion Arch       | Similar a Clean              | Menos documentacao            |

### Consequencias

- GUI depende de interfaces, nao de implementacoes
- Testes de logica de negocio possiveis sem GUI
- Trocar SQLite por outro BD: mudar so adapters
- DI Container para injecao de dependencias
- Plugin System para auto-registro de ferramentas

---

## ADR-007: Plugin System com Auto-Discovery

**Status:** Aceito  
**Data:** 2026-06-02  
**Decisor:** Auditoria de Arquitetura  

### Contexto

Adicionar uma nova ferramenta exigia alterar 5+ arquivos manualmente (tool, page, registry, config, imports).

### Decisao

Implementar **Plugin Registry** com decorator `@plugin` e auto-discovery via `pkgutil`.

### Implementacao

```python
@plugin(key="consolidador", name="Consolidador", page_module="consolidador_page")
class Consolidador(ITool):
    def execute(self, params): ...
```

### Consequencias

- Nova ferramenta: criar arquivo + decorator (2 pontos de alteracao)
- Compatibilidade com registry legado via fallback
- Auto-discovery via `pkgutil.iter_modules()`
- Reducao de 5+ para 2 pontos de alteracao por ferramenta

---

## ADR-008: Circuit Breaker para Serviços Externos

**Status:** Aceito  
**Data:** 2026-06-02  
**Decisor:** Auditoria de Arquitetura  

### Contexto

Chamadas ao Supabase e ScraperAPI podiam falhar em cascata, travando o app inteiro.

### Decisao

Implementar **Circuit Breaker** com estados CLOSED → OPEN → HALF_OPEN.

### Parametros

| Parametro            | Valor  | Descricao                     |
|----------------------|--------|-------------------------------|
| failure_threshold    | 5      | Falhas antes de abrir circuito|
| recovery_timeout     | 60s    | Tempo antes de testar novamente|
| half_open_max_calls  | 1      | Chamadas de teste em HALF_OPEN |

### Consequencias

- Falhas em cascata prevenidas
- Retry interno com backoff exponencial
- Integrado ao SyncManager para upload/download
- Log de estado para monitoramento

---

## ADR-009: FastAPI para API Desktop

**Status:** Aceito  
**Data:** 2026-06-02  
**Decisor:** Equipe DataMaster  

### Contexto

Desktop falava diretamente com Supabase. Precisavamos de uma camada intermediaria para validacao, cache e logging.

### Decisao

Criar **FastAPI** local (localhost:8000) como API intermediaria.

### Endpoints Principais

- `GET /health` — Health check
- `GET /api/users/me` — Usuario atual
- `POST /api/tasks/submit` — Criar tarefa
- `GET /api/stats` — Estatisticas

### Consequencias

- Desacoplamento do Supabase
- Rate limiting local
- JWT auth proprio
- Cache de estatisticas
- Bind em 127.0.0.1 (nao 0.0.0.0)

---

*Documentacao de decisoes arquiteturais. Cada ADR registra o contexto, decisao alternativas consideradas e consequencias.*
