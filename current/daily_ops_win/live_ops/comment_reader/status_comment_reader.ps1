param(
    [string]$RuntimeDirectory = 'C:\masao\comment_reader'
)

$configPath = Join-Path $RuntimeDirectory 'config.json'
if (-not (Test-Path -LiteralPath $configPath -PathType Leaf)) {
    throw "Runtime config was not found: $configPath"
}
$configText = [IO.File]::ReadAllText($configPath, [Text.UTF8Encoding]::new($false)).TrimStart([char]0xFEFF)
$config = $configText | ConvertFrom-Json
$endpointPath = 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\MMDevices\Audio\Render\' + $config.bluetooth_endpoint_registry_id
$endpointState = if (Test-Path -LiteralPath $endpointPath) { (Get-ItemProperty -LiteralPath $endpointPath).DeviceState } else { $null }

[pscustomobject]@{
    ShokzActive = ([int]$endpointState -eq 1)
    ExistingBouyomi50001 = [bool](Get-NetTCPConnection -State Listen -LocalPort ([int]$config.primary_bouyomi_port) -ErrorAction SilentlyContinue)
    PrivateBouyomi50003 = [bool](Get-NetTCPConnection -State Listen -LocalPort ([int]$config.bouyomi_port) -ErrorAction SilentlyContinue)
    CommentListener50002 = [bool](Get-NetTCPConnection -State Listen -LocalPort ([int]$config.listen_port) -ErrorAction SilentlyContinue)
    LogPath = Join-Path $RuntimeDirectory 'logs\comment_reader.log'
} | Format-List
