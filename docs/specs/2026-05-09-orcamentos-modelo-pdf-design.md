# Design: Modelo de Orçamento PDF com Configuração Personalizável

## Visão Geral

Sistema para geração de orçamentos em PDF com layout pré-definido, onde usuários Pro/Enterprise podem configurar quais campos aparecem no modelo.

## Modelo Base PDF

### Campos disponíveis:
1. **Logo** - Imagem carregada pelo usuário
2. **Dados da empresa** - Nome, endereço, telefone, email
3. **Dados do cliente** - Nome, telefone, email
4. **Data do orçamento**
5. **Itens** - Tabela com produto, quantidade, preço unitário, total
6. **Total geral**
7. **Validade do orçamento**
8. **Condições de pagamento**
9. **Observações**
10. **Rodapé**

### Marca d'água:
- **Grátis**: Texto "DataMaster Pro" diagonal no centro
- **Pro/Enterprise**: Sem marca d'água

## Sistema de Configuração

### Acesso:
- Apenas usuários com plano Pro ou Enterprise
- Usuários grátis veem mensagem para upgrade

### Interface:
- Lista de campos com toggle (ativar/desativar)
- Preview simples (texto mostrando campos ativos)
- Campos salvos no perfil do usuário (tabela usuarios)

### Dados armazenados:
- `orcamento_config` JSON na tabela usuarios:
```json
{
  "logo_path": "/path/to/logo.png",
  "empresa_nome": "Minha Empresa",
  "empresa_endereco": "Rua X, 123",
  "empresa_telefone": "(11) 99999-9999",
  "empresa_email": "email@empresa.com",
  "campos_ativos": ["logo", "empresa", "cliente", "data", "itens", "total", "validade", "pagamento", "observacoes", "rodape"],
  "watermark_text": "DataMaster Pro",
  "observacoes_default": "Orçamento válido por 30 dias."
}
```

## Fluxo de Uso

1. Usuário acessa ferramenta Orçamentos
2. Se Pro/Enterprise: acessa "Configurar Modelo" para ajustar campos
3. Carrega arquivo Excel com dados dos clientes
4. Sistema gera PDF aplicando config do usuário
5. PDF final inclui/watermark conforme plano

## Dados do Cliente (vindos do Excel)

O arquivo Excel deve conter colunas para:
- nome_cliente
- telefone_cliente
- email_cliente
- data (opcional, usa data atual se não tiver)
- itens (formato: "Produto|Quantidade|Preço" uma linha por item)
- validade_dias
- condicoes_pagamento
- observacoes

## Implementação

### Arquivos a criar/modificar:
1. `src/tools/orcamentos/orcamentos.py` - adicionar geração de PDF com marca d'água
2. `src/gui/pages/tools/orcamentos_page.py` - adicionar UI de configuração
3. Modificar tabela usuarios no banco/adicionar storage local para config

### Prioridades:
1. Marca d'água automática (grátis)
2. UI de configuração (Pro/Enterprise)
3. Suporte a logo e dados da empresa