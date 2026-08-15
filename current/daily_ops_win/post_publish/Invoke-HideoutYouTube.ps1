[CmdletBinding()]
param(
    [ValidateSet('status', 'list-recent', 'inspect', 'upload-manifest')]
    [string]$Command = 'status',

    [string]$VideoId,
    [string]$Manifest,

    [ValidateRange(1, 50)]
    [int]$Limit = 20,

    [switch]$Execute,
    [switch]$Json
)

$ErrorActionPreference = 'Stop'

$python = 'D:\ツール\masao_app\runtime\python314\python.exe'
$script = Join-Path $PSScriptRoot 'youtube_hideout_manage.py'

if (-not (Test-Path -LiteralPath $python)) {
    throw "Python runtime not found: $python"
}
if (-not (Test-Path -LiteralPath $script)) {
    throw "Hideout API script not found: $script"
}

$arguments = @($script)
if ($Json) {
    $arguments += '--json'
}

switch ($Command) {
    'status' {
        $arguments += 'status'
    }
    'list-recent' {
        $arguments += @('list-recent', '--limit', $Limit)
    }
    'inspect' {
        if (-not $VideoId) {
            throw '-VideoId is required for inspect.'
        }
        $arguments += @('inspect', $VideoId)
    }
    'upload-manifest' {
        if (-not $Manifest) {
            throw '-Manifest is required for upload-manifest.'
        }
        $arguments += @('upload-manifest', $Manifest)
        if ($Execute) {
            $arguments += '--execute'
        }
    }
}

& $python @arguments
exit $LASTEXITCODE
