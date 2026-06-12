param(
    [string]$ProjectDir = "C:\Users\123\autotrade",
    [int]$DurationMinutes = 120,
    [int]$IntervalSeconds = 300,
    [string]$RunId = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-BasicAuthHeaders {
    param(
        [string]$Username,
        [string]$Password
    )

    $bytes = [System.Text.Encoding]::ASCII.GetBytes("${Username}:${Password}")
    $token = [Convert]::ToBase64String($bytes)
    return @{ Authorization = "Basic $token" }
}

function Invoke-DbJson {
    param(
        [Parameter(Mandatory = $true)][string]$Sql
    )

    try {
        $raw = docker exec pure_rl_fullauto_db psql -U freqtrade -d freqtrade_paper -t -A -c $Sql
        if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($raw)) {
            return $null
        }
        return ($raw | Select-Object -First 1) | ConvertFrom-Json
    }
    catch {
        return [pscustomobject]@{ error = $_.Exception.Message }
    }
}

function Get-ModelReadyState {
    param(
        [Parameter(Mandatory = $true)][string]$ModelRoot
    )

    $pairDictionaryPath = Join-Path $ModelRoot "pair_dictionary.json"
    if (-not (Test-Path -LiteralPath $pairDictionaryPath)) {
        return [pscustomobject]@{
            total_pairs = 0
            ready_pairs = 0
            pending_pairs = 0
            names_ready = @()
            names_pending = @()
        }
    }

    try {
        $pairDictionary = Get-Content -LiteralPath $pairDictionaryPath -Raw | ConvertFrom-Json
        $ready = New-Object System.Collections.Generic.List[string]
        $pending = New-Object System.Collections.Generic.List[string]
        foreach ($property in $pairDictionary.PSObject.Properties) {
            $pairName = [string]$property.Name
            $info = $property.Value
            $modelFilename = [string]($info.PSObject.Properties["model_filename"].Value)
            $trainedTimestamp = [long]($info.PSObject.Properties["trained_timestamp"].Value)
            if (-not [string]::IsNullOrWhiteSpace($modelFilename) -and $trainedTimestamp -gt 0) {
                $ready.Add($pairName)
            }
            else {
                $pending.Add($pairName)
            }
        }

        return [pscustomobject]@{
            total_pairs = $ready.Count + $pending.Count
            ready_pairs = $ready.Count
            pending_pairs = $pending.Count
            names_ready = @($ready)
            names_pending = @($pending)
        }
    }
    catch {
        return [pscustomobject]@{
            total_pairs = 0
            ready_pairs = 0
            pending_pairs = 0
            names_ready = @()
            names_pending = @()
            error = $_.Exception.Message
        }
    }
}

function Get-AuditSummary {
    param(
        [Parameter(Mandatory = $true)][string]$AuditPath,
        [Parameter(Mandatory = $true)][datetime]$StartUtc
    )

    if (-not (Test-Path -LiteralPath $AuditPath)) {
        return [pscustomobject]@{
            checked_tail = 0
            actions = @{}
            adjustment_reasons = @{}
            risk_gate_count = 0
        }
    }

    $actions = @{}
    $reasons = @{}
    $riskGateCount = 0
    $checked = 0

    foreach ($line in Get-Content -LiteralPath $AuditPath -Tail 5000 -ErrorAction SilentlyContinue) {
        if ([string]::IsNullOrWhiteSpace($line)) {
            continue
        }

        try {
            $entry = $line | ConvertFrom-Json
            $loggedAt = ([datetimeoffset]$entry.logged_at).UtcDateTime
        }
        catch {
            continue
        }

        if ($loggedAt -lt $StartUtc) {
            continue
        }

        $checked += 1
        $action = [string]$entry.final_action_name
        if (-not $actions.ContainsKey($action)) {
            $actions[$action] = 0
        }
        $actions[$action] += 1

        $reason = [string]$entry.adjustment_reason
        if ([string]::IsNullOrWhiteSpace($reason)) {
            $reason = [string]$entry.sanitized_to_final_reason
        }
        if (-not $reasons.ContainsKey($reason)) {
            $reasons[$reason] = 0
        }
        $reasons[$reason] += 1
        if ($reason -like "risk_gate_*") {
            $riskGateCount += 1
        }
    }

    return [pscustomobject]@{
        checked_tail = $checked
        actions = $actions
        adjustment_reasons = $reasons
        risk_gate_count = $riskGateCount
    }
}

if ([string]::IsNullOrWhiteSpace($RunId)) {
    $RunId = Get-Date -Format "yyyyMMdd_HHmmss"
}

