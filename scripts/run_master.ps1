param(
    [int]$Port = 8000,
    [string]$HostAddress = "0.0.0.0",
    [switch]$Reload
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    throw "Python venv tidak ditemukan di $python. Jalankan: python -m venv .venv; .venv\Scripts\pip install -r requirements.txt"
}

$env:CRAWLMESH_PORT = "$Port"
$env:CRAWLMESH_HOST = $HostAddress
Set-Location $root

if ($Reload) {
    & $python -m uvicorn master.app.main:app --host $HostAddress --port $Port --reload
} else {
    & $python -m master.app.main
}
