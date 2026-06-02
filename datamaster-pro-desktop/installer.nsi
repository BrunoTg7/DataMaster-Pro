; DataMaster Pro - Instalador NSIS Profissional
; Versão v3.8 - Full Branding

!include "MUI2.nsh"
!include "x64.nsh"

; ==================== DEFINIÇÕES ====================
!define APP_NAME "DataMaster Pro"
!define APP_VERSION "1.5.0" ; <--- Mude aqui para atualizar o nome do instalador
!define EXE_NAME "DataMaster Pro.exe"
!define COMPANY "DataMaster"
!define ICON_PATH "assets\datamaster.ico"

Name "${APP_NAME}"
OutFile "${APP_NAME} Setup v${APP_VERSION}.exe"
InstallDir "$PROGRAMFILES\${APP_NAME}"

; Verificar privilégios de admin
RequestExecutionLevel admin

; ==================== INTERFACE VISUAL ====================
!define MUI_ICON "${ICON_PATH}"
!define MUI_UNICON "${ICON_PATH}"
; !define MUI_HEADERIMAGE
; !define MUI_HEADERIMAGE_BITMAP "assets\header.bmp" ; Opcional: Imagem de topo
!define MUI_ABORTWARNING

; Páginas do Instalador
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE.txt"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES

; Página final (Opção de Executar)
!define MUI_FINISHPAGE_RUN "$INSTDIR\${EXE_NAME}"
!insertmacro MUI_PAGE_FINISH

; Páginas do Desinstalador
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "PortugueseBR"

; ==================== INSTALAÇÃO ====================
Section "Instalar ${APP_NAME}"
    SetOutPath "$INSTDIR"
    
    ; Copia os arquivos do build (PYINSTALLER)
    File "dist\${EXE_NAME}"
    
    ; Cria atalhos
    CreateDirectory "$SMPROGRAMS\${APP_NAME}"
    CreateShortCut "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk" "$INSTDIR\${EXE_NAME}"
    CreateShortCut "$SMPROGRAMS\${APP_NAME}\Desinstalar.lnk" "$INSTDIR\Uninstall.exe"
    
    ; Atalho na área de trabalho
    CreateShortCut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\${EXE_NAME}"
    
    ; Cria desinstalador
    WriteUninstaller "$INSTDIR\Uninstall.exe"
    
    ; Registro para o Windows (Painel de Controle)
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayName" "${APP_NAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "UninstallString" "$INSTDIR\Uninstall.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayVersion" "${APP_VERSION}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "Publisher" "${COMPANY}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayIcon" "$INSTDIR\${EXE_NAME}"
SectionEnd

; ==================== DESINSTALAÇÃO ====================
Section "Uninstall"
    ; Remove arquivos
    Delete "$INSTDIR\${EXE_NAME}"
    Delete "$INSTDIR\Uninstall.exe"
    
    ; Remove atalhos
    Delete "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk"
    Delete "$SMPROGRAMS\${APP_NAME}\Desinstalar.lnk"
    RMDir "$SMPROGRAMS\${APP_NAME}"
    
    ; Remove atalho da área de trabalho
    Delete "$DESKTOP\${APP_NAME}.lnk"
    
    ; Remove diretório principal
    RMDir /r "$INSTDIR"
    
    ; Remove Registro
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}"
SectionEnd