$configPath = Join-Path $ProjectDir "user_data\config.json"
$paperConfigPath = Join-Path $ProjectDir "user_data\config.paper.json"
$logsDir = Join-Path $ProjectDir "user_data\logs"
$watchDir = Join-Path $ProjectDir "user_data\watchdog"
New-Item -ItemType Directory -Force -Path $logsDir | Out-Null
New-Item -ItemType Directory -Force -Path $watchDir | Out-Null

$jsonlPath = Join-Path $logsDir "rewardfix_monitor_${RunId}.jsonl"
$summaryPath = Join-Path $logsDir "rewardfix_monitor_${RunId}.summary.json"
$latestPath = Join-Path $watchDir "rewardfix_monitor.latest.json"
$stdoutPath = Join-Path $logsDir "rewardfix_monitor_${RunId}.stdout.log"

$config = Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json
$paperConfig = Get-Content -LiteralPath $paperConfigPath -Raw | ConvertFrom-Json
$identifier = [string]$paperConfig.freqai.identifier
$modelRoot = Join-Path $ProjectDir "user_data\models\$identifier"
$headers = Get-BasicAuthHeaders -Username $config.api_server.username -Password $config.api_server.password
$apiBase = "http://127.0.0.1:8088/api/v1"
$auditPath = Join-Path $logsDir "rl_decision_audit.jsonl"

$start = Get-Date
$startUtc = $start.ToUniversalTime()
$startSql = $start.ToString("yyyy-MM-dd HH:mm:ss")
$end = $start.AddMinutes($DurationMinutes)
$since = $start.AddSeconds(-5)

$summary = [ordered]@{
    run_id = $RunId
    started_at = $start.ToString("o")
    ended_at = $null
    duration_minutes = $DurationMinutes
    interval_seconds = $IntervalSeconds
    identifier = $identifier
    checks = 0
    api_failures = 0
    container_not_running_checks = 0
    restart_count_start = $null
    restart_count_end = $null
    restart_count_delta = $null
    severe_event_count = 0
    warning_event_count = 0
    new_closed_trades = 0
    new_wins = 0
    new_losses = 0
    new_profit_abs = 0.0
    max_open_trades_seen = 0
    max_ready_pairs_seen = 0
    risk_gate_count = 0
    latest = $null
    result = "unknown"
    jsonl = $jsonlPath
    summary = $summaryPath
    latest_path = $latestPath
}

