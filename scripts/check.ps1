$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$python = Join-Path $repo '.venv\Scripts\python.exe'

if (-not (Test-Path -LiteralPath $python)) {
    throw 'Missing .venv. Run scripts\bootstrap.ps1 first.'
}

Push-Location $repo
try {
    & $python -m ruff format --check server scripts
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $python -m ruff check server scripts
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $python -m mypy
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $python -m pytest
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $python scripts\check_contracts.py
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $python scripts\check_migrations.py
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $python -m donna_server validate-config
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    $cargo = Get-Command cargo -ErrorAction SilentlyContinue
    $cargoPath = if ($cargo) { $cargo.Source } else { $null }
    $toolchain = $null
    if (-not $cargo) {
        $localCargo = Join-Path $repo '.tools\cargo\bin\cargo.exe'
        if (-not (Test-Path -LiteralPath $localCargo)) {
            throw 'Cargo is unavailable. Install the pinned Rust toolchain from rust-toolchain.toml.'
        }
        $env:CARGO_HOME = Join-Path $repo '.tools\cargo'
        $env:RUSTUP_HOME = Join-Path $repo '.tools\rustup'
        $env:PATH = "$env:CARGO_HOME\bin;$env:PATH"
        $cargoPath = $localCargo

        $localGcc = Join-Path $repo '.tools\winlibs\mingw64\bin\gcc.exe'
        if (Test-Path -LiteralPath $localGcc) {
            $mingwBin = Split-Path -Parent $localGcc
            $env:PATH = "$mingwBin;$env:PATH"
            $env:CARGO_TARGET_X86_64_PC_WINDOWS_GNU_LINKER = $localGcc
            $toolchain = '+1.97.1-x86_64-pc-windows-gnu'
        }
    }

    $cargoArgs = @()
    if ($toolchain) { $cargoArgs += $toolchain }
    & $cargoPath @cargoArgs fmt --check
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $cargoPath @cargoArgs test --locked
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $cargoPath @cargoArgs clippy --locked --all-targets --all-features -- -D warnings
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $cargoPath @cargoArgs build --locked --release
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
finally {
    Pop-Location
}
