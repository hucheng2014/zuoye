param(
    [string]$ProjectDir = "C:\Users\123\autotrade",
    [int]$Tail = 20,
    [int]$DurationMinutes = 30,
    [int]$PollSeconds = 5
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$auditPath = Join-Path $ProjectDir "user_data\logs\rl_decision_audit.jsonl"
if (-not (Test-Path -LiteralPath $auditPath)) {
    throw "Audit file not found: $auditPath"
}

$seen = [System.Collections.Generic.HashSet[string]]::new()

function Get-EntryKey {
    param(
        [Parameter(Mandatory = $true)]$Entry
    )

    $parts = @(
        [string]$Entry.logged_at,
        [string]$Entry.pair,
        [string]$Entry.candle_ts,
        [string]$Entry.trade_id,
        [string]$Entry.final_action,
        [string]$Entry.adjustment_reason
    )
    return ($parts -join "|")
}

function Get-ReasonText {
    param(
        [Parameter(Mandatory = $true)]$Entry
    )

    if ($Entry.was_neutralized -and -not [string]::IsNullOrWhiteSpace([string]$Entry.neutralize_reason)) {
        return [string]$Entry.neutralize_reason
    }
    if ([string]$Entry.sanitized_to_final_reason -ne "" -and [string]$Entry.sanitized_to_final_reason -ne "valid") {
        return [string]$Entry.sanitized_to_final_reason
    }
    if ([string]$Entry.raw_to_sanitized_reason -ne "" -and [string]$Entry.raw_to_sanitized_reason -ne "valid") {
        return [string]$Entry.raw_to_sanitized_reason
    }
    if ([string]$Entry.adjustment_reason -ne "") {
        return [string]$Entry.adjustment_reason
    }
    return "valid"
}

function Format-AuditEntry {
    param(
        [Parameter(Mandatory = $true)]$Entry
    )

    $loggedAt = try {
        (Get-Date ([datetimeoffset]$Entry.logged_at) -Format "yyyy-MM-dd HH:mm:ss")
    } catch {
        [string]$Entry.logged_at
    }

    $rawAction = if ($null -ne $Entry.raw_action_name) { [string]$Entry.raw_action_name } else { [string]$Entry.raw_action }
    $sanitizedAction = if ($null -ne $Entry.sanitized_action_name) { [string]$Entry.sanitized_action_name } else { [string]$Entry.final_action_name }
    $finalAction = if ($null -ne $Entry.final_action_name) { [string]$Entry.final_action_name } else { [string]$Entry.final_action }
    $signal = if ($null -ne $Entry.strategy_signal) { [string]$Entry.strategy_signal } else { "unknown" }
    $tag = if ($null -ne $Entry.strategy_tag -and [string]$Entry.strategy_tag -ne "") { [string]$Entry.strategy_tag } else { "-" }
    $neutralized = if ($Entry.was_neutralized) { "yes" } else { "no" }
    $doPredict = if ($null -ne $Entry.do_predict) { [string]$Entry.do_predict } else { "-" }
    $reason = Get-ReasonText -Entry $Entry

    return "[{0}] {1} pos={2} trade={3} do_predict={4} raw={5} -> sanitized={6} -> final={7} signal={8} tag={9} neutralized={10} reason={11}" -f `
        $loggedAt, `
        [string]$Entry.pair, `
        [string]$Entry.position, `
        [string]$Entry.trade_id, `
        $doPredict, `
        $rawAction, `
        $sanitizedAction, `
        $finalAction, `
        $signal, `
        $tag, `
        $neutralized, `
        $reason
}

function Show-NewEntries {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][int]$TailCount
    )

    $lines = @(Get-Content -LiteralPath $Path -Tail $TailCount -ErrorAction SilentlyContinue)
    foreach ($line in $lines) {
        if ([string]::IsNullOrWhiteSpace($line)) {
            continue
        }

        try {
            $entry = $line | ConvertFrom-Json
        } catch {
            continue
        }

        $key = Get-EntryKey -Entry $entry
        if (-not $seen.Add($key)) {
            continue
        }

        Write-Host (Format-AuditEntry -Entry $entry)
    }
}

Write-Host "Watching RL audit at: $auditPath"
Write-Host "Showing up to $Tail recent entries first, then following for $DurationMinutes minute(s)."
Write-Host "Press Ctrl+C to stop early."
Write-Host ""

Show-NewEntries -Path $auditPath -TailCount $Tail

$endTime = (Get-Date).AddMinutes($DurationMinutes)
while ((Get-Date) -lt $endTime) {
    Start-Sleep -Seconds $PollSeconds
    if (Test-Path -LiteralPath $auditPath) {
        Show-NewEntries -Path $auditPath -TailCount $Tail
    }
}

Write-Host ""
Write-Host "Stopped watching RL audit."
