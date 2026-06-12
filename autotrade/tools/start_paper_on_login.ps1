param(
    [string]$ProjectDir = "C:\Users\123\autotrade",
    [int]$DockerTimeoutSeconds = 300,
    [int]$PostgresTimeoutSeconds = 180,
    [int]$ApiTimeoutSeconds = 360
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$composeFile = Join-Path $ProjectDir "docker-compose.yml"
$logDir = Join-Path $ProjectDir "user_data\logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$logFile = Join-Path $logDir "startup_autotrade.log"

function Write-Log {
    param(
        [Parameter(Mandatory = $true)][object]$Message
    )

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"
    Add-Content -LiteralPath $logFile -Value "[$timestamp] $Message"
}

function Test-DockerReady {
    & docker info > $null 2>&1
    return $LASTEXITCODE -eq 0
}

function Invoke-Docker {
    param(
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [int[]]$AcceptedExitCodes = @(0)
    )

    Write-Log "docker $($Arguments -join ' ')"
    $previousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        & docker @Arguments 2>&1 | ForEach-Object { Write-Log $_ }
        $exitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }

    if ($AcceptedExitCodes -notcontains $exitCode) {
        throw "docker $($Arguments -join ' ') failed with exit code $exitCode"
    }
}

function Start-DockerDesktop {
    if (Test-DockerReady) {
        Write-Log "Docker engine is already ready."
        return
    }

    $dockerDesktop = Join-Path $env:ProgramFiles "Docker\Docker\Docker Desktop.exe"
    if (-not (Test-Path -LiteralPath $dockerDesktop)) {
        throw "Docker Desktop executable not found: $dockerDesktop"
    }

    $existing = @(Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue)
    if ($existing.Count -eq 0) {
        Write-Log "Starting Docker Desktop."
        Start-Process -FilePath $dockerDesktop | Out-Null
    }
    else {
        Write-Log "Docker Desktop process is already running."
    }
}

function Wait-DockerReady {
    param(
        [Parameter(Mandatory = $true)][int]$TimeoutSeconds
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        if (Test-DockerReady) {
            Write-Log "Docker engine is ready."
            return
        }

        Start-Sleep -Seconds 5
    }

    throw "Docker engine did not become ready within $TimeoutSeconds seconds."
}

function Wait-ContainerRunning {
    param(
        [Parameter(Mandatory = $true)][string]$ContainerName,
        [Parameter(Mandatory = $true)][int]$TimeoutSeconds
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        $state = (& docker inspect $ContainerName --format "{{.State.Status}}" 2>$null)
        if ($LASTEXITCODE -eq 0 -and $state -eq "running") {
            Write-Log "$ContainerName is running."
            return
        }

        Start-Sleep -Seconds 5
    }

    throw "$ContainerName did not reach running state within $TimeoutSeconds seconds."
}

function Wait-PostgresHealthy {
    param(
        [Parameter(Mandatory = $true)][int]$TimeoutSeconds
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        $health = (& docker inspect pure_rl_fullauto_db --format "{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}" 2>$null)
        if ($LASTEXITCODE -eq 0 -and $health -eq "healthy") {
            Write-Log "pure_rl_fullauto_db is healthy."
            return
        }

        Write-Log "Waiting for pure_rl_fullauto_db health, current: $health"
        Start-Sleep -Seconds 10
    }

    throw "pure_rl_fullauto_db did not become healthy within $TimeoutSeconds seconds."
}

function Wait-FreqtradeApi {
    param(
        [Parameter(Mandatory = $true)][int]$TimeoutSeconds
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        try {
            $response = Invoke-RestMethod -Uri "http://127.0.0.1:8088/api/v1/ping" -TimeoutSec 10
            if ($response.status -eq "pong") {
                Write-Log "Freqtrade API ping returned pong."
                return
            }
        }
        catch {
            Write-Log "Waiting for Freqtrade API: $($_.Exception.Message)"
        }

        Start-Sleep -Seconds 10
    }

    throw "Freqtrade API did not answer within $TimeoutSeconds seconds."
}

if (-not (Test-Path -LiteralPath $ProjectDir)) {
    throw "Project directory not found: $ProjectDir"
}

if (-not (Test-Path -LiteralPath $composeFile)) {
    throw "Compose file not found: $composeFile"
}

Write-Log "========== AutoTrade paper startup begin =========="
Write-Log "ProjectDir: $ProjectDir"

Push-Location $ProjectDir
try {
    Start-DockerDesktop
    Wait-DockerReady -TimeoutSeconds $DockerTimeoutSeconds

    Invoke-Docker -Arguments @("compose", "-f", $composeFile, "up", "-d", "--no-build")

    Wait-ContainerRunning -ContainerName "pure_rl_fullauto_db" -TimeoutSeconds 120
    Wait-PostgresHealthy -TimeoutSeconds $PostgresTimeoutSeconds
    Wait-ContainerRunning -ContainerName "pure_rl_fullauto" -TimeoutSeconds 120
    Wait-FreqtradeApi -TimeoutSeconds $ApiTimeoutSeconds

    Invoke-Docker -Arguments @("compose", "-f", $composeFile, "ps")
    Write-Log "AutoTrade paper startup completed."
}
catch {
    Write-Log "ERROR: $($_.Exception.Message)"
    throw
}
finally {
    Pop-Location
    Write-Log "========== AutoTrade paper startup end =========="
}
