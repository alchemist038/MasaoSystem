param(
  [string]$Destination = 'C:\Users\alche\Desktop\OBS\scripts',
  [switch]$IncludeYoutubeLive
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $MyInvocation.MyCommand.Path

if (-not (Test-Path -LiteralPath $Destination)) {
  throw "Destination does not exist: $Destination"
}

$copySets = @(
  @{ Source = Join-Path $root 'obs_scripts'; Pattern = '*' },
  @{ Source = Join-Path $root 'fallback'; Pattern = '*' }
)

if ($IncludeYoutubeLive) {
  $copySets += @{ Source = Join-Path $root 'youtube_live'; Pattern = 'youtube_live_broadcasts.py' }
} else {
  Write-Output 'skip: YouTube Live script and thumbnails (use -IncludeYoutubeLive after token env/local setup is confirmed)'
}

foreach ($set in $copySets) {
  Get-ChildItem -LiteralPath $set.Source -File -Filter $set.Pattern | ForEach-Object {
    $target = Join-Path $Destination $_.Name
    Copy-Item -LiteralPath $_.FullName -Destination $target -Force
    Write-Output "deployed: $($_.FullName) -> $target"
  }
}

if ($IncludeYoutubeLive) {
  $thumbnailSource = Join-Path $root 'youtube_live\thumbnails'
  $thumbnailDestination = Join-Path (Split-Path -Parent $Destination) 'サムネ'
  New-Item -ItemType Directory -Force -Path $thumbnailDestination | Out-Null
  Get-ChildItem -LiteralPath $thumbnailSource -File -Filter '*.jpg' | ForEach-Object {
    $target = Join-Path $thumbnailDestination $_.Name
    Copy-Item -LiteralPath $_.FullName -Destination $target -Force
    Write-Output "deployed: $($_.FullName) -> $target"
  }
}
