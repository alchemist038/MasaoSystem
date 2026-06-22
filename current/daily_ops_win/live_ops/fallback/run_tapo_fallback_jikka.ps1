Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

node .\tapo_fallback_controller.js --config="$scriptDir\tapo_fallback_config_jikka.json" @args
