Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = (Get-Command py.exe -ErrorAction Stop).Source
$updater = Join-Path $scriptDir 'update_room_sensor_hub.py'
$rootDir = Split-Path -Parent (Split-Path -Parent $scriptDir)
$logDir = Join-Path $rootDir 'logs'
$out = Join-Path $logDir 'masao_room_sensor_hub_watch.out.log'
$err = Join-Path $logDir 'masao_room_sensor_hub_watch.err.log'
$runtimeOut = Join-Path $logDir 'masao_room_sensor_hub_runtime.out.log'
$runtimeErr = Join-Path $logDir 'masao_room_sensor_hub_runtime.err.log'
$period = if ($env:MASAO_ROOM_SENSOR_HUB_PERIOD) { [double]$env:MASAO_ROOM_SENSOR_HUB_PERIOD } else { 60.0 }

function Write-LauncherLog {
    param(
        [string]$Level,
        [string]$Message
    )
    $line = "[$(Get-Date -Format o)] [$Level] $Message"
    try {
        New-Item -ItemType Directory -Force -Path $logDir -ErrorAction Stop | Out-Null
        $target = if ($Level -eq 'WARN') { $err } else { $out }
        $line | Out-File -FilePath $target -Append -Encoding utf8 -ErrorAction Stop
    } catch {
        try {
            [Console]::Error.WriteLine("[room-sensor-launcher-log-write-failed] $($_.Exception.Message)")
            [Console]::Error.WriteLine($line)
        } catch {
            # Ignore logging failures. The watcher should survive temporary D: I/O loss.
        }
    }
}

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
try {
    New-Item -ItemType Directory -Force -Path $logDir -ErrorAction Stop | Out-Null
} catch {
    Write-LauncherLog 'WARN' "log directory is temporarily unavailable: $($_.Exception.Message)"
}

if (-not $env:SWITCHBOT_TOKEN -or -not $env:SWITCHBOT_SECRET) {
    throw 'SWITCHBOT_TOKEN or SWITCHBOT_SECRET is not set'
}

$hubEscaped = [regex]::Escape($updater)
$existing = @(Get-CimInstance Win32_Process |
    Where-Object {
        $_.ProcessId -ne $PID -and
        $_.Name -match '^(python|py)\.exe$' -and
        (
            ($_.CommandLine -match $hubEscaped -and $_.CommandLine -match '--periodic') -or
            ($_.CommandLine -match 'update_room_sensor\.py' -and $_.CommandLine -match '--periodic')
        )
    })
foreach ($process in $existing) {
    try {
        if (-not (Get-Process -Id $process.ProcessId -ErrorAction SilentlyContinue)) {
            Write-LauncherLog 'INFO' "existing room sensor watcher already exited pid=$($process.ProcessId)"
            continue
        }
        Stop-Process -Id $process.ProcessId -Force -ErrorAction Stop
        Write-LauncherLog 'INFO' "stopped existing room sensor watcher pid=$($process.ProcessId)"
    } catch {
        Write-LauncherLog 'WARN' "failed to stop existing room sensor watcher pid=$($process.ProcessId): $($_.Exception.Message)"
    }
}

if ($existing.Count -gt 0) {
    Start-Sleep -Milliseconds 500
}

Write-LauncherLog 'INFO' "launching hub room sensor watcher period=$period"
$periodText = $period.ToString([Globalization.CultureInfo]::InvariantCulture)
$process = Start-Process -FilePath $python `
    -ArgumentList @('-3', $updater, '--periodic', '--period', $periodText) `
    -WindowStyle Hidden `
    -RedirectStandardOutput $runtimeOut `
    -RedirectStandardError $runtimeErr `
    -PassThru

Start-Sleep -Seconds 2
if ($process.HasExited) {
    $detail = Get-Content -LiteralPath $runtimeErr -Tail 20 -ErrorAction SilentlyContinue
    throw "Room sensor watcher exited during startup (exit=$($process.ExitCode)): $($detail -join ' ')"
}

Write-LauncherLog 'INFO' "started detached hub room sensor watcher pid=$($process.Id) period=$period"
Write-Output "Room sensor watcher started PID $($process.Id)."
