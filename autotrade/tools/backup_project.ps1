param(
    [string]$ProjectRoot = "D:\autotrade",
    [string]$BackupRoot = "",
    [string]$PostgresContainer = "pure_rl_fullauto_db",
    [string]$FreqtradeContainer = "pure_rl_fullauto",
    [string]$DbUser = "freqtrade",
    [string]$DbPassword = "local_freqtrade_db_2026",
    [string[]]$Databases = @("freqtrade", "freqtrade_paper"),
    [string]$ApiUrl = "http://127.0.0.1:8088/api/v1/show_config",
    [string]$ApiUsername = "freqtrader",
    [string]$ApiPassword = "local_freqtrade_2026"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($BackupRoot)) {
    $BackupRoot = Join-Path $ProjectRoot "backups"
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$snapshotDir = Join-Path $BackupRoot "project_snapshot_$timestamp"
$filesDir = Join-Path $snapshotDir "files"
$dbDir = Join-Path $snapshotDir "db"
$metaDir = Join-Path $snapshotDir "meta"

New-Item -ItemType Directory -Force -Path $filesDir | Out-Null
New-Item -ItemType Directory -Force -Path $dbDir | Out-Null
New-Item -ItemType Directory -Force -Path $metaDir | Out-Null

function Copy-RelativeFile {
    param(
        [Parameter(Mandatory = $true)][string]$RelativePath
    )

    $source = Join-Path $ProjectRoot $RelativePath
    if (-not (Test-Path -LiteralPath $source)) {
        return $false
    }

    $target = Join-Path $filesDir $RelativePath
    $targetParent = Split-Path -Parent $target
    New-Item -ItemType Directory -Force -Path $targetParent | Out-Null
    Copy-Item -LiteralPath $source -Destination $target -Force
    return $true
}

function Get-DirectorySummary {
    param(
        [Parameter(Mandatory = $true)][string]$RelativePath
    )

    $fullPath = Join-Path $ProjectRoot $RelativePath
    if (-not (Test-Path -LiteralPath $fullPath)) {
        return [pscustomobject]@{
            path = $RelativePath
            exists = $false
        }
    }

    $files = @(Get-ChildItem -LiteralPath $fullPath -Recurse -File -ErrorAction SilentlyContinue)
    $dirs = @(Get-ChildItem -LiteralPath $fullPath -Directory -ErrorAction SilentlyContinue)
    $latestWrite = $null
    if ($files.Count -gt 0) {
        $latestWrite = ($files | Sort-Object LastWriteTime -Descending | Select-Object -First 1).LastWriteTime
    } elseif ($dirs.Count -gt 0) {
        $latestWrite = ($dirs | Sort-Object LastWriteTime -Descending | Select-Object -First 1).LastWriteTime
    } else {
        $latestWrite = (Get-Item -LiteralPath $fullPath).LastWriteTime
    }

    return [pscustomobject]@{
        path = $RelativePath
        exists = $true
        file_count = @($files).Count
        total_bytes = (@($files) | Measure-Object -Property Length -Sum).Sum
        top_level_directories = @($dirs | Select-Object -ExpandProperty Name)
        latest_write_time = $latestWrite
    }
}

$copiedFiles = @()
$fileList = @(
    "docker-compose.yml",
    "Dockerfile.freqtrade-pg",
    "user_data\config.json",
    "user_data\config.live.json",
    "user_data\config.paper.json",
    "user_data\config.base.example.json",
    "user_data\config.live.example.json",
    "user_data\strategies\PureRL_FullAuto.py",
    "user_data\freqaimodels\MyRLEnv_FullAuto.py",
    "tools\monitor_live_30m.ps1",
    "tools\monitor_live_window.ps1",
    "tools\walk_forward_eval.py",
    "tools\watchdog_live.ps1",
    "tools\sql\freqtrade_postgres_queries.sql"
)

foreach ($relativePath in $fileList) {
    if (Copy-RelativeFile -RelativePath $relativePath) {
        $copiedFiles += $relativePath
    }
}

$dbResults = @()
foreach ($database in $Databases) {
    $outputFile = Join-Path $dbDir "$database.sql"
    try {
        $dump = & docker exec $PostgresContainer sh -lc "PGPASSWORD='$DbPassword' pg_dump -U $DbUser -d $database --no-owner --no-privileges"
        $dump | Set-Content -LiteralPath $outputFile -Encoding UTF8
        $dbResults += [pscustomobject]@{
            database = $database
            status = "ok"
            file = $outputFile
        }
    } catch {
        $errorFile = Join-Path $dbDir "$database.error.txt"
        $_ | Out-String | Set-Content -LiteralPath $errorFile -Encoding UTF8
        $dbResults += [pscustomobject]@{
            database = $database
            status = "error"
            file = $errorFile
        }
    }
}

$dirSummary = @(
    (Get-DirectorySummary -RelativePath "user_data\models")
    (Get-DirectorySummary -RelativePath "user_data\data")
    (Get-DirectorySummary -RelativePath "user_data\logs")
    (Get-DirectorySummary -RelativePath "user_data\rl_state")
    (Get-DirectorySummary -RelativePath "postgres_data")
)

$dirSummary | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $metaDir "directory_summary.json") -Encoding UTF8

try {
    & docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Image}}" | Set-Content -LiteralPath (Join-Path $metaDir "docker_ps.txt") -Encoding UTF8
} catch {
    $_ | Out-String | Set-Content -LiteralPath (Join-Path $metaDir "docker_ps.error.txt") -Encoding UTF8
}

try {
    $apiResponse = & curl.exe -s -u "${ApiUsername}:${ApiPassword}" $ApiUrl
    $apiResponse | Set-Content -LiteralPath (Join-Path $metaDir "show_config.json") -Encoding UTF8
} catch {
    $_ | Out-String | Set-Content -LiteralPath (Join-Path $metaDir "show_config.error.txt") -Encoding UTF8
}

try {
    & git -C $ProjectRoot status --short | Set-Content -LiteralPath (Join-Path $metaDir "git_status.txt") -Encoding UTF8
} catch {
    $_ | Out-String | Set-Content -LiteralPath (Join-Path $metaDir "git_status.error.txt") -Encoding UTF8
}

$summary = [pscustomobject]@{
    created_at = (Get-Date).ToString("s")
    project_root = $ProjectRoot
    snapshot_dir = $snapshotDir
    freqtrade_container = $FreqtradeContainer
    postgres_container = $PostgresContainer
    copied_files = $copiedFiles
    database_exports = $dbResults
    directory_summary = $dirSummary
}

$summary | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $snapshotDir "summary.json") -Encoding UTF8

Write-Host "Project snapshot created:" $snapshotDir
