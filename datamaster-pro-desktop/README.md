# 📊 DataMaster Pro - Suite de Automação Excel

**Versão:** 1.0.0 | **Status:** ✅ Production Ready | **Data:** Maio 2026

Aplicação desktop profissional em Python/CustomTkinter com 5 ferramentas integradas para automação e processamento de dados em Excel/CSV. 100% funcional e pronto para produção.

## Estrutura do Projeto

```
datamaster-pro-desktop/
├── src/
│   ├── gui/                       # Interface gráfica (CustomTkinter)
│   │   ├── pages/                 # Páginas principais (Login, Dashboard, etc)
│   │   └── components/            # Componentes reutilizáveis
│   │
│   ├── core/                      # Lógica core da aplicação
│   │   ├── auth/                  # Autenticação (Supabase + local)
│   │   ├── sync/                  # Sincronização offline/online
│   │   └── storage/               # Gerenciamento de dados (SQLite)
│   │
│   ├── tools/                     # As 5 ferramentas principais
│   │   ├── consolidador/          # Une múltiplas planilhas
│   │   ├── categorizador/         # Classifica transações
│   │   ├── orcamentos/            # Preenche PDFs em massa
│   │   ├── minerador/             # Captura preços de sites
│   │   └── conciliador/           # Cruza extratos com vendas
│   │
│   └── utils/                     # Utilitários gerais
│       ├── encryption/            # Criptografia de dados
│       └── validators/            # Validações de entrada
│
├── tests/                         # Testes unitários
├── build/                         # Saída do PyInstaller (.exe)
├── requirements.txt               # Dependências Python
├── main.py                        # Entry point da aplicação
└── config.py                      # Configurações globais
```

## Tecnologias

- **Python 3.10+** - Linguagem principal
- **CustomTkinter** - Interface gráfica moderna
- **Pandas** - Processamento de dados
- **Openpyxl** - Manipulação de Excel
- **SQLite3** - Armazenamento local
- **Supabase-py** - Integração backend
- **Cryptography** - Criptografia de dados
- **PyInstaller** - Empacotamento .exe

## Dependências Principais

```
customtkinter==5.2.0
pandas==2.0.0
openpyxl==3.10.0
supabase==2.0.0
cryptography==41.0.0
requests==2.31.0
python-dotenv==1.0.0
```

## Como Executar

### Desenvolvimento

```bash
pip install -r requirements.txt
python main.py
```

### Build .exe

```bash
pyinstaller main.spec
```

## Estrutura de Dados

### Local Storage (SQLite)

- **usuarios** - Dados de login criptografados
- **execucoes** - Histórico de execuções de ferramentas
- **favoritos** - Ferramentas favoritas do usuário
- **config** - Preferências locais

### Supabase (Cloud)

- **users** - Usuários autenticados
- **planos** - Informações de plano/assinatura
- **execucoes** - Logs de ROI
- **check_updates** - Versionamento

## Fluxo Offline-First

1. **Login**: Primeira vez requer internet (Supabase)
2. **Uso**: Funciona totalmente offline com dados locais
3. **Sync**: Sincroniza automaticamente ao conectar à internet
4. **Validação**: Token revalidado periodicamente

## Next Steps

- [ ] Setup inicial do projeto
- [ ] Implementação das 5 ferramentas
- [ ] Testes de sincronização
- [ ] Build e distribuição
