<#
start-docker.ps1

Runs docker-compose up --build from the repository root. Use this if you
have Docker Desktop installed and prefer containerized development.

Usage: .\start-docker.ps1
#>

Set-StrictMode -Version Latest
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition

Write-Host "Starting Docker Compose (requires Docker Desktop)..."
Push-Location $ScriptDir
try {
    docker-compose up --build
} finally {
    Pop-Location
}
