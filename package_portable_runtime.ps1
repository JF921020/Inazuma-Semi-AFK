$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$runtimeRoot = Join-Path $projectRoot "portable_runtime"
$distRoot = Join-Path $projectRoot "dist"
$zipPath = Join-Path $distRoot "portable_runtime.zip"

if (-not (Test-Path $runtimeRoot)) {
    throw "Missing portable_runtime. Run build_portable_runtime.ps1 first."
}

if (-not (Test-Path $distRoot)) {
    New-Item -ItemType Directory -Path $distRoot -Force | Out-Null
}

if (Test-Path $zipPath) {
    Remove-Item -LiteralPath $zipPath -Force
}

Compress-Archive -Path (Join-Path $runtimeRoot "*") -DestinationPath $zipPath -Force

Write-Host "Portable runtime zip created at: $zipPath"
