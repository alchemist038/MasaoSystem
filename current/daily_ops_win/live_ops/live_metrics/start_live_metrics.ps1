param(
  [string]$Date = (Get-Date -Format 'yyyy-MM-dd'),
  [int]$Port = 8791,
  [int]$PollSeconds = 60,
  [string]$Python = ''
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($env:MASAO_YOUTUBE_LIVE_TOKEN_FILE)) {
  throw 'MASAO_YOUTUBE_LIVE_TOKEN_FILE is required.'
}

if ([string]::IsNullOrWhiteSpace($Python)) {
  $preferredPython = 'D:\\ツール\\masao_app\\runtime\\python314\\python.exe'
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
& $Python (Join-Path $scriptDir 'live_metrics_server.py') `
  --date $Date `
  --port $Port `
  --poll-seconds $PollSeconds
