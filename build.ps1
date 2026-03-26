$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$venvPath = Join-Path $root ".venv"
if (!(Test-Path $venvPath)) {
    python -m venv $venvPath
}

$python = Join-Path $venvPath "Scripts\\python.exe"
$hooksPath = Join-Path $root "hooks"

& $python -m pip install --upgrade pip
& $python -m pip install -r requirements.txt
& $python -m pip install pyinstaller

$iconPath = Join-Path $root "logo\logo_reca.ico"
$pyiArgs = @(
    "--noconfirm",
    "--clean",
    "--windowed",
    "--add-data", "logo\logo_reca.png;logo",
    "--additional-hooks-dir", $hooksPath,
    "--exclude-module", "pydantic.v1",
    "--exclude-module", "pydantic.mypy",
    "--exclude-module", "pydantic._hypothesis_plugin",
    "--name", "RECA",
    "--collect-all", "supabase",
    "app.py"
)
if (Test-Path $iconPath) {
    $pyiArgs = @("--icon", $iconPath) + $pyiArgs
}

& $python -m PyInstaller @pyiArgs
