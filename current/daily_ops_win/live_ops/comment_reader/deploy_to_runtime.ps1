param(
    [string]$RuntimeDirectory = 'C:\masao\comment_reader'
)

$ErrorActionPreference = 'Stop'
$sourceDirectory = $PSScriptRoot
New-Item -ItemType Directory -Path $RuntimeDirectory -Force | Out-Null

foreach ($name in @('comment_reader.py', 'start_comment_reader.ps1', 'stop_comment_reader.ps1', 'status_comment_reader.ps1', 'install_firewall_rule.ps1')) {
    Copy-Item -LiteralPath (Join-Path $sourceDirectory $name) -Destination (Join-Path $RuntimeDirectory $name) -Force
}

$configPath = Join-Path $RuntimeDirectory 'config.json'
if (-not (Test-Path -LiteralPath $configPath)) {
    Copy-Item -LiteralPath (Join-Path $sourceDirectory 'config.example.json') -Destination $configPath
}
$aliasesPath = Join-Path $RuntimeDirectory 'aliases.json'
if (-not (Test-Path -LiteralPath $aliasesPath)) {
    Copy-Item -LiteralPath (Join-Path $sourceDirectory 'aliases.example.json') -Destination $aliasesPath
}

Write-Output "Deployed private comment-reader files to $RuntimeDirectory"
Write-Output 'Existing runtime config and aliases were preserved.'
