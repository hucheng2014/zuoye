Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Test-IsAdministrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Invoke-ExternalCommand {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [Parameter(Mandatory = $true)][int[]]$AcceptedExitCodes,
        [Parameter(Mandatory = $true)][string]$FailureMessage
    )

    & $FilePath @Arguments
    $exitCode = $LASTEXITCODE
    if ($AcceptedExitCodes -notcontains $exitCode) {
        throw "$FailureMessage Exit code: $exitCode"
    }
    return $exitCode
}

if (-not (Test-IsAdministrator)) {
    throw "Please run this script from an elevated PowerShell session."
}

Write-Host "Enabling Windows features required by WSL/Docker..."

$restartRequired = $false

$wslFeatureExit = Invoke-ExternalCommand `
    -FilePath "dism.exe" `
    -Arguments @("/online", "/enable-feature", "/featurename:Microsoft-Windows-Subsystem-Linux", "/all", "/norestart") `
    -AcceptedExitCodes @(0, 3010) `
    -FailureMessage "Failed to enable Microsoft-Windows-Subsystem-Linux."
if ($wslFeatureExit -eq 3010) {
    $restartRequired = $true
}

$vmpFeatureExit = Invoke-ExternalCommand `
    -FilePath "dism.exe" `
    -Arguments @("/online", "/enable-feature", "/featurename:VirtualMachinePlatform", "/all", "/norestart") `
    -AcceptedExitCodes @(0, 3010) `
    -FailureMessage "Failed to enable VirtualMachinePlatform."
if ($vmpFeatureExit -eq 3010) {
    $restartRequired = $true
}

if ($restartRequired) {
    Write-Host ""
    Write-Host "Windows features were enabled successfully, but a reboot is required before continuing."
    Write-Host "Please restart Windows, then rerun this same script."
    exit 3010
}

Write-Host "Installing WSL package..."
Invoke-ExternalCommand `
    -FilePath "winget" `
    -Arguments @("install", "--id", "Microsoft.WSL", "--accept-package-agreements", "--accept-source-agreements", "--disable-interactivity") `
    -AcceptedExitCodes @(0, 3010, 1641) `
    -FailureMessage "WSL installation failed." | Out-Null

Write-Host "Installing Docker Desktop..."
Invoke-ExternalCommand `
    -FilePath "winget" `
    -Arguments @("install", "--id", "Docker.DockerDesktop", "--accept-package-agreements", "--accept-source-agreements", "--disable-interactivity") `
    -AcceptedExitCodes @(0, 3010, 1641) `
    -FailureMessage "Docker Desktop installation failed." | Out-Null

Write-Host ""
Write-Host "Docker runtime installation steps completed."
Write-Host "A reboot is usually required before Docker Desktop can start correctly."
