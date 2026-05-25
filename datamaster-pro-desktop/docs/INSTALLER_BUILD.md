# Instalador do DataMaster Pro - Guia de Construção

## Visão Geral

O instalador profissional do DataMaster Pro oferece uma experiência fluida de instalação com:

✅ **Tela de Boas-vindas** - Apresentação do aplicativo
✅ **Seleção de Diretório** - Escolha o local de instalação (padrão: `C:\Program Files\DataMaster Pro`)
✅ **Validação de Permissões** - Verifica se você tem direitos de escrita
✅ **Opções de Instalação**:

- Criar atalho na área de trabalho
- Iniciar aplicação após instalação
  ✅ **Progresso Visual** - Feedback em tempo real durante a instalação
  ✅ **Tela de Sucesso** - Confirmação e próximos passos

---

## Arquivos do Instalador

| Arquivo              | Descrição                                            |
| -------------------- | ---------------------------------------------------- |
| `installer.py`       | Script principal do instalador com UI em Tkinter     |
| `datamaster.spec`    | Configuração PyInstaller para gerar executáveis      |
| `INSTALLER_BUILD.md` | Este guia                                            |
| `requirements.txt`   | Dependências Python (incluindo pywin32 para atalhos) |

---

## Pré-requisitos

### 1. Ambiente Python

```bash
# Verificar versão
python --version  # Requer Python 3.10+

# Criar ambiente virtual
python -m venv .venv

# Ativar ambiente
# Windows
.venv\Scripts\activate

# ou Linux/Mac
source .venv/bin/activate
```

### 2. Instalar Dependências

```bash
pip install -r requirements.txt
```

Principais dependências:

- `PyInstaller` - Criar executáveis a partir do Python
- `pywin32` - Suporte a atalhos Windows (Windows apenas)
- `customtkinter` - Framework UI moderno
- `python-dotenv` - Gerenciamento de variáveis de ambiente

---

## Construir o Instalador

### Opção 1: Build Completo (Recomendado)

```bash
# 1. Ativar ambiente virtual
.venv\Scripts\activate

# 2. Construir usando PyInstaller
pyinstaller datamaster.spec --clean --onedir

# instalador
cd "c:\Users\Public\projetos\ferramente excel\datamaster-pro-desktop" ; & "C:\Program Files (x86)\NSIS\makensis.exe" "installer.nsi"
# Saída esperada:
# - dist/DataMaster Pro/  (aplicação principal)
# - dist/DataMaster Pro Setup.exe  (instalador)
```

**Tempo de Build:** ~2-5 minutos (primeira vez)
**Tamanho:** ~300-500 MB (com todas as dependências)

### Opção 2: Build Rápido (Apenas Instalador)

```bash
# Para testar apenas o instalador sem empacotar a aplicação principal
pyinstaller --onefile --windowed \
    --icon=assets/icon.ico \
    --name="DataMaster Pro Setup" \
    installer.py

# Saída: dist/DataMaster Pro Setup.exe (~50 MB)
```

### Opção 3: Build para Distribuição (Com UPX)

```bash
# Compressão adicional do executável
pyinstaller datamaster.spec --clean --upx-dir=upx

# Requer UPX instalado: https://upx.github.io/
```

---

## Estrutura de Saída

Após o build, a estrutura será:

```
dist/
├── DataMaster Pro/           # Aplicação principal
│   ├── main.exe
│   ├── config.py
│   ├── src/
│   ├── assets/
│   ├── requirements.txt
│   └── .env.example
└── DataMaster Pro Setup.exe  # Instalador
```

---

## Testar o Instalador

### Teste Local

```bash
# 1. Executar o instalador
dist/"DataMaster Pro Setup.exe"

# 2. Seguir os passos:
#    - Aceitar boas-vindas
#    - Selecionar pasta de instalação (ex: C:\Users\{user}\AppData\Local\DataMaster)
#    - Marcar "Criar atalho na área de trabalho"
#    - Marcar "Iniciar após instalação"
#    - Clicar em "Instalar"

# 3. Verificar:
#    ✓ Arquivos instalados em C:\Users\{user}\AppData\Local\DataMaster
#    ✓ Atalho criado na área de trabalho
#    ✓ Aplicação iniciada automaticamente
```

### Verificar Log de Instalação

```bash
# O instalador cria um log em:
# {working_dir}/installer.log

# Ver últimas entradas
type installer.log | tail -20
```

### Desinstalar (Modo Manual)

```bash
# 1. Deletar atalho da área de trabalho
# 2. Deletar pasta de instalação (C:\Program Files\DataMaster Pro)
# 3. Deletar atalhos do menu Iniciar

# Verificar entrada no Registro (Windows 10+)
reg query "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Uninstall" | find "DataMasterPro"
```

---

## Funcionalidades Implementadas

### 1. **Interface em Múltiplas Telas**

```
[Boas-vindas] → [Seleção de Pasta] → [Opções] → [Instalação] → [Sucesso]
```

Cada tela possui:

