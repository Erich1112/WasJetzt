; Instalator WasJetzt (per utilizator, fără drepturi de administrator).
; Compilare: ISCC.exe installer\windows_installer.iss  (după python scripts\build.py)

#define MyAppName "WasJetzt"
#define MyAppVersion "1.0.0"
#define MyAppExeName "WasJetzt.exe"

[Setup]
AppId={{B3F2A5C1-7D4E-4F6A-9C2B-5E8D1A3F7B90}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher=WasJetzt
PrivilegesRequired=lowest
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=Output
OutputBaseFilename=WasJetzt_Setup
SetupIconFile=..\src\wasjetzt\resources\app.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
; Nu permite instalarea/dezinstalarea cât timp aplicația rulează (mutex creat de aplicație).
AppMutex=WasJetzt_SingleInstance_Mutex

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Creează o pictogramă pe Desktop"; GroupDescription: "Pictograme:"
Name: "startup"; Description: "Pornește WasJetzt automat când pornește Windows"; GroupDescription: "Pornire automată:"

[Files]
Source: "..\dist\WasJetzt\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
; Aceeași intrare ca cea creată din aplicație (valoarea „WasJetzt” din Run, doar pentru utilizatorul curent).
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "WasJetzt"; \
  ValueData: """{app}\{#MyAppExeName}"" --background"; Flags: uninsdeletevalue; Tasks: startup

[Run]
; Prima pornire (fără argumente) deschide wizard-ul de configurare inițială.
Filename: "{app}\{#MyAppExeName}"; Description: "Pornește WasJetzt acum"; Flags: nowait postinstall skipifsilent

[Code]
// Dezinstalare: elimină intrarea de startup (inclusiv cea creată din setările aplicației).
// Baza de date și exporturile din %LOCALAPPDATA%\WasJetzt, %APPDATA%\WasJetzt și directorul de export NU se șterg.
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
    RegDeleteValue(HKEY_CURRENT_USER, 'Software\Microsoft\Windows\CurrentVersion\Run', 'WasJetzt');
end;
