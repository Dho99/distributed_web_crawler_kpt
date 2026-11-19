param(
    [Parameter(Mandatory = $true)][string]$Master,
    [Parameter(Mandatory = $true)][string]$Token,
    [int]$Port = 8010,
    [int]$PoolSize = 0,
    [string]$TaskName = "CrawlMesh Worker Agent"
)

$ErrorActionPreference = "Stop"

$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator
)
if (-not $isAdmin) {
    throw "Jalankan script ini sebagai Administrator (Register-ScheduledTask butuh elevation)."
}

$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    throw "Python venv tidak ditemukan di $python. Siapkan venv dan requirements.txt terlebih dahulu."
}

$arguments = @(
    "-m", "worker.agent",
    "--master", $Master,
    "--token=$Token",
    "--port", "$Port",
    "--discovery-port", "5599"
)
if ($PoolSize -gt 0) { $arguments += @("--pool-size", "$PoolSize") }

$action = New-ScheduledTaskAction -Execute $python -Argument ($arguments -join " ") -WorkingDirectory $root
$trigger = New-ScheduledTaskTrigger -AtStartup
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -RestartCount 999 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit (New-TimeSpan -Days 0)
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger `
    -Settings $settings -Principal $principal -Force | Out-Null
Start-ScheduledTask -TaskName $TaskName

Write-Host "Task '$TaskName' terpasang dan dijalankan."
Write-Host "Cek status:  Get-ScheduledTask -TaskName '$TaskName' | Get-ScheduledTaskInfo"
Write-Host "Hentikan  :  Stop-ScheduledTask -TaskName '$TaskName'"
Write-Host "Hapus     :  Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false"

