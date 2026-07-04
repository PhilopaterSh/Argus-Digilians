#Requires -Version 5.1
<#
.SYNOPSIS
    Argus Security Framework - Single Master Installer.

.DESCRIPTION
    A single, self-contained module that self-elevates up front, then installs,
    configures, and validates the entire Argus environment (Python + Ollama +
    WSL2/Kali + AI venv + Kali tools + SSH bridge + embedded health check) and
    leaves the project ready to run.

    This script supersedes the legacy Setup/Step_*.bat orchestration by embedding all
    step logic in one idempotent, self-elevating PowerShell module.

.PARAMETER Offline
    Skip all network downloads (Python winget, Ollama install, ollama pull).

.PARAMETER Interactive
    Prompt for confirmation before each critical step.

.PARAMETER DryRun
    Run the logic without making any system changes (to verify paths and logic only).

.PARAMETER SkipHealthCheck
    Skip the embedded final health check.

.PARAMETER RetryCount
    Number of retry attempts per step (default 2).

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\INSTALL_EVERYTHING.ps1
.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\INSTALL_EVERYTHING.ps1 -DryRun
.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\INSTALL_EVERYTHING.ps1 -Offline -Interactive
#>

[CmdletBinding()]
param(
    [switch]$Offline,
    [switch]$Interactive,
    [switch]$DryRun,
    [switch]$SkipHealthCheck,
    [int]$RetryCount = 2
)

# ---------------------------------------------------------------------------
# CONFIG BLOCK  (single source of truth for all tunables)
# ---------------------------------------------------------------------------
$MIN_RAM_GB            = 8
$MIN_DISK_GB           = 20
$PYTHON_REQUIRED       = "3.12"
$KALI_DISTRO           = "kali-linux"
$OLLAMA_MODEL          = if ($env:ARGUS_MODEL) { $env:ARGUS_MODEL } else { "WhiteRabbitNeo/WhiteRabbitNeo-V3-7B:latest" }  # default AI model
$OLLAMA_EMBEDDING_MODEL = "nomic-embed-text"  # embedding model for RAG
$OLLAMA_MODEL_MIN_GB   = if ($env:ARGUS_MODEL_MIN_GB) { [int]$env:ARGUS_MODEL_MIN_GB } else { 8 }
$MODEL_PULL_RETRIES    = if ($env:ARGUS_MODEL_PULL_RETRIES) { [int]$env:ARGUS_MODEL_PULL_RETRIES } else { 3 }
$SETUP_DIR             = "Setup"   # contains check_and_install.sh + requirements.txt
$VENV_NAME             = "Argus_venv"

# ---------------------------------------------------------------------------
# ENVIRONMENT / PATHS
# ---------------------------------------------------------------------------
$ErrorActionPreference = "Stop"
$ScriptDir   = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ProjectRoot = Split-Path -Parent $ScriptDir
$SetupRoot   = Join-Path $ProjectRoot $SETUP_DIR
$LogsDir     = Join-Path $ProjectRoot "logs"
$null = New-Item -ItemType Directory -Force -Path $LogsDir -ErrorAction SilentlyContinue
$LogFile     = Join-Path $LogsDir ("argus_install_{0}.log" -f (Get-Date -Format "yyyyMMdd_HHmmss"))

$env:ARGUS_AUTO_INSTALL = if ($Interactive) { "" } else { "1" }
if ($Offline) { $env:ARGUS_OFFLINE = "1" }
if ($DryRun)  { $env:ARGUS_DRY_RUN = "1" }

Set-Location -LiteralPath $ProjectRoot

# Track per-step results for the final report
$script:StepResults = New-Object System.Collections.Generic.List[object]

# ---------------------------------------------------------------------------
# LOGGING HELPERS
# ---------------------------------------------------------------------------
function Write-Log {
    param(
        [string]$Level,
        [string]$Message,
        [ConsoleColor]$Color = [ConsoleColor]::White
    )
    $line = "[{0}] [{1}] {2}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Level, $Message
    Write-Host $line -ForegroundColor $Color
    Add-Content -LiteralPath $LogFile -Value $line -ErrorAction SilentlyContinue
}

function Write-Header {
    param([string]$Text)
    $bar = "========================================================"
    Write-Host ""
    Write-Host $bar -ForegroundColor Cyan
    Write-Host "         $Text" -ForegroundColor Cyan
    Write-Host $bar -ForegroundColor Cyan
    Write-Host ""
    Add-Content -LiteralPath $LogFile -Value "`n$bar`n         $Text`n$bar" -ErrorAction SilentlyContinue
}

