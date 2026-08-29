param(
    [string]$RuntimeDirectory = 'C:\masao\comment_reader'
)

$ErrorActionPreference = 'Stop'
$pidPath = Join-Path $RuntimeDirectory 'state\processes.json'
$configPath = Join-Path $RuntimeDirectory 'config.json'
if (-not (Test-Path -LiteralPath $pidPath -PathType Leaf)) {
    Write-Output 'No private comment-reader PID record was found.'
    exit 0
}

$recordText = [IO.File]::ReadAllText($pidPath, [Text.UTF8Encoding]::new($false)).TrimStart([char]0xFEFF)
$record = $recordText | ConvertFrom-Json
$configText = [IO.File]::ReadAllText($configPath, [Text.UTF8Encoding]::new($false)).TrimStart([char]0xFEFF)
$config = $configText | ConvertFrom-Json
$targets = @(
    [pscustomobject]@{ Id = [int]$record.listener_pid; ExpectedPath = [string]$record.listener_path; Kind = 'listener' },
    [pscustomobject]@{ Id = [int]$record.bouyomi_pid; ExpectedPath = [string]$record.bouyomi_path; Kind = 'bouyomi' }
)

foreach ($target in $targets) {
    $process = Get-CimInstance Win32_Process -Filter "ProcessId=$($target.Id)" -ErrorAction SilentlyContinue
    if (-not $process) { continue }
    $matches = $process.ExecutablePath -eq $target.ExpectedPath -or $process.CommandLine -like "*$($target.ExpectedPath)*"
    if (-not $matches) {
        throw "PID $($target.Id) no longer belongs to the private $($target.Kind). It was not stopped."
    }
    Stop-Process -Id $target.Id -Force
}

$privatePorts = @([int]$config.listen_port, [int]$config.bouyomi_port)
$deadline = (Get-Date).AddSeconds(20)
do {
    $openPorts = @(
        Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
            Where-Object { $privatePorts -contains [int]$_.LocalPort }
    )
    if (-not $openPorts) { break }
    Start-Sleep -Milliseconds 250
} until ((Get-Date) -gt $deadline)

if ($openPorts) {
    throw "Private comment-reader ports did not close: $($openPorts.LocalPort -join ', ')"
}

foreach ($target in $targets) {
    Stop-Process -Id $target.Id -Force -ErrorAction SilentlyContinue
}

Remove-Item -LiteralPath $pidPath
Write-Output 'Private comment reader stopped. Existing stream BouyomiChan was not touched.'
