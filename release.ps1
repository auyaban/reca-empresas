$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

if (-not $args[0]) {
    Write-Host "Usage: .\\release.ps1 vX.Y.Z"
    exit 1
}

$version = $args[0]

$gh = "gh"
if (-not (Get-Command $gh -ErrorAction SilentlyContinue)) {
    $ghPath = "C:\\Program Files\\GitHub CLI\\gh.exe"
    if (Test-Path $ghPath) {
        $gh = $ghPath
    } else {
        Write-Host "GitHub CLI not found. Install it with winget or set PATH."
        exit 1
    }
}

& $gh auth status -h github.com | Out-Null

powershell -ExecutionPolicy Bypass -File build.ps1

& "C:\\Program Files (x86)\\Inno Setup 6\\ISCC.exe" installer.iss

$hash = (Get-FileHash -Algorithm SHA256 installer\\RECA_Setup.exe).Hash.ToLower()
"$hash  RECA_Setup.exe" | Set-Content installer\\RECA_Setup.exe.sha256

& $gh release create $version installer\\RECA_Setup.exe installer\\RECA_Setup.exe.sha256 `
  --title "RECA Empresas $version" `
  --notes "Release $version"
