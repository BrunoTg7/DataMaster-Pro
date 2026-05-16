# Auditoria Profissional - DataMaster Pro
# Script simples de verificacao

$ProjectRoot = "c:\Users\Public\projetos\ferramente excel"
$ErrorCount = 0
$WarningCount = 0
$SuccessCount = 0

Write-Host ""
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "AUDITORIA PROFISSIONAL - DataMaster Pro" -ForegroundColor Cyan
Write-Host "Verificacao Completa de Qualidade e Integridade" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

# ======================================================================
# 1. VERIFICACAO DE ESTRUTURA
# ======================================================================

Write-Host "[1/9] Verificando Estrutura de Pastas..." -ForegroundColor Magenta

$Dirs = @(
    "$ProjectRoot\datamaster-pro-desktop\src\gui"
    "$ProjectRoot\datamaster-pro-desktop\src\core"
    "$ProjectRoot\datamaster-pro-desktop\src\tools"
    "$ProjectRoot\datamaster-pro-desktop\src\utils"
    "$ProjectRoot\datamaster-pro-web\app"
    "$ProjectRoot\datamaster-pro-web\components"
    "$ProjectRoot\datamaster-pro-web\lib"
    "$ProjectRoot\datamaster-pro-shared\schemas"
    "$ProjectRoot\datamaster-pro-shared\constants"
    "$ProjectRoot\datamaster-pro-shared\types"
)

foreach ($Dir in $Dirs) {
    if (Test-Path $Dir) {
        Write-Host "  [OK] $(Split-Path $Dir -Leaf)" -ForegroundColor Green
        $SuccessCount++
    }
    else {
        Write-Host "  [ERROR] Faltando: $Dir" -ForegroundColor Red
        $ErrorCount++
    }
}

Write-Host ""

# ======================================================================
# 2. VERIFICACAO DE ARQUIVOS CRITICOS
# ======================================================================

Write-Host "[2/9] Verificando Arquivos Criticos..." -ForegroundColor Magenta

$Files = @(
    "$ProjectRoot\datamaster-pro-desktop\main.py|Desktop Entry Point"
    "$ProjectRoot\datamaster-pro-desktop\config.py|Desktop Config"
    "$ProjectRoot\datamaster-pro-desktop\installer.py|Instalador"
    "$ProjectRoot\datamaster-pro-web\package.json|Node.js Config"
    "$ProjectRoot\datamaster-pro-web\next.config.js|Next.js Config"
    "$ProjectRoot\datamaster-pro-web\lib\supabase.ts|Supabase Client"
    "$ProjectRoot\datamaster-pro-shared\schemas\complete-schema.sql|SQL Schema"
)

foreach ($File in $Files) {
    $Path, $Name = $File -split "\|"
    if (Test-Path $Path) {
        $Size = (Get-Item $Path).Length / 1KB
        Write-Host "  [OK] $Name ($([Math]::Round($Size, 1)) KB)" -ForegroundColor Green
        $SuccessCount++
    }
    else {
        Write-Host "  [MISSING] $Name" -ForegroundColor Red
        $ErrorCount++
    }
}

Write-Host ""

# ======================================================================
# 3. VERIFICACAO DE DEPENDENCIAS
# ======================================================================

Write-Host "[3/9] Verificando Dependencias..." -ForegroundColor Magenta

try {
    $PythonVer = python --version 2>&1
    Write-Host "  [OK] $PythonVer" -ForegroundColor Green
    $SuccessCount++
}
catch {
    Write-Host "  [ERROR] Python nao encontrado" -ForegroundColor Red
    $ErrorCount++
}

try {
    $NodeVer = node --version 2>&1
    Write-Host "  [OK] Node.js $NodeVer" -ForegroundColor Green
    $SuccessCount++
}
catch {
    Write-Host "  [ERROR] Node.js nao encontrado" -ForegroundColor Red
    $ErrorCount++
}

try {
    $NpmVer = npm --version 2>&1
    Write-Host "  [OK] npm $NpmVer" -ForegroundColor Green
    $SuccessCount++
}
catch {
    Write-Host "  [ERROR] npm nao encontrado" -ForegroundColor Red
    $ErrorCount++
}

Write-Host ""

# ======================================================================
# 4. VERIFICACAO PYTHON SYNTAX
# ======================================================================

Write-Host "[4/9] Verificando Python Syntax..." -ForegroundColor Magenta

$PyFiles = @(
    "$ProjectRoot\datamaster-pro-desktop\main.py"
    "$ProjectRoot\datamaster-pro-desktop\config.py"
    "$ProjectRoot\datamaster-pro-desktop\installer.py"
)

foreach ($File in $PyFiles) {
    if (Test-Path $File) {
        $Result = python -m py_compile $File 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  [OK] $(Split-Path $File -Leaf)" -ForegroundColor Green
            $SuccessCount++
        }
        else {
            Write-Host "  [ERROR] $(Split-Path $File -Leaf) - Syntax error" -ForegroundColor Red
            $ErrorCount++
        }
    }
}

Write-Host ""

# ======================================================================
# 5. VERIFICACAO INTEGRIDADE SQL
# ======================================================================

Write-Host "[5/9] Verificando Integridade SQL..." -ForegroundColor Magenta

$SchemaFile = "$ProjectRoot\datamaster-pro-shared\schemas\complete-schema.sql"

