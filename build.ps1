$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$venvPath = Join-Path $root ".venv"
if (!(Test-Path $venvPath)) {
    python -m venv $venvPath
}

$python = Join-Path $venvPath "Scripts\\python.exe"

& $python -m pip install --upgrade pip
& $python -m pip install -r requirements.txt
& $python -m pip install pyinstaller

& $python -m PyInstaller `
    --noconfirm `
    --clean `
    --windowed `
    --onefile `
    --name "RECA" `
    --collect-all supabase `
    app.py