function Write-OK    { param([string]$Msg) Write-Log "OK"   $Msg Green }
function Write-Warn  { param([string]$Msg) Write-Log "WARN" $Msg Yellow }
function Write-Err   { param([string]$Msg) Write-Log "ERROR" $Msg Red }
function Write-Step  { param([int]$S, [string]$Msg) Write-Log "STEP $S" $Msg Magenta }
function Write-Info  { param([string]$Msg) Write-Log "INFO" $Msg Cyan }

function Record-Step {
    param([int]$Id, [string]$Name, [string]$Status, [string]$Detail = "")
    $script:StepResults.Add([pscustomobject]@{ Id = $Id; Name = $Name; Status = $Status; Detail = $Detail })
}

# ---------------------------------------------------------------------------
# SELF-ELEVATION  (Admin-first principle - happens once at the very start)
# ---------------------------------------------------------------------------
function Test-IsAdministrator {
    $currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    return $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Invoke-SelfElevation {
    # Relaunch ourselves elevated, preserving arguments.
    if (Test-IsAdministrator) { return }

    Write-Warn "Not running as Administrator. Requesting elevation..."

    $argList = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "`"$PSCommandPath`"")
    if ($Offline)         { $argList += "-Offline" }
    if ($Interactive)     { $argList += "-Interactive" }
    if ($DryRun)          { $argList += "-DryRun" }
    if ($SkipHealthCheck) { $argList += "-SkipHealthCheck" }
    $argList += "-RetryCount $RetryCount"

    try {
        Start-Process -FilePath "powershell.exe" -Verb RunAs -ArgumentList $argList -ErrorAction Stop
    } catch {
        Write-Err "Elevation was declined or failed: $($_.Exception.Message)"
        Write-Err "Please right-click PowerShell -> 'Run as administrator' and rerun."
    }
    exit 0
}

# ---------------------------------------------------------------------------
# GENERIC UTILITIES
# ---------------------------------------------------------------------------
function Test-CommandWorks {
    param(
        [Parameter(Mandatory)][string]$CommandPath,
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

function Confirm-Step {
    param([int]$Id, [string]$Name)
    if (-not $Interactive) {
        Write-Info "Auto-executing Step $Id : $Name"
        return $true
    }
    $confirm = Read-Host "`nProceed with Step $Id : $Name? [Y/n]"
    if ($confirm -eq "n") {
        Write-Warn "Step $Id skipped by user."
        return $false
    }
    return $true
}

# Retry wrapper used by mutating operations.
function Invoke-WithRetry {
    param(
        [scriptblock]$Action,
        [string]$Label,
        [int]$Attempts = [Math]::Max(1, $RetryCount)
    )
    for ($i = 1; $i -le $Attempts; $i++) {
        if ($DryRun) {
            Write-Info "[DryRun] Would execute: $Label"
            return $true
        }
        try {
            & $Action
            return $true
        } catch {
            Write-Warn "$Label failed (attempt $i/$Attempts): $($_.Exception.Message)"
            if ($i -lt $Attempts) { Start-Sleep -Seconds 5 }
        }
    }
    return $false
}

# ---------------------------------------------------------------------------
# STEP 0 - SYSTEM READINESS
# ---------------------------------------------------------------------------
function Test-SystemReadiness {
    Write-Step 0 "Verifying System Readiness"
    $ok = $true

    if ($env:ARGUS_OFFLINE -ne "1") {
        try {
            $conn = Test-NetConnection -ComputerName "www.google.com" -Port 443 -InformationLevel Quiet -WarningAction SilentlyContinue
            if ($conn) { Write-OK "Internet connection verified." }
            else {
                Write-Warn "Internet check failed. Use -Offline or ARGUS_OFFLINE=1 if installing from local assets."
            }
        } catch { Write-Warn "Internet check failed: $($_.Exception.Message)" }
    } else {
        Write-Warn "Offline mode enabled; network installs will be skipped."
    }

    try {
        $os = Get-CimInstance Win32_OperatingSystem -ErrorAction Stop
        $ram = [Math]::Round($os.TotalVisibleMemorySize / 1MB)
        if ($ram -lt $MIN_RAM_GB) {
            Write-Warn "Low RAM ($ram GB). 16GB+ recommended for AI models."
        } else { Write-OK "RAM: $ram GB detected." }
    } catch { Write-Warn "Could not verify RAM: $($_.Exception.Message)" }

    try {
        $driveName = ([System.IO.Path]::GetPathRoot($ProjectRoot)).TrimEnd("\").TrimEnd(":")
        $drive = Get-PSDrive -Name $driveName -ErrorAction Stop
        $free = [Math]::Round($drive.Free / 1GB, 1)
        if ($free -lt $MIN_DISK_GB) {
            Write-Warn "Low disk space ($free GB free on ${driveName}:). You may need ${MIN_DISK_GB}GB+."
        } else { Write-OK "Disk space: $free GB free on ${driveName}:." }
    } catch { Write-Warn "Could not verify disk space: $($_.Exception.Message)" }

    return $ok
}

# ---------------------------------------------------------------------------
# STEP 1 - PYTHON 3.12 (bootstrap once, used by all later steps)
# ---------------------------------------------------------------------------
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
        if ($path -and (Test-Path -LiteralPath $path)) { $candidates.Add($path) }
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
    Write-Step 1 "Ensuring Python $PYTHON_REQUIRED is available"

    $python = Get-UsablePython
    if ($null -ne $python) {
        Write-OK "Python is available: $($python.Version)"
        $pyDir   = Split-Path -Parent $python.Path
        $scrDir  = Join-Path $pyDir "Scripts"
        $env:Path = "$pyDir;$scrDir;$env:Path"
        Record-Step 1 "Python $PYTHON_REQUIRED" "OK" $python.Version
        return $true
    }

    if ($env:ARGUS_OFFLINE -eq "1") {
        Write-Err "Offline mode is enabled. Install Python $PYTHON_REQUIRED manually, then rerun."
        Record-Step 1 "Python $PYTHON_REQUIRED" "FAILED" "Not found (offline)"
        return $false
    }

    if (-not (Get-Command winget.exe -ErrorAction SilentlyContinue)) {
        Write-Err "Winget not found. Install Python $PYTHON_REQUIRED manually from python.org."
        Record-Step 1 "Python $PYTHON_REQUIRED" "FAILED" "winget missing"
        return $false
    }

    if ($DryRun) {
        Write-Info "[DryRun] Would install Python $PYTHON_REQUIRED via winget."
        Record-Step 1 "Python $PYTHON_REQUIRED" "DRYRUN" "winget install (simulated)"
        return $true
    }

    Write-Info "Installing Python $PYTHON_REQUIRED via winget..."
    $action = {
        $process = Start-Process winget -ArgumentList "install --id Python.Python.3.12 --source winget --exact --silent --accept-package-agreements --accept-source-agreements" -Wait -PassThru -NoNewWindow
        if ($process.ExitCode -ne 0) { throw "winget exit code $($process.ExitCode)" }
    }
    if (-not (Invoke-WithRetry -Action $action -Label "winget install Python")) {
        Record-Step 1 "Python $PYTHON_REQUIRED" "FAILED" "winget failed"
        return $false
    }

    # Refresh PATH after machine-wide install
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
    $python = Get-UsablePython
    if ($null -eq $python) {
        Write-Err "Python install finished but $PYTHON_REQUIRED still not usable. Restart PowerShell and rerun."
        Record-Step 1 "Python $PYTHON_REQUIRED" "FAILED" "not usable post-install"
        return $false
    }

    Write-OK "Python installed and verified: $($python.Version)"
    Record-Step 1 "Python $PYTHON_REQUIRED" "OK" $python.Version
    return $true
}

# ---------------------------------------------------------------------------
# STEP 2 - HOST FOUNDATION (WSL2 + Kali distro + Ollama)
# ---------------------------------------------------------------------------
function Enable-WindowsFeature {
    param([string]$FeatureName)
    if ($DryRun) {
        Write-Info "[DryRun] Would ensure feature '$FeatureName' is enabled."
        return $true
    }
    try {
        $state = (Get-WindowsOptionalFeature -Online -FeatureName $FeatureName -ErrorAction Stop).State
        if ($state -eq "Enabled") {
            Write-OK "Feature '$FeatureName' already enabled."
            return $true
        }
        Enable-WindowsOptionalFeature -Online -FeatureName $FeatureName -All -NoRestart -ErrorAction Stop | Out-Null
        Write-OK "Feature '$FeatureName' enabled (may require reboot)."
        return $true
    } catch {
        Write-Warn "Could not enable feature '$FeatureName': $($_.Exception.Message)"
        return $false
    }
}

function Test-WslCommand {
    $cmd = Get-Command wsl.exe -ErrorAction SilentlyContinue
    if ($null -eq $cmd) {
        # Fall back to bare 'wsl' which Get-Command may surface differently on older builds
        $cmd = Get-Command wsl -ErrorAction SilentlyContinue
    }
    return $null -ne $cmd
}

function Test-KaliDistro {
    if (-not (Test-WslCommand)) { return $false }
    try {
        $names = (wsl -l -q 2>$null) -replace "`0", ""
        return ($names | Where-Object { $_.Trim() -ieq $KALI_DISTRO }).Count -gt 0
    } catch { return $false }
}

function Install-KaliDistro {
    if (Test-KaliDistro) {
        Write-OK "Kali Linux distro '$KALI_DISTRO' is already installed."
        return $true
    }
    if ($env:ARGUS_OFFLINE -eq "1") {
        Write-Warn "Offline mode: cannot install Kali distro. Install it manually then rerun."
        return $false
    }
    if ($DryRun) {
        Write-Info "[DryRun] Would install Kali distro '$KALI_DISTRO' via wsl --install."
        return $true
    }
    Write-Info "Installing Kali Linux distro '$KALI_DISTRO'..."
    try {
        wsl --install -d $KALI_DISTRO --web-download 2>&1 | ForEach-Object { Write-Info $_ }
        if (-not (Test-KaliDistro)) {
            Write-Warn "Kali distro not detected after install attempt (may need first-run init or reboot)."
            return $false
        }
        Write-OK "Kali Linux distro installed."
        return $true
    } catch {
        Write-Warn "Kali install failed: $($_.Exception.Message)"
        return $false
    }
}

function Test-Ollama {
    return $null -ne (Get-Command ollama.exe -ErrorAction SilentlyContinue)
}

function Install-Ollama {
    if (Test-Ollama) {
        Write-OK "Ollama engine is already installed."
        return $true
    }
    if ($env:ARGUS_OFFLINE -eq "1") {
        Write-Warn "Offline mode: cannot download Ollama. Install from https://ollama.com/ then rerun."
        return $false
    }
    if ($DryRun) {
        Write-Info "[DryRun] Would download and install Ollama from ollama.com/install.ps1."
        return $true
    }
    Write-Info "Downloading and installing Ollama..."
    try {
        & powershell -Command "irm https://ollama.com/install.ps1 | iex"
        if (-not (Test-Ollama)) {
            Write-Warn "Ollama not on PATH after install. You may need to restart the shell."
            return $false
        }
        Write-OK "Ollama installed."
        return $true
    } catch {
        Write-Warn "Ollama install failed: $($_.Exception.Message)"
        return $false
    }
}

function Start-OllamaIfNeeded {
    $running = $false
    $procs = Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -like "*ollama*" }
    if ($procs) { $running = $true }

    if ($running) {
        Write-OK "Ollama engine is already running."
        return $true
    }
    if ($DryRun) {
        Write-Info "[DryRun] Would start the Ollama engine."
        return $true
    }
    try {
        $ollamaApp = Get-Command "ollama app.exe" -ErrorAction SilentlyContinue
        if ($null -ne $ollamaApp) {
            Start-Process -FilePath $ollamaApp.Source -ErrorAction Stop
            Start-Sleep -Seconds 5
            Write-OK "Ollama engine started."
        } else {
            Start-Process -FilePath "ollama" -ArgumentList "serve" -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 5
            Write-OK "Ollama engine started (serve mode)."
        }
        return $true
    } catch {
        Write-Warn "Could not auto-start Ollama: $($_.Exception.Message)"
        return $false
    }
}

