param(
    [string]$ProjectDir = "D:\autotrade",
    [int]$DurationMinutes = 10
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$startScript = Join-Path $ProjectDir "tools\start_local.ps1"
if (-not (Test-Path -LiteralPath $startScript)) {
    throw "Start script not found: $startScript"
}

& powershell -ExecutionPolicy Bypass -File $startScript -ProjectDir $ProjectDir
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

$endTime = (Get-Date).AddMinutes($DurationMinutes)
Write-Host ""
Write-Host "Watching freqtrade and postgres logs for $DurationMinutes minute(s)..."
Write-Host "Press Ctrl+C to stop early."
Write-Host ""

while ((Get-Date) -lt $endTime) {
    & docker compose -f (Join-Path $ProjectDir "docker-compose.yml") logs --no-color --timestamps --tail 200 freqtrade postgres
    if ($LASTEXITCODE -ne 0) {
        throw "docker compose logs failed."
    }

    $remaining = [int][math]::Ceiling(($endTime - (Get-Date)).TotalSeconds)
    if ($remaining -le 0) {
        break
    }

    Write-Host ""
    Write-Host "Sleeping 15s, about $remaining second(s) remaining..."
    Start-Sleep -Seconds ([Math]::Min(15, $remaining))
}
