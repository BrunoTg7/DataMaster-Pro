# 📦 GUIA DE INSTALAÇÃO - DataMaster Pro

## 🚀 Instalação Rápida (Recomendado)

### Passo 1: Requisitos do Sistema

- **Windows:** 10 ou 11 (64-bit)
- **RAM:** Mínimo 2GB
- **Espaço:** 500MB livres
- **Privilégios:** Administrador (para instalação)

### Passo 2: Download

- Baixe: **`DataMaster Pro Setup.exe`** (210 MB)

### Passo 3: Instalação

1. Execute `DataMaster Pro Setup.exe` com duplo clique
2. Clique em "Avançar" na tela de boas-vindas
3. Escolha pasta de instalação (padrão: `C:\Program Files\DataMaster Pro`)
4. Clique "Instalar"
5. Aguarde conclusão (2-3 minutos)
6. Clique "Concluir"

### Passo 4: Primeiro Uso

- Clique no atalho da Área de Trabalho, ou
- Menu Iniciar → DataMaster Pro → DataMaster Pro

---

## 🔧 Instalação Manual

Se preferir não usar o instalador NSIS:

### 1. Crie a pasta

```powershell
mkdir "C:\DataMaster Pro"
```

### 2. Copie o executável

```powershell
Copy-Item "DataMaster Pro.exe" -Destination "C:\DataMaster Pro\"
```

### 3. Crie atalho (opcional)

```powershell
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$HOME\Desktop\DataMaster Pro.lnk")
$Shortcut.TargetPath = "C:\DataMaster Pro\DataMaster Pro.exe"
$Shortcut.Save()
```

### 4. Execute

```powershell
& "C:\DataMaster Pro\DataMaster Pro.exe"
```

---

## 📍 Localização dos Arquivos

Após instalação:

```
C:\Program Files\DataMaster Pro\
├── DataMaster Pro.exe       (Aplicativo)
├── Uninstall.exe            (Desinstalador)
└── _internal/               (Dependências bundladas)
```

---

## ⚙️ Configuração Inicial

### 1. Primeiro Launch

- Aplicação abre com interface vazia
- Clique em qualquer ferramenta para começar

### 2. Carregar Dados

- Cada ferramenta tem botão "Abrir Arquivo"
- Suporta: .xlsx, .xls, .csv, .ods

### 3. Processar

- Configure opções específicas de cada ferramenta
- Clique "Processar" ou "Executar"
- Resultado aparece em abas/janelas novas

---

## 🗑️ Desinstalação

### Via Instalador (Recomendado)

1. Painel de Controle → Programas
2. Procure "DataMaster Pro"
3. Clique "Desinstalar"
4. Confirme remoção

### Manual

1. Delete: `C:\Program Files\DataMaster Pro\`
2. Delete atalhos da Área de Trabalho
3. Delete atalho do Menu Iniciar

---

## 🐛 Troubleshooting

### Erro: "Windows SmartScreen"

**Causa:** Windows bloqueando .exe desconhecido  
**Solução:** Clique "Mais informações" → "Executar mesmo assim"

### Erro: "Arquivo danificado"

**Causa:** Download incompleto  
**Solução:** Redownload `DataMaster Pro Setup.exe`

### Erro: "Acesso Negado"

**Causa:** Sem privilégios de administrador  
**Solução:** Clique direito → "Executar como administrador"

### Erro: "Porta em Uso"

**Causa:** Outra instância rodando  
**Solução:** Feche outras janelas DataMaster Pro

### Lentidão

**Causa:** Volume de dados muito grande  
**Solução:** Processar em lotes menores

---

## 📊 Especificações Técnicas

### Estrutura de Compilação

```
PyInstaller 6.20.0
├── Base Image: Python 3.12.10
├── Modo: One-file (--onefile)
├── GUI: Windowed (sem console)
├── Tamanho Final: ~65 MB (comprimido em .exe)
└── Dependências: 40+ pacotes bundlados
```

### Dependências Incluídas

- customtkinter (GUI framework)
- pandas, numpy (processamento)
- reportlab (PDF generation)
- beautifulsoup4, requests (web scraping)
- playwright (automação)
- cryptography (segurança)
- qrcode (códigos QR)
- fuzzywuzzy (fuzzy matching)

---

## 🎯 Próximas Etapas

Após instalar com sucesso:

1. **Explorar Ferramentas:** Abra cada uma para conhecer funcionalidades
2. **Testar com Dados:** Use planilhas de teste antes de dados reais
3. **Customizar:** Configure preferências em cada ferramenta
4. **Integrar:** Use resultados em seus processos

---

## 📞 Suporte

- **Versão Atual:** 1.0.0
- **Compilação:** Maio 2026
- **Compatibilidade:** Windows 10/11 64-bit
- **Licença:** Proprietary

---

**Instalação Concluída! Aproveite o DataMaster Pro! 🚀**
