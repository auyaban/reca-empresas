#define MyAppName "RECA Empresas"
#define MyAppVersion "1.0.10"
#define MyAppPublisher "RECA"
#define MyAppExeName "RECA.exe"
#define SupabaseUrl "https://zvhjosktmfisryqcjxbh.supabase.co"
#define SupabaseKey "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inp2aGpvc2t0bWZpc3J5cWNqeGJoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjU5OTI4MjksImV4cCI6MjA4MTU2ODgyOX0.jU9Y7exHXD4oePKZ_zOOzYy8tX4p8yLK_N_kHXD-lgg"

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
SetupIconFile=logo\logo_reca.ico

[Files]
Source: "dist\\RECA\\*"; DestDir: "{app}\\RECA"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\\{#MyAppName}"; Filename: "{app}\\RECA\\{#MyAppExeName}"
Name: "{commondesktop}\\{#MyAppName}"; Filename: "{app}\\RECA\\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop icon"; GroupDescription: "Additional icons:"

[Run]
Filename: "powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -Command ""$p=Join-Path $env:TEMP 'vc_redist.x64.exe'; if (!(Test-Path $p)) {{Invoke-WebRequest -Uri 'https://aka.ms/vs/17/release/vc_redist.x64.exe' -OutFile $p}}; Start-Process -Wait -FilePath $p -ArgumentList '/install /quiet /norestart'"""; StatusMsg: "Installing Visual C++ Runtime..."; Check: not IsVCRuntimeInstalled; Flags: runhidden
Filename: "{app}\\RECA\\{#MyAppExeName}"; Description: "Launch RECA Empresas"; Flags: nowait postinstall skipifsilent

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

procedure CurStepChanged(CurStep: TSetupStep);
var
  EnvPath: string;
  EnvContent: string;
begin
  if CurStep = ssInstall then
  begin
    ForceDirectories(ExpandConstant('{userappdata}\\{#MyAppName}'));
    EnvPath := ExpandConstant('{userappdata}\\{#MyAppName}\\.env');
    EnvContent := 'SUPABASE_URL={#SupabaseUrl}' + #13#10 +
                  'SUPABASE_KEY={#SupabaseKey}' + #13#10;
    SaveStringToFile(EnvPath, EnvContent, False);
  end;
end;
