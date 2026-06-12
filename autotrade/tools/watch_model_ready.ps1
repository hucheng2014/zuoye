param(
    [string]$ProjectDir = "C:\Users\123\autotrade",
    [int]$IntervalSeconds = 60,
    [int]$TimeoutMinutes = 720,
    [int]$RecentLogsLimit = 250,
    [string]$ModelIdentifier = ""
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

function Get-NestedPropertyValue {
    param(
        [Parameter(Mandatory = $true)]$Object,
        [Parameter(Mandatory = $true)][string[]]$Path,
        $DefaultValue = $null
    )

    $current = $Object
    foreach ($segment in $Path) {
        if ($null -eq $current) {
            return $DefaultValue
        }
        $property = $current.PSObject.Properties[$segment]
        if ($null -eq $property) {
            return $DefaultValue
        }
        $current = $property.Value
    }
    if ($null -eq $current) {
        return $DefaultValue
    }
    return $current
}

function Get-ResolvedModelIdentifier {
    param(
        [string]$BaseConfigPath,
        [string]$OverlayConfigPath,
        [string]$ExplicitIdentifier
    )

    if (-not [string]::IsNullOrWhiteSpace($ExplicitIdentifier)) {
        return $ExplicitIdentifier.Trim()
    }

    $candidates = @($OverlayConfigPath, $BaseConfigPath)
    foreach ($path in $candidates) {
        if (-not (Test-Path -LiteralPath $path)) {
            continue
        }
        try {
            $config = Get-Content -LiteralPath $path -Raw | ConvertFrom-Json
            $identifier = Get-NestedPropertyValue -Object $config -Path @("freqai", "identifier") -DefaultValue ""
            if (-not [string]::IsNullOrWhiteSpace([string]$identifier)) {
                return [string]$identifier
            }
        } catch {
        }
    }

    throw "Could not resolve freqai.identifier from config files."
}

function Get-ReadyState {
    param(
        [string]$PairDictionaryPath
    )

    $readyPairs = New-Object System.Collections.Generic.List[string]
    $pendingPairs = New-Object System.Collections.Generic.List[string]

    if (-not (Test-Path -LiteralPath $PairDictionaryPath)) {
        return [pscustomobject]@{
            total_pairs = 0
            ready_pairs = @()
            pending_pairs = @()
        }
    }

    $pairDictionary = Get-Content -LiteralPath $PairDictionaryPath -Raw | ConvertFrom-Json
    foreach ($pairProperty in $pairDictionary.PSObject.Properties) {
        $pairName = [string]$pairProperty.Name
        $pairInfo = $pairProperty.Value
        $modelFilename = [string](Get-NestedPropertyValue -Object $pairInfo -Path @("model_filename") -DefaultValue "")
        $trainedTimestamp = [long](Get-NestedPropertyValue -Object $pairInfo -Path @("trained_timestamp") -DefaultValue 0)

        if (-not [string]::IsNullOrWhiteSpace($modelFilename) -and $trainedTimestamp -gt 0) {
            $readyPairs.Add($pairName)
        } else {
            $pendingPairs.Add($pairName)
        }
    }

    return [pscustomobject]@{
        total_pairs = $readyPairs.Count + $pendingPairs.Count
        ready_pairs = @($readyPairs)
        pending_pairs = @($pendingPairs)
    }
}

function Get-RecentModelFiles {
    param(
        [string]$ModelRoot
    )

    if (-not (Test-Path -LiteralPath $ModelRoot)) {
        return @()
    }

    return @(
        Get-ChildItem -Path $ModelRoot -Recurse -File -ErrorAction SilentlyContinue |
            Sort-Object LastWriteTime -Descending |
            Select-Object -First 5 @{Name = "path"; Expression = { $_.FullName } }, Length, LastWriteTime
    )
}

function Get-RecentLogState {
    param(
        [string]$ApiBase,
        [hashtable]$Headers,
        [int]$Limit
    )

    $result = [ordered]@{
        api_error = $null
        no_model_ready_pairs = @()
        severe_events = @()
        warning_events = @()
        inferencing = @()
    }

    $severePatterns = @(
        "Pipeline expected",
        "Unexpected error",
        "Unable to analyze candle",
        "Training .* raised exception"
    )

    $warningPatterns = @(
        "No model ready",
        "Outdated history",
        "ExchangeNotAvailable",
        "Exception happened while polling for updates",
        "telegram.error.NetworkError"
    )

    try {
        $logsResponse = Invoke-RestMethod -Uri "$ApiBase/logs?limit=$Limit" -Headers $Headers -TimeoutSec 30
        $logs = @($logsResponse.logs)
    } catch {
        $result.api_error = $_.Exception.Message
        return [pscustomobject]$result
    }

    $pendingPairs = New-Object System.Collections.Generic.HashSet[string]
    $severeEvents = New-Object System.Collections.Generic.List[string]
    $warningEvents = New-Object System.Collections.Generic.List[string]
    $inferencing = New-Object System.Collections.Generic.List[string]

    foreach ($entry in $logs) {
        $timestamp = [string]$entry[0]
        $message = [string]$entry[4]
        $singleLineMessage = (($message -split "`r?`n")[0]).Trim()

        if ($message -match "No model ready for (.+?), returning null values to strategy\.") {
            [void]$pendingPairs.Add($matches[1])
        }

        foreach ($pattern in $severePatterns) {
            if ($message -match $pattern) {
                $severeEvents.Add("$timestamp $singleLineMessage")
                break
            }
        }

        foreach ($pattern in $warningPatterns) {
            if ($message -match $pattern) {
                $warningEvents.Add("$timestamp $singleLineMessage")
                break
            }
        }

        if ($message -like "*Total time spent inferencing pairlist*") {
            $inferencing.Add("$timestamp $singleLineMessage")
        }
    }

    $result.no_model_ready_pairs = @($pendingPairs | Sort-Object)
    $result.severe_events = @($severeEvents | Select-Object -Unique | Select-Object -Last 10)
    $result.warning_events = @($warningEvents | Select-Object -Unique | Select-Object -Last 10)
    $result.inferencing = @($inferencing | Select-Object -Last 5)
    return [pscustomobject]$result
}

$configPath = Join-Path $ProjectDir "user_data\config.json"
$overlayConfigPath = Join-Path $ProjectDir "user_data\config.paper.json"
$logsDir = Join-Path $ProjectDir "user_data\logs"
$watchDir = Join-Path $ProjectDir "user_data\watchdog"
$runId = Get-Date -Format "yyyyMMdd_HHmmss"
$jsonlPath = Join-Path $logsDir "model_ready_watch_${runId}.jsonl"
$summaryPath = Join-Path $logsDir "model_ready_watch_${runId}.summary.json"
$latestPath = Join-Path $watchDir "model_ready_watch.latest.json"
$apiBase = "http://127.0.0.1:8088/api/v1"

New-Item -ItemType Directory -Path $logsDir -Force | Out-Null
New-Item -ItemType Directory -Path $watchDir -Force | Out-Null

$identifier = Get-ResolvedModelIdentifier -BaseConfigPath $configPath -OverlayConfigPath $overlayConfigPath -ExplicitIdentifier $ModelIdentifier
$modelRoot = Join-Path $ProjectDir "user_data\models\$identifier"
$pairDictionaryPath = Join-Path $modelRoot "pair_dictionary.json"

$config = Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json
$apiUsername = [string](Get-NestedPropertyValue -Object $config -Path @("api_server", "username") -DefaultValue "")
$apiPassword = [string](Get-NestedPropertyValue -Object $config -Path @("api_server", "password") -DefaultValue "")
$headers = Get-BasicAuthHeaders -Username $apiUsername -Password $apiPassword

$manifest = [ordered]@{
    pid = $PID
    run_id = $runId
    started_at = (Get-Date).ToString("o")
    project_dir = $ProjectDir
    model_identifier = $identifier
    model_root = $modelRoot
    pair_dictionary_path = $pairDictionaryPath
    jsonl = $jsonlPath
    summary = $summaryPath
}
$manifest | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $latestPath -Encoding UTF8

$summary = [ordered]@{
    started_at = (Get-Date).ToString("o")
    ended_at = $null
    result = "running"
    timeout_minutes = $TimeoutMinutes
    interval_seconds = $IntervalSeconds
    model_identifier = $identifier
    model_root = $modelRoot
    checks = 0
    max_ready_count = 0
    total_pairs = 0
    first_all_ready_at = $null
    latest_snapshot = $null
}

$endTime = (Get-Date).AddMinutes($TimeoutMinutes)

Write-Output "watch_started=$($summary.started_at)"
Write-Output "model_identifier=$identifier"
Write-Output "jsonl=$jsonlPath"
Write-Output "summary=$summaryPath"

while ((Get-Date) -lt $endTime) {
    $timestamp = Get-Date
    $readyState = Get-ReadyState -PairDictionaryPath $pairDictionaryPath
    $readyCount = @($readyState.ready_pairs).Count
    $totalPairs = [int]$readyState.total_pairs

    if ($readyCount -gt $summary.max_ready_count) {
        $summary.max_ready_count = $readyCount
    }
    if ($totalPairs -gt 0) {
        $summary.total_pairs = $totalPairs
    }

    $health = $null
    $healthError = $null
    try {
        $health = Invoke-RestMethod -Uri "$apiBase/health" -Headers $headers -TimeoutSec 30
    } catch {
        $healthError = $_.Exception.Message
    }

    $recentLogState = Get-RecentLogState -ApiBase $apiBase -Headers $headers -Limit $RecentLogsLimit
    $recentModelFiles = Get-RecentModelFiles -ModelRoot $modelRoot
    $allReady = ($totalPairs -gt 0 -and $readyCount -eq $totalPairs)

    $snapshot = [ordered]@{
        timestamp = $timestamp.ToString("o")
        ready_count = $readyCount
        total_pairs = $totalPairs
        all_ready = $allReady
        ready_pairs = @($readyState.ready_pairs)
        pending_pairs = @($readyState.pending_pairs)
        last_process = if ($null -ne $health) { $health.last_process } else { $null }
        bot_startup = if ($null -ne $health) { $health.bot_startup } else { $null }
        health_error = $healthError
        no_model_ready_pairs = @($recentLogState.no_model_ready_pairs)
        severe_events = @($recentLogState.severe_events)
        warning_events = @($recentLogState.warning_events)
        inferencing = @($recentLogState.inferencing)
        recent_model_files = @($recentModelFiles)
    }

    ($snapshot | ConvertTo-Json -Compress -Depth 8) | Add-Content -LiteralPath $jsonlPath -Encoding UTF8
    $summary.latest_snapshot = $snapshot
    $summary.checks += 1

    if ($allReady) {
        $summary.result = "all_ready"
        $summary.first_all_ready_at = $timestamp.ToString("o")
        break
    }

    Start-Sleep -Seconds $IntervalSeconds
}

if ($summary.result -eq "running") {
    $summary.result = "timeout"
}

$summary.ended_at = (Get-Date).ToString("o")
$summary | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $summaryPath -Encoding UTF8

Write-Output "watch_finished=$($summary.ended_at)"
Write-Output "result=$($summary.result)"
