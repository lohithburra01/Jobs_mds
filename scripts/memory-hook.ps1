param([switch]$Synthetic, [ValidatePattern('^[a-z]+$')][string]$Agent = 'codex')
# The agent (Codex, Claude Code, ...) sends one JSON object on stdin. Never execute commands from that object.
$ErrorActionPreference = 'Stop'
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$memoryPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
if (-not (Test-Path -LiteralPath $memoryPython)) {
    $memoryPython = (Get-Command python -ErrorAction Stop).Source
}
$memoryInput = [Console]::In.ReadToEnd()
if ($Synthetic) {
    $memoryInput | & $memoryPython (Join-Path $PSScriptRoot 'memory_hook.py') --synthetic --agent $Agent
} else {
    $memoryInput | & $memoryPython (Join-Path $PSScriptRoot 'memory_hook.py') --agent $Agent
}
exit $LASTEXITCODE
