param (
    [string]$Remote = "origin",
    [string]$MainBranch = "main"
)

# Identify device and setup branch name
$ComputerName = $env:COMPUTERNAME.Replace(" ", "-")
$DeviceBranch = "argus/$ComputerName"

function Show-Header {
    Clear-Host
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "     ARGUS SECURITY FRAMEWORK: AUTOMATED LOOP V9.0          " -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host " Device Identity : $ComputerName" -ForegroundColor Yellow
    Write-Host " Secure Branch   : $DeviceBranch" -ForegroundColor Yellow
    Write-Host " Workflow        : PUSH to Branch -> PULL from Main" -ForegroundColor Green
    Write-Host "------------------------------------------------------------" -ForegroundColor Gray
}

function Show-Help {
    Clear-Host
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "        ARGUS SECURITY FRAMEWORK | SYNC ENGINE              " -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host " [Identity] : $ComputerName" -ForegroundColor Yellow
    Write-Host " [Branch]   : $DeviceBranch" -ForegroundColor Yellow
    Write-Host "------------------------------------------------------------" -ForegroundColor Gray
    Write-Host ""
    Write-Host "   DESCRIPTION" -ForegroundColor White -BackgroundColor Blue
    Write-Host "     Automated synchronization bridge for Argus Intelligence."
    Write-Host "     Protects local findings and pulls global project updates."
    Write-Host ""
    Write-Host "   USAGE" -ForegroundColor White -BackgroundColor DarkGreen
    Write-Host "     .\Argus_Secure_Sync.ps1 [-Remote name] [-MainBranch name]"
    Write-Host "     .\Argus_Secure_Sync.ps1 --help"
    Write-Host ""
    Write-Host "   OPTIONS" -ForegroundColor White -BackgroundColor DarkGray
    Write-Host "     -Remote       Git remote target (Default: origin)" -ForegroundColor Gray
    Write-Host "     -MainBranch   Source for updates (Default: main)" -ForegroundColor Gray
    Write-Host "     --help, -h    Display this technical reference" -ForegroundColor Gray
    Write-Host ""
    Write-Host "   WORKFLOW STEPS" -ForegroundColor Black -BackgroundColor Yellow
    Write-Host "     1. [SECURE]     Commit findings to local branch" -ForegroundColor Yellow
    Write-Host "     2. [TRANSMIT]   Push intelligence to private cloud" -ForegroundColor Cyan
    Write-Host "     3. [INTEGRATE]  Merge latest changes from main team" -ForegroundColor Green
    Write-Host ""
    Write-Host "------------------------------------------------------------" -ForegroundColor Gray
    Write-Host " Press any key to return to terminal..." -ForegroundColor White
    [void]$Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

# Check for help arguments
foreach ($arg in $args) {
    if ($arg -match '^(-h|--help|help|--h|-\?|/h|/\?)$') {
        Show-Help
        exit 0
    }
}

# Initial Setup - Dependency Check (Git)
if (!(Get-Command git -ErrorAction SilentlyContinue)) {
    Show-Header
    Write-Host "[!] Git is missing. Attempting automated installation via Winget..." -ForegroundColor Yellow
    
    # Check if Winget is available
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Write-Host "[*] Installing Git... Please wait." -ForegroundColor Cyan
        winget install --id Git.Git --exact --silent --accept-package-agreements --accept-source-agreements
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[SUCCESS] Git installed. You MUST restart this terminal/script to apply changes." -ForegroundColor Green
        } else {
            Write-Host "[ERROR] Winget failed to install Git. Please install it manually from https://git-scm.com/" -ForegroundColor Red
        }
    } else {
        Write-Host "[ERROR] Winget not found. Please install Git manually from https://git-scm.com/" -ForegroundColor Red
    }
    
    Write-Host "`nPress any key to exit..." -ForegroundColor Gray
    [void]$Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown"); exit 1
}

# Initial Setup - Repo Check
$isGit = git rev-parse --is-inside-work-tree 2>$null
if ($LASTEXITCODE -ne 0) {
    Show-Header
    Write-Host "CRITICAL ERROR: Argus repository not found." -ForegroundColor Red
    Write-Host "`nPress any key to exit..." -ForegroundColor Gray
    [void]$Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown"); exit 1
}

Show-Header

# MAINTENANCE: Clean up problematic Windows system files in .git folder
if (Test-Path ".git") {
    # Remove desktop.ini files that can corrupt Git's internal references
    Get-ChildItem -Path ".git" -Filter "desktop.ini" -Recurse -Force -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
}

try {
    # Ensure we are on the Device Branch
    $currentBranch = git rev-parse --abbrev-ref HEAD
    if ($currentBranch -ne $DeviceBranch) {
        Write-Host "[1/4] INITIALIZING: Switching to secure device branch..." -ForegroundColor Gray
        git checkout -b $DeviceBranch 2>$null
        git checkout $DeviceBranch 2>$null
    }

    # PHASE 1: SECURE & TRANSMIT (Push to Device Branch)
    Write-Host "[2/4] SECURING: Transmitting findings to $DeviceBranch..." -ForegroundColor Cyan
    git add .
    $status = git status --porcelain
    if (![string]::IsNullOrEmpty($status)) {
        $timeStr = Get-Date -Format "yyyy-MM-dd HH:mm"
        git commit -m "[Argus-$ComputerName] Intelligence Captured"
    }
    
    # Sync with cloud version of THIS branch first to avoid push rejection
    git pull $Remote $DeviceBranch --no-edit -s recursive -X ours 2>$null
    git push $Remote $DeviceBranch
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "SUCCESS: Data secured on private branch." -ForegroundColor Green
    } else {
        Write-Host "WARNING: Private sync failed. Check cloud connectivity." -ForegroundColor Yellow
    }

    # PHASE 2: INTEGRATE (Pull from Main)
    Write-Host "`n[3/4] INTEGRATING: Fetching global updates from $MainBranch..." -ForegroundColor Cyan
    git fetch $Remote $MainBranch --quiet
    
    # Merge Main into Device Branch
    # Using -X ours to ensure that if there's a conflict, the local work (which was just pushed) is preserved
    git merge "$Remote/$MainBranch" --no-edit -s recursive -X ours
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "SUCCESS: Global updates integrated into workspace." -ForegroundColor Green
    } else {
        Write-Host "INFO: Local findings are already ahead or unified with Main." -ForegroundColor Gray
    }

    # PHASE 3: FINAL STATUS
    Write-Host "`n[4/4] COMPLETED: Your workspace is now fully synchronized." -ForegroundColor Green

} catch {
    Write-Host "`nCRITICAL ERROR during automated loop: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "------------------------------------------------------------" -ForegroundColor Gray
Write-Host "Press any key to close..." -ForegroundColor White
[void]$Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
