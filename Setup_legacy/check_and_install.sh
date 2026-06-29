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
        cat > /usr/local/bin/finalrecon <<'EOF'
#!/usr/bin/env bash
exec /opt/finalrecon/.venv/bin/python /opt/finalrecon/finalrecon.py "$@"
EOF
        chmod +x /usr/local/bin/finalrecon
    else
        warn_optional "FinalRecon"
    fi
fi

install_git_repo PayloadsAllTheThings https://github.com/swisskyrepo/PayloadsAllTheThings.git /opt/payloads/PayloadsAllTheThings || warn_optional "PayloadsAllTheThings"
install_git_repo SecLists https://github.com/danielmiessler/SecLists.git /usr/share/seclists || warn_optional "SecLists"
[ -d /usr/share/seclists ] && ln -sf /usr/share/seclists "$HOME/seclists"

echo "[INFO] Creating Argus native recon command..."
cat > /usr/local/bin/argus_recon <<'EOF'
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
EOF
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
