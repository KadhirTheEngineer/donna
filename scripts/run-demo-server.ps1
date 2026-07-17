$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$python = Join-Path $repo '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) {
    throw 'Missing .venv. Run scripts\bootstrap.ps1 first.'
}
Push-Location $repo
try {
    & $python -m donna_server
}
finally {
    Pop-Location
}
