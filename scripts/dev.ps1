param(
    [int]$MasterPort = 8000,
    [int]$WebPort = 5173
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    throw "Python venv tidak ditemukan. Jalankan: python -m venv .venv; .venv\Scripts\pip install -r requirements.txt"
}

Set-Location $root
$master = Start-Process -FilePath $python `
    -ArgumentList "-m", "uvicorn", "master.app.main:app", "--host", "0.0.0.0", "--port", "$MasterPort", "--reload" `
    -PassThru -WindowStyle Hidden `
    -RedirectStandardOutput (Join-Path $root "data\master.out.log") `
    -RedirectStandardError (Join-Path $root "data\master.err.log")

Write-Host "Master PID $($master.Id) -> http://127.0.0.1:$MasterPort (docs: /docs)"
Write-Host "Menjalankan Vite dev server..."

Push-Location (Join-Path $root "web")
try {
    npm run dev -- --port $WebPort
} finally {
    Pop-Location
    if (-not $master.HasExited) { Stop-Process -Id $master.Id -Force }
}
