param(
    [string]$Master = "http://127.0.0.1:8000",
    [string]$Token = "",
    [int]$Port = 8010,
    [int]$PoolSize = 0,
    [int]$Capacity = 0,
    [string]$Name = "",
    [int]$DiscoveryPort = 5599
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    throw "Python venv tidak ditemukan di $python."
}
if (-not $Token) {
    $envFile = Join-Path $root ".env"
    if (Test-Path $envFile) {
        $line = Get-Content $envFile | Where-Object { $_ -match '^CRAWLMESH_TOKEN=' } | Select-Object -First 1
        if ($line) { $Token = $line.Split("=", 2)[1].Trim() }
    }
}
if (-not $Token) {
    throw "Pairing token kosong. Ambil dari GUI (Settings/Cluster) atau salin ke .env sebagai CRAWLMESH_TOKEN=..."
}

$argsList = @(
    "-m", "worker.agent",
    "--master", $Master,
    "--token=$Token",
    "--port", "$Port",
    "--discovery-port", "$DiscoveryPort"
)
if ($PoolSize -gt 0) { $argsList += @("--pool-size", "$PoolSize") }
if ($Capacity -gt 0) { $argsList += @("--capacity", "$Capacity") }
if ($Name) { $argsList += @("--name", $Name) }

Set-Location $root
& $python @argsList

