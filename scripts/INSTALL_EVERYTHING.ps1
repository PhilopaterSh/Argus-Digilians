# Argus Security Framework - Master Installer (PowerShell Version)
# Requirements: Windows 10/11, Internet unless ARGUS_OFFLINE=1 or -Offline is used.

[CmdletBinding()]
param(
    [switch]$Offline,
    [switch]$Interactive,
    [switch]$SkipHealthCheck,
    [int]$RetryCount = 2
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Definition)
$env:ARGUS_AUTO_INSTALL = if ($Interactive) { "" } else { "1" }
if ($Offline) { $env:ARGUS_OFFLINE = "1" }

Set-Location -LiteralPath $ScriptDir

$MIN_RAM_GB = 8
$MIN_DISK_GB = 20
$PYTHON_REQUIRED = "3.12"

function Write-Log {
    param(
        [string]$Level,
        [string]$Message,
        [ConsoleColor]$Color = [ConsoleColor]::White
    )

    $line = "[{0}] [{1}] {2}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Level, $Message
    Write-Host $line -ForegroundColor $Color
}

function Write-Header {
    param([string]$Text)
    Write-Host ""
    Write-Host "========================================================" -ForegroundColor Cyan
    Write-Host "         $Text" -ForegroundColor Cyan
    Write-Host "========================================================" -ForegroundColor Cyan
    Write-Host ""
}

function Write-OK { param([string]$Msg) Write-Log "OK" $Msg Green }
function Write-Warn { param([string]$Msg) Write-Log "WARN" $Msg Yellow }
function Write-ErrorMsg { param([string]$Msg) Write-Log "ERROR" $Msg Red }
function Write-Step { param([int]$Step, [string]$Msg) Write-Log "STEP $Step" $Msg Magenta }