function Invoke-StepHostFoundation {
    Write-Step 2 "Host Foundation (WSL2 + Kali + Ollama)"
    if (-not (Confirm-Step 2 "Host Foundation")) { Record-Step 2 "Host Foundation" "SKIPPED" ""; return $true }

    $featuresOk = $true
    $featuresOk = (Enable-WindowsFeature "Microsoft-Windows-Subsystem-Linux") -and $featuresOk
    $featuresOk = (Enable-WindowsFeature "VirtualMachinePlatform") -and $featuresOk

    if (-not (Test-WslCommand)) {
        Write-Err "wsl.exe not available after enabling features. Please REBOOT and rerun the installer."
        Record-Step 2 "Host Foundation" "FAILED" "WSL unavailable (reboot needed)"
        return $false
    }

    $kaliOk = Install-KaliDistro
    if (-not (Test-KaliDistro)) {
        Write-Err "Kali distro not installed/functional. Run Step 1, reboot if features were enabled, then rerun."
        Record-Step 2 "Host Foundation" "FAILED" "Kali distro missing"
        return $false
    }
    if ($DryRun) {
        Write-Info "[DryRun] Would run 'wsl --set-default-version 2'."
    } else {
        wsl --set-default-version 2 > $null 2>&1
    }

    $ollamaOk = Install-Ollama
    if ($ollamaOk) { $null = Start-OllamaIfNeeded }

    Record-Step 2 "Host Foundation" $(if ($kaliOk) { "OK" } else { "WARN" }) "Kali=$kaliOk Ollama=$ollamaOk Features=$featuresOk"
    return $true
}

