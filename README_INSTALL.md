Build and installer (Windows)

Prereqs (build machine only):
- Python 3.10+ in PATH
- Inno Setup 6 installed

Build steps:
1) Run:
   powershell -ExecutionPolicy Bypass -File build.ps1
2) The executable is generated at:
   dist\RECA.exe

Installer steps:
1) Open installer.iss in Inno Setup.
2) Click Build > Compile.
3) The installer is generated at:
   installer\RECA_Setup.exe

Notes:
- The installer checks for the Visual C++ 2015-2022 runtime. If missing, it downloads and installs it.
- The app currently bundles config.py with Supabase credentials. Treat the installer as sensitive.
