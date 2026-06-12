param(
    [string]$ProjectDir = "D:\autotrade",
    [int]$IntervalSeconds = 60,
    [int]$AlertCooldownMinutes = 15,
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

function Get-ConfigValue {
    param(
        [pscustomobject]$Config,
        [string]$PropertyName,
        $DefaultValue = $null
    )

    $property = $Config.PSObject.Properties[$PropertyName]
    if ($null -eq $property) {
        return $DefaultValue
    }
    return $property.Value
}

function Send-TelegramMessage {
    param(
        [string]$Token,
        [string]$ChatId,
        [string]$Text
    )

    if ([string]::IsNullOrWhiteSpace($Token) -or [string]::IsNullOrWhiteSpace($ChatId)) {
        return
    }

    $uri = "https://api.telegram.org/bot$Token/sendMessage"
    $body = @{
        chat_id = $ChatId
        text = $Text
        disable_web_page_preview = $true
    }
    Invoke-RestMethod -Method Post -Uri $uri -Body $body -TimeoutSec 20 | Out-Null
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

function Format-IncidentText {
    param(
        [string]$Level,
        [hashtable]$Snapshot,
        [string[]]$Matches
    )

    $title = switch ($Level) {
        "ALERT" { "【告警】pure_rl_fullauto" }
        "RECOVERY" { "【恢复】pure_rl_fullauto" }
        default { "【信息】pure_rl_fullauto" }
    }

    $statusText = switch ($Level) {
        "ALERT" { "检测结果：发现异常" }
        "RECOVERY" { "检测结果：服务恢复正常" }
        default { "检测结果：状态更新" }
    }

    $lines = @()
    $lines += $title
    $lines += $statusText
    $lines += "时间: $($Snapshot.timestamp)"
    $lines += "容器状态: $($Snapshot.container_status)"
    $lines += "API 状态: $($Snapshot.api_state)"
    $lines += "运行模式: $($Snapshot.runmode)"
    $lines += "模拟盘: $($Snapshot.dry_run)"
    $lines += "当前持仓数: $($Snapshot.open_trades)"
    if ($Snapshot.api_error) {
        $lines += "接口错误: $($Snapshot.api_error)"
    }
    if (@($Matches).Count -gt 0) {
        $lines += "匹配日志:"
        $lines += @($Matches | Select-Object -First 5)
    }
    return ($lines -join "`n")
}

$configPath = Join-Path $ProjectDir "user_data\config.json"
$logDir = Join-Path $ProjectDir "user_data\logs"
$stateDir = Join-Path $ProjectDir "user_data\watchdog"
$statePath = Join-Path $stateDir "watchdog_live_state.json"
$pidPath = Join-Path $stateDir "watchdog_live.pid"
$watchdogLog = Join-Path $logDir "watchdog_live.log"
$apiBase = "http://127.0.0.1:8088/api/v1"

New-Item -ItemType Directory -Path $logDir -Force | Out-Null
New-Item -ItemType Directory -Path $stateDir -Force | Out-Null

if (Test-Path $pidPath) {
    try {
        $existingPidText = (Get-Content $pidPath -Raw).Trim()
        if ($existingPidText) {
            $existingPid = [int]$existingPidText
            $existingProcess = Get-Process -Id $existingPid -ErrorAction SilentlyContinue
            if ($null -ne $existingProcess) {
                Write-Output "watchdog already running pid=$existingPid"
                exit 0
            }
        }
    } catch {
    }
}

$PID.ToString() | Set-Content -Encoding ASCII $pidPath

$config = Get-Content $configPath -Raw | ConvertFrom-Json
$liveConfigPath = Join-Path $ProjectDir "user_data\config.live.json"
if (Test-Path $liveConfigPath) {
    $liveConfig = Get-Content $liveConfigPath -Raw | ConvertFrom-Json
} else {
    $liveConfig = $null
}

$apiConfig = $config.api_server
$telegramConfig = $config.telegram
$headers = Get-BasicAuthHeaders -Username $apiConfig.username -Password $apiConfig.password

$telegramToken = Get-ConfigValue -Config $telegramConfig -PropertyName "token" -DefaultValue ""
$telegramChatId = Get-ConfigValue -Config $telegramConfig -PropertyName "chat_id" -DefaultValue ""

$severePatterns = @(
    "Could not load markets",
    "451 restricted location",
    "403 Forbidden",
    "process died",
    "Traceback",
    "Could not update funding fees",
    "Outdated history",
    "Unable to analyze candle",
    "RL predict failed",
    "Training .* raised exception"
)

$warningPatterns = @(
    "TemporaryError",
    "Exception happened while polling for updates",
    "dropped .* prediction data points due to NaNs",
    "No model ready"
)

$state = @{
    last_status = "unknown"
    last_alert_at = $null
    last_recovery_at = $null
    last_log_scan_utc = (Get-Date).AddMinutes(-2).ToUniversalTime().ToString("o")
    last_incident_signature = ""
}

if (Test-Path $statePath) {
    try {
        $savedState = Get-Content $statePath -Raw | ConvertFrom-Json
        $savedProperties = $savedState.PSObject.Properties.Name
        foreach ($name in $savedProperties) {
            $state[$name] = $savedState.$name
        }
    } catch {
    }
}

Push-Location $ProjectDir
try {
    $startupMessage = "【信息】实时 watchdog 已启动`n时间: $(Get-Date -Format s)`n项目目录: $ProjectDir`n容器: $ContainerName"
    try {
        Send-TelegramMessage -Token $telegramToken -ChatId $telegramChatId -Text $startupMessage
    } catch {
        Add-Content -Encoding UTF8 $watchdogLog "$(Get-Date -Format o) startup_telegram_error $($_.Exception.Message)"
    }

    while ($true) {
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
            $ping = Invoke-WebRequest -UseBasicParsing -Uri "$apiBase/ping" -Headers $headers -TimeoutSec 15
            $pingOk = $ping.Content -match '"status":"pong"'
            $showConfig = Invoke-RestMethod -Uri "$apiBase/show_config" -Headers $headers -TimeoutSec 15
            $status = Invoke-RestMethod -Uri "$apiBase/status" -Headers $headers -TimeoutSec 15
            $apiState = $showConfig.state
            $runmode = $showConfig.runmode
            $dryRun = [bool]$showConfig.dry_run
            $openTrades = Get-OpenTradeCount -StatusResponse $status
        } catch {
            $apiError = $_.Exception.Message
        }

        $sinceUtc = [DateTime]::Parse($state.last_log_scan_utc).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
        $logLines = @()
        try {
            $rawLogs = docker compose logs --since $sinceUtc 2>$null
            if ($rawLogs) {
                $logLines = @($rawLogs -split "`r?`n" | Where-Object { $_ -and $_.Trim() })
            }
        } catch {
            $logLines = @("docker compose logs failed: $($_.Exception.Message)")
        }
        $state.last_log_scan_utc = $timestamp.ToUniversalTime().ToString("o")

        $severeMatches = Get-Matches -Lines $logLines -Patterns $severePatterns
        $warningMatches = Get-Matches -Lines $logLines -Patterns $warningPatterns

        $snapshot = @{
            timestamp = $timestamp.ToString("s")
            container_status = $containerStatus
            ping_ok = $pingOk
            api_state = $apiState
            runmode = $runmode
            dry_run = $dryRun
            open_trades = $openTrades
            api_error = $apiError
        }

        $isHealthy = (
            $containerStatus -eq "running" -and
            $pingOk -and
            $apiState -eq "running" -and
            $runmode -eq "live" -and
            -not $dryRun -and
            @($severeMatches).Count -eq 0
        )

        $statusLabel = if ($isHealthy) { "healthy" } else { "incident" }
        $incidentSignature = (
            @(
                $containerStatus,
                $apiState,
                $runmode,
                [string]$dryRun,
                [string]$openTrades,
                [string]$apiError,
                (@($severeMatches) -join " || ")
            ) -join " | "
        )

        $logEntry = @{
            timestamp = $snapshot.timestamp
            status = $statusLabel
            container_status = $containerStatus
            ping_ok = $pingOk
            api_state = $apiState
            runmode = $runmode
            dry_run = $dryRun
            open_trades = $openTrades
            api_error = $apiError
            severe_matches = $severeMatches
            warning_matches = $warningMatches
        } | ConvertTo-Json -Compress
        Add-Content -Encoding UTF8 $watchdogLog $logEntry

        $shouldSendIncident = $false
        $lastAlertAt = $null
        if ($state.last_alert_at) {
            $lastAlertAt = [DateTime]::Parse($state.last_alert_at)
        }
        if (-not $isHealthy) {
            if ($state.last_status -ne "incident") {
                $shouldSendIncident = $true
            } elseif ($state.last_incident_signature -ne $incidentSignature) {
                $shouldSendIncident = $true
            } elseif ($null -eq $lastAlertAt -or $timestamp -ge $lastAlertAt.AddMinutes($AlertCooldownMinutes)) {
                $shouldSendIncident = $true
            }
        }

        if ($shouldSendIncident) {
            $incidentText = Format-IncidentText -Level "ALERT" -Snapshot $snapshot -Matches $severeMatches
            try {
                Send-TelegramMessage -Token $telegramToken -ChatId $telegramChatId -Text $incidentText
                $state.last_alert_at = $timestamp.ToString("o")
            } catch {
                Add-Content -Encoding UTF8 $watchdogLog "$(Get-Date -Format o) telegram_alert_error $($_.Exception.Message)"
            }
        }

        if ($isHealthy -and $state.last_status -eq "incident") {
            $recoveryText = Format-IncidentText -Level "RECOVERY" -Snapshot $snapshot -Matches @()
            try {
                Send-TelegramMessage -Token $telegramToken -ChatId $telegramChatId -Text $recoveryText
                $state.last_recovery_at = $timestamp.ToString("o")
            } catch {
                Add-Content -Encoding UTF8 $watchdogLog "$(Get-Date -Format o) telegram_recovery_error $($_.Exception.Message)"
            }
        }

        $state.last_status = $statusLabel
        if (-not $isHealthy) {
            $state.last_incident_signature = $incidentSignature
        } else {
            $state.last_incident_signature = ""
        }
        $state | ConvertTo-Json | Set-Content -Encoding UTF8 $statePath

        Start-Sleep -Seconds $IntervalSeconds
    }
}
finally {
    Remove-Item $pidPath -ErrorAction SilentlyContinue
    Pop-Location
}
