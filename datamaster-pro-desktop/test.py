import pandas as pd
import os

# Criar pasta de testes
folder = "Testes_DataMaster"
if not os.path.exists(folder):
    os.makedirs(folder)

# 1. CONCILIADOR (Vendas vs Banco)
vendas = pd.DataFrame({
    'ID_Venda': [f'V{i:03}' for i in range(1, 51)],
    'Data': ['08/05/2026'] * 50,
    'Valor_Esperado': [100.00 + i for i in range(50)],
    'Cliente': [f'Cliente {i}' for i in range(50)]
})
vendas.to_excel(f"{folder}/vendas_sistema.xlsx", index=False)

banco = pd.DataFrame({
    'Data_Transacao': ['08/05/2026'] * 50,
    'Descricao': [f'PIX RECEBIDO CLIENTE {i}' for i in range(50)],
    'Valor_Recebido': [100.00 + i if i != 15 else 95.00 for i in range(50)] # Erro na linha 15
})
banco.to_csv(f"{folder}/extrato_bancario.csv", index=False)

# 2. ORÇAMENTOS (Base para PDF)
orcamentos = pd.DataFrame({
    'Nome_Cliente': [f'Empresa {i} Ltda' for i in range(1, 51)],
    'CPF_CNPJ': [f'00.000.000/0001-{i:02}' for i in range(1, 51)],
    'Endereco': [f'Rua Teste, {i}, Itabaiana-SE' for i in range(1, 51)],
    'Item_Servico': ['Consultoria Tech' for _ in range(50)],
    'Quantidade': [1] * 50,
    'Preco_Unitario': [1500.00 for _ in range(50)],
    'Email_Envio': [f'cliente{i}@teste.com' for i in range(50)]
})
orcamentos.to_excel(f"{folder}/base_orcamentos.xlsx", index=False)

# 3. MINERADOR (Links de Exemplo)
minerador = pd.DataFrame({
    'Produto': [f'Produto Tech {i}' for i in range(1, 51)],
    'Link_Concorrente_A': ['https://www.google.com/search?q=iphone' for _ in range(50)],
    'Preco_Atual_A': [0.0] * 50,
    'Link_Concorrente_B': ['https://www.google.com/search?q=macbook' for _ in range(50)],
    'Preco_Atual_B': [0.0] * 50
})
minerador.to_excel(f"{folder}/links_mineracao.xlsx", index=False)

# 4. CATEGORIZADOR (Dados Sujos)
descricoes = ['POSTO SHELL', 'MERCADO PEIXOTO', 'APPLE STORE', 'RESTAURANTE BOA VISTA', 'AMAZON AWS'] * 10
categorias = pd.DataFrame({
    'Descricao_Transacao': descricoes,
    'Valor': [50.0 * i for i in range(1, 51)],
    'Categoria_Sugerida': [''] * 50
})
categorias.to_excel(f"{folder}/dados_para_categorizar.xlsx", index=False)

# 5. CONSOLIDADOR (3 arquivos separados)
for mes in ['Jan', 'Fev', 'Mar']:
    df_mes = pd.DataFrame({
        'Vendedor': ['Bruno', 'Anthony', 'Felipe', 'Cesar', 'Reinan'] * 10,
        'Data_Venda': [f'01/{mes}/2026'] * 50,
        'Produto': ['SaaS Pro'] * 50,
        'Total_Venda': [500.00 for _ in range(50)]
    })
    df_mes.to_excel(f"{folder}/vendas_{mes}.xlsx", index=False)

print(f"✅ Sucesso! As 5 planilhas foram criadas na pasta '{folder}'.")