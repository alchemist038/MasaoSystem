param(
    [string]$SourceDirectory = 'C:\masao\BouyomiChan_0_1_11_0_Beta21',
    [string]$DestinationDirectory = 'C:\masao\BouyomiChan_Comments_BT'
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $SourceDirectory -PathType Container)) {
    throw "Source BouyomiChan directory was not found: $SourceDirectory"
}
if (Test-Path -LiteralPath $DestinationDirectory) {
    throw "Destination already exists. It was not overwritten: $DestinationDirectory"
}

Copy-Item -LiteralPath $SourceDirectory -Destination $DestinationDirectory -Recurse

$oldExe = Join-Path $DestinationDirectory 'BouyomiChan.exe'
$newExe = Join-Path $DestinationDirectory 'BouyomiChanComments.exe'
Rename-Item -LiteralPath $oldExe -NewName 'BouyomiChanComments.exe'

$oldConfig = Join-Path $DestinationDirectory 'BouyomiChan.exe.config'
if (Test-Path -LiteralPath $oldConfig) {
    Rename-Item -LiteralPath $oldConfig -NewName 'BouyomiChanComments.exe.config'
}

$originalSettingPath = Join-Path $DestinationDirectory 'BouyomiChan.setting'
$settingPath = Join-Path $DestinationDirectory 'BouyomiChanComments.setting'
Copy-Item -LiteralPath $originalSettingPath -Destination $settingPath
$settingText = [IO.File]::ReadAllText($settingPath, [Text.UTF8Encoding]::new($false)).TrimStart([char]0xFEFF)
[xml]$setting = $settingText
$setting.Settings.EnableIpcChannel = 'false'
$setting.Settings.IpcChannelName = 'BouyomiChanComments'
$setting.Settings.EnableSocket = 'true'
$setting.Settings.PortNumber = '50003'
$setting.Settings.EnableHttpd = 'false'
$setting.Settings.PortNumberHttp = '50082'
$setting.Settings.OutDeviceID = '-1'
$setting.Settings.MinimizeTaskTray = 'true'
$setting.Settings.VersionCheck = 'false'
$setting.Settings.BroadcasterMode = 'false'
foreach ($plugin in $setting.Settings.Plugins.PluginInfo) {
    $plugin.Enabled = 'false'
}
$setting.Save($settingPath)

Write-Output "Prepared: $newExe"
Write-Output 'The output device remains unset. start_comment_reader.ps1 resolves Shokz and writes its WaveOut ID before launch.'
