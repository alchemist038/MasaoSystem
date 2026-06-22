Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = 'py'
$updater = Join-Path $scriptDir 'update_room_sensor_hub.py'
$rootDir = Split-Path -Parent (Split-Path -Parent $scriptDir)
$logDir = Join-Path $rootDir 'logs'
$out = Join-Path $logDir 'masao_room_sensor_hub_watch.out.log'
$err = Join-Path $logDir 'masao_room_sensor_hub_watch.err.log'
$period = if ($env:MASAO_ROOM_SENSOR_HUB_PERIOD) { [double]$env:MASAO_ROOM_SENSOR_HUB_PERIOD } else { 60.0 }

function Import-UserSecretEnv {
    param([string]$Name)
    if (-not [Environment]::GetEnvironmentVariable($Name, 'Process')) {
        $value = [Environment]::GetEnvironmentVariable($Name, 'User')
        if (-not $value) {
            $value = [Environment]::GetEnvironmentVariable($Name, 'Machine')
        }
        if ($value) {
            [Environment]::SetEnvironmentVariable($Name, $value, 'Process')
        }
    }
}

Import-UserSecretEnv 'SWITCHBOT_TOKEN'
Import-UserSecretEnv 'SWITCHBOT_SECRET'
$env:PYTHONUNBUFFERED = '1'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

if (-not $env:SWITCHBOT_TOKEN -or -not $env:SWITCHBOT_SECRET) {
    throw 'SWITCHBOT_TOKEN or SWITCHBOT_SECRET is not set'
}

$hubEscaped = [regex]::Escape($updater)
$existing = Get-CimInstance Win32_Process |
    Where-Object {
        $_.ProcessId -ne $PID -and
        $_.Name -match '^(python|py)\.exe$' -and
        (
            ($_.CommandLine -match $hubEscaped -and $_.CommandLine -match '--periodic') -or
            ($_.CommandLine -match 'update_room_sensor\.py' -and $_.CommandLine -match '--periodic')
        )
    }
foreach ($process in $existing) {
    try {
        Stop-Process -Id $process.ProcessId -Force -ErrorAction Stop
        "[$(Get-Date -Format o)] [INFO] stopped existing room sensor watcher pid=$($process.ProcessId)" | Out-File -FilePath $out -Append -Encoding utf8
    } catch {
        "[$(Get-Date -Format o)] [WARN] failed to stop existing room sensor watcher pid=$($process.ProcessId): $($_.Exception.Message)" | Out-File -FilePath $err -Append -Encoding utf8
    }
}

"[$(Get-Date -Format o)] [INFO] launching hub room sensor watcher period=$period" | Out-File -FilePath $out -Append -Encoding utf8
& $python -3 $updater --periodic --period $period 1>> $out 2>> $err
