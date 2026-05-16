# Build DataMaster Pro Installer
# Versão PowerShell do script de construção
# Uso: .\build_installer.ps1

param(
    [switch]$Clean = $false,
    [switch]$Quick = $false,
    [string]$PyVersion = "3.10"
)

# ======================================================================
# Configurações
# ======================================================================

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvPath = Join-Path $ScriptDir ".venv"
$DistPath = Join-Path $ScriptDir "dist"
$BuildPath = Join-Path $ScriptDir "build"

# Cores
$Colors = @{
    "Info"    = "Cyan"
    "Success" = "Green"
    "Warning" = "Yellow"
    "Error"   = "Red"
}

function Write-Log {
    param(
        [string]$Message,
        [string]$Level = "Info"
    )
    $Color = $Colors[$Level]
    Write-Host "[$($Level.ToUpper())] $Message" -ForegroundColor $Color
}

# ======================================================================
# Funções
# ======================================================================

function Test-Python {
    try {
        $Version = python --version 2>&1
        Write-Log "Python encontrado: $Version" -Level "Success"
        return $true
    }
    catch {
        Write-Log "Python não encontrado. Instale Python 3.10+" -Level "Error"
        return $false
    }
}

function Setup-VirtualEnv {
    if (Test-Path $VenvPath) {
        Write-Log "Ambiente virtual já existe" -Level "Success"
    }
    else {
        Write-Log "Criando ambiente virtual..." -Level "Info"
        python -m venv $VenvPath
        
        if ($LASTEXITCODE -ne 0) {
            Write-Log "Falha ao criar ambiente virtual" -Level "Error"
            return $false
        }
        Write-Log "Ambiente virtual criado" -Level "Success"
    }
    
    # Ativar
    $ActivateScript = Join-Path $VenvPath "Scripts\Activate.ps1"
    & $ActivateScript
    
    return $true
}

function Install-Dependencies {
    Write-Log "Instalando dependências..." -Level "Info"
    $RequirementsFile = Join-Path $ScriptDir "requirements.txt"
    
    pip install -q -r $RequirementsFile
    
    if ($LASTEXITCODE -ne 0) {
        Write-Log "Falha ao instalar dependências" -Level "Error"
        return $false
    }
    
    Write-Log "Dependências instaladas" -Level "Success"
    return $true
}

function Test-PyInstaller {
    try {
        $Version = pyinstaller --version 2>&1
        Write-Log "PyInstaller encontrado: $Version" -Level "Success"
        return $true
    }
    catch {
        Write-Log "PyInstaller não encontrado, instalando..." -Level "Warning"
        pip install -q PyInstaller
        return $?
    }
}

function Clean-PreviousBuilds {
    if ($Clean -or (Test-Path $BuildPath) -or (Test-Path $DistPath)) {
        Write-Log "Limpando builds anteriores..." -Level "Info"
        Remove-Item $BuildPath -Recurse -Force -ErrorAction SilentlyContinue
        Remove-Item $DistPath -Recurse -Force -ErrorAction SilentlyContinue
        Write-Log "Build limpo" -Level "Success"
    }
}

function Build-Installer {
    Write-Log "Iniciando build do instalador..." -Level "Info"
    $SpecFile = Join-Path $ScriptDir "datamaster.spec"
    
    if ($Quick) {
        Write-Log "Modo rápido (sem otimizações)" -Level "Warning"
        pyinstaller $SpecFile --clean --noupx
    }
    else {
        pyinstaller $SpecFile --clean
    }
    
    if ($LASTEXITCODE -ne 0) {
        Write-Log "Falha no build" -Level "Error"
        return $false
    }
    
    Write-Log "Build concluído com sucesso!" -Level "Success"
    return $true
}

function Verify-Output {
    Write-Log "Verificando arquivos gerados..." -Level "Info"
    
    $SetupExe = Join-Path $DistPath "DataMaster Pro Setup.exe"
    $AppDir = Join-Path $DistPath "DataMaster Pro"
    
    $AllGood = $true
    
    if (Test-Path $SetupExe) {
        Write-Log "✓ Instalador: $(Split-Path $SetupExe -Leaf)" -Level "Success"
        $Size = (Get-Item $SetupExe).Length / 1MB
        Write-Log "  Tamanho: $([Math]::Round($Size, 2)) MB"
    }
    else {
        Write-Log "✗ Instalador não encontrado" -Level "Error"
        $AllGood = $false
    }
    
    if (Test-Path $AppDir) {
        Write-Log "✓ Diretório da aplicação: $(Split-Path $AppDir -Leaf)\" -Level "Success"
        $MainExe = Join-Path $AppDir "DataMaster Pro.exe"
        if (Test-Path $MainExe) {
            Write-Log "  ✓ Executável principal encontrado"
        }
    }
    else {
        Write-Log "✗ Diretório da aplicação não encontrado" -Level "Error"
        $AllGood = $false
    }
    
    return $AllGood
}

function Show-Summary {
    Write-Host ""
    Write-Host "═" * 50 -ForegroundColor Cyan
    Write-Log "Resumo da Construção" -Level "Info"
    Write-Host "═" * 50 -ForegroundColor Cyan
    Write-Host ""
    
    $DistPath = Join-Path $ScriptDir "dist"
    if (Test-Path $DistPath) {
        Write-Host "Local dos arquivos: $DistPath`n" -ForegroundColor Green
        Write-Host "Próximos passos:" -ForegroundColor Cyan
        Write-Host "  1. Testar instalador:"
        Write-Host "     & '$DistPath\DataMaster Pro Setup.exe'" -ForegroundColor Yellow
        Write-Host "  2. Selecionar pasta de instalação"
        Write-Host "  3. Marcar opções desejadas"
        Write-Host "  4. Clicar em 'Instalar'"
    }
    
    Write-Host ""
    Write-Host "Documentação: INSTALLER_BUILD.md`n" -ForegroundColor Cyan
}

# ======================================================================
# Main
# ======================================================================

Clear-Host
Write-Host ""
Write-Host "╔════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   DataMaster Pro - Construtor de Instalador   ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Verificações pré-requisitos
Write-Log "Verificando pré-requisitos..." -Level "Info"
Write-Host ""

if (-not (Test-Python)) {
    exit 1
}

if (-not (Setup-VirtualEnv)) {
    Write-Log "Falha ao configurar ambiente virtual" -Level "Error"
    exit 1
}

if (-not (Install-Dependencies)) {
    Write-Log "Falha ao instalar dependências" -Level "Error"
    exit 1
}

if (-not (Test-PyInstaller)) {
    Write-Log "Falha ao configurar PyInstaller" -Level "Error"
    exit 1
}

Write-Host ""
Clean-PreviousBuilds

Write-Host ""
Write-Host "╔════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║      Iniciando Build do Instalador...         ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

if (-not (Build-Installer)) {
    Write-Log "Construção falhou" -Level "Error"
    exit 1
}

Write-Host ""
if (-not (Verify-Output)) {
    Write-Log "Aviso: Alguns arquivos podem estar faltando" -Level "Warning"
}

Show-Summary
Write-Host "Pressione Enter para sair..." -ForegroundColor Gray
Read-Host
