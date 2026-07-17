$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$venv = Join-Path $repo '.venv'
$python = Join-Path $venv 'Scripts\python.exe'

if (-not (Test-Path -LiteralPath $python)) {
    py -m venv $venv
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

& $python -m pip install --disable-pip-version-check -r (Join-Path $repo 'requirements-dev.lock')
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Output 'Python environment ready.'
if (-not (Get-Command cargo -ErrorAction SilentlyContinue)) {
    Write-Warning 'Cargo is not on PATH. Install Rust 1.97.1 with rustfmt and clippy; no system install was attempted.'
}
