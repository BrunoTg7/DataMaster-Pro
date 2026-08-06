@echo off
REM ============================================================
REM DataMaster Pro v1.5 - Build Completo: EXE (NSIS) + MSIX (opcional)
REM ============================================================
REM 
REM PRIORIDADE: EXE (NSIS) como distribuição principal
REM MSIX apenas para Microsoft Store futuro (certificado OV/EV $89)
REM ============================================================

setlocal enabledelayedexpansion

echo.
echo ============================================================
echo   🚀 DataMaster Pro v1.5 - BUILD COMPLETO (EXE PRINCIPAL)
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
echo [1/5] Verificando Python...
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
echo [2/5] Verificando arquivo .env...
if not exist ".env" (
    echo ❌ Arquivo .env não encontrado
    exit /b 1
)
echo ✅ Arquivo .env OK
echo.

REM ============================================================
REM PASSO 3: Compilar Executável com PyInstaller (--onedir)
REM ============================================================
echo [3/5] Compilando executável com PyInstaller...
echo         Modo: --onedir (melhor para instalador NSIS)
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
REM PASSO 4: Compilar Instalador NSIS (DISTRIBUIÇÃO PRINCIPAL)
REM ============================================================
echo [4/5] Compilando instalador NSIS (DISTRIBUIÇÃO PRINCIPAL)...
echo         Instalador EXE padrão Windows - funciona sem certificados especiais
echo.

if exist "DataMaster Pro Setup.exe" (
    del "DataMaster Pro Setup.exe" >nul 2>&1
)

"C:\Program Files (x86)\NSIS\makensis.exe" "installer.nsi" >nsis_log.txt 2>&1

if errorlevel 1 (
    echo ❌ Erro ao compilar instalador NSIS
    type nsis_log.txt | findstr /i "error"
    exit /b 1
)

if not exist "DataMaster Pro Setup.exe" (
    echo ❌ Instalador NSIS não foi criado
    exit /b 1
)

for /f %%A in ('dir "DataMaster Pro Setup.exe" ^| find "DataMaster Pro"') do (
    set setup_size=%%~zA
)

echo ✅ Instalador NSIS criado com sucesso
echo    📦 Artefato: DataMaster Pro Setup.exe (%setup_size% bytes)
echo    ✅ Instala sem certificados especiais - Next → Next → Finish
echo.

REM ============================================================
REM PASSO 5: Gerar MSIX (OPCIONAL - apenas para Microsoft Store futuro)
REM ============================================================
echo [5/5] Gerando MSIX (OPCIONAL - apenas para Microsoft Store futuro)...
echo         Requer certificado OV/EV ($89) para Microsoft Store
echo         Self-signed apenas para testes locais / sideload
echo.

powershell -ExecutionPolicy Bypass -File "build_msix.ps1" >msix_log.txt 2>&1

if errorlevel 1 (
    echo ⚠️  MSIX falhou (EXE já pronto, continuando...)
    type msix_log.txt | findstr /i "error"
) else (
    if exist "DataMasterPro_1.5.0.0_x64.msix" (
        echo ✅ MSIX gerado (opcional - para Store futuro)
    )
)
echo.

REM ============================================================
REM RESUMO FINAL
REM ============================================================
echo ============================================================
echo ✅ BUILD v1.5 CONCLUÍDO - DISTRIBUIÇÃO PRONTA
echo ============================================================
echo.
echo 📦 ARTEFATOS GERADOS:
echo    ✅ DataMaster Pro Setup.exe (%setup_size% bytes)  <- DISTRIBUIÇÃO PRINCIPAL
echo    ✅ dist\DataMaster Pro\          (pasta app --onedir)
if exist "DataMasterPro_1.5.0.0_x64.msix" (
    echo    • DataMasterPro_1.5.0.0_x64.msix  (opcional - Store futuro)
)
echo.
echo ✅ DISTRIBUIÇÃO PRINCIPAL (EXE NSIS):
echo    • Instala sem certificados especiais
echo    • Next → Next → Finish (padrão Windows)
echo    • Funciona em Windows 10/11
echo    • Distribua via GitHub Releases / Site
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