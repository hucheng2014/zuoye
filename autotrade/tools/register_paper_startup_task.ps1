param(
    [string]$ProjectDir = "C:\Users\123\autotrade",
    [string]$TaskName = "AutoTrade Paper Startup",
    [string]$TaskPath = "\AutoTrade\",
    [switch]$RunNow
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$startupScript = Join-Path $ProjectDir "tools\start_paper_on_login.ps1"
if (-not (Test-Path -LiteralPath $startupScript)) {
    throw "Startup script not found: $startupScript"
}

$powershell = Join-Path $env:SystemRoot "System32\WindowsPowerShell\v1.0\powershell.exe"
$user = [Security.Principal.WindowsIdentity]::GetCurrent().Name
$arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$startupScript`" -ProjectDir `"$ProjectDir`""

$action = New-ScheduledTaskAction `
    -Execute $powershell `
    -Argument $arguments `
    -WorkingDirectory $ProjectDir

$trigger = New-ScheduledTaskTrigger -AtLogOn -User $user
try {
    $trigger.Delay = "PT45S"
}
catch {
    Write-Warning "Could not set logon delay on this Windows version: $($_.Exception.Message)"
}

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 20) `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 2)

function Register-TaskWithRunLevel {
    param(
        [Parameter(Mandatory = $true)][string]$RunLevel
    )

    $principal = New-ScheduledTaskPrincipal `
        -UserId $user `
        -LogonType Interactive `
        -RunLevel $RunLevel

    Register-ScheduledTask `
        -TaskName $TaskName `
        -TaskPath $TaskPath `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $principal `
        -Description "Start Docker Desktop and the AutoTrade Freqtrade paper-trading compose stack after Windows logon." `
        -Force | Out-Null
}

try {
    Register-TaskWithRunLevel -RunLevel Highest
}
catch {
    Write-Warning "Could not register with highest privileges, retrying with limited privileges: $($_.Exception.Message)"
    Register-TaskWithRunLevel -RunLevel Limited
}

Enable-ScheduledTask -TaskName $TaskName -TaskPath $TaskPath | Out-Null

$task = Get-ScheduledTask -TaskName $TaskName -TaskPath $TaskPath
$info = Get-ScheduledTaskInfo -TaskName $TaskName -TaskPath $TaskPath

Write-Host "Registered scheduled task:"
Write-Host "  Name: $($task.TaskPath)$($task.TaskName)"
Write-Host "  User: $user"
Write-Host "  State: $($task.State)"
Write-Host "  LastRunTime: $($info.LastRunTime)"
Write-Host "  LastTaskResult: $($info.LastTaskResult)"
Write-Host "  Action: $powershell $arguments"

if ($RunNow) {
    Write-Host "Starting task now..."
    Start-ScheduledTask -TaskName $TaskName -TaskPath $TaskPath
}