function Test-IsAdministrator {
    $currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    return $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Test-CommandWorks {
    param(
        [Parameter(Mandatory = $true)][string]$CommandPath,
        [string[]]$Arguments = @("--version")
    )

    try {
        $output = & $CommandPath @Arguments 2>&1
        if ($LASTEXITCODE -eq 0 -or $null -eq $LASTEXITCODE) {
            return [pscustomobject]@{ Works = $true; Output = ($output -join " ").Trim() }
        }

        return [pscustomobject]@{ Works = $false; Output = ($output -join " ").Trim() }
    } catch {
        return [pscustomobject]@{ Works = $false; Output = $_.Exception.Message }
    }
}

function Get-UsablePython {
    $candidates = New-Object System.Collections.Generic.List[string]

    foreach ($command in @(Get-Command python.exe -All -ErrorAction SilentlyContinue)) {
        if ($command.Source -and $command.Source -notlike "*\Microsoft\WindowsApps\*") {
            $candidates.Add($command.Source)
        }
    }

    $knownPaths = @(
        (Join-Path $env:LocalAppData "Programs\Python\Python312\python.exe"),
        "C:\Program Files\Python312\python.exe",
        "C:\Program Files (x86)\Python312\python.exe"
    )

    foreach ($path in $knownPaths) {
        if ($path -and (Test-Path -LiteralPath $path)) {
            $candidates.Add($path)
        }
    }

    foreach ($path in ($candidates | Select-Object -Unique)) {
        $test = Test-CommandWorks -CommandPath $path
        if ($test.Works -and $test.Output -match "Python\s+3\.12") {
            return [pscustomobject]@{ Path = $path; Version = $test.Output }
        }
    }

    return $null
}

function Install-Python {
    Write-Log "INFO" "Checking for Python $PYTHON_REQUIRED..."

    $python = Get-UsablePython
    if ($null -ne $python) {
        Write-OK "Python is available: $($python.Version) at $($python.Path)"
        $pythonDir = Split-Path -Parent $python.Path
        $scriptsDir = Join-Path $pythonDir "Scripts"
        $env:Path = "$pythonDir;$scriptsDir;$env:Path"
        return $true
    }

    $storeAlias = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($storeAlias -and $storeAlias.Source -like "*\Microsoft\WindowsApps\*") {
        Write-Warn "Only the Windows Store Python alias was found; it is not a usable Python installation."
    } else {
        Write-Warn "Python $PYTHON_REQUIRED was not found."
    }

    if ($env:ARGUS_OFFLINE -eq "1") {
        Write-ErrorMsg "Offline mode is enabled. Install Python $PYTHON_REQUIRED manually, then rerun this installer."
        return $false
    }

    if (-not (Get-Command winget.exe -ErrorAction SilentlyContinue)) {
        Write-ErrorMsg "Winget was not found. Install Python $PYTHON_REQUIRED manually from python.org."
        return $false
    }

    Write-Log "INFO" "Attempting to install Python $PYTHON_REQUIRED via winget..."
    $process = Start-Process winget -ArgumentList "install --id Python.Python.3.12 --source winget --exact --silent --accept-package-agreements --accept-source-agreements" -Wait -PassThru -NoNewWindow
    if ($process.ExitCode -ne 0) {
        Write-ErrorMsg "Winget failed to install Python. Exit code: $($process.ExitCode)"
        return $false
    }

    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
    $python = Get-UsablePython
    if ($null -eq $python) {
        Write-ErrorMsg "Python installation finished, but Python $PYTHON_REQUIRED is still not usable in this session. Restart PowerShell and rerun."
        return $false
    }

    Write-OK "Python installed and verified: $($python.Version)"
    return $true
}

function Test-SystemReadiness {
    Write-Log "INFO" "Verifying system readiness..."

    if ($env:ARGUS_OFFLINE -ne "1") {
        try {
            $connection = Test-NetConnection -ComputerName "www.google.com" -Port 443 -InformationLevel Quiet -WarningAction SilentlyContinue
            if ($connection) {
                Write-OK "Internet connection verified."
            } else {
                Write-Warn "Internet check failed. Use -Offline or set ARGUS_OFFLINE=1 if installing from local assets."
            }
        } catch {
            Write-Warn "Internet check failed: $($_.Exception.Message)"
        }
    } else {
        Write-Warn "Offline mode enabled; network installs will be skipped or may fail in child scripts."
    }

    try {
        $os = Get-CimInstance Win32_OperatingSystem -ErrorAction Stop
        $totalRam = [Math]::Round($os.TotalVisibleMemorySize / 1MB)
        if ($totalRam -lt $MIN_RAM_GB) {
            Write-Warn "Low RAM detected ($totalRam GB). 16GB+ is recommended for AI models."
        } else {
            Write-OK "RAM: $totalRam GB detected."
        }
    } catch {
        Write-Warn "Could not verify RAM size: $($_.Exception.Message)"
    }

    try {
        $driveName = ([System.IO.Path]::GetPathRoot($ScriptDir)).TrimEnd("\").TrimEnd(":")
        $drive = Get-PSDrive -Name $driveName -ErrorAction Stop
        $freeSpace = [Math]::Round($drive.Free / 1GB, 1)
        if ($freeSpace -lt $MIN_DISK_GB) {
            Write-Warn "Low disk space ($freeSpace GB free on ${driveName}:). You may need 20GB+."
        } else {
            Write-OK "Disk space: $freeSpace GB free on ${driveName}:."
        }
    } catch {
        Write-Warn "Could not verify disk space: $($_.Exception.Message)"
    }
}

function Invoke-InstallerStep {
    param(
        [int]$ID,
        [string]$Name,
        [string]$Script,
        [bool]$RequiresAdmin = $false
    )

    if ($RequiresAdmin -and -not (Test-IsAdministrator)) {
        Write-ErrorMsg "Step $ID requires Administrator privileges. Restart PowerShell as Administrator and rerun the installer."
        return $false
    }

    if ($Interactive) {
        $confirm = Read-Host "`nProceed with Step $ID`: $Name? [Y/n]"
        if ($confirm -eq "n") {
            Write-Warn "Step $ID skipped by user."
            return $true
        }
    } else {
        Write-Log "INFO" "Auto executing Step $ID`: $Name"
    }

    Write-Step $ID $Name
    $scriptPath = Join-Path $ScriptDir $Script
    if (-not (Test-Path -LiteralPath $scriptPath)) {
        Write-ErrorMsg "Script not found: $scriptPath"
        return $false
    }

    for ($attempt = 1; $attempt -le [Math]::Max(1, $RetryCount); $attempt++) {
        Write-Log "INFO" "Starting Step $ID attempt $attempt/${RetryCount}: $scriptPath"
        $process = Start-Process cmd.exe -ArgumentList "/c `"$scriptPath`"" -Wait -NoNewWindow -PassThru
        if ($process.ExitCode -eq 0) {
            Write-OK "Step $ID completed successfully."
            return $true
        }

        Write-Warn "Step $ID failed with exit code $($process.ExitCode) on attempt $attempt."
        if ($attempt -lt $RetryCount) {
            Start-Sleep -Seconds 5
        }
    }

    Write-ErrorMsg "Step $ID failed after $RetryCount attempt(s)."
    return $false
}

Write-Header "ARGUS SECURITY FRAMEWORK - INSTALLER"

if (-not (Test-IsAdministrator)) {
    Write-Warn "This installer is not running as Administrator. WSL, Windows features, and winget installs may fail."
}

Test-SystemReadiness

if (-not (Install-Python)) {
    Write-ErrorMsg "Python prerequisite is not satisfied. Aborting before system-changing setup steps."
    exit 10
}

$steps = @(
    @{ ID = 1; Name = "Preparing Host and Kali Linux Foundation"; Script = "Setup\Step_1_Core_Foundation.bat"; Critical = $true; RequiresAdmin = $true },
    @{ ID = 2; Name = "Preparing Python AI Environment and Models"; Script = "Setup\Step_2_AI_Python_Env.bat"; Critical = $true; RequiresAdmin = $false },
    @{ ID = 3; Name = "Preparing Security Tools inside Kali Linux"; Script = "Setup\Step_3_Kali_Tools_Setup.bat"; Critical = $false; RequiresAdmin = $false }
)

$failed = @()
foreach ($step in $steps) {
    $ok = Invoke-InstallerStep -ID $step.ID -Name $step.Name -Script $step.Script -RequiresAdmin $step.RequiresAdmin
    if (-not $ok) {
        $failed += $step.ID
        if ($step.Critical) {
            Write-ErrorMsg "Critical step $($step.ID) failed. Aborting remaining setup."
            exit $step.ID
        }
    }
}

if (-not $SkipHealthCheck) {
    Write-Header "RUNNING SYSTEM FINAL VALIDATION"
    $healthCheck = Join-Path $ScriptDir "scripts\CHECK_HEALTH.bat"
    if (Test-Path -LiteralPath $healthCheck) {
        $env:ARGUS_SKIP_PAUSE = "1"
        $process = Start-Process cmd.exe -ArgumentList "/c `"$healthCheck`"" -Wait -NoNewWindow -PassThru
        if ($process.ExitCode -ne 0) {
            Write-Warn "Health check exited with code $($process.ExitCode)."
        }
    } else {
        Write-Warn "Health check not found: $healthCheck"
    }
}

if ($failed.Count -gt 0) {
    Write-Header "ARGUS INSTALLATION FINISHED WITH WARNINGS"
    Write-Warn "Failed non-critical steps: $($failed -join ', ')"
    exit 20
}

Write-Header "ARGUS INSTALLATION FINISHED"
Write-OK "Use LAUNCH_STUDIO.bat to start the system."
