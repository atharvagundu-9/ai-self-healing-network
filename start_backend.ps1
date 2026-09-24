$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    throw "Virtual environment not found. Follow the backend setup steps in README.md first."
}
Set-Location -LiteralPath $projectRoot
& $python -m uvicorn backend.main:app --reload --port 8000

