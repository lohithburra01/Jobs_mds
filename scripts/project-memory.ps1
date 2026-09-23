$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$memoryPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
if (-not (Test-Path -LiteralPath $memoryPython)) {
    $memoryPython = (Get-Command python -ErrorAction Stop).Source
}
& $memoryPython (Join-Path $PSScriptRoot 'project_memory.py') @args
exit $LASTEXITCODE
