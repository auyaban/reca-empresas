Build and installer (Windows)

Prereqs (build machine only):
- Python 3.10+ in PATH
- Inno Setup 6 installed

Build steps:
1) Run:
   powershell -ExecutionPolicy Bypass -File build.ps1
2) The executable is generated at:
   dist\RECA\RECA.exe

Installer steps:
1) Open installer.iss in Inno Setup.
2) Click Build > Compile.
3) The installer is generated at:
   installer\RECA_Setup.exe

Notes:
- The installer checks for the Visual C++ 2015-2022 runtime. If missing, it downloads and installs it.
- The installer writes a per-user .env file under AppData for Supabase credentials.
- Auto-update uses GitHub Releases and expects assets named RECA_Setup.exe and RECA_Setup.exe.sha256 in the latest release.

Release automation:
1) Ensure GitHub CLI is installed and logged in.
2) Run:
   powershell -ExecutionPolicy Bypass -File release.ps1 vX.Y.Z
3) The release is created with both assets attached.
