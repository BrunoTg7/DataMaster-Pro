<# 
DataMaster Pro - Build MSIX com Self-Signed Cert
Gera pacote MSIX assinado para teste local / sideload
Uso: .\build_msix.ps1 [-CertPath "caminho\cert.pfx"] [-CertPassword "senha"]
#>

param(
    [string]$CertPath = "datamaster_selfsigned.pfx",
    [string]$CertPassword = "datamaster2026",
    [string]$Version = "1.5.0.0",
    [string]$Publisher = "CN=DataMaster",
    [string]$AppName = "DataMaster Pro",
    [switch]$SkipPyInstaller
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $ScriptDir

$SDK_PATH = "C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x64"
$MAKEAPPX = "$SDK_PATH\makeappx.exe"
$SIGNTOOL = "$SDK_PATH\signtool.exe"

function Write-Log($msg) { Write-Host "[$(Get-Date -Format 'HH:mm:ss')] $msg" -ForegroundColor Cyan }
function Write-OK($msg) { Write-Host "✅ $msg" -ForegroundColor Green }
function Write-ERR($msg) { Write-Host "❌ $msg" -ForegroundColor Red }

Write-Log "=== DataMaster Pro MSIX Build v$Version ==="

# 1. Verificar/gerar certificado self-signed
if (-not (Test-Path $CertPath)) {
    Write-Log "Gerando certificado self-signed..."
    $cert = New-SelfSignedCertificate `
        -Subject $Publisher `
        -Type CodeSigningCert `
        -KeyUsage DigitalSignature `
        -FriendlyName "DataMaster Pro Self-Signed" `
        -CertStoreLocation "Cert:\CurrentUser\My" `
        -KeyExportPolicy Exportable `
        -NotAfter (Get-Date).AddYears(1)

    $pwd = ConvertTo-SecureString -String $CertPassword -Force -AsPlainText
    Export-PfxCertificate -Cert $cert -FilePath $CertPath -Password $pwd | Out-Null
    Write-OK "Certificado criado: $CertPath"
} else {
    Write-OK "Certificado existente: $CertPath"
}

# 2. PyInstaller (se não skip)
if (-not $SkipPyInstaller) {
    Write-Log "Compilando com PyInstaller..."
    python -m PyInstaller datamaster.spec --clean 2>&1 | Tee-Object build_log.txt
    if ($LASTEXITCODE -ne 0) { Write-ERR "PyInstaller falhou"; exit 1 }
    if (-not (Test-Path "dist\DataMaster Pro\DataMaster Pro.exe")) { Write-ERR "EXE não gerado"; exit 1 }
    Write-OK "PyInstaller OK"
}

# 3. Preparar layout MSIX
Write-Log "Preparando layout MSIX..."
$msixLayout = "msix_layout"
if (Test-Path $msixLayout) { Remove-Item $msixLayout -Recurse -Force }
New-Item -ItemType Directory -Path $msixLayout | Out-Null
New-Item -ItemType Directory -Path "$msixLayout\assets" | Out-Null

# Copiar executável (suporta tanto --onedir quanto single-file)
if (Test-Path "dist\DataMaster Pro\DataMaster Pro.exe") {
    # Modo --onedir (pasta)
    Copy-Item "dist\DataMaster Pro\*" $msixLayout -Recurse -Force
} elseif (Test-Path "dist\DataMaster Pro.exe") {
    # Modo single-file (EXE único)
    Copy-Item "dist\DataMaster Pro.exe" $msixLayout -Force
} else {
    Write-ERR "Executável não encontrado em dist\"
    exit 1
}

# Copiar assets preservando pasta assets/
Copy-Item "assets\StoreLogo_*.png" "$msixLayout\assets\" -Force
Copy-Item "assets\WideLogo_*.png" "$msixLayout\assets\" -Force
Copy-Item "assets\SplashScreen_*.png" "$msixLayout\assets\" -Force
Copy-Item "assets\datamaster.ico" "$msixLayout\assets\" -Force

# Copiar AppxManifest
Copy-Item "AppxManifest.xml" $msixLayout -Force

# 4. Gerar MSIX
Write-Log "Criando pacote MSIX..."
$msixFile = "DataMasterPro_${Version}_x64.msix"
if (Test-Path $msixFile) { Remove-Item $msixFile -Force }
& $MAKEAPPX pack /d $msixLayout /p $msixFile /l /o
if ($LASTEXITCODE -ne 0) { Write-ERR "makeappx falhou"; exit 1 }
Write-OK "MSIX criado: $msixFile"

# 5. Assinar MSIX
Write-Log "Assinando MSIX..."
$pwd = ConvertTo-SecureString -String $CertPassword -Force -AsPlainText
& $SIGNTOOL sign /f $CertPath /p $CertPassword /fd SHA256 /tr "http://timestamp.digicert.com" /td SHA256 $msixFile
if ($LASTEXITCODE -ne 0) { Write-ERR "signtool falhou"; exit 1 }
Write-OK "MSIX assinado: $msixFile"

# 6. Verificar assinatura
& $SIGNTOOL verify /pa $msixFile
Write-OK "Assinatura verificada"

# 7. Instalar certificado no Trusted People (para teste local)
Write-Log "Instalando certificado no Trusted People (requer Admin)..."
try {
    $cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($CertPath, $CertPassword, [System.Security.Cryptography.X509Certificates.X509KeyStorageFlags]::Exportable)
    $store = New-Object System.Security.Cryptography.X509Certificates.X509Store("TrustedPeople", "LocalMachine")
    $store.Open("ReadWrite")
    $store.Add($cert)
    $store.Close()
    Write-OK "Certificado confiável para sideload local"
} catch {
    Write-Host "⚠️  Não instalou certificado (precisa Admin): $_" -ForegroundColor Yellow
}

Write-Log "=== BUILD MSIX CONCLUÍDO ==="
Write-OK "Artefato: $msixFile"
Write-Host ""
Write-Host "📦 PARA INSTALAR LOCALMENTE (PowerShell Admin):" -ForegroundColor Cyan
Write-Host "   Add-AppxPackage -Path `"$PWD\$msixFile`""
Write-Host ""
Write-Host "🔄 PARA CERTIFICADO REAL (OV/EV) DEPOIS:" -ForegroundColor Cyan
Write-Host "   .\build_msix.ps1 -CertPath `"real_cert.pfx`" -CertPassword `"sua_senha`""
Write-Host ""
Write-Host "📤 PARA DISTRIBUIR VIA GITHUB RELEASES:" -ForegroundColor Cyan
Write-Host "   Upload $msixFile + instrução de instalar certificado self-signed"