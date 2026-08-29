param(
    [string]$RuntimeDirectory = 'C:\masao\comment_reader_control',
    [string]$DesktopDirectory = [Environment]::GetFolderPath('Desktop')
)

$ErrorActionPreference = 'Stop'
$pythonw = 'C:\masao_ptz\_runtime_python314\pythonw.exe'
$appName = -join [char[]]@(
    0x307E, 0x3055, 0x304A, 0x0020,
    0x30B3, 0x30E1, 0x30F3, 0x30C8,
    0x8AAD, 0x307F, 0x4E0A, 0x3052
)
$appPath = Join-Path $RuntimeDirectory 'masao_comment_control.pyw'

if (-not (Test-Path -LiteralPath $pythonw -PathType Leaf)) {
    throw "pythonw.exe was not found: $pythonw"
}

New-Item -ItemType Directory -Path $RuntimeDirectory -Force | Out-Null
foreach ($name in @('masao_comment_control.pyw', 'obs_bridge.js', 'README.md')) {
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot $name) -Destination (Join-Path $RuntimeDirectory $name) -Force
}

$shortcutPath = Join-Path $DesktopDirectory "$appName.lnk"
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $pythonw
$shortcut.Arguments = '"' + $appPath + '"'
$shortcut.WorkingDirectory = $RuntimeDirectory
$shortcut.Description = 'Masao comment reader control'
$shortcut.Save()

Write-Output "Deployed: $RuntimeDirectory"
Write-Output "Shortcut: $shortcutPath"
