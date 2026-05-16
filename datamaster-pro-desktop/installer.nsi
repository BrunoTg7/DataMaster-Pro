; DataMaster Pro - Instalador NSIS
; Cria um instalador profissional para Windows

!include "MUI2.nsh"
!include "x64.nsh"

; Definições
Name "DataMaster Pro"
OutFile "DataMaster Pro Setup.exe"
InstallDir "$PROGRAMFILES\DataMaster Pro"

; Verificar privilégios de admin
RequestExecutionLevel admin

; Configuração MUI
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_LANGUAGE "PortugueseBR"

; Seção de instalação
Section "Instalar DataMaster Pro"
    SetOutPath "$INSTDIR"
    
    ; Copia o executável
    File "dist\DataMaster Pro.exe"
    
    ; Copia arquivo de configuração (.env)
    File ".env"
    
    ; Cria atalhos
    CreateDirectory "$SMPROGRAMS\DataMaster Pro"
    CreateShortCut "$SMPROGRAMS\DataMaster Pro\DataMaster Pro.lnk" "$INSTDIR\DataMaster Pro.exe"
    CreateShortCut "$SMPROGRAMS\DataMaster Pro\Desinstalar.lnk" "$INSTDIR\Uninstall.exe"
    
    ; Atalho na área de trabalho
    CreateShortCut "$DESKTOP\DataMaster Pro.lnk" "$INSTDIR\DataMaster Pro.exe"
    
    ; Cria desinstalador
    WriteUninstaller "$INSTDIR\Uninstall.exe"
    
    ; Registry para Add/Remove Programs
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\DataMasterPro" "DisplayName" "DataMaster Pro"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\DataMasterPro" "UninstallString" "$INSTDIR\Uninstall.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\DataMasterPro" "DisplayVersion" "1.0.0"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\DataMasterPro" "Publisher" "DataMaster"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\DataMasterPro" "DisplayIcon" "$INSTDIR\DataMaster Pro.exe"
SectionEnd

; Seção de desinstalação
Section "Uninstall"
    ; Remove arquivos
    Delete "$INSTDIR\DataMaster Pro.exe"
    Delete "$INSTDIR\.env"
    Delete "$INSTDIR\Uninstall.exe"
    
    ; Remove atalhos
    Delete "$SMPROGRAMS\DataMaster Pro\DataMaster Pro.lnk"
    Delete "$SMPROGRAMS\DataMaster Pro\Desinstalar.lnk"
    RMDir "$SMPROGRAMS\DataMaster Pro"
    
    ; Remove atalho da área de trabalho
    Delete "$DESKTOP\DataMaster Pro.lnk"
    
    ; Remove diretório
    RMDir "$INSTDIR"
    
    ; Remove Registry
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\DataMasterPro"
SectionEnd
