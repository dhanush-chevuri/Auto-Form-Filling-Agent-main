<#
start-frontend.ps1

Installs frontend packages (if needed) and starts the React dev server in a
new PowerShell window so it stays running.

Usage: .\start-frontend.ps1
#>

Set-StrictMode -Version Latest
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$FrontendDir = Join-Path $ScriptDir 'frontend'

Write-Host "Installing frontend dependencies (npm ci)..."
Push-Location $FrontendDir
try {
    # Use npm ci for reproducible installs
    npm ci
} finally {
    Pop-Location
}

$Cmd = "cd `"$FrontendDir`"; npm start"
Write-Host "Starting frontend in a new PowerShell window..."
Start-Process -FilePath powershell -ArgumentList @('-NoExit','-Command',$Cmd)
