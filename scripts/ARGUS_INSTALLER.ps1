#Requires -Version 5.1
<#
.SYNOPSIS
    Argus Security Framework - Self-Contained Single-File Installer.

.DESCRIPTION
    A single, self-contained PowerShell script that self-elevates up front, then
    installs, configures, and validates the entire Argus environment (Python +
    Ollama + WSL2/Kali + AI venv + Kali tools + SSH bridge + embedded health
    check) and leaves the project ready to run.

    This script embeds all external dependencies (requirements.txt,
    check_and_install.sh, argus_recon_fixed.sh) internally as here-strings.
    It has ZERO external file dependencies - copy this ONE file and run it.

    If a `Setup/` directory is present (an older checkout - a fresh clone of this
    repository no longer ships one, removed 2026-07-19), a successful first run
    archives it to `Setup_legacy/`.

.PARAMETER Offline
    Skip all network downloads (Python winget, Ollama install, ollama pull).

.PARAMETER Interactive
    Prompt for confirmation before each critical step.

.PARAMETER DryRun
    Run the logic without making any system changes (to verify paths and logic only).

.PARAMETER SkipHealthCheck
    Skip the embedded final health check.

.PARAMETER OnlyHealthCheck
    Run ONLY the embedded health check - no self-elevation, no install steps,
    no cleanup. Exits with 0 if healthy, non-zero otherwise.

.PARAMETER RetryCount
    Number of retry attempts per step (default 2).

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\ARGUS_INSTALLER.ps1
.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\ARGUS_INSTALLER.ps1 -DryRun
.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\ARGUS_INSTALLER.ps1 -Offline -Interactive
.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\ARGUS_INSTALLER.ps1 -OnlyHealthCheck
#>

[CmdletBinding()]
param(
    [switch]$Offline,
    [switch]$Interactive,
    [switch]$DryRun,
    [switch]$SkipHealthCheck,
    [switch]$OnlyHealthCheck,
    [int]$RetryCount = 2
)

# ============================================================================
# EMBEDDED DEPENDENCIES (self-contained: no external files needed)
# ============================================================================

# requirements.txt - Python package dependencies
$EMBEDDED_REQUIREMENTS = @"
langchain
langchain-ollama
langchain-classic
langchain-huggingface
langchain-community
langchain-core
langchain-text-splitters
streamlit
duckduckgo-search
faiss-cpu
sentence-transformers
pypdf
python-dotenv
paramiko
torchvision
networkx
pyvis
"@

# check_and_install.sh - Kali Linux tool installer (run inside WSL as root)
$EMBEDDED_CHECK_INSTALL_SH = @'
#!/usr/bin/env bash
set -u

echo "--------------------------------------------------------"
echo "ARGUS KALI ADVANCED ENVIRONMENT SETUP"
echo "--------------------------------------------------------"

INSTALLED_COUNT=0
ALREADY_COUNT=0
FAILED_OPTIONAL=()

retry() {
    local max_attempts="$1"
    local delay_seconds="$2"
    shift 2

    local attempt=1
    while true; do
        "$@"
        local rc=$?
        if [ "$rc" -eq 0 ]; then
            return 0
        fi
        if [ "$attempt" -ge "$max_attempts" ]; then
            return "$rc"
        fi
        echo "[WARN] Command failed with exit code $rc. Retrying in ${delay_seconds}s ($attempt/$max_attempts)..."
        sleep "$delay_seconds"
        attempt=$((attempt + 1))
    done
}

fail() {
    echo "[ERROR] $*"
    exit 1
}

warn_optional() {
    echo "[WARN] Optional install failed: $*"
    FAILED_OPTIONAL+=("$*")
}

have_cmd() {
    command -v "$1" >/dev/null 2>&1
}

