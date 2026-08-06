@echo off
REM ============================================================
REM DataMaster Pro v1.5 - Build Completo: EXE + NSIS + MSIX
REM ============================================================

setlocal enabledelayedexpansion

echo.
echo ============================================================
echo   🚀 DataMaster Pro v1.5 - BUILD COMPLETO
echo ============================================================
echo.

REM Definir diretório
cd /d "c:\Users\Public\projetos\ferramente excel\datamaster-pro-desktop"

if errorlevel 1 (
    echo ❌ Erro: Não foi possível acessar o diretório
    exit /b 1
)

echo ✅ Diretório: %cd%
echo.

REM ============================================================
REM PASSO 1: Verificar Python
REM ============================================================
echo [1/6] Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python não encontrado
    exit /b 1
)
echo ✅ Python detectado
echo.

REM ============================================================
REM PASSO 2: Verificar .env
REM ============================================================
echo [2/6] Verificando arquivo .env...
if not exist ".env" (
    echo ❌ Arquivo .env não encontrado
    exit /b 1
)
echo ✅ Arquivo .env OK
echo.

REM ============================================================
REM PASSO 3: Compilar Executável com PyInstaller (--onedir)
REM ============================================================
echo [3/6] Compilando executável com PyInstaller...
echo         Modo: --onedir (melhor para MSIX/Instalador)
echo.

python -m PyInstaller datamaster.spec --clean >build_log.txt 2>&1

if errorlevel 1 (
    echo ❌ Erro ao compilar executável
    type build_log.txt | findstr /i "error"
    exit /b 1
)

if not exist "dist\DataMaster Pro\DataMaster Pro.exe" (
    echo ❌ Executável não foi criado
    exit /b 1
)

echo ✅ Executável compilado com sucesso
echo    📂 Localização: dist\DataMaster Pro\
echo.

REM ============================================================
REM PASSO 4: Gerar MSIX (Self-Signed para teste / Real para Store)
REM ============================================================
echo [4/6] Gerando pacote MSIX...
echo         (Self-signed para teste local / sideload)
echo.

powershell -ExecutionPolicy Bypass -File "build_msix.ps1" >msix_log.txt 2>&1

if errorlevel 1 (
    echo ❌ Erro ao gerar MSIX
    type msix_log.txt | findstr /i "error"
    exit /b 1
)

if not exist "DataMasterPro_1.5.0.0_x64.msix" (
    echo ❌ MSIX não foi criado
    exit /b 1
)

echo ✅ MSIX gerado e assinado com sucesso
echo    📦 Artefato: DataMasterPro_1.5.0.0_x64.msix
echo.

REM ============================================================
REM PASSO 5: Compilar Instalador NSIS (opcional, legado)
REM ============================================================
echo [5/6] Compilando instalador NSIS...
if exist "DataMaster Pro Setup.exe" (
    del "DataMaster Pro Setup.exe" >nul 2>&1
)

"C:\Program Files (x86)\NSIS\makensis.exe" "installer.nsi" >nsis_log.txt 2>&1

if errorlevel 1 (
    echo ⚠️  NSIS falhou (MSIX já pronto, continuando...)
    type nsis_log.txt | findstr /i "error"
) else (
    if exist "DataMaster Pro Setup.exe" (
        for /f %%A in ('dir "DataMaster Pro Setup.exe" ^| find "DataMaster Pro"') do (
            set setup_size=%%~zA
        )
        echo ✅ Instalador NSIS: DataMaster Pro Setup.exe (%setup_size% bytes)
    )
)
echo.

REM ============================================================
REM PASSO 6: Resumo Final
REM ============================================================
echo [6/6] Resumo dos artefatos...
echo.

echo ============================================================
echo ✅ BUILD v1.5 CONCLUÍDO - PRONTO PARA DISTRIBUIÇÃO
echo ============================================================
echo.
echo 📦 ARTEFATOS GERADOS:
echo    • dist\DataMaster Pro\          (pasta app --onedir)
echo    • DataMasterPro_1.5.0.0_x64.msix  (MSIX assinado self-signed)
if defined setup_size echo    • DataMaster Pro Setup.exe (%setup_size% bytes)  (NSIS legado)
echo.
echo ✅ MSIX PRONTO PARA:
echo    • Teste local:  Add-AppxPackage .\DataMasterPro_1.5.0.0_x64.msix  (PowerShell Admin)
echo    • Sideload:     Distribuir .msix + certificado self-signed
echo    • GitHub Releases: Upload .msix + instruções
echo.
echo 🎯 PARA MICROSOFT STORE (quando tiver certificado OV/EV $89):
echo    1. Comprar certificado OV (SSL.com, Sectigo ~$89/ano)
echo    2. Re-executar: powershell -File build_msix.ps1 -CertPath "real.pfx" -CertPassword "senha"
echo    3. Submeter .msix assinado no Partner Center
echo.
echo 📊 VERSÃO: 1.5.0.0 | Publisher: CN=DataMaster
echo ============================================================
echo.

pause