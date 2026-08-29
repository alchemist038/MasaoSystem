$ErrorActionPreference = 'Stop'
$ruleName = 'Masao Private Comment Reader - i5 Tailscale'

$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = [Security.Principal.WindowsPrincipal]::new($identity)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Run this script once from PowerShell opened as Administrator.'
}

$existing = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Output "Firewall rule already exists: $ruleName"
    exit 0
}

New-NetFirewallRule `
    -DisplayName $ruleName `
    -Direction Inbound `
    -Action Allow `
    -Enabled True `
    -Profile Any `
    -Protocol TCP `
    -LocalAddress '100.106.183.15' `
    -LocalPort 50002 `
    -RemoteAddress '100.124.36.15' `
    -Program 'C:\masao_ptz\_runtime_python314\python.exe' | Out-Null

Write-Output "Created firewall rule: $ruleName"
