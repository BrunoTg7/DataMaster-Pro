📊 DataMaster Pro - Estrutura da Interface & Regras de Negócio

Este documento detalha a arquitetura visual, o fluxo do usuário e as integrações técnicas do software DataMaster Pro. O design segue uma estética Modern Dark com foco em usabilidade profissional.

1. Fluxo de Navegação e Integração Supabase

O software utiliza o Supabase como backend para gerenciamento de usuários e telemetria, operando em uma estrutura de Single Page Application (SPA).

Tela de Login/Ativação: Autenticação via Supabase Auth.

Dashboard Principal: Seleção das ferramentas baseada no plano ativo.

Tela da Ferramenta: Upload de arquivos e execução local.

Página de Planos: Gestão de assinatura e logs de uso.

🔐 Autenticação e Persistência Offline

Login Inicial: Requer conexão com a internet para validar as credenciais no Supabase.

Persistência Local: Após o login bem-sucedido, o token de sessão, a data de expiração e o nível do plano são criptografados e salvos localmente no diretório do usuário (usando a biblioteca cryptography).

Modo Offline: O usuário pode abrir a ferramenta sem internet; o software descriptografa os dados locais para permitir o uso. A revalidação online ocorre silenciosamente sempre que houver conexão detectada.

2. Detalhamento das Ferramentas (Páginas Internas)

Cada ferramenta possui uma página dedicada com interface de "arrastar e soltar" (Drag & Drop):

Conciliador:

Função: Cruza extratos (OFX/CSV) com planilhas de vendas para achar divergências de centavos.

Na Página: Área de upload para dois arquivos e botão "Conciliar".

Orçamentos:

Função: Preenche templates de PDF em massa (ex: 500 orçamentos em 10 segundos).

Na Página: Seleção de template PDF e upload da base de dados (Excel/CSV).

Minerador:

Função: Captura preços de sites concorrentes através de links fornecidos.

Na Página: Campo para colar links ou subir lista de produtos; botão "Iniciar Captura".

Categorizador:

Função: Classifica transações por palavras-chave (ex: "Posto Shell" -> "Combustível").

Na Página: Upload da lista suja e seleção do dicionário de categorias.

Consolidador:

Função: Une múltiplas planilhas diferentes em uma estrutura única e limpa.

Na Página: Seletor de pasta (processa todos os arquivos dentro) e botão "Unificar".

3. Modelo de Planos (Assinatura Mensal)

Recurso

🆓 Grátis (Trial)

💎 Pro (Mensal)

🏢 Enterprise (Mensal)

Preço Estimado

R$ 0,00

R$ 29,90 /mês

R$ 99,90 /mês

Acesso

2 Ferramentas (Consolidador/Cat)

Todas as 5

Todas + Customizadas

Linhas

Máx. 10 por execução

Ilimitado

Ilimitado

Marca d'água

Sim

Não

Não

Logs/ROI

Simples local

Detalhado localmente

Histórico completo local

Suporte

FAQ Online

E-mail (Até 48h)

E-mail Prioritário (Até 12h)

4. Estrutura das Páginas Externas

💰 Página de Vendas (Landing Page)

Hero Section: "Economize 20h de trabalho manual por mês com um clique."

Grade de Planos: Foco na recorrência mensal para facilitar o acesso.

Botão de Ação: Checkout da Cakto configurado para Assinatura (Recorrência).

📥 Central de Download e Atualização (Pós-Venda)

Dashboard de Licença: Exibe "Sua assinatura vence em X dias".

Download Center: Acesso à versão mais recente do .exe.

Botão de Suporte: Link direto para o e-mail de suporte.

5. Lógica de Atualização e Telemetria no PC

Verificação de Versão: Consulta check_updates no Supabase ao iniciar.

Logs de ROI: Armazenados em banco local (SQLite) criptografado.

Validação de Assinatura: O software verifica localmente se a data de expiração (vinda do Supabase) ainda é válida; caso expire e esteja offline, solicita conexão para renovar o token.

6. Especificações de UI (Design System)

Fundo: #0F172A | Destaque: #10B981 (Verde Excel).

Indicador de Status: LED no rodapé (Verde = Assinatura Ativa | Vermelho = Assinatura Expirada).
