param(
    [string]$RuntimeDirectory = 'C:\masao\comment_reader',
    [string]$BouyomiDirectory = 'C:\masao\BouyomiChan_Comments_BT',
    [string]$PythonExe = 'C:\masao_ptz\_runtime_python314\python.exe',
    [ValidateSet('Hidden', 'Minimized', 'Normal')]
    [string]$BouyomiWindowStyle = 'Normal'
)

$ErrorActionPreference = 'Stop'

$configPath = Join-Path $RuntimeDirectory 'config.json'
$listenerPath = Join-Path $RuntimeDirectory 'comment_reader.py'
$bouyomiExe = Join-Path $BouyomiDirectory 'BouyomiChanComments.exe'
$settingPath = Join-Path $BouyomiDirectory 'BouyomiChanComments.setting'
$stateDirectory = Join-Path $RuntimeDirectory 'state'
$pidPath = Join-Path $stateDirectory 'processes.json'

foreach ($requiredPath in @($configPath, $listenerPath, $bouyomiExe, $settingPath, $PythonExe)) {
    if (-not (Test-Path -LiteralPath $requiredPath -PathType Leaf)) {
        throw "Required file was not found: $requiredPath"
    }
}

$configText = [IO.File]::ReadAllText($configPath, [Text.UTF8Encoding]::new($false)).TrimStart([char]0xFEFF)
$config = $configText | ConvertFrom-Json
$endpointPath = 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\MMDevices\Audio\Render\' + $config.bluetooth_endpoint_registry_id
if (-not (Test-Path -LiteralPath $endpointPath)) {
    throw 'The configured Bluetooth audio endpoint is not registered.'
}
$endpoint = Get-ItemProperty -LiteralPath $endpointPath
if ([int]$endpoint.DeviceState -ne 1) {
    throw 'OpenRun Pro 2 is not connected as an active audio output. Nothing was started.'
}

$primaryConnection = Get-NetTCPConnection -State Listen -LocalPort ([int]$config.primary_bouyomi_port) -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $primaryConnection) {
    throw 'The existing stream BouyomiChan on port 50001 is not running. Private reading stays off.'
}

if (Get-NetTCPConnection -State Listen -LocalPort ([int]$config.bouyomi_port) -ErrorAction SilentlyContinue) {
    throw "Port $($config.bouyomi_port) is already in use. Nothing was started."
}
if (Get-NetTCPConnection -State Listen -LocalPort ([int]$config.listen_port) -ErrorAction SilentlyContinue) {
    throw "Port $($config.listen_port) is already in use. Nothing was started."
}

if (-not ('WaveOut.NativeMethods' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
namespace WaveOut {
    public static class NativeMethods {
        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
        public struct WAVEOUTCAPS {
            public ushort wMid;
            public ushort wPid;
            public uint vDriverVersion;
            [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)] public string szPname;
            public uint dwFormats;
            public ushort wChannels;
            public ushort wReserved1;
            public uint dwSupport;
        }
        [DllImport("winmm.dll")] public static extern uint waveOutGetNumDevs();
        [DllImport("winmm.dll", CharSet = CharSet.Unicode)]
        public static extern uint waveOutGetDevCaps(UIntPtr uDeviceID, out WAVEOUTCAPS caps, uint cbwoc);
    }
}
'@
}

$matches = @()
$deviceCount = [WaveOut.NativeMethods]::waveOutGetNumDevs()
for ($index = 0; $index -lt $deviceCount; $index++) {
    $caps = New-Object WaveOut.NativeMethods+WAVEOUTCAPS
    $result = [WaveOut.NativeMethods]::waveOutGetDevCaps([UIntPtr]::new([uint64]$index), [ref]$caps, [Runtime.InteropServices.Marshal]::SizeOf($caps))
    if ($result -eq 0 -and $caps.szPname -like "*$($config.bluetooth_waveout_name_contains)*") {
        $matches += [pscustomobject]@{ Id = $index; Name = $caps.szPname }
    }
}
if ($matches.Count -ne 1) {
    throw "Expected exactly one Shokz WaveOut device, found $($matches.Count). Nothing was started."
}

$settingText = [IO.File]::ReadAllText($settingPath, [Text.UTF8Encoding]::new($false)).TrimStart([char]0xFEFF)
[xml]$setting = $settingText
$setting.Settings.OutDeviceID = [string]$matches[0].Id
$setting.Settings.PortNumber = [string]$config.bouyomi_port
$setting.Settings.EnableSocket = 'true'
$setting.Settings.EnableHttpd = 'false'
if ($BouyomiWindowStyle -eq 'Normal') {
    $setting.Settings.MinimizeTaskTray = 'false'
    $setting.Settings.XssFormMain.WindowState = 'Normal'
}
$setting.Save($settingPath)

New-Item -ItemType Directory -Path $stateDirectory -Force | Out-Null
$bouyomiProcess = Start-Process -FilePath $bouyomiExe -WorkingDirectory $BouyomiDirectory -WindowStyle $BouyomiWindowStyle -PassThru

$deadline = (Get-Date).AddSeconds(20)
do {
    Start-Sleep -Milliseconds 250
    $bouyomiProcess.Refresh()
    $ready = Get-NetTCPConnection -State Listen -LocalPort ([int]$config.bouyomi_port) -ErrorAction SilentlyContinue
} until ($ready -or (Get-Date) -gt $deadline -or $bouyomiProcess.HasExited)

if (-not $ready -or $bouyomiProcess.HasExited) {
    if (-not $bouyomiProcess.HasExited) { Stop-Process -Id $bouyomiProcess.Id }
    throw 'The private BouyomiChan did not open port 50003.'
}

$listenerProcess = Start-Process -FilePath $PythonExe -ArgumentList @($listenerPath, '--config', $configPath) -WorkingDirectory $RuntimeDirectory -WindowStyle Hidden -PassThru
Start-Sleep -Seconds 1
if ($listenerProcess.HasExited) {
    Stop-Process -Id $bouyomiProcess.Id -ErrorAction SilentlyContinue
    throw 'The private comment listener exited during startup.'
}

@{
    started_at = (Get-Date).ToString('o')
    listener_pid = $listenerProcess.Id
    listener_path = $listenerPath
    bouyomi_pid = $bouyomiProcess.Id
    bouyomi_path = $bouyomiExe
    waveout_id = $matches[0].Id
    waveout_name = $matches[0].Name
} | ConvertTo-Json | Set-Content -LiteralPath $pidPath -Encoding utf8

Write-Output "Private comment reader started. listener=$($listenerProcess.Id) bouyomi=$($bouyomiProcess.Id) device=$($matches[0].Name)"