apt_install_missing() {
    local packages=("$@")
    local missing=()

    for package in "${packages[@]}"; do
        if ! dpkg -s "$package" >/dev/null 2>&1; then
            missing+=("$package")
        else
            ALREADY_COUNT=$((ALREADY_COUNT + 1))
        fi
    done

    if [ "${#missing[@]}" -eq 0 ]; then
        echo "[OK] APT packages already present: ${packages[*]}"
        return 0
    fi

    echo "[INFO] Installing APT packages: ${missing[*]}"
    retry 3 10 apt-get install -y "${missing[@]}" || return 1
    INSTALLED_COUNT=$((INSTALLED_COUNT + ${#missing[@]}))
}

install_go_tool() {
    local binary="$1"
    local module="$2"

    if have_cmd "$binary"; then
        echo "[OK] $binary already installed."
        ALREADY_COUNT=$((ALREADY_COUNT + 1))
        return 0
    fi

    echo "[INFO] Installing Go tool: $binary"
    retry 3 10 go install "$module" || return 1

    local go_bin
    go_bin="$(go env GOPATH 2>/dev/null)/bin/$binary"
    if [ -x "$go_bin" ]; then
        ln -sf "$go_bin" "/usr/local/bin/$binary"
    elif [ -x "/root/go/bin/$binary" ]; then
        ln -sf "/root/go/bin/$binary" "/usr/local/bin/$binary"
    else
        return 1
    fi

    INSTALLED_COUNT=$((INSTALLED_COUNT + 1))
}

install_pipx_tool() {
    local binary="$1"
    local package="$2"

    if have_cmd "$binary"; then
        echo "[OK] $binary already installed."
        ALREADY_COUNT=$((ALREADY_COUNT + 1))
        return 0
    fi

    echo "[INFO] Installing Python tool with pipx: $package"
    retry 3 10 pipx install "$package" || return 1
    if [ -d "/root/.local/bin" ]; then
        find /root/.local/bin -maxdepth 1 -type f -executable -exec ln -sf {} /usr/local/bin/ \;
    fi
    have_cmd "$binary" || return 1
    INSTALLED_COUNT=$((INSTALLED_COUNT + 1))
}

install_git_repo() {
    local name="$1"
    local repo="$2"
    local target="$3"

    if [ -d "$target/.git" ] || [ -d "$target" ]; then
        echo "[OK] $name already present at $target."
        ALREADY_COUNT=$((ALREADY_COUNT + 1))
        return 0
    fi

    echo "[INFO] Cloning $name..."
    mkdir -p "$(dirname "$target")"
    retry 3 10 git clone --depth 1 "$repo" "$target" || return 1
    INSTALLED_COUNT=$((INSTALLED_COUNT + 1))
}

echo "[INFO] Running preflight checks..."
[ "$(id -u)" -eq 0 ] || fail "Run this script as root inside Kali/WSL."
have_cmd apt-get || fail "apt-get is not available. This installer expects Kali/Debian."

echo "[INFO] Waiting for APT/dpkg locks..."
while fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1 || fuser /var/lib/dpkg/lock >/dev/null 2>&1; do
    echo "[WARN] Another package manager is running. Waiting..."
    sleep 3
done

# Optimized: Only run apt update if it hasn't been run in the last 24 hours
UPDATE_MARKER="/var/lib/apt/periodic/update-success-stamp"
SHOULD_UPDATE=true
if [ -f "$UPDATE_MARKER" ]; then
    last_update=$(stat -c %Y "$UPDATE_MARKER")
    now=$(date +%s)
    if [ $((now - last_update)) -lt 86400 ]; then
        SHOULD_UPDATE=false
    fi
fi

if [ "$SHOULD_UPDATE" = true ]; then
    echo "[INFO] Updating APT metadata..."
    retry 3 10 apt-get update -y || fail "apt-get update failed."
else
    echo "[OK] APT metadata is fresh (skip update)."
fi

CRITICAL_APT=(
    ca-certificates curl wget git python3 python3-pip python3-venv pipx
    golang nodejs npm build-essential make libpcap-dev jq unzip openssh-server
    dnsutils nmap gobuster ffuf whois
)

OPTIONAL_APT=(
    whatweb wafw00f nikto theharvester recon-ng spiderfoot amass fierce dnsenum dnsrecon
)

apt_install_missing "${CRITICAL_APT[@]}" || fail "Failed to install critical APT dependencies."
apt_install_missing "${OPTIONAL_APT[@]}" || warn_optional "some optional APT tools"

export PIPX_HOME="${PIPX_HOME:-/opt/pipx}"
export PIPX_BIN_DIR="${PIPX_BIN_DIR:-/usr/local/bin}"
pipx ensurepath --global >/dev/null 2>&1 || true

echo "[INFO] Configuring SSH for WSL bridge..."
mkdir -p /run/sshd
ssh-keygen -A >/dev/null 2>&1 || true
if [ -f /etc/ssh/sshd_config ]; then
    sed -i 's/^#PasswordAuthentication .*/PasswordAuthentication yes/' /etc/ssh/sshd_config
    sed -i 's/^#Port .*/Port 22/' /etc/ssh/sshd_config
fi

echo "[INFO] Installing ProjectDiscovery tool manager..."
if ! have_cmd pdtm; then
    install_go_tool pdtm github.com/projectdiscovery/pdtm/cmd/pdtm@latest || warn_optional "pdtm"
fi
if have_cmd pdtm; then
    PDTM_MARKER="/root/.pdtm_last_sync"
    SHOULD_PDTM=true
    if [ -f "$PDTM_MARKER" ]; then
        last_pdtm=$(cat "$PDTM_MARKER")
        now=$(date +%s)
        if [ $((now - last_pdtm)) -lt 604800 ]; then
            SHOULD_PDTM=false
        fi
    fi

    if [ "$SHOULD_PDTM" = true ]; then
        echo "[INFO] Installing/Updating ProjectDiscovery tools via pdtm..."
        PDTM_LOG="/tmp/argus_pdtm_install.log"
        if ! retry 2 10 pdtm -ia > "$PDTM_LOG" 2>&1; then
            warn_optional "ProjectDiscovery tool bundle"
            tail -n 25 "$PDTM_LOG" 2>/dev/null || true
        else
            date +%s > "$PDTM_MARKER"
        fi
    else
        echo "[OK] ProjectDiscovery tools are recently synced (skip)."
    fi

    if [ -d "/root/.pdtm/go/bin" ]; then
        find /root/.pdtm/go/bin -maxdepth 1 -type f -executable -exec ln -sf {} /usr/local/bin/ \;
    fi
fi

echo "[INFO] Installing Go utilities..."
install_go_tool assetfinder github.com/tomnomnom/assetfinder@latest || warn_optional "assetfinder"
install_go_tool anew github.com/tomnomnom/anew@latest || warn_optional "anew"
install_go_tool puredns github.com/d3mondev/puredns/v2@latest || warn_optional "puredns"
install_go_tool goaltdns github.com/subfinder/goaltdns@latest || warn_optional "goaltdns"
install_go_tool Ph.Sh_url github.com/PhilopaterSh/Ph.Sh_url@latest || warn_optional "Ph.Sh_url"
install_go_tool alterx github.com/projectdiscovery/alterx/cmd/alterx@latest || warn_optional "alterx"

echo "[INFO] Installing Python utilities with pipx..."
install_pipx_tool dnsgen dnsgen || warn_optional "dnsgen"
install_pipx_tool altdns py-altdns || warn_optional "py-altdns"

echo "[INFO] Installing Findomain..."
if ! have_cmd findomain; then
    tmp_dir="$(mktemp -d)"
    if retry 3 10 curl -fsSL -o "$tmp_dir/findomain-linux.zip" https://github.com/Findomain/Findomain/releases/latest/download/findomain-linux.zip &&
       unzip -q "$tmp_dir/findomain-linux.zip" -d "$tmp_dir" &&
       [ -f "$tmp_dir/findomain" ]; then
        chmod +x "$tmp_dir/findomain"
        mv "$tmp_dir/findomain" /usr/local/bin/findomain
        INSTALLED_COUNT=$((INSTALLED_COUNT + 1))
    else
        warn_optional "findomain"
    fi
    rm -rf "$tmp_dir"
else
    echo "[OK] findomain already installed."
    ALREADY_COUNT=$((ALREADY_COUNT + 1))
fi

echo "[INFO] Installing MassDNS..."
if [ ! -x "/usr/local/bin/massdns" ]; then
    if install_git_repo MassDNS https://github.com/blechschmidt/massdns.git /opt/massdns &&
       make -C /opt/massdns &&
       ln -sf /opt/massdns/bin/massdns /usr/local/bin/massdns; then
        echo "[OK] massdns installed."
    else
        warn_optional "massdns"
    fi
else
    echo "[OK] massdns already installed."
    ALREADY_COUNT=$((ALREADY_COUNT + 1))
fi

echo "[INFO] Installing optional repositories..."
if [ ! -d "/opt/Ph.Sh-Subdomain" ]; then
    if install_git_repo Ph.Sh-Subdomain https://github.com/PhilopaterSh/Ph.Sh-Subdomain.git /opt/Ph.Sh-Subdomain; then
        python3 -m venv /opt/Ph.Sh-Subdomain/.venv || warn_optional "Ph.Sh-Subdomain venv"
        if [ -x /opt/Ph.Sh-Subdomain/.venv/bin/pip ] && [ -f /opt/Ph.Sh-Subdomain/requirements.txt ]; then
            /opt/Ph.Sh-Subdomain/.venv/bin/pip install -r /opt/Ph.Sh-Subdomain/requirements.txt || warn_optional "Ph.Sh-Subdomain Python requirements"
        fi
        (cd /opt/Ph.Sh-Subdomain && go build) && ln -sf /opt/Ph.Sh-Subdomain/Ph.Sh-Subdomain /usr/local/bin/Ph.Sh-Subdomain || warn_optional "Ph.Sh-Subdomain build"
    else
        warn_optional "Ph.Sh-Subdomain"
    fi
fi

if [ ! -d "/opt/finalrecon" ]; then
    if install_git_repo FinalRecon https://github.com/thewhiteh4t/FinalRecon.git /opt/finalrecon; then
        python3 -m venv /opt/finalrecon/.venv || warn_optional "FinalRecon venv"
        if [ -x /opt/finalrecon/.venv/bin/pip ] && [ -f /opt/finalrecon/requirements.txt ]; then
            /opt/finalrecon/.venv/bin/pip install -r /opt/finalrecon/requirements.txt || warn_optional "FinalRecon Python requirements"
        fi
        cat > /usr/local/bin/finalrecon <<'WRAPPER'
#!/usr/bin/env bash
exec /opt/finalrecon/.venv/bin/python /opt/finalrecon/finalrecon.py "$@"
WRAPPER
        chmod +x /usr/local/bin/finalrecon
    else
        warn_optional "FinalRecon"
    fi
fi

install_git_repo PayloadsAllTheThings https://github.com/swisskyrepo/PayloadsAllTheThings.git /opt/payloads/PayloadsAllTheThings || warn_optional "PayloadsAllTheThings"
install_git_repo SecLists https://github.com/danielmiessler/SecLists.git /usr/share/seclists || warn_optional "SecLists"
[ -d /usr/share/seclists ] && ln -sf /usr/share/seclists "$HOME/seclists"

echo "[INFO] Creating Argus native recon command..."
cat > /usr/local/bin/argus_recon <<'ARGUSRECON'
#!/usr/bin/env bash
set -u

DOMAIN="${1:-}"
if [ -z "$DOMAIN" ]; then
    echo "Usage: argus_recon <domain>"
    exit 1
fi

RAW_FILE="/tmp/argus_raw_${DOMAIN}.txt"
ALIVE_FILE="/tmp/argus_alive_${DOMAIN}.txt"
UNIQUE_FILE="/tmp/argus_unique_${DOMAIN}.txt"
WORDLIST="/usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt"
if [ ! -f "$WORDLIST" ]; then
    WORDLIST="/tmp/argus_mini_wordlist.txt"
    echo "www" > "$WORDLIST"
fi

: > "$RAW_FILE"

echo "[INFO] Phase 1: Passive OSINT..."
command -v subfinder >/dev/null 2>&1 && subfinder -d "$DOMAIN" -silent >> "$RAW_FILE" || true
command -v assetfinder >/dev/null 2>&1 && assetfinder --subs-only "$DOMAIN" >> "$RAW_FILE" || true
command -v findomain >/dev/null 2>&1 && findomain -t "$DOMAIN" -q >> "$RAW_FILE" || true
command -v amass >/dev/null 2>&1 && amass enum -passive -d "$DOMAIN" >> "$RAW_FILE" || true

echo "[INFO] Phase 2: Active brute force..."
command -v gobuster >/dev/null 2>&1 && gobuster dns -d "$DOMAIN" -w "$WORDLIST" -z --quiet | awk '/Found:/ {print $2}' >> "$RAW_FILE" || true

sort -u "$RAW_FILE" -o "$RAW_FILE"

echo "[INFO] Phase 3: Permutations..."
if command -v dnsgen >/dev/null 2>&1; then
    dnsgen "$RAW_FILE" >> "$RAW_FILE" || true
    sort -u "$RAW_FILE" -o "$RAW_FILE"
fi

echo "[INFO] Phase 4: Resolution and validation..."
if command -v anew >/dev/null 2>&1; then
    anew "$UNIQUE_FILE" < "$RAW_FILE" >/dev/null
else
    cp "$RAW_FILE" "$UNIQUE_FILE"
fi

if command -v httpx >/dev/null 2>&1; then
    httpx -silent -fc 404,500,502 -threads 50 < "$UNIQUE_FILE" > "$ALIVE_FILE"
elif command -v puredns >/dev/null 2>&1; then
    puredns resolve "$UNIQUE_FILE" --quiet > "$ALIVE_FILE"
else
    xargs -r -I{} host -W 2 {} < "$UNIQUE_FILE" | awk '/has address/ {print $1}' > "$ALIVE_FILE"
fi

ALIVE_COUNT="$(wc -l < "$ALIVE_FILE" 2>/dev/null || echo 0)"
echo "--- ARGUS SUBDOMAIN DISCOVERY: $DOMAIN ---"
echo "[INFO] Total potential: $(wc -l < "$RAW_FILE" 2>/dev/null || echo 0)"
echo "[INFO] Total verified alive: $ALIVE_COUNT"
echo ""
echo "[INFO] Top verified subdomains:"
head -n 50 "$ALIVE_FILE" 2>/dev/null || true
echo ""
echo "[INFO] Infrastructure pointers:"
head -n 10 "$ALIVE_FILE" 2>/dev/null | while read -r sub; do
    clean_sub="$(echo "$sub" | sed -E 's|https?://||; s|/.*$||')"
    cname="$(dig CNAME +short +time=3 +tries=2 "$clean_sub")"
    [ -n "$cname" ] && echo "[CNAME] $sub -> $cname"
    mx="$(dig MX +short +time=3 +tries=2 "$clean_sub")"
    [ -n "$mx" ] && echo "[MX] $sub -> $mx"
done

rm -f "$RAW_FILE" "$ALIVE_FILE" "$UNIQUE_FILE"
ARGUSRECON
chmod +x /usr/local/bin/argus_recon

echo ""
echo "========================================================"
echo "INSTALLATION SUMMARY (KALI TOOLS)"
echo "========================================================"
echo "[OK] Tools already present: $ALREADY_COUNT"
echo "[OK] New tools installed:   $INSTALLED_COUNT"
if [ "${#FAILED_OPTIONAL[@]}" -gt 0 ]; then
    echo "[WARN] Optional failures:"
    printf ' - %s\n' "${FAILED_OPTIONAL[@]}"
else
    echo "[OK] Optional tools completed without recorded failures."
fi
echo "[OK] Argus environment is synchronized."
echo "========================================================"
'@

# argus_recon_fixed.sh - standalone recon script (legacy, embedded for reference)
$EMBEDDED_ARGUS_RECON_SH = @'
#!/bin/bash
# Argus Recon Engine - Robust Version
DOMAIN=$1
[ -z "$DOMAIN" ] && echo "Usage: argus_recon <domain>" && exit 1

# Setup Paths
export PATH=$PATH:/home/kali/go/bin:/home/kali/.pdtm/go/bin
RAW_FILE="/tmp/argus_raw_$DOMAIN.txt"
ALIVE_FILE="/tmp/argus_alive_$DOMAIN.txt"

rm -f $RAW_FILE $ALIVE_FILE

echo "[INFO] Phase 1: OSINT Discovery..."
subfinder -d $DOMAIN -silent >> $RAW_FILE
assetfinder --subs-only $DOMAIN >> $RAW_FILE
findomain -t $DOMAIN -q >> $RAW_FILE

echo "[INFO] Phase 2: Brute-Force..."
WORDLIST="/usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt"
[ ! -f "$WORDLIST" ] && echo "www" > /tmp/mini.txt && WORDLIST="/tmp/mini.txt"
gobuster dns --domain $DOMAIN -w $WORDLIST --quiet | grep "Found:" | awk '{print $2}' >> $RAW_FILE

echo "[INFO] Phase 3: Validation..."
sort -u $RAW_FILE -o $RAW_FILE

# Use ProjectDiscovery httpx if possible
HTTPX="/home/kali/.pdtm/go/bin/httpx"
[ ! -x "$HTTPX" ] && HTTPX=$(which httpx)

if [ -f "$RAW_FILE" ] && [ -s "$RAW_FILE" ]; then
    cat $RAW_FILE | $HTTPX -silent -threads 50 > $ALIVE_FILE
fi

echo "--- ARGUS SUBDOMAIN DISCOVERY: $DOMAIN ---"
echo "[INFO] Total potential: $(wc -l < $RAW_FILE 2>/dev/null || echo "0")"
echo "[INFO] Total verified alive: $(wc -l < $ALIVE_FILE 2>/dev/null || echo "0")"
echo ""
echo "[INFO] TOP VERIFIED SUBDOMAINS:"
cat $ALIVE_FILE | head -n 50
echo ""
echo "[INFO] INFRASTRUCTURE POINTERS:"
cat $ALIVE_FILE | head -n 10 | while read sub; do
    clean_sub=$(echo "$sub" | sed -E 's|https?://||; s|/.*$||')
    cname=$(dig CNAME +short "$clean_sub" | head -n 1)
    [ -n "$cname" ] && echo "[CNAME] $sub -> $cname"
done

# DO NOT delete ALIVE_FILE so Argus can read it
rm -f $RAW_FILE 2>/dev/null
'@

# ============================================================================
# CONFIG BLOCK (single source of truth for all tunables)
# ============================================================================
$MIN_RAM_GB            = 8
$MIN_DISK_GB           = 20
$PYTHON_REQUIRED       = "3.12"
$KALI_DISTRO           = "kali-linux"
$OLLAMA_MODEL          = if ($env:ARGUS_MODEL) { $env:ARGUS_MODEL } else { "hf.co/bartowski/WhiteRabbitNeo_WhiteRabbitNeo-V3-7B-GGUF:Q5_K_M" }  # default AI model (Q5_K_M quantized, ~5.4GB vs ~15GB F16 - specs/018); overridden by config.yaml at runtime if present
$OLLAMA_MODEL_MIN_GB   = if ($env:ARGUS_MODEL_MIN_GB) { [int]$env:ARGUS_MODEL_MIN_GB } else { 6 }
$OLLAMA_EMBED_MODEL    = if ($env:ARGUS_EMBED_MODEL) { $env:ARGUS_EMBED_MODEL } else { "nomic-embed-text" }  # RAG embedding model; overridden by config.yaml's rag.embedding_model if present
$OLLAMA_EMBED_MODEL_MIN_GB = 1
$MODEL_PULL_RETRIES    = if ($env:ARGUS_MODEL_PULL_RETRIES) { [int]$env:ARGUS_MODEL_PULL_RETRIES } else { 3 }
$VENV_NAME             = "Argus_venv"

# ============================================================================
# ENVIRONMENT / PATHS
# ============================================================================
$ErrorActionPreference = "Stop"
$ScriptDir   = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ProjectRoot = Split-Path -Parent $ScriptDir
$LogsDir     = Join-Path $ProjectRoot "logs"
$null = New-Item -ItemType Directory -Force -Path $LogsDir -ErrorAction SilentlyContinue
$LogFile     = Join-Path $LogsDir ("argus_install_{0}.log" -f (Get-Date -Format "yyyyMMdd_HHmmss"))

$env:ARGUS_AUTO_INSTALL = if ($Interactive) { "" } else { "1" }
if ($Offline) { $env:ARGUS_OFFLINE = "1" }
if ($DryRun)  { $env:ARGUS_DRY_RUN = "1" }

Set-Location -LiteralPath $ProjectRoot

# Track per-step results for the final report
$script:StepResults = New-Object System.Collections.Generic.List[object]

# ============================================================================
# LOGGING HELPERS
# ============================================================================
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

# ============================================================================
# MODEL NAME RESOLUTION (config.yaml is the single source of truth when present)
# ============================================================================
function Resolve-OllamaModelNames {
    # Explicit $script: scope so this actually persists back to the caller -
    # the previous version of this logic lived inline inside the AI Environment
    # step and did a bare `$OLLAMA_MODEL = ...` assignment, which in PowerShell
    # only ever updates a function-local shadow, never the script-scope
    # variable. That meant anything reading $OLLAMA_MODEL/$OLLAMA_EMBED_MODEL
    # from a different function (like the health check, which can run standalone
    # via -OnlyHealthCheck before this step ever executes) would silently see
    # the env-var/hardcoded default instead of the config.yaml value.
    $resolvedModel = $script:OLLAMA_MODEL
    $resolvedEmbedModel = $script:OLLAMA_EMBED_MODEL
    $cfgPath = Join-Path $ProjectRoot "config\config.yaml"
    if (Test-Path -LiteralPath $cfgPath) {
        try {
            $yaml = Get-Content -LiteralPath $cfgPath -Raw
            if (-not $env:ARGUS_MODEL -and $yaml -match 'model_name:\s*"(.+)"') { $resolvedModel = $Matches[1] }
            if (-not $env:ARGUS_EMBED_MODEL -and $yaml -match 'embedding_model:\s*"(.+)"') { $resolvedEmbedModel = $Matches[1] }
        } catch { }
    }
    $script:OLLAMA_MODEL = $resolvedModel
    $script:OLLAMA_EMBED_MODEL = $resolvedEmbedModel
}

# ============================================================================
# SELF-ELEVATION (Admin-first principle - happens once at the very start)
# ============================================================================
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
    if ($OnlyHealthCheck) { $argList += "-OnlyHealthCheck" }
    $argList += "-RetryCount $RetryCount"

    try {
        Start-Process -FilePath "powershell.exe" -Verb RunAs -ArgumentList $argList -ErrorAction Stop
    } catch {
        Write-Err "Elevation was declined or failed: $($_.Exception.Message)"
        Write-Err "Please right-click PowerShell -> 'Run as administrator' and rerun."
    }
    exit 0
}

# ============================================================================
# GENERIC UTILITIES
# ============================================================================
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

# ============================================================================
# STEP 0 - SYSTEM READINESS
# ============================================================================
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

# ============================================================================
# STEP 1 - PYTHON 3.12 (bootstrap once, used by all later steps)
# ============================================================================
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

# ============================================================================
# STEP 2 - HOST FOUNDATION (WSL2 + Kali distro + Ollama)
# ============================================================================
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

function Test-KaliDistroRunning {
    # Distro can be installed but Stopped (a normal idle state, not an error) - the
    # installer previously never checked this distinction at all, so a genuinely
    # working install could be misreported as broken simply because the VM hadn't
    # been booted yet this session.
    if (-not (Test-KaliDistro)) { return $false }
    try {
        $verbose = (wsl -l -v 2>$null) -replace "`0", ""
        $line = $verbose | Where-Object { $_ -match [regex]::Escape($KALI_DISTRO) }
        return ($null -ne $line -and ($line -join " ") -match "Running")
    } catch { return $false }
}

function Start-KaliDistroIfNeeded {
    if (Test-KaliDistroRunning) {
        Write-OK "Kali distro '$KALI_DISTRO' is already running."
        return $true
    }
    if (-not (Test-KaliDistro)) { return $false }
    if ($DryRun) {
        Write-Info "[DryRun] Would boot Kali distro '$KALI_DISTRO' (wsl -d $KALI_DISTRO -- true)."
        return $true
    }
    Write-Info "Kali distro '$KALI_DISTRO' is installed but not running. Booting it..."
    try {
        wsl -d $KALI_DISTRO -- true 2>&1 | ForEach-Object { Write-Info $_ }
        if (Test-KaliDistroRunning) {
            Write-OK "Kali distro '$KALI_DISTRO' booted successfully."
            return $true
        }
        Write-Warn "Kali distro did not report Running state after boot attempt."
        return $false
    } catch {
        Write-Warn "Failed to boot Kali distro: $($_.Exception.Message)"
        return $false
    }
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

function Test-OllamaApiResponding {
    # A running *process* is not the same guarantee as a responding *API* - the
    # engine could be starting up, crashed after launch, or bound to a different
    # port. Check the actual port, matching what app/core/llm_factory.py talks to.
    try {
        $res = Test-NetConnection -ComputerName "127.0.0.1" -Port 11434 -WarningAction SilentlyContinue
        return [bool]$res.TcpTestSucceeded
    } catch { return $false }
}

function Wait-ForOllamaApi {
    param([int]$MaxAttempts = 10, [int]$DelaySeconds = 2)
    for ($i = 1; $i -le $MaxAttempts; $i++) {
        if (Test-OllamaApiResponding) { return $true }
        Start-Sleep -Seconds $DelaySeconds
    }
    return $false
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
    # Detect -> fix -> RE-VERIFY: a process existing is not proof the API is live,
    # so every path below ends by actually polling the port rather than assuming
    # success after a fixed sleep.
    if (Test-OllamaApiResponding) {
        Write-OK "Ollama engine is already running and the API is responding."
        return $true
    }

    $procs = Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -like "*ollama*" }
    if ($procs) {
        Write-Warn "Ollama process is running but the API (port 11434) is not responding yet. Waiting..."
        if (Wait-ForOllamaApi -MaxAttempts 10 -DelaySeconds 2) {
            Write-OK "Ollama API is now responding."
            return $true
        }
        Write-Warn "Ollama process is running but the API never came up. It may need a manual restart."
        return $false
    }

    if ($DryRun) {
        Write-Info "[DryRun] Would start the Ollama engine and wait for the API to respond."
        return $true
    }
    try {
        Start-Process -FilePath "ollama" -ArgumentList "serve" -ErrorAction SilentlyContinue
        if (Wait-ForOllamaApi -MaxAttempts 15 -DelaySeconds 2) {
            Write-OK "Ollama engine started and API is responding."
            return $true
        }
        Write-Warn "Ollama process started but the API did not respond within the wait window."
        return $false
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

    # Update WSL kernel to avoid common Kali boot errors on fresh systems
    if (-not $DryRun) {
        try {
            Write-Info "Updating WSL kernel (best-effort, non-fatal)..."
            & wsl --update 2>&1 | ForEach-Object { Write-Info $_ }
            Write-OK "WSL kernel update completed (or already current)."
        } catch {
            Write-Warn "WSL kernel update failed (non-fatal): $($_.Exception.Message)"
        }
    } else {
        Write-Info "[DryRun] Would run 'wsl --update'."
    }

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

    # Detect -> fix -> re-verify: a distro can be installed but Stopped (a normal
    # idle state after a reboot or `wsl --shutdown`) - this was never checked
    # before, so a working install could be reported as broken simply because
    # the VM hadn't booted yet this session.
    $kaliRunningOk = Start-KaliDistroIfNeeded
    if (-not $kaliRunningOk) {
        Write-Warn "Kali distro is installed but could not be confirmed running. Later steps that need it may fail."
    }

    $ollamaOk = Install-Ollama
    if ($ollamaOk) { $ollamaOk = Start-OllamaIfNeeded }

    Record-Step 2 "Host Foundation" $(if ($kaliOk -and $kaliRunningOk -and $ollamaOk) { "OK" } else { "WARN" }) "Kali=$kaliOk Running=$kaliRunningOk Ollama=$ollamaOk Features=$featuresOk"
    return $true
}

# ============================================================================
# STEP 3 - AI ENVIRONMENT (Argus_venv + pip + model pull)
# ============================================================================
function Test-OllamaModelResponds {
    param([Parameter(Mandatory)][string]$ModelName)
    try {
        $modelResponse = & ollama run $ModelName "Say OK" 2>&1
        return ($LASTEXITCODE -eq 0 -and $null -ne $modelResponse -and "$modelResponse".Trim().Length -gt 0)
    } catch { return $false }
}

function Ensure-OllamaModel {
    # Shared detect -> install -> verify -> (fix by pulling) -> re-verify flow for
    # any Ollama model. Used for both the reasoning model and the RAG embedding
    # model, which previously had no check/pull logic at all (a confirmed real
    # gap: RAG silently disables itself when its embedding model is missing).
    param(
        [Parameter(Mandatory)][string]$ModelName,
        [int]$MinFreeGB = 1
    )

    if ($DryRun) {
        Write-Info "[DryRun] Would verify/pull model '$ModelName'"
        return $true
    }

    try {
        $driveName = ([System.IO.Path]::GetPathRoot($ProjectRoot)).TrimEnd("\").TrimEnd(":")
        $free = [Math]::Round((Get-PSDrive -Name $driveName).Free / 1GB, 1)
        if ($free -lt $MinFreeGB) {
            Write-Warn "Less than ${MinFreeGB}GB free ($free GB). Skipping pull of '$ModelName'."
            return $false
        }
    } catch { }

    $already = $false
    try {
        $listOut = (ollama list 2>$null) -join "`n"
        if ($listOut -match [regex]::Escape($ModelName.Split(':')[0])) { $already = $true }
    } catch { }

    if (-not $already) {
        Write-Info "Pulling model '$ModelName' (depends on internet speed)..."
        $pulled = $false
        for ($a = 1; $a -le $MODEL_PULL_RETRIES; $a++) {
            Write-Info "Pull attempt $a/$MODEL_PULL_RETRIES..."
            & ollama pull $ModelName
            if ($LASTEXITCODE -eq 0) { $pulled = $true; break }
            Write-Warn "Pull failed (attempt $a). Retrying in 10s..."
            Start-Sleep -Seconds 10
        }
        if (-not $pulled) {
            Write-Warn "Model '$ModelName' pull failed after $MODEL_PULL_RETRIES attempts."
            return $false
        }
        Write-OK "Model '$ModelName' pulled successfully."
    } else {
        Write-OK "Model '$ModelName' already present."
    }

    # Re-verify regardless of which branch got us here: listed (or freshly
    # pulled) is not proof it actually loads and responds.
    Write-Info "Verifying '$ModelName' responds..."
    if (Test-OllamaModelResponds -ModelName $ModelName) {
        Write-OK "Model '$ModelName' responds correctly."
        return $true
    }
    Write-Warn "Model '$ModelName' is present but did not respond to a test prompt."
    return $false
}

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

    # --- pip install (using embedded requirements) ---
    # Always (re)write the embedded requirements file, then decide whether to
    # rerun pip based on a CONTENT hash, not file existence/timestamps. The old
    # logic only ever wrote requirements_embedded.txt once (gated on
    # -not Test-Path): if a later version of this installer changed
    # $EMBEDDED_REQUIREMENTS, an existing venv would silently never pick up the
    # change on rerun. Idempotent either way: identical content -> identical
    # hash -> pip is skipped, exactly as before.
    $reqPath = Join-Path $venvPath "requirements_embedded.txt"
    $sha256 = [System.Security.Cryptography.SHA256]::Create()
    $reqHash = [System.BitConverter]::ToString($sha256.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($EMBEDDED_REQUIREMENTS))) -replace '-', ''

    if ($DryRun) {
        Write-Info "[DryRun] Would write embedded requirements.txt to $reqPath"
    } else {
        Set-Content -LiteralPath $reqPath -Value $EMBEDDED_REQUIREMENTS -ErrorAction Stop
    }

    $marker = Join-Path $venvPath ".requirements_installed"
    $runPip = $true
    if (Test-Path -LiteralPath $marker) {
        try {
            $markedHash = (Get-Content -LiteralPath $marker -Raw -ErrorAction Stop).Trim()
            if ($markedHash -eq $reqHash) { $runPip = $false }
        } catch { $runPip = $true }
    }

    $venvPython = Join-Path $venvPath "Scripts\python.exe"
    if ($runPip) {
        if ($DryRun) {
            Write-Info "[DryRun] Would run pip install -r $reqPath"
        } else {
            Write-Info "Synchronizing Python libraries (this may take a moment)..."
            $action = {
                & $venvPython -m pip install --upgrade pip --quiet
                & $venvPython -m pip install -r $reqPath --quiet
                if ($LASTEXITCODE -ne 0) { throw "pip install failed (exit $LASTEXITCODE)" }
            }
            if (Invoke-WithRetry -Action $action -Label "pip install requirements") {
                Set-Content -LiteralPath $marker -Value $reqHash -ErrorAction SilentlyContinue
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

    # --- model pull ---
    # Override model names from config.yaml if available (keeps installer in
    # sync with Python config). Shared with the health check so both agree.
    Resolve-OllamaModelNames

    $modelOk = $false
    $embedModelOk = $false
    if (-not (Test-Ollama)) {
        Write-Warn "Ollama is not installed; cannot verify/pull models."
    } elseif (-not (Wait-ForOllamaApi -MaxAttempts 5 -DelaySeconds 2)) {
        Write-Warn "Ollama API is not responding; cannot verify/pull models. Check Step 2 (Host Foundation)."
    } else {
        # Reasoning model (critical - the agent cannot run at all without it).
        $modelOk = Ensure-OllamaModel -ModelName $OLLAMA_MODEL -MinFreeGB $OLLAMA_MODEL_MIN_GB
        if (-not $modelOk) {
            Write-Warn "Reasoning model '$OLLAMA_MODEL' is not ready. Set a different model via ARGUS_MODEL if needed."
        }

        # Embedding model (optional - RAG degrades gracefully without it per
        # app/core/rag/vector_store.py's manifest guard, so a failure here is a
        # warning, not a step failure).
        $embedModelOk = Ensure-OllamaModel -ModelName $OLLAMA_EMBED_MODEL -MinFreeGB $OLLAMA_EMBED_MODEL_MIN_GB
        if (-not $embedModelOk) {
            Write-Warn "Embedding model '$OLLAMA_EMBED_MODEL' is not ready. RAG will run in degraded (Blackboard-only) mode until it is pulled."
        }
    }

    $status = if ($modelOk -and $embedModelOk) { "OK" } else { "WARN" }
    Record-Step 3 "AI Environment" $status "venv + pip + model=$modelOk + embed_model=$embedModelOk"
    return $true
}

# ============================================================================
# STEP 4 - KALI TOOLS (run embedded check_and_install.sh inside WSL)
# ============================================================================
function Invoke-StepKaliTools {
    Write-Step 4 "Kali Security Tools (inside WSL)"
    if (-not (Confirm-Step 4 "Kali Tools")) { Record-Step 4 "Kali Tools" "SKIPPED" ""; return $true }

    if (-not (Test-KaliDistro)) {
        Write-Err "WSL distro '$KALI_DISTRO' not installed/functional. Run host foundation first."
        Record-Step 4 "Kali Tools" "FAILED" "Kali distro missing"
        return $false
    }

    if ($DryRun) {
        Write-Info "[DryRun] Would write embedded check_and_install.sh to /tmp/ inside WSL and execute."
        Record-Step 4 "Kali Tools" "DRYRUN" "embedded script (simulated)"
        return $true
    }

    try {
        # Step A: Write embedded script to a Windows temp file (avoids complex quoting in WSL heredoc)
        $tempSh = Join-Path $env:TEMP "argus_check_and_install.sh"
        Set-Content -LiteralPath $tempSh -Value $EMBEDDED_CHECK_INSTALL_SH -Force -Encoding ASCII -ErrorAction Stop
        Write-Info "Embedded script written to Windows temp: $tempSh"

        # Step B: Convert Windows path to WSL /mnt/... path
        $drive = $tempSh.Substring(0, 1).ToLowerInvariant()
        $rest  = $tempSh.Substring(2).Replace('\', '/')
        $wslSrcPath = "/mnt/$drive$rest"
        $wslDstPath = "/tmp/argus_check_and_install.sh"

        Write-Info "Copying script from $wslSrcPath to $wslDstPath inside WSL..."
        wsl -u root bash -lc "cp '$wslSrcPath' '$wslDstPath'" 2>&1 | ForEach-Object { Write-Info $_ }

        Write-Info "Normalizing line endings and making executable..."
        wsl -u root bash -lc "sed -i 's/\r$//' '$wslDstPath' && chmod +x '$wslDstPath'" 2>&1 | ForEach-Object { Write-Info $_ }

        Write-Info "Running Kali tool installer..."
        $wslOutput = wsl -u root bash -lc "bash '$wslDstPath'" 2>&1
        $wslExit = $LASTEXITCODE
        $wslOutput | ForEach-Object { Write-Info $_ }
        if ($wslExit -ne 0) {
            Write-Warn "Kali tool setup exited with code $wslExit (some optional tools may have failed)."
            Record-Step 4 "Kali Tools" "WARN" "exit $wslExit (optional tools may be partial)"
            return $true
        }
        Write-OK "Kali tool setup completed."
        Record-Step 4 "Kali Tools" "OK" "embedded check_and_install.sh ran"
        return $true
    } catch {
        Write-Err "Kali tool setup failed: $($_.Exception.Message)"
        Record-Step 4 "Kali Tools" "FAILED" $_.Exception.Message
        return $false
    }
}

# ============================================================================
# STEP 5 - SSH BRIDGE
# ============================================================================
function Test-Port22Reachable {
    try {
        $res = Test-NetConnection -ComputerName "127.0.0.1" -Port 22 -WarningAction SilentlyContinue
        return [bool]$res.TcpTestSucceeded
    } catch { return $false }
}

function Invoke-StepSshBridge {
    Write-Step 5 "SSH Bridge to WSL (Kali)"
    if (-not (Confirm-Step 5 "SSH Bridge")) { Record-Step 5 "SSH Bridge" "SKIPPED" ""; return $true }
    if (-not (Test-KaliDistro)) {
        Write-Warn "Kali distro missing; skipping SSH bridge setup."
        Record-Step 5 "SSH Bridge" "WARN" "Kali missing"
        return $true
    }

    if ($DryRun) {
        Write-Info "[DryRun] Would ensure the distro is running, enable+start sshd, and test port 22."
        Record-Step 5 "SSH Bridge" "DRYRUN" "sshd + port 22 test (simulated)"
        return $true
    }

    try {
        # SSH needs a running VM underneath it - ensure that first rather than
        # assuming Step 2 already covered it (this step can run standalone via
        # -OnlyHealthCheck-adjacent flows or after a reboot).
        if (-not (Start-KaliDistroIfNeeded)) {
            Write-Warn "Could not confirm Kali is running; SSH bridge setup skipped."
            Record-Step 5 "SSH Bridge" "WARN" "Kali not running"
            return $true
        }

        # Persist across WSL restarts, not just this session: if systemd is
        # active inside the distro (`systemctl enable` succeeds), the SSH
        # daemon survives `wsl --shutdown`/reboot instead of going dormant
        # again - which is exactly the state a prior real-environment check
        # found (installed, but "inactive (dead)" and disabled at boot).
        # Falls back to the direct sshd invocation on images without systemd.
        $initSystem = (wsl -d $KALI_DISTRO -u root -- bash -c "cat /proc/1/comm 2>/dev/null" 2>&1 | Out-String).Trim()
        if ($initSystem -eq "systemd") {
            Write-Info "systemd detected inside Kali - enabling ssh to persist across restarts..."
            wsl -d $KALI_DISTRO -u root -- bash -c "systemctl enable ssh && systemctl start ssh" 2>&1 | ForEach-Object { Write-Info $_ }
        } else {
            Write-Info "No systemd inside Kali (init: '$initSystem') - starting sshd directly for this session only."
            wsl -d $KALI_DISTRO -u root -- bash -c "mkdir -p /run/sshd && /usr/sbin/sshd" 2>&1 | ForEach-Object { Write-Info $_ }
        }

        # Re-verify with an actual retry loop instead of one fixed sleep + check.
        $reachable = $false
        for ($a = 1; $a -le 5; $a++) {
            if (Test-Port22Reachable) { $reachable = $true; break }
            Start-Sleep -Seconds 2
        }

        if ($reachable) {
            Write-OK "SSH bridge (port 22) is active."
            Record-Step 5 "SSH Bridge" "OK" "port 22 reachable"
            return $true
        }

        # Diagnose why, rather than just reporting failure.
        Write-Warn "SSH bridge (port 22) is not reachable after 5 attempts. Diagnosing..."
        $sshdConfigCheck = (wsl -d $KALI_DISTRO -u root -- bash -c "sshd -t 2>&1; echo EXIT:\$?" 2>&1 | Out-String).Trim()
        Write-Info "sshd config test: $sshdConfigCheck"
        Record-Step 5 "SSH Bridge" "WARN" "port 22 not reachable; sshd -t: $sshdConfigCheck"
        return $true
    } catch {
        Write-Warn "SSH bridge setup issue: $($_.Exception.Message)"
        Record-Step 5 "SSH Bridge" "WARN" $_.Exception.Message
        return $true
    }
}

# ============================================================================
# STEP 6 - INLINE HEALTH CHECK (no external file)
# ============================================================================
function Invoke-HealthCheck {
    # This is the single source of truth for "is the system actually ready" -
    # every check here probes real, observable state (a port responding, a
    # distro's reported run state, a model actually listed) rather than a
    # proxy for it (a process existing, a distro merely being installed).
    # Resolve model names independently so -OnlyHealthCheck (which never runs
    # Step 3) still checks against the config.yaml-driven names, not stale
    # defaults.
    Resolve-OllamaModelNames

    Write-Header "SYSTEM HEALTH CHECK (Embedded)"
    $healthy = $true
    $checks = @()

    # venv - existence, then an actual import to catch a partially-installed
    # environment (venv exists but a pip install was interrupted mid-way).
    $venvPy = Join-Path $ProjectRoot "$VENV_NAME\Scripts\python.exe"
    $venvOk = Test-Path -LiteralPath $venvPy
    if ($venvOk) {
        try {
            & $venvPy -c "import streamlit, langchain, langgraph" 2>&1 | Out-Null
            $venvOk = ($LASTEXITCODE -eq 0)
        } catch { $venvOk = $false }
    }
    $checks += [pscustomobject]@{ Component = "Argus_venv (+imports)"; Status = $(if ($venvOk) { "OK" } else { "MISSING/BROKEN" }) }
    if (-not $venvOk) { $healthy = $false }

    # Kali distro: installed vs actually running are different failure modes.
    $kaliInstalled = Test-KaliDistro
    $kaliRunning = if ($kaliInstalled) { Test-KaliDistroRunning } else { $false }
    $kaliStatus = if (-not $kaliInstalled) { "NOT INSTALLED" } elseif ($kaliRunning) { "RUNNING" } else { "STOPPED" }
    $checks += [pscustomobject]@{ Component = "Kali (WSL)"; Status = $kaliStatus }
    if (-not $kaliInstalled) { $healthy = $false }
    # Stopped-but-installed is not fatal on its own - `wsl -d ... -- true` boots
    # it on demand (see Start-KaliDistroIfNeeded) - so it doesn't flip $healthy.

    # Ollama: process existing is not proof the API is live.
    $ollamaOk = Test-OllamaApiResponding
    $checks += [pscustomobject]@{ Component = "Ollama API (11434)"; Status = $(if ($ollamaOk) { "ONLINE" } else { "OFFLINE" }) }
    if (-not $ollamaOk) { $healthy = $false }

    # Reasoning model: must actually be listed, not just "Ollama is up".
    $modelOk = $false
    if ($ollamaOk) {
        try {
            $listOut = (ollama list 2>$null) -join "`n"
            $modelOk = ($listOut -match [regex]::Escape($OLLAMA_MODEL.Split(':')[0]))
        } catch { }
    }
    $checks += [pscustomobject]@{ Component = "Model: $OLLAMA_MODEL"; Status = $(if ($modelOk) { "PRESENT" } else { "MISSING" }) }
    if (-not $modelOk) { $healthy = $false }

    # Embedding model: reported, but non-fatal to overall health - RAG
    # degrades to Blackboard-only without it (app/core/rag/vector_store.py's
    # manifest guard), it does not break the agent.
    $embedModelOk = $false
    if ($ollamaOk) {
        try {
            $listOut = (ollama list 2>$null) -join "`n"
            $embedModelOk = ($listOut -match [regex]::Escape($OLLAMA_EMBED_MODEL.Split(':')[0]))
        } catch { }
    }
    $checks += [pscustomobject]@{ Component = "Embed model: $OLLAMA_EMBED_MODEL"; Status = $(if ($embedModelOk) { "PRESENT" } else { "MISSING (RAG degraded)" }) }

    # SSH bridge.
    $sshOk = Test-Port22Reachable
    $checks += [pscustomobject]@{ Component = "SSH bridge (22)"; Status = $(if ($sshOk) { "ACTIVE" } else { "DOWN" }) }
    if (-not $sshOk) { $healthy = $false }

    $checks | Format-Table -AutoSize | Out-String | Write-Host
    $checks | ForEach-Object { Add-Content -LiteralPath $LogFile -Value ("{0,-30} {1}" -f $_.Component, $_.Status) -ErrorAction SilentlyContinue }

    if ($healthy) { Write-OK "SYSTEM IS HEALTHY AND READY!" }
    else { Write-Warn "SYSTEM HAS ISSUES - see the table above." }
    return $healthy
}

# ============================================================================
# STEP 7 - CLEANUP (archive Setup/ to Setup_legacy/ after first success)
# ============================================================================
function Invoke-StepCleanup {
    Write-Step 7 "Archiving legacy Setup/ directory"
    if ($DryRun) {
        $setupPath = Join-Path $ProjectRoot "Setup"
        $legacyPath = Join-Path $ProjectRoot "Setup_legacy"
        if (Test-Path -LiteralPath $setupPath) {
            Write-Info "[DryRun] Would rename '$setupPath' -> '$legacyPath'"
        } else {
            Write-Info "[DryRun] Setup/ directory not found; nothing to archive."
        }
        Record-Step 7 "Archive Setup/" "DRYRUN" ""
        return $true
    }

    $setupPath  = Join-Path $ProjectRoot "Setup"
    $legacyPath = Join-Path $ProjectRoot "Setup_legacy"

    if (-not (Test-Path -LiteralPath $setupPath)) {
        Write-OK "Setup/ directory not found; nothing to archive."
        Record-Step 7 "Archive Setup/" "OK" "not needed"
        return $true
    }

    if (Test-Path -LiteralPath $legacyPath) {
        Write-Warn "Setup_legacy/ already exists. Skipping archive to avoid overwrite."
        Record-Step 7 "Archive Setup/" "WARN" "Setup_legacy already exists"
        return $true
    }

    try {
        Rename-Item -LiteralPath $setupPath -NewName "Setup_legacy" -ErrorAction Stop
        Write-OK "Setup/ directory archived as Setup_legacy/."
        Record-Step 7 "Archive Setup/" "OK" "Setup -> Setup_legacy"
        return $true
    } catch {
        Write-Warn "Could not archive Setup/ directory: $($_.Exception.Message)"
        Record-Step 7 "Archive Setup/" "WARN" $_.Exception.Message
        return $true
    }
}

# ============================================================================
# FINAL REPORT
# ============================================================================
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

# ============================================================================
# MAIN PIPELINE
# ============================================================================
if ($MyInvocation.InvocationName -ne '.') {
    Write-Header "ARGUS SECURITY FRAMEWORK - INSTALLER (Self-Contained)"
    if ($DryRun) { Write-Warn "DRY RUN mode: no system changes will be made." }

    # -OnlyHealthCheck: fast diagnostic, no elevation, no install steps.
    if ($OnlyHealthCheck) {
        Write-Info "OnlyHealthCheck mode - skipping self-elevation and all install steps."
        $healthy = Invoke-HealthCheck
        exit $(if ($healthy) { 0 } else { 1 })
    }

    # Admin-first: self-elevate before anything mutating happens.
    Invoke-SelfElevation

    # At this point we are guaranteed to be elevated (or the user declined elevation).
    if (-not (Test-IsAdministrator)) {
        Write-Err "Administrator privileges are required. Aborting."
        Write-Info "Right-click PowerShell -> 'Run as administrator' and rerun."
        exit 1
    }
    Write-OK "Running with Administrator privileges."
    Write-OK "This script is fully self-contained - no external file dependencies."

    $null = Test-SystemReadiness

    # Step 1 - Python (critical prerequisite)
    if (-not (Install-Python)) {
        Write-Err "Python prerequisite not satisfied. Aborting before system-changing steps."
        $null = Show-FinalReport -Failed @(1)
        exit 10
    }

    # Steps 2..7 - orchestrated, non-critical failures collected
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

    # Step 7 - cleanup (archive Setup/ to Setup_legacy/)
    $ok7 = Invoke-StepCleanup
    if (-not $ok7) { $failed += 7 }

    $exitCode = Show-FinalReport -Failed $failed
    exit $exitCode
}
