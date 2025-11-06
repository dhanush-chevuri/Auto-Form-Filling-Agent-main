<#
start-all.ps1

Starts both backend and frontend by launching the helper scripts in separate
PowerShell windows. Use this when you want to run the full app locally.

Usage: .\start-all.ps1
#>

Set-StrictMode -Version Latest
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition

Write-Host "Starting backend and frontend..."
Start-Process -FilePath powershell -ArgumentList @('-NoExit','-Command',"& `"$ScriptDir\start-backend.ps1`"")
Start-Process -FilePath powershell -ArgumentList @('-NoExit','-Command',"& `"$ScriptDir\start-frontend.ps1`"")

Write-Host "Both windows launched. Check their consoles for server logs. Backend: http://localhost:8000  Frontend: http://localhost:3000"
