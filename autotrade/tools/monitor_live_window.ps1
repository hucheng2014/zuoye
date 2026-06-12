param(
    [int]$DurationMinutes = 240,
    [int]$IntervalSeconds = 60,
    [string]$ProjectDir = "D:\autotrade",
    [string]$ContainerName = "pure_rl_fullauto"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Get-BasicAuthHeaders {
    param(
        [string]$Username,
        [string]$Password
    )

    $bytes = [System.Text.Encoding]::ASCII.GetBytes("${Username}:${Password}")
    $token = [Convert]::ToBase64String($bytes)
    return @{ Authorization = "Basic $token" }
}

function Get-OpenTradeCount {
    param($StatusResponse)

    if ($null -eq $StatusResponse) {
        return 0
    }
    $valueProperty = $StatusResponse.PSObject.Properties["value"]
    if ($null -ne $valueProperty) {
        return @($StatusResponse.value).Count
    }
    return @($StatusResponse).Count
}

function Get-Matches {
    param(
        [string[]]$Lines,
        [string[]]$Patterns
    )

    $resultMatches = @()
    foreach ($line in $Lines) {
        foreach ($pattern in $Patterns) {
            if ($line -match $pattern) {
                $resultMatches += [string]$line.Trim()
                break
            }
        }
    }
    return @($resultMatches | Select-Object -Unique)
}

$configPath = Join-Path $ProjectDir "user_data\config.json"
$logsDir = Join-Path $ProjectDir "user_data\logs"
$runId = Get-Date -Format "yyyyMMdd_HHmmss"
$jsonlPath = Join-Path $logsDir "monitor_live_${runId}.jsonl"
$summaryPath = Join-Path $logsDir "monitor_live_${runId}.summary.json"
$apiBase = "http://127.0.0.1:8088/api/v1"

New-Item -ItemType Directory -Path $logsDir -Force | Out-Null

$config = Get-Content $configPath -Raw | ConvertFrom-Json
$headers = Get-BasicAuthHeaders -Username $config.api_server.username -Password $config.api_server.password
$apiTimeoutSec = 30

$severePatterns = @(
    "Could not load markets",
    "451 restricted location",
    "403 Forbidden",
    "429 Too Many Requests",
    "produced invalid logits",
    "non-finite actions",
    "Invalid start time",
    "InvalidNonce",
    "Timestamp for this request was 1000ms ahead of the server's time",
    "process died",
    "unable to open database file",
    "Could not update funding fees",
    "Outdated history",
    "Unable to analyze candle",
    "RL predict failed",
    "Training .* raised exception"
)

$warningPatterns = @(
    "TemporaryError",
    "Exception happened while polling for updates",
    "telegram\.error\.NetworkError",
    "dropped .* prediction data points due to NaNs",
    "No model ready"
)

$start = Get-Date
$end = $start.AddMinutes($DurationMinutes)
$summary = [ordered]@{
    started_at = $start.ToString("o")
    ended_at = $null
    duration_minutes = $DurationMinutes
    interval_seconds = $IntervalSeconds
    checks = 0
    api_failures = 0
    non_live_checks = 0
    non_running_checks = 0
    container_not_running_checks = 0
    severe_event_count = 0
    warning_event_count = 0
    max_open_trades_seen = 0
    samples = @{
        severe = @()
        warning = @()
    }
    last_snapshot = $null
    result = "unknown"
}

Push-Location $ProjectDir
try {
    $since = $start.AddSeconds(-5)
    while ((Get-Date) -lt $end) {
        $timestamp = Get-Date
        $containerStatus = "unknown"
        $pingOk = $false
        $apiState = $null
        $runmode = $null
        $dryRun = $null
        $openTrades = 0
        $apiError = $null

        try {
            $containerStatus = (docker inspect $ContainerName --format "{{.State.Status}}" 2>$null).Trim()
        } catch {
            $containerStatus = "missing"
        }

        try {
            $ping = Invoke-WebRequest -UseBasicParsing -Uri "$apiBase/ping" -Headers $headers -TimeoutSec $apiTimeoutSec
            $pingOk = $ping.Content -match '"status":"pong"'
            $showConfig = Invoke-RestMethod -Uri "$apiBase/show_config" -Headers $headers -TimeoutSec $apiTimeoutSec
            $status = Invoke-RestMethod -Uri "$apiBase/status" -Headers $headers -TimeoutSec $apiTimeoutSec
            $apiState = $showConfig.state
            $runmode = $showConfig.runmode
            $dryRun = [bool]$showConfig.dry_run
            $openTrades = Get-OpenTradeCount -StatusResponse $status
        } catch {
            $apiError = $_.Exception.Message
            $summary.api_failures += 1
        }

        if ($containerStatus -ne "running") {
            $summary.container_not_running_checks += 1
        }
        if ($apiState -ne "running") {
            $summary.non_running_checks += 1
        }
        if ($runmode -ne "live" -or $dryRun) {
            $summary.non_live_checks += 1
        }
        if ($openTrades -gt $summary.max_open_trades_seen) {
            $summary.max_open_trades_seen = $openTrades
        }

        $sinceIso = $since.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
        $logLines = @()
        try {
            $rawLogs = docker compose logs --since $sinceIso 2>$null
            if ($rawLogs) {
                $logLines = @($rawLogs -split "`r?`n" | Where-Object { $_ -and $_.Trim() })
            }
        } catch {
            $logLines = @("docker compose logs failed: $($_.Exception.Message)")
        }
        $since = $timestamp

        $severeMatches = Get-Matches -Lines $logLines -Patterns $severePatterns
        $warningMatches = Get-Matches -Lines $logLines -Patterns $warningPatterns

        $summary.severe_event_count += @($severeMatches).Count
        $summary.warning_event_count += @($warningMatches).Count
        if (@($severeMatches).Count -gt 0) {
            $summary.samples.severe = @($summary.samples.severe + $severeMatches | Select-Object -Unique | Select-Object -First 20)
        }
        if (@($warningMatches).Count -gt 0) {
            $summary.samples.warning = @($summary.samples.warning + $warningMatches | Select-Object -Unique | Select-Object -First 20)
        }

        $snapshot = [ordered]@{
            timestamp = $timestamp.ToString("o")
            container_status = $containerStatus
            ping_ok = $pingOk
            api_state = $apiState
            runmode = $runmode
            dry_run = $dryRun
            open_trades = $openTrades
            api_error = $apiError
            severe_matches = $severeMatches
            warning_matches = $warningMatches
        }

        ($snapshot | ConvertTo-Json -Compress) | Add-Content -Encoding UTF8 $jsonlPath
        $summary.last_snapshot = $snapshot
        $summary.checks += 1

        Start-Sleep -Seconds $IntervalSeconds
    }
}
finally {
    Pop-Location
}

$summary.ended_at = (Get-Date).ToString("o")
if (
    $summary.api_failures -eq 0 -and
    $summary.non_live_checks -eq 0 -and
    $summary.non_running_checks -eq 0 -and
    $summary.container_not_running_checks -eq 0 -and
    $summary.severe_event_count -eq 0
) {
    $summary.result = "healthy"
} elseif ($summary.severe_event_count -gt 0) {
    $summary.result = "unhealthy"
} else {
    $summary.result = "degraded"
}

$summary | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 $summaryPath
Write-Output "jsonl=$jsonlPath"
Write-Output "summary=$summaryPath"
