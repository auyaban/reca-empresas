#define MyAppName "RECA Empresas"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "RECA"
#define MyAppExeName "RECA.exe"

[Setup]
AppId={{E5B8B38C-97C4-4B5C-9F59-7D2DA7E3A9C2}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=installer
OutputBaseFilename=RECA_Setup
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64
WizardStyle=modern

[Files]
Source: "dist\\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\\{#MyAppName}"; Filename: "{app}\\{#MyAppExeName}"
Name: "{commondesktop}\\{#MyAppName}"; Filename: "{app}\\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop icon"; GroupDescription: "Additional icons:"

[Run]
Filename: "powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -Command ""$p=Join-Path $env:TEMP 'vc_redist.x64.exe'; if (!(Test-Path $p)) {Invoke-WebRequest -Uri 'https://aka.ms/vs/17/release/vc_redist.x64.exe' -OutFile $p}; Start-Process -Wait -FilePath $p -ArgumentList '/install /quiet /norestart'"""; StatusMsg: "Installing Visual C++ Runtime..."; Check: not IsVCRuntimeInstalled; Flags: runhidden
Filename: "{app}\\{#MyAppExeName}"; Description: "Launch RECA Empresas"; Flags: nowait postinstall skipifsilent

[Code]
function IsVCRuntimeInstalled: Boolean;
var
  Installed: Cardinal;
begin
  if RegQueryDWordValue(HKLM, 'SOFTWARE\\Microsoft\\VisualStudio\\14.0\\VC\\Runtimes\\x64', 'Installed', Installed) then
    Result := Installed = 1
  else
    Result := False;
end;
