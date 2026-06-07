param (
    [string]$Remote = "origin",
    [string]$MainBranch = "main",
    [switch]$Detailed 
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
    Write-Host "     This engine acts as a secure bridge between your local "
    Write-Host "     intelligence (findings) and the global Argus repository."
    Write-Host ""
    Write-Host " [1] THE WORKFLOW SIGNALS (What happens and why?)" -ForegroundColor Yellow
    Write-Host "     - SECURE    : Captures your current work and creates a "
    Write-Host "                   local 'Save Point' (Git Commit)."
    Write-Host "     - TRANSMIT  : Encrypts/Uploads your findings to your   "
    Write-Host "                   private branch '$DeviceBranch'."
    Write-Host "     - INTEGRATE : Carefully merges global updates from the "
    Write-Host "                   '$MainBranch' branch into your workspace."
    Write-Host ""
    Write-Host " [2] COMMAND SIGNALS (Flags & Options)" -ForegroundColor Yellow
    Write-Host "     -h, --help    : Shows this comprehensive guide."
    Write-Host "     -Detailed     : PRO MODE. Shows every raw Git command "
    Write-Host "                     and its full output (Transparent Mode)."
    Write-Host "     -Remote       : Specify a custom Git remote (Def: origin)."
    Write-Host "     -MainBranch   : Target branch for updates (Def: main)."
    Write-Host ""
    Write-Host " [3] SAFETY & INTEGRITY" -ForegroundColor Yellow
    Write-Host "     - Anti-Corruption: Automatically detects and removes   "
    Write-Host "       problematic 'desktop.ini' files in the .git folder."
    Write-Host "     - Conflict Shield: Uses 'ours' strategy to ensure YOUR "
    Write-Host "       code is NEVER overwritten by global updates."
    Write-Host ""
    Write-Host " [!] USAGE EXAMPLES" -ForegroundColor Black -BackgroundColor Yellow
    Write-Host "     Standard Sync : .\Argus_Secure_Sync.ps1"
    Write-Host "     Debug Sync    : .\Argus_Secure_Sync.ps1 -Detailed"
    Write-Host "     Custom Remote : .\Argus_Secure_Sync.ps1 -Remote 'github'"
    Write-Host "------------------------------------------------------------" -ForegroundColor Gray
    Write-Host " Press any key to exit help..." -ForegroundColor White
    [void]$Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

# Help Check - Robust detection for any help signal
$HelpFlags = @('-h', '--help', 'help', '-?', '/?', '-H', '--HELP')
if ($HelpFlags -contains $Remote -or $HelpFlags -contains $MainBranch) {
    Show-Help
    exit 0
}

function Show-Header {
    Clear-Host
    Write-Host ">>> ARGUS SYNC ENGINE | $ComputerName | $DeviceBranch" -ForegroundColor Cyan
    if ($Detailed) { Write-Host "!!! DETAILED LOGGING ENABLED !!!" -ForegroundColor Magenta }
    Write-Host "------------------------------------------------------------" -ForegroundColor Gray
}

# Helper to run Git with error capturing
function Invoke-Git {
    param([string]$Command, [string]$StepName)
    if ($Detailed) {
        Invoke-Expression $Command
    } else {
        $output = Invoke-Expression "$Command 2>&1"
        if ($LASTEXITCODE -ne 0) {
            Write-Host "`n[!] ERROR IN ${StepName}:" -ForegroundColor Red
            Write-Host $output -ForegroundColor Gray
            throw "Git command failed."
        }
        return $output
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
        Write-Host "[1/3] Switching to branch: $DeviceBranch" -ForegroundColor Gray
        Invoke-Git "git checkout -b $DeviceBranch 2>$null; git checkout $DeviceBranch" "Branch Setup"
    }

    # 2. Secure & Transmit
    Write-Host "[2/3] Securing intelligence..." -ForegroundColor Cyan
    git add .
    $changes = git status --porcelain
    if (![string]::IsNullOrEmpty($changes)) {
        $count = ($changes -split "`n").Length
        Invoke-Git "git commit -m '[Argus-$ComputerName] Intelligence Captured' --quiet" "Local Commit"
        Write-Host "      > Captured $count modified files." -ForegroundColor Green
    } else {
        Write-Host "      > No new findings to secure." -ForegroundColor Gray
    }
    
    Write-Host "      > Transmitting to cloud..." -ForegroundColor Cyan
    Invoke-Git "git pull $Remote $DeviceBranch --no-rebase --no-edit --quiet" "Cloud Pull"
    Invoke-Git "git push $Remote $DeviceBranch --quiet" "Cloud Push"
    Write-Host "      > Sync with private cloud successful." -ForegroundColor Green

    # 3. Integrate Team Updates
    Write-Host "[3/3] Integrating team updates ($MainBranch)..." -ForegroundColor Cyan
    Invoke-Git "git fetch $Remote $MainBranch --quiet" "Fetch Updates"
    
    $preMerge = git rev-parse HEAD
    Invoke-Git "git merge $Remote/$MainBranch --no-edit -X ours --quiet" "Merge Updates"
    $postMerge = git rev-parse HEAD

    if ($preMerge -ne $postMerge) {
        Write-Host "      > NEW UPDATES INTEGRATED." -ForegroundColor Green
    } else {
        Write-Host "      > Workspace is already up to date." -ForegroundColor Gray
    }

    Write-Host "`n[SUCCESS] Argus Intelligence Synchronized." -ForegroundColor Black -BackgroundColor Green

} catch {
    Write-Host "`n[TERMINATED] Sync stopped due to the error above." -ForegroundColor Red
}

Write-Host "------------------------------------------------------------" -ForegroundColor Gray
Write-Host "Press any key to close..." -ForegroundColor White
[void]$Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