# ---------------------------------------------------------------------------
# STEP 3 - AI ENVIRONMENT (Argus_venv + pip + model pull)
# ---------------------------------------------------------------------------
function Invoke-StepAiEnvironment {
    Write-Step 3 "AI Environment (venv + pip + model pull)"
    if (-not (Confirm-Step 3 "AI Environment")) { Record-Step 3 "AI Environment" "SKIPPED" ""; return $true }

    # Ollama must be present and running for the model step
    if (-not (Test-Ollama)) {
        Write-Warn "Ollama is not installed. Skipping model pull (host foundation may have failed)."
        Record-Step 3 "AI Environment" "WARN" "Ollama missing -> model skipped"
    }

    # --- venv ---
    $venvPath = Join-Path $ProjectRoot $VENV_NAME
    if (Test-Path -LiteralPath (Join-Path $venvPath "Scripts\python.exe")) {
        Write-OK "Virtual environment already exists at $venvPath"
    } else {
        if ($DryRun) {
            Write-Info "[DryRun] Would create venv at $venvPath"
        } else {
            Write-Info "Creating virtual environment at $venvPath..."
            $python = Get-UsablePython
            if ($null -eq $python) {
                Write-Err "Python is not available; cannot create venv."
                Record-Step 3 "AI Environment" "FAILED" "Python missing"
                return $false
            }
            & $python.Path -m venv $venvPath
            if (-not (Test-Path -LiteralPath (Join-Path $venvPath "Scripts\activate.bat"))) {
                Write-Err "Failed to create virtual environment."
                Record-Step 3 "AI Environment" "FAILED" "venv creation failed"
                return $false
            }
            Write-OK "Virtual environment created."
        }
    }

    # --- pip install ---
    $reqPath = Join-Path $SetupRoot "requirements.txt"
    if (-not (Test-Path -LiteralPath $reqPath)) {
        Write-Err "requirements.txt not found at $reqPath"
        Record-Step 3 "AI Environment" "FAILED" "requirements.txt missing"
        return $false
    }

    $marker = Join-Path $venvPath ".requirements_installed"
    $runPip = $true
    if (Test-Path -LiteralPath $marker) {
        try {
            $reqTime  = (Get-Item -LiteralPath $reqPath).LastWriteTime
            $markTime = (Get-Item -LiteralPath $marker).LastWriteTime
            if ($reqTime -le $markTime) { $runPip = $false }
        } catch { $runPip = $true }
    }

    $venvPython = Join-Path $venvPath "Scripts\python.exe"
    if ($runPip) {
        if ($DryRun) {
            Write-Info "[DryRun] Would run pip install -r requirements.txt"
        } else {
            Write-Info "Synchronizing Python libraries (this may take a moment)..."
            $action = {
                & $venvPython -m pip install --upgrade pip --quiet
                & $venvPython -m pip install -r $reqPath --quiet
                if ($LASTEXITCODE -ne 0) { throw "pip install failed (exit $LASTEXITCODE)" }
            }
            if (Invoke-WithRetry -Action $action -Label "pip install requirements") {
                Set-Content -LiteralPath $marker -Value "installed" -ErrorAction SilentlyContinue
                Write-OK "All Python libraries are up to date."
            } else {
                Write-Err "Library synchronization failed."
                Record-Step 3 "AI Environment" "FAILED" "pip install failed"
                return $false
            }
        }
    } else {
        Write-OK "Libraries already satisfied (skip)."
    }

    # --- model pull: main LLM ---
    $modelOk = $true
    if (Test-Ollama) {
        if ($DryRun) {
            Write-Info "[DryRun] Would verify/pull model '$OLLAMA_MODEL'"
        } else {
            # Disk space guard before pulling
            try {
                $driveName = ([System.IO.Path]::GetPathRoot($ProjectRoot)).TrimEnd("\").TrimEnd(":")
                $free = [Math]::Round((Get-PSDrive -Name $driveName).Free / 1GB, 1)
                if ($free -lt $OLLAMA_MODEL_MIN_GB) {
                    Write-Warn "Less than ${OLLAMA_MODEL_MIN_GB}GB free ($free GB). Skipping model pull; set a smaller model via ARGUS_MODEL."
                    $modelOk = $false
                }
            } catch { }

            if ($modelOk) {
                $already = $false
                try {
                    $listOut = (ollama list 2>$null) -join "`n"
                    if ($listOut -match [regex]::Escape($OLLAMA_MODEL.Split(':')[0])) { $already = $true }
                } catch { }
                if ($already) {
                    Write-OK "Model '$OLLAMA_MODEL' already present."
                } else {
                    Write-Info "Pulling model '$OLLAMA_MODEL' (depends on internet speed)..."
                    $pulled = $false
                    for ($a = 1; $a -le $MODEL_PULL_RETRIES; $a++) {
                        Write-Info "Pull attempt $a/$MODEL_PULL_RETRIES..."
                        & ollama pull $OLLAMA_MODEL
                        if ($LASTEXITCODE -eq 0) { $pulled = $true; break }
                        Write-Warn "Pull failed (attempt $a). Retrying in 10s..."
                        Start-Sleep -Seconds 10
                    }
                    if ($pulled) { Write-OK "Model pulled successfully." }
                    else { Write-Warn "Model pull failed after $MODEL_PULL_RETRIES attempts."; $modelOk = $false }
                }
            }
        }
    }

    # --- model pull: embedding model for RAG ---
    $embOk = $true
    if (Test-Ollama) {
        if ($DryRun) {
            Write-Info "[DryRun] Would verify/pull embedding model '$OLLAMA_EMBEDDING_MODEL'"
        } else {
            $already = $false
            try {
                $listOut = (ollama list 2>$null) -join "`n"
                if ($listOut -match [regex]::Escape($OLLAMA_EMBEDDING_MODEL)) { $already = $true }
            } catch { }
            if ($already) {
                Write-OK "Embedding model '$OLLAMA_EMBEDDING_MODEL' already present."
            } else {
                Write-Info "Pulling embedding model '$OLLAMA_EMBEDDING_MODEL'..."
                & ollama pull $OLLAMA_EMBEDDING_MODEL
                if ($LASTEXITCODE -eq 0) {
                    Write-OK "Embedding model pulled successfully."
                } else {
                    Write-Warn "Embedding model pull failed."
                    $embOk = $false
                }
            }
        }
    }

    Record-Step 3 "AI Environment" $(if ($modelOk -and $embOk) { "OK" } else { "WARN" }) "venv + pip + model=$modelOk emb=$embOk"
    return $true
}

# ---------------------------------------------------------------------------
# STEP 4 - KALI TOOLS (run check_and_install.sh inside WSL)
# ---------------------------------------------------------------------------
function Invoke-StepKaliTools {
    Write-Step 4 "Kali Security Tools (inside WSL)"
    if (-not (Confirm-Step 4 "Kali Tools")) { Record-Step 4 "Kali Tools" "SKIPPED" ""; return $true }

    $shScript = Join-Path $SetupRoot "check_and_install.sh"
    if (-not (Test-Path -LiteralPath $shScript)) {
        Write-Err "Missing Kali installer script: $shScript"
        Record-Step 4 "Kali Tools" "FAILED" "check_and_install.sh missing"
        return $false
    }
    if (-not (Test-KaliDistro)) {
        Write-Err "WSL distro '$KALI_DISTRO' not installed/functional. Run host foundation first."
        Record-Step 4 "Kali Tools" "FAILED" "Kali distro missing"
        return $false
    }

    if ($DryRun) {
        Write-Info "[DryRun] Would translate path and run bash '$shScript' inside WSL root."
        Record-Step 4 "Kali Tools" "DRYRUN" "check_and_install.sh (simulated)"
        return $true
    }

    # Translate Windows path -> /mnt/... WSL path
    try {
        $wslPath = (& wsl wslpath -u $shScript).Trim()
    } catch {
        # Manual fallback
        $drive = $shScript.Substring(0,1).ToLowerInvariant()
        $rest  = $shScript.Substring(2).Replace('\','/')
        $wslPath = "/mnt/$drive$rest"
    }
    Write-Info "Linux script path: $wslPath"

    try {
        Write-Info "Normalizing line endings..."
        wsl -u root bash -lc "sed -i 's/\r$//' '$wslPath'" 2>&1 | ForEach-Object { Write-Info $_ }
        Write-Info "Running Kali tool installer..."
        wsl -u root bash -lc "bash '$wslPath'" 2>&1 | ForEach-Object { Write-Info $_ }
        if ($LASTEXITCODE -ne 0) {
            Write-Warn "Kali tool setup exited with code $LASTEXITCODE (some optional tools may have failed)."
            Record-Step 4 "Kali Tools" "WARN" "exit $LASTEXITCODE (optional tools may be partial)"
            return $true
        }
        Write-OK "Kali tool setup completed."
        Record-Step 4 "Kali Tools" "OK" "check_and_install.sh ran"
        return $true
    } catch {
        Write-Err "Kali tool setup failed: $($_.Exception.Message)"
        Record-Step 4 "Kali Tools" "FAILED" $_.Exception.Message
        return $false
    }
}

# ---------------------------------------------------------------------------
# STEP 5 - SSH BRIDGE
# ---------------------------------------------------------------------------
function Invoke-StepSshBridge {
    Write-Step 5 "SSH Bridge to WSL (Kali)"
    if (-not (Confirm-Step 5 "SSH Bridge")) { Record-Step 5 "SSH Bridge" "SKIPPED" ""; return $true }
    if (-not (Test-KaliDistro)) {
        Write-Warn "Kali distro missing; skipping SSH bridge setup."
        Record-Step 5 "SSH Bridge" "WARN" "Kali missing"
        return $true
    }

    if ($DryRun) {
        Write-Info "[DryRun] Would start sshd inside Kali and test port 22."
        Record-Step 5 "SSH Bridge" "DRYRUN" "sshd + port 22 test (simulated)"
        return $true
    }

    try {
        wsl -d $KALI_DISTRO -u root bash -c "mkdir -p /run/sshd && /usr/sbin/sshd" 2>&1 | ForEach-Object { Write-Info $_ }
        Start-Sleep -Seconds 2
        $res = Test-NetConnection -ComputerName "127.0.0.1" -Port 22 -WarningAction SilentlyContinue
        if ($res.TcpTestSucceeded) {
            Write-OK "SSH bridge (port 22) is active."
            Record-Step 5 "SSH Bridge" "OK" "port 22 reachable"
            return $true
        }
        Write-Warn "SSH bridge (port 22) is not reachable yet. It may start on next WSL boot."
        Record-Step 5 "SSH Bridge" "WARN" "port 22 not reachable"
        return $true
    } catch {
        Write-Warn "SSH bridge setup issue: $($_.Exception.Message)"
        Record-Step 5 "SSH Bridge" "WARN" $_.Exception.Message
        return $true
    }
}

# ---------------------------------------------------------------------------
# STEP 6 - INLINE HEALTH CHECK (no external file)
# ---------------------------------------------------------------------------
function Invoke-HealthCheck {
    Write-Header "SYSTEM HEALTH CHECK (Embedded)"
    $healthy = $true
    $checks = @()

    # venv
    $venvPy = Join-Path $ProjectRoot "$VENV_NAME\Scripts\python.exe"
    $venvOk = Test-Path -LiteralPath $venvPy
    $checks += [pscustomobject]@{ Component = "Argus_venv";   Status = $(if ($venvOk) { "OK" } else { "MISSING" }) }
    if (-not $venvOk) { $healthy = $false }

    # Ollama running
    $ollamaProc = Get-Process | Where-Object { $_.ProcessName -like "*ollama*" }
    $ollamaOk = $null -ne $ollamaProc
    $checks += [pscustomobject]@{ Component = "Ollama engine"; Status = $(if ($ollamaOk) { "ONLINE" } else { "OFFLINE" }) }
    if (-not $ollamaOk) { $healthy = $false }

    # Kali
    $kaliOk = Test-KaliDistro
    $checks += [pscustomobject]@{ Component = "Kali (WSL)";    Status = $(if ($kaliOk) { "OK" } else { "NOT FOUND" }) }
    if (-not $kaliOk) { $healthy = $false }

    # nomic-embed-text model
    $nomicOk = $false
    try {
        $listOut = (ollama list 2>$null) -join "`n"
        if ($listOut -match "nomic-embed-text") { $nomicOk = $true }
    } catch { }
    $checks += [pscustomobject]@{ Component = "nomic-embed-text"; Status = $(if ($nomicOk) { "OK" } else { "MISSING" }) }
    if (-not $nomicOk) { $healthy = $false }

    # SSH bridge
    $sshOk = $false
    try {
        $r = Test-NetConnection -ComputerName "127.0.0.1" -Port 22 -WarningAction SilentlyContinue
        $sshOk = $r.TcpTestSucceeded
    } catch { $sshOk = $false }
    $checks += [pscustomobject]@{ Component = "SSH bridge (22)"; Status = $(if ($sshOk) { "ACTIVE" } else { "DOWN" }) }
    if (-not $sshOk) { $healthy = $false }

    $checks | Format-Table -AutoSize | Out-String | Write-Host
    $checks | ForEach-Object { Add-Content -LiteralPath $LogFile -Value ("{0,-20} {1}" -f $_.Component, $_.Status) -ErrorAction SilentlyContinue }

    if ($healthy) { Write-OK "SYSTEM IS HEALTHY AND READY!" }
    else { Write-Warn "SYSTEM HAS ISSUES - see the table above." }
    return $healthy
}

# ---------------------------------------------------------------------------
# FINAL REPORT
# ---------------------------------------------------------------------------
function Show-FinalReport {
    param([string[]]$Failed)
    Write-Header "ARGUS INSTALLATION SUMMARY"

    Write-Host "Per-step results:" -ForegroundColor White
    $script:StepResults | Format-Table -AutoSize | Out-String | Write-Host
    $script:StepResults | ForEach-Object {
        Add-Content -LiteralPath $LogFile -Value ("Step {0}: {1,-16} {2} {3}" -f $_.Id, $_.Status, $_.Name, $_.Detail) -ErrorAction SilentlyContinue
    }

    Write-Info "Log file: $LogFile"

    if ($Failed.Count -gt 0) {
        Write-Header "INSTALLATION FINISHED WITH WARNINGS"
        Write-Warn "Failed non-critical steps: $($Failed -join ', ')"
        return 20
    }

    Write-Header "ARGUS INSTALLATION FINISHED"
    Write-OK "Use scripts\LAUNCH_STUDIO.bat to start the system."
    Write-OK "Use scripts\LAUNCH_CLI.bat to start the CLI agent."
    return 0
}

# ===========================================================================
# MAIN PIPELINE
# ===========================================================================
Write-Header "ARGUS SECURITY FRAMEWORK - INSTALLER (Unified)"
if ($DryRun) { Write-Warn "DRY RUN mode: no system changes will be made." }

# Admin-first: self-elevate before anything mutating happens.
Invoke-SelfElevation

# At this point we are guaranteed to be elevated (or the user declined elevation).
if (-not (Test-IsAdministrator)) {
    Write-Err "Administrator privileges are required. Aborting."
    Write-Info "Right-click PowerShell -> 'Run as administrator' and rerun, or run INSTALL.bat."
    exit 1
}
Write-OK "Running with Administrator privileges."

$null = Test-SystemReadiness

# Step 1 - Python (critical prerequisite)
if (-not (Install-Python)) {
    Write-Err "Python prerequisite not satisfied. Aborting before system-changing steps."
    $null = Show-FinalReport -Failed @(1)
    exit 10
}

# Steps 2..5 - orchestrated, non-critical failures collected
$failed = @()

$ok2 = Invoke-StepHostFoundation
if (-not $ok2) { $failed += 2 }

$ok3 = Invoke-StepAiEnvironment
if (-not $ok3) { $failed += 3 }

$ok4 = Invoke-StepKaliTools
if (-not $ok4) { $failed += 4 }

$ok5 = Invoke-StepSshBridge
if (-not $ok5) { $failed += 5 }

# Step 6 - embedded health check
if (-not $SkipHealthCheck) {
    $null = Invoke-HealthCheck
} else {
    Write-Info "Health check skipped (-SkipHealthCheck)."
}

$exitCode = Show-FinalReport -Failed $failed
exit $exitCode
