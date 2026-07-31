param(
  [int]$Port = 8791
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$targets = @(Get-CimInstance Win32_Process | Where-Object {
  $_.CommandLine -match 'live_metrics_server\.py' -and
  $_.CommandLine -match "--port\s+$Port(?:\s|$)"
})

foreach ($target in $targets) {
  Stop-Process -Id $target.ProcessId -Force -ErrorAction Stop
}

Start-Sleep -Milliseconds 300
$remaining = @(Get-NetTCPConnection -LocalAddress '127.0.0.1' -LocalPort $Port `
  -State Listen -ErrorAction SilentlyContinue)

if ($remaining.Count -gt 0) {
  throw "Live metrics port $Port is still listening."
}

Write-Output "Stopped $($targets.Count) live metrics process(es); port $Port is closed."
