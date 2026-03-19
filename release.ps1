$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

if (-not (Test-Path "app.py")) {
    Write-Host "app.py not found."
    exit 1
}

$appPy = Get-Content "app.py" -Raw
$appVersionMatch = [regex]::Match($appPy, 'APP_VERSION\s*=\s*"([^"]+)"')
if (-not $appVersionMatch.Success) {
    Write-Host "Could not read APP_VERSION from app.py"
    exit 1
}

$appVersion = $appVersionMatch.Groups[1].Value
$version = if ($args[0]) { $args[0] } else { "v$appVersion" }
$normalizedVersion = $version.TrimStart("v")

if ($normalizedVersion -ne $appVersion) {
    Write-Host "Version mismatch: app.py has $appVersion but release requested $version"
    exit 1
}

$installerIss = "installer.iss"
if (-not (Test-Path $installerIss)) {
    Write-Host "installer.iss not found."
    exit 1
}

$installerContent = Get-Content $installerIss -Raw
$updatedInstallerContent = [regex]::Replace(
    $installerContent,
    '#define MyAppVersion "[^"]+"',
    "#define MyAppVersion `"$appVersion`"",
    1
)

if ($installerContent -ne $updatedInstallerContent) {
    Set-Content -Path $installerIss -Value $updatedInstallerContent -Encoding UTF8
}

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

$releaseCheck = Start-Process -FilePath $gh -ArgumentList @("release", "view", $version) -NoNewWindow -Wait -PassThru -RedirectStandardOutput $null -RedirectStandardError $null
if ($releaseCheck.ExitCode -eq 0) {
    Write-Host "Release $version already exists."
    exit 1
}

powershell -ExecutionPolicy Bypass -File build.ps1

& "C:\\Program Files (x86)\\Inno Setup 6\\ISCC.exe" installer.iss

$hash = (Get-FileHash -Algorithm SHA256 installer\\RECA_Setup.exe).Hash.ToLower()
"$hash  RECA_Setup.exe" | Set-Content installer\\RECA_Setup.exe.sha256

& $gh release create $version installer\\RECA_Setup.exe installer\\RECA_Setup.exe.sha256 `
  --title "RECA Empresas $version" `
  --notes "Release $version"
