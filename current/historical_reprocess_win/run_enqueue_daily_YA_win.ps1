$ErrorActionPreference = 'Stop'
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) {
  throw 'python command not found'
}
& $py.Source (Join-Path $scriptDir 'scripts\enqueue_daily_YA_win.py') --config (Join-Path $scriptDir 'config.json') @args
