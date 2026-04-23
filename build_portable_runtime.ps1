$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    throw "Missing .venv\Scripts\python.exe. Create the venv and install packages first."
}

$basePrefix = & $venvPython -c "import sys; print(sys.base_prefix)"
if (-not $basePrefix) {
    throw "Failed to resolve the base Python installation path."
}

$runtimeRoot = Join-Path $projectRoot "portable_runtime"
$pythonRoot = Join-Path $runtimeRoot "python"
$venvSitePackages = Join-Path $projectRoot ".venv\Lib\site-packages"

if (Test-Path $runtimeRoot) {
    Remove-Item -LiteralPath $runtimeRoot -Recurse -Force
}

New-Item -ItemType Directory -Path $pythonRoot -Force | Out-Null

$baseFiles = @(
    "python.exe",
    "pythonw.exe",
    "python3.dll",
    "python310.dll",
    "vcruntime140.dll",
    "vcruntime140_1.dll",
    "LICENSE.txt"
)

foreach ($file in $baseFiles) {
    $source = Join-Path $basePrefix $file
    if (Test-Path $source) {
        Copy-Item -LiteralPath $source -Destination $pythonRoot -Force
    }
}

foreach ($dir in @("DLLs", "Lib")) {
    $source = Join-Path $basePrefix $dir
    $destination = Join-Path $pythonRoot $dir
    Copy-Item -LiteralPath $source -Destination $destination -Recurse -Force
}

$stdlibSitePackages = Join-Path $pythonRoot "Lib\site-packages"
if (Test-Path $stdlibSitePackages) {
    Remove-Item -LiteralPath $stdlibSitePackages -Recurse -Force
}

Copy-Item -LiteralPath $venvSitePackages -Destination $stdlibSitePackages -Recurse -Force

$runtimeReadme = @"
Portable runtime built from:
- Base Python: $basePrefix
- Venv packages: $venvSitePackages

Usage:
1. Keep this portable_runtime folder next to main.py
2. Start the project with start_portable.bat
"@

Set-Content -LiteralPath (Join-Path $runtimeRoot "README.txt") -Value $runtimeReadme -Encoding UTF8

Write-Host "Portable runtime created at: $runtimeRoot"
