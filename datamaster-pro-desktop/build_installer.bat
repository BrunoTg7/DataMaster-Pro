@echo off
REM ======================================================================
REM DataMaster Pro Installer Builder
REM
REM Script para facilitar a construção do instalador do DataMaster Pro
REM
REM Uso: build_installer.bat
REM ======================================================================

setlocal enabledelayedexpansion

REM Cores (ANSI)
set "GREEN=[92m"
set "BLUE=[94m"
set "YELLOW=[93m"
set "RED=[91m"
set "RESET=[0m"

echo %BLUE%=====================================================%RESET%
echo %BLUE%DataMaster Pro - Construtor de Instalador%RESET%
echo %BLUE%=====================================================%RESET%
echo.

REM Verificar se Python está instalado
python --version > nul 2>&1
if errorlevel 1 (
    echo %RED%[ERRO] Python não encontrado!%RESET%
    echo Por favor, instale Python 3.10+ antes de continuar.
    pause
    exit /b 1
)

echo %GREEN%[OK] Python encontrado%RESET%
python --version
echo.

REM Verificar ambiente virtual
if not exist ".venv" (
    echo %YELLOW%[INFO] Criando ambiente virtual...%RESET%
    python -m venv .venv
    if errorlevel 1 (
        echo %RED%[ERRO] Falha ao criar ambiente virtual%RESET%
        pause
        exit /b 1
    )
    echo %GREEN%[OK] Ambiente virtual criado%RESET%
) else (
    echo %GREEN%[OK] Ambiente virtual já existe%RESET%
)
echo.

REM Ativar ambiente virtual
echo %YELLOW%[INFO] Ativando ambiente virtual...%RESET%
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo %RED%[ERRO] Falha ao ativar ambiente virtual%RESET%
    pause
    exit /b 1
)
echo %GREEN%[OK] Ambiente virtual ativo%RESET%
echo.

REM Instalar dependências
echo %YELLOW%[INFO] Instalando dependências Python...%RESET%
pip install -q -r requirements.txt
if errorlevel 1 (
    echo %RED%[ERRO] Falha ao instalar dependências%RESET%
    pause
    exit /b 1
)
echo %GREEN%[OK] Dependências instaladas%RESET%
echo.

REM Verificar PyInstaller
pyinstaller --version > nul 2>&1
if errorlevel 1 (
    echo %RED%[ERRO] PyInstaller não encontrado%RESET%
    echo Instalando PyInstaller...
    pip install -q PyInstaller
)
echo %GREEN%[OK] PyInstaller pronto%RESET%
echo.

REM Limpar builds anteriores
echo %YELLOW%[INFO] Limpando builds anteriores...%RESET%
if exist "build" rmdir /s /q build > nul 2>&1
if exist "dist" rmdir /s /q dist > nul 2>&1
echo %GREEN%[OK] Pasta limpa%RESET%
echo.

REM Construir com PyInstaller
echo %BLUE%=====================================================%RESET%
echo %BLUE%Iniciando build do instalador...%RESET%
echo %BLUE%=====================================================%RESET%
echo.

pyinstaller datamaster.spec --clean

if errorlevel 1 (
    echo.
    echo %RED%[ERRO] Falha durante o build!%RESET%
    echo Verifique os erros acima e tente novamente.
    pause
    exit /b 1
)

echo.
echo %GREEN%=====================================================%RESET%
echo %GREEN%Build concluído com sucesso!%RESET%
echo %GREEN%=====================================================%RESET%
echo.

REM Verificar arquivos gerados
echo %BLUE%[INFO] Arquivos gerados:%RESET%
if exist "dist\DataMaster Pro Setup.exe" (
    echo %GREEN%  ✓ dist\DataMaster Pro Setup.exe%RESET%
) else (
    echo %RED%  ✗ dist\DataMaster Pro Setup.exe (não encontrado)%RESET%
)

if exist "dist\DataMaster Pro" (
    echo %GREEN%  ✓ dist\DataMaster Pro\%RESET%
) else (
    echo %RED%  ✗ dist\DataMaster Pro\ (não encontrado)%RESET%
)

echo.
echo %YELLOW%[INFO] Próximos passos:%RESET%
echo  1. Testar o instalador: dist\"DataMaster Pro Setup.exe"
echo  2. Escolher pasta de instalação
echo  3. Marcar opções desejadas
echo  4. Instalar e validar
echo.

echo %BLUE%[INFO] Documentação: INSTALLER_BUILD.md%RESET%
echo.

pause