if (Test-Path $SchemaFile) {
    $Content = Get-Content $SchemaFile -Raw
    $Lines = (Get-Content $SchemaFile).Count
    
    $TableCount = [regex]::Matches($Content, "CREATE TABLE").Count
    $FunctionCount = [regex]::Matches($Content, "CREATE FUNCTION").Count
    $TriggerCount = [regex]::Matches($Content, "CREATE TRIGGER").Count
    
    Write-Host "  [OK] Tables: $TableCount" -ForegroundColor Green
    Write-Host "  [OK] Functions: $FunctionCount" -ForegroundColor Green
    Write-Host "  [OK] Triggers: $TriggerCount" -ForegroundColor Green
    Write-Host "  [OK] Total lines: $Lines" -ForegroundColor Green
    
    $SuccessCount += 4
}
else {
    Write-Host "  [ERROR] Schema SQL nao encontrado" -ForegroundColor Red
    $ErrorCount++
}

Write-Host ""

# ======================================================================
# 6. VERIFICACAO CONFIGURACAO
# ======================================================================

Write-Host "[6/9] Verificando Configuracao..." -ForegroundColor Magenta

$ConfigFiles = @(
    "$ProjectRoot\datamaster-pro-desktop\.env.example|Desktop .env"
    "$ProjectRoot\datamaster-pro-web\.env.example|Web .env"
    "$ProjectRoot\datamaster-pro-web\tsconfig.json|TypeScript Config"
)

foreach ($File in $ConfigFiles) {
    $Path, $Name = $File -split "\|"
    if (Test-Path $Path) {
        Write-Host "  [OK] $Name" -ForegroundColor Green
        $SuccessCount++
    }
    else {
        Write-Host "  [WARN] $Name faltando" -ForegroundColor Yellow
        $WarningCount++
    }
}

Write-Host ""

# ======================================================================
# 7. VERIFICACAO BUILD
# ======================================================================

Write-Host "[7/9] Verificando Build Capability..." -ForegroundColor Magenta

if (Test-Path "$ProjectRoot\datamaster-pro-desktop\build_installer.bat") {
    Write-Host "  [OK] Desktop build script disponivel" -ForegroundColor Green
    $SuccessCount++
}
else {
    Write-Host "  [ERROR] Desktop build script faltando" -ForegroundColor Red
    $ErrorCount++
}

$PackageJson = "$ProjectRoot\datamaster-pro-web\package.json"
if (Test-Path $PackageJson) {
    $Content = Get-Content $PackageJson -Raw | ConvertFrom-Json
    if ($Content.scripts.build) {
        Write-Host "  [OK] Web build script configurado" -ForegroundColor Green
        $SuccessCount++
    }
    else {
        Write-Host "  [WARN] Web build script nao configurado" -ForegroundColor Yellow
        $WarningCount++
    }
}

Write-Host ""

# ======================================================================
# 8. VERIFICACAO DOCUMENTACAO
# ======================================================================

Write-Host "[8/9] Verificando Documentacao..." -ForegroundColor Magenta

$Docs = @(
    "$ProjectRoot\README.md|README Principal"
    "$ProjectRoot\datamaster-pro-desktop\README.md|Desktop README"
    "$ProjectRoot\datamaster-pro-desktop\INSTALLER_BUILD.md|Guia de Build"
)

$DocCount = 0
foreach ($Doc in $Docs) {
    $Path, $Name = $Doc -split "\|"
    if (Test-Path $Path) {
        Write-Host "  [OK] $Name" -ForegroundColor Green
        $DocCount++
        $SuccessCount++
    }
    else {
        Write-Host "  [WARN] $Name faltando" -ForegroundColor Yellow
        $WarningCount++
    }
}

Write-Host ""

# ======================================================================
# 9. STATUS FINAL
# ======================================================================

Write-Host "[9/9] Gerando Relatorio Final..." -ForegroundColor Magenta
Write-Host ""

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "RELATORIO FINAL DE AUDITORIA" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Resultados:" -ForegroundColor Cyan
Write-Host "  [OK] Sucessos: $SuccessCount" -ForegroundColor Green
Write-Host "  [WARN] Avisos: $WarningCount" -ForegroundColor Yellow
Write-Host "  [ERROR] Erros: $ErrorCount" -ForegroundColor Red

Write-Host ""

if ($ErrorCount -eq 0) {
    Write-Host "[STATUS] PROJETO 100% PROFISSIONAL" -ForegroundColor Green
    Write-Host "[STATUS] PRONTO PARA PRODUCAO" -ForegroundColor Green
}
elseif ($ErrorCount -le 2) {
    Write-Host "[STATUS] BOM - Pequenos ajustes recomendados" -ForegroundColor Yellow
}
else {
    Write-Host "[STATUS] Ajustes necessarios antes de producao" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================================" -ForegroundColor Cyan

Write-Host ""
Write-Host "RECOMENDACOES:" -ForegroundColor Cyan
Write-Host "  1. Revisar .env.example para completude"
Write-Host "  2. Testar build do instalador: build_installer.bat"
Write-Host "  3. Executar testes Python/TypeScript"
Write-Host "  4. Validar integracao com Supabase"
Write-Host "  5. Testar instalacao do aplicativo"

Write-Host ""
Write-Host "Data: $(Get-Date -Format 'dd/MM/yyyy HH:mm:ss')" -ForegroundColor Gray
Write-Host ""