Push-Location $ProjectDir
try {
    while ((Get-Date) -lt $end) {
        $timestamp = Get-Date
        $containerStatus = "unknown"
        $restartCount = 0
        try {
            $containerStatus = (docker inspect pure_rl_fullauto --format "{{.State.Status}}" 2>$null).Trim()
            $restartRaw = (docker inspect pure_rl_fullauto --format "{{.RestartCount}}" 2>$null).Trim()
            if ($restartRaw) {
                $restartCount = [int]$restartRaw
            }
        }
        catch {
            $containerStatus = "missing"
        }

        if ($null -eq $summary.restart_count_start) {
            $summary.restart_count_start = $restartCount
        }
        $summary.restart_count_end = $restartCount
        if ($containerStatus -ne "running") {
            $summary.container_not_running_checks += 1
        }

        $apiError = $null
        $pingOk = $false
        $countResponse = $null
        $profitResponse = $null
        try {
            $ping = Invoke-RestMethod -Uri "$apiBase/ping" -Headers $headers -TimeoutSec 10
            $pingOk = $ping.status -eq "pong"
            $countResponse = Invoke-RestMethod -Uri "$apiBase/count" -Headers $headers -TimeoutSec 30
            $profitResponse = Invoke-RestMethod -Uri "$apiBase/profit" -Headers $headers -TimeoutSec 30
        }
        catch {
            $apiError = $_.Exception.Message
            $summary.api_failures += 1
        }

        $dbStats = Invoke-DbJson -Sql "select row_to_json(t) from (select count(*) filter (where is_open=false and close_date >= timestamp '$startSql') as closed, count(*) filter (where is_open=false and close_date >= timestamp '$startSql' and close_profit > 0) as wins, count(*) filter (where is_open=false and close_date >= timestamp '$startSql' and close_profit <= 0) as losses, coalesce(sum(close_profit_abs) filter (where is_open=false and close_date >= timestamp '$startSql'),0) as profit_abs, count(*) filter (where open_date >= timestamp '$startSql') as new_entries, count(*) filter (where is_open=true) as open_trades, max(close_date) filter (where is_open=false and close_date >= timestamp '$startSql') as latest_close from trades) t;"
        $modelReady = Get-ModelReadyState -ModelRoot $modelRoot
        $auditSummary = Get-AuditSummary -AuditPath $auditPath -StartUtc $startUtc

        $sinceIso = $since.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
        $logLines = @()
        try {
            $logText = docker logs --since $sinceIso pure_rl_fullauto 2>&1
            if ($logText) {
                $logLines = @($logText -split "`r?`n" | Where-Object { $_ -and $_.Trim() })
            }
        }
        catch {
            $logLines = @("failed to read docker logs: $($_.Exception.Message)")
        }
        $since = $timestamp

        $severeMatches = @(
            $logLines | Where-Object {
                $_ -match "Traceback|\\bERROR\\b|process died|Unexpected error|Training .* raised exception"
            } | Select-Object -Unique
        )
        $warningMatches = @(
            $logLines | Where-Object {
                $_ -match "No model ready|NetworkError|RemoteProtocolError|dropped .* prediction data points|GivebackGuard|LossGuard|risk_gate"
            } | Select-Object -Unique
        )

        $openCount = 0
        if ($null -ne $countResponse -and $null -ne $countResponse.current) {
            $openCount = [int]$countResponse.current
        }
        if ($openCount -gt $summary.max_open_trades_seen) {
            $summary.max_open_trades_seen = $openCount
        }
        if ($modelReady.ready_pairs -gt $summary.max_ready_pairs_seen) {
            $summary.max_ready_pairs_seen = $modelReady.ready_pairs
        }

        $summary.severe_event_count += @($severeMatches).Count
        $summary.warning_event_count += @($warningMatches).Count
        $summary.risk_gate_count = [int]$auditSummary.risk_gate_count

        $dbErrorProperty = $null
        if ($null -ne $dbStats) {
            $dbErrorProperty = $dbStats.PSObject.Properties["error"]
        }
        if (
            $null -ne $dbStats -and
            ($null -eq $dbErrorProperty -or $null -eq $dbErrorProperty.Value)
        ) {
            $summary.new_closed_trades = [int]$dbStats.closed
            $summary.new_wins = [int]$dbStats.wins
            $summary.new_losses = [int]$dbStats.losses
            $summary.new_profit_abs = [double]$dbStats.profit_abs
        }

        $snapshot = [ordered]@{
            timestamp = $timestamp.ToString("o")
            container_status = $containerStatus
            restart_count = $restartCount
            ping_ok = $pingOk
            api_error = $apiError
            open_count = $openCount
            total_stake = if ($null -ne $countResponse) { $countResponse.total_stake } else { $null }
            profit_all_coin = if ($null -ne $profitResponse) { $profitResponse.profit_all_coin } else { $null }
            trade_count = if ($null -ne $profitResponse) { $profitResponse.trade_count } else { $null }
            db = $dbStats
            model_ready = $modelReady
            audit = $auditSummary
            severe_matches = @($severeMatches | Select-Object -First 12)
            warning_matches = @($warningMatches | Select-Object -First 12)
        }

        ($snapshot | ConvertTo-Json -Depth 8 -Compress) | Add-Content -LiteralPath $jsonlPath -Encoding UTF8
        $snapshot | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $latestPath -Encoding UTF8
        $summary.checks += 1
        $summary.latest = $snapshot

        $line = "[{0}] open={1} closed={2} wins={3} losses={4} pnl={5:N4} ready={6}/{7} gates={8} api={9} severe={10}" -f `
            $timestamp.ToString("yyyy-MM-dd HH:mm:ss"),
            $openCount,
            $summary.new_closed_trades,
            $summary.new_wins,
            $summary.new_losses,
            $summary.new_profit_abs,
            $modelReady.ready_pairs,
            $modelReady.total_pairs,
            $auditSummary.risk_gate_count,
            $pingOk,
            @($severeMatches).Count
        Add-Content -LiteralPath $stdoutPath -Value $line -Encoding UTF8

        Start-Sleep -Seconds $IntervalSeconds
    }
}
finally {
    Pop-Location
}

$summary.ended_at = (Get-Date).ToString("o")
$summary.restart_count_delta = [int]$summary.restart_count_end - [int]$summary.restart_count_start

if (
    $summary.api_failures -eq 0 -and
    $summary.container_not_running_checks -eq 0 -and
    $summary.restart_count_delta -eq 0 -and
    $summary.severe_event_count -eq 0
) {
    $summary.result = "healthy"
}
elseif ($summary.severe_event_count -gt 0 -or $summary.restart_count_delta -gt 0) {
    $summary.result = "unhealthy"
}
else {
    $summary.result = "degraded"
}

$summary | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $summaryPath -Encoding UTF8
Write-Output "jsonl=$jsonlPath"
Write-Output "summary=$summaryPath"
Write-Output "latest=$latestPath"