- Design moderno com tema azul profissional
- Botões "Voltar", "Próximo", "Cancelar"
- Validação de entrada
- Mensagens de erro claras

### 2. **Seleção de Diretório**

- Dialog nativo do Windows para browsear pastas
- Validação de permissões de escrita
- Sugestão de caminho padrão: `C:\Program Files\DataMaster Pro`
- Mensagem de aviso sobre espaço em disco (500 MB)

### 3. **Criação de Atalho**

Utilizando `pywin32.win32com.client`:

```python
# Cria atalho com:
# - Caminho do executável
# - Diretório de trabalho
# - Ícone (se disponível)
# - Local: Desktop
```

Resultado: `C:\Users\{user}\Desktop\DataMaster Pro.lnk`

### 4. **Instalação de Dependências**

Após copiar arquivos, o instalador executa:

```bash
pip install -r requirements.txt -q
```

Isso garante que todas as bibliotecas Python estejam disponíveis.

### 5. **Entrada no Registro (Windows)**

Adicionado em:

```
HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Uninstall\DataMasterPro
```

Valores:

- `DisplayName`: DataMaster Pro
- `InstallLocation`: {caminho escolhido}
- `Publisher`: DataMaster Pro
- `DisplayVersion`: 1.0.0

Permite remover via "Programas e Recursos".

### 6. **Launch Automático (Opcional)**

Se marcado, o instalador executa:

```python
subprocess.Popen([str(exe_path)])
```

Inicia `main.exe` após conclusão da instalação.

---

## Troubleshooting

### ❌ Erro: "pywin32 não disponível"

**Problema:** Atalhos não são criados

**Solução:**

```bash
pip install pywin32
python -m pywin32_postinstall -install
```

### ❌ Erro: "Permissão negada ao instalar"

**Problema:** Não tem direitos de escrita no diretório

**Solução:**

1. Executar como Administrador: `Shift + Ctrl + Click` → "Executar como administrador"
2. Escolher diretório em `C:\Users\{user}` ao invés de `C:\Program Files`
3. Verificar se arquivo não está aberto/bloqueado

### ❌ Erro: "Arquivo não encontrado" durante build

**Problema:** `icon.ico` ou `assets/` faltam

**Solução:**

```bash
# Criar arquivo de ícone mínimo
# Ou remover referência de ícone do datamaster.spec
```

### ❌ Aplicação não inicia após instalação

**Problema:** `main.exe` não encontrado

**Solução:**

1. Verificar se `dist/DataMaster Pro/main.exe` existe
2. Verificar permissões de execução
3. Consultar `installer.log` para detalhes

### ⚠️ Warning: "UPX not found"

**Problema:** UPX não instalado (opcional)

**Solução:** Ignora - apenas reduz tamanho do executável. Para usar:

```bash
# Download: https://upx.github.io/
# Extrair em pasta e adicionar ao PATH
pyinstaller datamaster.spec --upx-dir=C:\upx
```

---

## Otimizações e Melhorias Futuras

### Curto Prazo

- [ ] Adicionar ícone profissional (.ico de alta qualidade)
- [ ] Implementar desinstalador (uninstaller.exe)
- [ ] Gerar NSIS script para instalador.msi nativo
- [ ] Suporte a atualizações automáticas

### Médio Prazo

- [ ] Assinatura digital de código (Code Signing)
- [ ] Verificação de integridade SHA256
- [ ] Suporte a múltiplos idiomas (i18n)
- [ ] Telemetria de instalação

### Longo Prazo

- [ ] Autoupdater integrado
- [ ] Instalação por empresa (Active Directory)
- [ ] Versioning e rollback
- [ ] Análise de compatibilidade do sistema

---

## Distribuição

### 1. Criar Release

```bash
# Copiar executável para distribuição
copy dist\"DataMaster Pro Setup.exe" releases\v1.0.0\

# Gerar checksum
certutil -hashfile releases\v1.0.0\"DataMaster Pro Setup.exe" SHA256 > releases\v1.0.0\CHECKSUM.txt
```

### 2. Hospedar em Servidor

```
https://download.datamaster.com/setup.exe
https://download.datamaster.com/setup-v1.0.0.exe
https://download.datamaster.com/CHECKSUM.txt
```

### 3. Instruções para Usuários

```
1. Download: https://datamaster.com/downloads
2. Executar: DataMaster Pro Setup.exe
3. Escolher pasta e opções
4. Clicar "Instalar"
5. Usar via atalho na área de trabalho
```

---

## Referências

- **PyInstaller Docs:** https://pyinstaller.org/en/stable/
- **pywin32 Docs:** https://github.com/pywin32
- **CustomTkinter:** https://github.com/TomSchimansky/CustomTkinter
- **NSIS (Advanced):** https://nsis.sourceforge.io/

---

## Contato & Suporte

Para problemas com o instalador:

1. Consultar `installer.log`
2. Verificar `troubleshooting` acima
3. Abrir issue em GitHub
4. Contatar support@datamaster.com

---

**Última Atualização:** Maio 2026
**Versão:** 1.0.0
