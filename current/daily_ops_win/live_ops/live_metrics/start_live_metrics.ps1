param(
  [string]$Date = (Get-Date -Format 'yyyy-MM-dd'),
  [int]$Port = 8791,
  [int]$PollSeconds = 60,
  [string]$Python = '',
  [string]$TokenFile = 'D:\MasaoSystem\shared\keys\youtube\token.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($env:MASAO_YOUTUBE_LIVE_TOKEN_FILE)) {
  if (-not (Test-Path -LiteralPath $TokenFile)) {
    throw "YouTube Live token file was not found: $TokenFile"
  }
  $env:MASAO_YOUTUBE_LIVE_TOKEN_FILE = $TokenFile
}

if ([string]::IsNullOrWhiteSpace($Python)) {
  $preferredPython = 'C:\masao_ptz\_runtime_python314\python.exe'
  if (Test-Path -LiteralPath $preferredPython) {
    $Python = $preferredPython
  }
  else {
    $py = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($null -eq $py) {
      throw 'Python was not found. Pass -Python with an explicit interpreter path.'
    }
    $Python = $py.Source
  }
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$server = Join-Path $scriptDir 'live_metrics_server.py'
$escapedServer = [regex]::Escape($server)
$existing = @(Get-CimInstance Win32_Process | Where-Object {
  $_.CommandLine -match $escapedServer -and $_.CommandLine -match "--port\s+$Port(?:\s|$)"
})
if ($existing.Count -gt 0) {
  Write-Output "Live metrics already running PID $($existing[0].ProcessId) on port $Port."
  return
}

$obsDir = Split-Path -Parent (Split-Path -Parent $scriptDir)
$logsDir = Join-Path $obsDir 'logs'
New-Item -ItemType Directory -Path $logsDir -Force | Out-Null
$stdout = Join-Path $logsDir "live_metrics_${Date}_${Port}.runtime.out.log"
$stderr = Join-Path $logsDir "live_metrics_${Date}_${Port}.runtime.err.log"
$arguments = @(
  $server,
  '--date', $Date,
  '--port', $Port,
  '--poll-seconds', $PollSeconds
)
$process = Start-Process -FilePath $Python `
  -ArgumentList $arguments `
  -WindowStyle Hidden `
  -RedirectStandardOutput $stdout `
  -RedirectStandardError $stderr `
  -PassThru
Start-Sleep -Seconds 2
if ($process.HasExited) {
  $detail = if (Test-Path -LiteralPath $stderr) {
    (Get-Content -LiteralPath $stderr -Tail 20) -join [Environment]::NewLine
  }
  else {
    'No error log was created.'
  }
  throw "Live metrics exited during startup.$([Environment]::NewLine)$detail"
}
Write-Output "Live metrics started PID $($process.Id) on port $Port."
