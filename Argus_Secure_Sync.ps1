param (
    [Parameter(Position=0)]
    [string]$Remote = "origin",
    
    [Parameter(Position=1)]
    [string]$MainBranch = "main",
    
    [switch]$Minimal, # Flag to hide raw Git output

    [Alias("h", "?")]
    [switch]$Help
)

# Identify device and setup branch name
$ComputerName = $env:COMPUTERNAME.Replace(" ", "-")
$DeviceBranch = "argus/$ComputerName"

function Show-Help {
    Clear-Host
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "        ARGUS SECURITY FRAMEWORK | SYNC ENGINE GUIDE        " -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host " [?] MISSION OBJECTIVE" -ForegroundColor White -BackgroundColor Blue
    Write-Host "     Automated secure bridge for Argus Intelligence."
    Write-Host ""
    Write-Host " [1] DEFAULT MODE (Transparent)" -ForegroundColor Yellow
    Write-Host "     The script now shows all raw Git output by default "
    Write-Host "     for maximum transparency and easier debugging."
    Write-Host ""
    Write-Host " [2] COMMAND SIGNALS (Flags & Options)" -ForegroundColor Yellow
    Write-Host "     -h, --help    : Shows this comprehensive guide."
    Write-Host "     -Minimal      : Enables Clean UI (Hides raw Git logs)."
    Write-Host "     -Remote       : Specify custom Remote (Def: origin)."
    Write-Host ""
    Write-Host " [!] USAGE EXAMPLES" -ForegroundColor Black -BackgroundColor Yellow
    Write-Host "     Default Sync  : .\Argus_Secure_Sync.ps1"
    Write-Host "     Clean UI Sync : .\Argus_Secure_Sync.ps1 -Minimal"
    Write-Host "------------------------------------------------------------" -ForegroundColor Gray
    Write-Host " Press any key to exit help..." -ForegroundColor White
    [void]$Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

# Explicit Help Trigger
if ($Help) { Show-Help; exit 0 }

function Show-Header {
    Clear-Host
    Write-Host ">>> ARGUS SYNC ENGINE | $ComputerName | $DeviceBranch" -ForegroundColor Cyan
    if (-not $Minimal) { Write-Host ">>> MODE: TRANSPARENT (Detailed)" -ForegroundColor Gray }
    Write-Host "------------------------------------------------------------" -ForegroundColor Gray
}

# --- Automated Git Installer ---
if (!(Get-Command git -ErrorAction SilentlyContinue)) {
    Show-Header
    Write-Host "[!] Git is missing. Attempting automated installation..." -ForegroundColor Yellow
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        winget install --id Git.Git --exact --silent --accept-package-agreements --accept-source-agreements
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[SUCCESS] Git installed. Restart the terminal." -ForegroundColor Green
        } else {
            Write-Host "[ERROR] Winget failed." -ForegroundColor Red
        }
    }
    exit 1
}

# Refined Invoke-Git for default transparency with safety
function Invoke-Git {
    param([string]$Command, [string]$StepName)
    if ($Minimal) {
        $output = Invoke-Expression "$Command 2>&1"
        if ($LASTEXITCODE -ne 0) {
            Write-Host "`n[!] ERROR IN ${StepName}:" -ForegroundColor Red
            Write-Host $output -ForegroundColor Gray
            throw "Git command failed."
        }
        return $output
    } else {
        # Default: Show output directly to console
        Invoke-Expression $Command
        if ($LASTEXITCODE -ne 0) {
            Write-Host "`n[!] CRITICAL ERROR during ${StepName}!" -ForegroundColor Red
            throw "Execution Halted."
        }
    }
}

Show-Header

# Fix Git corruption (desktop.ini)
if (Test-Path ".git") {
    Get-ChildItem -Path ".git" -Filter "desktop.ini" -Recurse -Force -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
}

try {
    # 1. Branch Management
    $currentBranch = git rev-parse --abbrev-ref HEAD
    if ($currentBranch -ne $DeviceBranch) {
        Write-Host "[1/3] INITIALIZING: Branch Setup..." -ForegroundColor Gray
        Invoke-Git "git checkout -b $DeviceBranch 2>$null; git checkout $DeviceBranch" "Branch Setup"
    }

    # 2. Secure & Transmit
    Write-Host "[2/3] SECURING: Local findings & Cloud Sync..." -ForegroundColor Cyan
    git add .
    $changes = git status --porcelain
    if (![string]::IsNullOrEmpty($changes)) {
        Invoke-Git "git commit -m '[Argus-$ComputerName] Intelligence Captured'" "Local Commit"
    } else {
        Write-Host "      > No new findings detected." -ForegroundColor Gray
    }
    
    Invoke-Git "git pull $Remote $DeviceBranch --no-rebase --no-edit" "Cloud Pull"
    Invoke-Git "git push $Remote $DeviceBranch" "Cloud Push"
    Write-Host "      > Transmission complete." -ForegroundColor Green

    # 3. Integrate Team Updates
    Write-Host "[3/3] INTEGRATING: Team Updates ($MainBranch)..." -ForegroundColor Cyan
    Invoke-Git "git fetch $Remote $MainBranch --quiet" "Fetch Updates"
    
    $preMerge = git rev-parse HEAD
    Invoke-Git "git merge $Remote/$MainBranch --no-edit -X ours" "Merge Updates"
    $postMerge = git rev-parse HEAD

    if ($preMerge -ne $postMerge) {
        Write-Host "      > GLOBAL UPDATES INTEGRATED." -ForegroundColor Green
    } else {
        Write-Host "      > Workspace is unified with Main." -ForegroundColor Gray
    }

    Write-Host "`n[SUCCESS] Argus Intelligence Synchronized." -ForegroundColor Black -BackgroundColor Green

} catch {
    Write-Host "`n[TERMINATED] Please resolve the Git issue above." -ForegroundColor Red
}

Write-Host "------------------------------------------------------------" -ForegroundColor Gray
Write-Host "Press any key to close..." -ForegroundColor White
[void]$Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
