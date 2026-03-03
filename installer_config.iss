; ============================================================
; CyberBot GRC - Inno Setup Installer
; ============================================================
; PRÉ-REQUISITO: Gerar main.exe antes de compilar este instalador:
;   cd cyber_seguranca-installer
;   pyinstaller main.spec
;   (Saída: dist\main.exe)
; ============================================================

[Setup]
; Informações Básicas do Projeto [cite: 301]
AppName=CyberBot GRC Monitor
AppVersion=1.0
AppPublisher=Paulo André Carminati
AppPublisherURL=https://github.com/pacarminati/cyber_seguranca-installer
AppSupportURL=https://github.com/carmipa

; Configurações de Instalação [cite: 301]
DefaultDirName={autopf}\CyberBotGRC
DefaultGroupName=CyberBot GRC
SetupIconFile=assets\icon.ico
LicenseFile=LICENSE.txt
OutputDir=dist_installer
OutputBaseFilename=CyberBot_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Files]
; Executável: PyInstaller gera main.exe (main.spec name='main')
; Renomeado para CyberBot.exe em {autopf}\CyberBotGRC
Source: "dist\main.exe"; DestDir: "{app}"; DestName: "CyberBot.exe"; Flags: ignoreversion
; Assets: fallback externo (onefile já inclui assets no bundle)
Source: "assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs

[Icons]
; Atalho no Menu Iniciar [cite: 303]
Name: "{group}\CyberBot GRC"; Filename: "{app}\CyberBot.exe"
; Persistência: Inicialização Automática com o Windows (SOC Always-On) [cite: 303]
Name: "{autostartup}\CyberBot GRC"; Filename: "{app}\CyberBot.exe"

[Run]
; Opção para lançar o SOC imediatamente após instalar [cite: 303]
Filename: "{app}\CyberBot.exe"; Description: "Lançar CyberBot agora"; Flags: nowait postinstall skipifsilent