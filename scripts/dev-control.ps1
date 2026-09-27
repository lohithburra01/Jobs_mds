# Run the local coding controls without activating a Python environment.
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$bundledPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
if (Test-Path -LiteralPath $bundledPython) {
    $controlPython = $bundledPython
} else {
    $controlPython = (Get-Command python -ErrorAction Stop).Source
}
Push-Location -LiteralPath $projectRoot
try {
    & $controlPython -m devcontrol @args
    $controlExitCode = $LASTEXITCODE
} finally {
    Pop-Location
}
exit $controlExitCode
