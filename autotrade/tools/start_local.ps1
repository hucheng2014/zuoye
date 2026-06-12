param(
    [string]$ProjectDir = "D:\autotrade",
    [switch]$SkipBuild,
    [switch]$SkipPostgresPidCleanup
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Test-CommandExists {
    param(
        [Parameter(Mandatory = $true)][string]$Name
    )

    return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

function Test-IsAdministrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Backup-AndRemovePostgresPid {
    param(
        [Parameter(Mandatory = $true)][string]$ProjectRoot
    )

    $pidFile = Join-Path $ProjectRoot "postgres_data\\postmaster.pid"
    if (-not (Test-Path -LiteralPath $pidFile)) {
        return $false
    }

    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupDir = Join-Path $ProjectRoot "backups\\migration_$timestamp"
    New-Item -ItemType Directory -Force -Path $backupDir | Out-Null

    $backupFile = Join-Path $backupDir "postmaster.pid"
    Copy-Item -LiteralPath $pidFile -Destination $backupFile -Force
    Remove-Item -LiteralPath $pidFile -Force

    Write-Host "Backed up stale PostgreSQL pid file to $backupFile and removed the original."
    return $true
}

function Ensure-FirewallRule {
    param(
        [int]$Port = 8088
    )

    $ruleName = "autotrade-freq-ui-$Port"
    if (-not (Test-IsAdministrator)) {
        Write-Host "Firewall rule not changed because this PowerShell session is not elevated. Port $Port is exposed by Docker, but Windows Firewall may still block remote access."
        return
    }

    $existingRule = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
    if ($null -ne $existingRule) {
        Write-Host "Firewall rule already present: $ruleName"
        return
    }

    New-NetFirewallRule `
        -DisplayName $ruleName `
        -Direction Inbound `
        -Action Allow `
        -Protocol TCP `
        -LocalPort $Port | Out-Null

    Write-Host "Created inbound firewall rule for TCP port $Port."
}

if (-not (Test-Path -LiteralPath $ProjectDir)) {
    throw "Project directory not found: $ProjectDir"
}

$composeFile = Join-Path $ProjectDir "docker-compose.yml"
if (-not (Test-Path -LiteralPath $composeFile)) {
    throw "Compose file not found: $composeFile"
}

if (-not (Test-CommandExists -Name "docker")) {
    Write-Host @"
Docker CLI is not available on this machine.

This project has already been migrated to:
  $ProjectDir

To actually run the containers locally, install Docker Desktop first, then rerun:
  powershell -ExecutionPolicy Bypass -File $ProjectDir\tools\start_local.ps1
"@
    exit 2
}

Push-Location $ProjectDir
try {
    & docker info *> $null
    if ($LASTEXITCODE -ne 0) {
        throw "Docker is installed but the Docker engine is not running."
    }

    $runningServices = @()
    $psOutput = & docker compose ps --status running --services 2>$null
    if ($LASTEXITCODE -eq 0 -and $null -ne $psOutput) {
        $runningServices = @($psOutput | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
    }

    if (-not $SkipPostgresPidCleanup -and $runningServices.Count -eq 0) {
        [void](Backup-AndRemovePostgresPid -ProjectRoot $ProjectDir)
    }

    Ensure-FirewallRule -Port 8088

    $upArgs = @("compose", "up", "-d")
    if (-not $SkipBuild) {
        $upArgs += "--build"
    }

    Write-Host "Starting local containers from $ProjectDir ..."
    & docker @upArgs
    if ($LASTEXITCODE -ne 0) {
        throw "docker compose up failed."
    }

    Write-Host ""
    Write-Host "Current container status:"
    & docker compose ps
    if ($LASTEXITCODE -ne 0) {
        throw "docker compose ps failed."
    }
}
finally {
    Pop-Location
}
