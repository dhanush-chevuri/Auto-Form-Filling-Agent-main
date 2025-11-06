<#
Start-backend.ps1

Creates a venv in backend (if missing), installs requirements, and launches the FastAPI
server (uvicorn) in a new PowerShell window so it remains running.

Usage: Right-click -> Run with PowerShell, or from a PowerShell prompt:
    .\start-backend.ps1
#>

Set-StrictMode -Version Latest
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$BackendDir = Join-Path $ScriptDir 'backend'
$VenvPython = Join-Path $BackendDir 'venv\Scripts\python.exe'

if (-not (Test-Path $VenvPython)) {
    Write-Host "Creating virtual environment in $BackendDir\venv..."
    python -m venv (Join-Path $BackendDir 'venv')
    if ($LASTEXITCODE -ne 0) { throw "Failed to create venv" }

    Write-Host "Upgrading pip and installing backend requirements..."
    & "$VenvPython" -m pip install --upgrade pip
    & "$VenvPython" -m pip install -r (Join-Path $BackendDir 'requirements.txt')
}

$Cmd = "cd `"$BackendDir`"; & `"$VenvPython`" -m uvicorn main:app --host 0.0.0.0 --port 8000"
Write-Host "Starting backend in a new PowerShell window..."
Start-Process -FilePath powershell -ArgumentList @('-NoExit','-Command',$Cmd)
