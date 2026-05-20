#!/bin/bash

# --- ARGUS ADVANCED KALI INSTALLER ---
# Inspired by PhilopaterSh's Tools_Install.sh
# Optimized for WSL Kali environment

echo "--------------------------------------------------------"
echo "🛡️  ARGUS KALI ADVANCED ENVIRONMENT SETUP"
echo "--------------------------------------------------------"

# 1. System Update & Base Dependencies
echo "[*] Checking for base dependencies..."
BASE_DEPS=("curl" "wget" "git" "python3-pip" "python3-venv" "golang" "nodejs" "npm" "build-essential" "libpcap-dev" "pipx" "jq" "sshd" "unzip")
MISSING_DEPS=()
for dep in "${BASE_DEPS[@]}"; do
    if ! command -v "$dep" &> /dev/null && [ "$dep" != "sshd" ] && [ "$dep" != "golang" ] && [ "$dep" != "nodejs" ]; then
        MISSING_DEPS+=("$dep")
    elif [ "$dep" == "golang" ] && ! command -v go &> /dev/null; then
        MISSING_DEPS+=("golang")
    elif [ "$dep" == "nodejs" ] && ! command -v node &> /dev/null; then
        MISSING_DEPS+=("nodejs")
    elif [ "$dep" == "sshd" ] && ! [ -f "/usr/sbin/sshd" ]; then
        MISSING_DEPS+=("openssh-server")
    else
        ((ALREADY_COUNT++))
    fi
done

if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    echo "[*] Missing dependencies: ${MISSING_DEPS[*]}. Updating repositories..."
    sudo apt update -y
    sudo apt install -y "${MISSING_DEPS[@]}"
    ((INSTALLED_COUNT+=${#MISSING_DEPS[@]}))
else
    echo "[OK] All base dependencies are present."
fi

# 1.5. Configure SSH for WSL Bridge (Self-Healing)
if ! [ -f "/etc/ssh/ssh_host_rsa_key" ]; then
    echo "[*] Configuring SSH Server for Argus Bridge..."
    sudo mkdir -p /run/sshd
    sudo ssh-keygen -A 2>/dev/null
    # Enable Password Authentication and ensure Port 22 is explicitly listening
    sudo sed -i 's/^#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config
    sudo sed -i 's/^#Port 22/Port 22/' /etc/ssh/sshd_config
    sudo sed -i 's/^#ListenAddress 0.0.0.0/ListenAddress 0.0.0.0/' /etc/ssh/sshd_config
    ((INSTALLED_COUNT++))
else
    echo "[OK] SSH Server already configured."
    ((ALREADY_COUNT++))
fi

# 2. Go Environment Configuration
# ... (existing code for GOPATH)
# 3. PDTM (ProjectDiscovery Tool Manager) Setup
if ! command -v pdtm &> /dev/null; then
    echo "[*] Installing PDTM for automated tool management..."
    go install -v github.com/projectdiscovery/pdtm/cmd/pdtm@latest
    # Move binary to a global location
    if [ -f "$HOME/go/bin/pdtm" ]; then
        sudo cp "$HOME/go/bin/pdtm" /usr/local/bin/pdtm
    elif [ -f "/root/go/bin/pdtm" ]; then
        sudo cp "/root/go/bin/pdtm" /usr/local/bin/pdtm
    fi
    echo "[*] Deploying ALL ProjectDiscovery tools via PDTM..."
    /usr/local/bin/pdtm -ia
else
    echo "[OK] PDTM is already installed. Skipping tool deployment."
fi

# Link all installed PDTM tools to /usr/local/bin for system-wide access
# We use /root/.pdtm/go/bin because that's where pdtm -ia installs them when run as root
echo "[*] Ensuring ProjectDiscovery tools are linked..."
if [ -d "/root/.pdtm/go/bin" ]; then
    for tool_path in "/root/.pdtm/go/bin"/*; do
        if [ -f "$tool_path" ]; then
            tool_name=$(basename "$tool_path")
            if [ ! -f "/usr/local/bin/$tool_name" ]; then
                sudo ln -sf "$tool_path" /usr/local/bin/"$tool_name"
            fi
        fi
    done
fi

# 4. Specialized Tools (APT)
echo "[*] Installing core security utilities via APT..."
APT_TOOLS=("nmap" "whatweb" "wafw00f" "whois" "nikto" "theharvester" "recon-ng" "spiderfoot" "amass" "gobuster" "ffuf" "fierce" "dnsenum" "dnsrecon" "dnsutils")
for tool in "${APT_TOOLS[@]}"; do
    if ! command -v "$tool" &> /dev/null; then
        echo "[+] Installing $tool..."
        sudo apt install -y "$tool"
        ((INSTALLED_COUNT++))
    else
        echo "[OK] $tool is already installed."
        ((ALREADY_COUNT++))
    fi
done

# 5. Manual & Custom Tooling (Git / Go / Python)
echo "[*] Checking Go-based utilities..."
GO_TOOLS=("assetfinder" "anew" "puredns" "goaltdns")
GO_REPOS=("github.com/tomnomnom/assetfinder@latest" "github.com/tomnomnom/anew@latest" "github.com/d3mondev/puredns/v2@latest" "github.com/subfinder/goaltdns@latest")

for i in "${!GO_TOOLS[@]}"; do
    if ! command -v "${GO_TOOLS[$i]}" &> /dev/null; then
        echo "[+] Installing ${GO_TOOLS[$i]}..."
        go install "${GO_REPOS[$i]}"
        sudo ln -sf $GOPATH/bin/"${GO_TOOLS[$i]}" /usr/local/bin/"${GO_TOOLS[$i]}"
        ((INSTALLED_COUNT++))
    else
        echo "[OK] ${GO_TOOLS[$i]} is already installed."
        ((ALREADY_COUNT++))
    fi
done

# Findomain (Binary)
if ! command -v findomain &> /dev/null; then
    echo "[+] Installing Findomain..."
    curl -LO https://github.com/Findomain/Findomain/releases/latest/download/findomain-linux.zip
    unzip findomain-linux.zip
    chmod +x findomain
    sudo mv findomain /usr/local/bin/findomain
    rm findomain-linux.zip
    ((INSTALLED_COUNT++))
else
    echo "[OK] Findomain is already installed."
    ((ALREADY_COUNT++))
fi

# Python-based Tools (Permutations & OSINT)
echo "[+] Checking Python-based permutation tools..."
PY_TOOLS=("dnsgen" "alterx") # pyaltdns doesn't always have a direct binary, or might be used as module
for tool in "${PY_TOOLS[@]}"; do
    if ! command -v "$tool" &> /dev/null; then
        echo "[+] Installing $tool..."
        sudo pip3 install "$tool" --break-system-packages
        ((INSTALLED_COUNT++))
    else
        echo "[OK] $tool is already installed."
        ((ALREADY_COUNT++))
    fi
done
# pyaltdns check
if ! python3 -c "import altdns" &> /dev/null; then
    echo "[+] Installing altdns..."
    sudo pip3 install py-altdns --break-system-packages
    ((INSTALLED_COUNT++))
else
    echo "[OK] altdns is already installed."
    ((ALREADY_COUNT++))
fi

# MassDNS (Build from Source)
if [ ! -f "/usr/local/bin/massdns" ]; then
    echo "[+] Installing MassDNS (High-performance DNS resolver)..."
    if [ ! -d "/opt/massdns" ]; then
        sudo git clone https://github.com/blechschmidt/massdns.git /opt/massdns
    fi
    cd /opt/massdns
    sudo make
    sudo ln -sf /opt/massdns/bin/massdns /usr/local/bin/massdns
    cd - >/dev/null
    ((INSTALLED_COUNT++))
else
    echo "[OK] MassDNS is already installed."
    ((ALREADY_COUNT++))
fi

# Ph.Sh_URL
if ! command -v Ph.Sh_url &> /dev/null; then
    echo "[+] Installing Ph.Sh_url via Go..."
    go install github.com/PhilopaterSh/Ph.Sh_url@latest
    sudo ln -sf $GOPATH/bin/Ph.Sh_url /usr/local/bin/Ph.Sh_url
fi

# Ph.Sh-Subdomain
if [ ! -d "/opt/Ph.Sh-Subdomain" ]; then
    echo "[+] Installing Ph.Sh-Subdomain..."
    sudo git clone https://github.com/PhilopaterSh/Ph.Sh-Subdomain.git /opt/Ph.Sh-Subdomain
    cd /opt/Ph.Sh-Subdomain
    sudo pip3 install -r requirements.txt --break-system-packages
    sudo go build
    sudo ln -sf /opt/Ph.Sh-Subdomain/Ph.Sh-Subdomain /usr/local/bin/Ph.Sh-Subdomain
    cd - >/dev/null
fi

# FinalRecon
if ! command -v finalrecon &> /dev/null; then
    echo "[+] Installing FinalRecon..."
    sudo git clone https://github.com/thewhiteh4t/FinalRecon.git /opt/finalrecon
    cd /opt/finalrecon
    sudo pip3 install -r requirements.txt --break-system-packages
    echo -e '#!/bin/bash\npython3 /opt/finalrecon/finalrecon.py "$@"' | sudo tee /usr/local/bin/finalrecon > /dev/null
    sudo chmod +x /usr/local/bin/finalrecon
    cd - >/dev/null
fi

# Osmedeus
# if ! command -v osmedeus &> /dev/null; then
#     echo "[+] Installing Osmedeus (Offensive Framework)..."
#     # Basic installation steps for Osmedeus
#     curl -fsSL https://raw.githubusercontent.com/osmedeus/osmedeus-base/master/install.sh | bash
#     # Osmedeus binary is usually installed in ~/osmedeus-base/ or similar, link it if found
#     if [ -f "$HOME/osmedeus-base/osmedeus" ]; then
#         sudo ln -sf "$HOME/osmedeus-base/osmedeus" /usr/local/bin/osmedeus
#     fi
# fi

# PayloadsAllTheThings
if [ ! -d "/opt/payloads/PayloadsAllTheThings" ]; then
    echo "[+] Deploying PayloadsAllTheThings (The ultimate exploit payloads)..."
    sudo mkdir -p /opt/payloads
    sudo git clone --depth 1 https://github.com/swisskyrepo/PayloadsAllTheThings.git /opt/payloads/PayloadsAllTheThings
    echo "[OK] PayloadsAllTheThings deployed to /opt/payloads/PayloadsAllTheThings"
fi

# SecLists
if [ ! -d "/usr/share/seclists" ]; then
    echo "[+] Deploying SecLists (The ultimate security wordlists)..."
    sudo git clone --depth 1 https://github.com/danielmiessler/SecLists.git /usr/share/seclists
    # Create a symlink in home for quick access
    ln -sf /usr/share/seclists ~/seclists
    echo "[OK] SecLists deployed to /usr/share/seclists and linked to ~/seclists"
fi

# --- 6. Argus Native Recon Engine ---
echo "[*] Creating Argus Native Recon Engine..."
sudo bash -c 'cat << "EOF" > /usr/local/bin/argus_recon
#!/bin/bash
# Argus Professional Recon Engine (Native Linux)
DOMAIN=$1
[ -z "$DOMAIN" ] && echo "Usage: argus_recon <domain>" && exit 1

RAW_FILE="/tmp/argus_raw_$DOMAIN.txt"
ALIVE_FILE="/tmp/argus_alive_$DOMAIN.txt"
WORDLIST="/usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt"
[ ! -f "$WORDLIST" ] && echo "www" > /tmp/mini.txt && WORDLIST="/tmp/mini.txt"

echo "[*] Phase 1: Passive OSINT..."
subfinder -d $DOMAIN -silent > $RAW_FILE
assetfinder --subs-only $DOMAIN >> $RAW_FILE
findomain -t $DOMAIN -q >> $RAW_FILE
amass enum -passive -d $DOMAIN >> $RAW_FILE

echo "[*] Phase 2: Active Brute-Force..."
gobuster dns -d $DOMAIN -w $WORDLIST -z --quiet | grep "Found:" | awk "{print \$2}" >> $RAW_FILE

echo "[*] Phase 3: Permutations..."
sort -u $RAW_FILE -o $RAW_FILE
if command -v dnsgen &>/dev/null; then
    dnsgen $RAW_FILE >> $RAW_FILE
fi

echo "[*] Phase 4: Resolution & Validation (anew + httpx)..."
sort -u $RAW_FILE -o $RAW_FILE

# Use anew to keep only unique entries
cat $RAW_FILE | /usr/local/bin/anew /tmp/unique_$DOMAIN.txt > /dev/null

# Use httpx to find truly ALIVE web servers (the most critical part)
if [ -f "/usr/local/bin/httpx" ]; then
    cat /tmp/unique_$DOMAIN.txt | /usr/local/bin/httpx -silent -fc 404,500,502 -threads 50 > $ALIVE_FILE
else
    # Fallback to puredns or host if httpx is missing
    if command -v puredns &>/dev/null; then
        puredns resolve /tmp/unique_$DOMAIN.txt --quiet > $ALIVE_FILE
    else
        cat /tmp/unique_$DOMAIN.txt | xargs -I{} host -W 2 {} | grep "has address" | awk "{print \$1}" > $ALIVE_FILE
    fi
fi

echo "[*] Phase 5: Deep DNS Analysis..."
ALIVE_COUNT=$(wc -l < $ALIVE_FILE)
echo "--- 🛡️ MAXIMIZED SUBDOMAIN DISCOVERY: $DOMAIN ---"
echo "[+] Total Potential: $(wc -l < $RAW_FILE)"
echo "[+] Total Verified Alive (Web): $ALIVE_COUNT"
rm /tmp/unique_$DOMAIN.txt 2>/dev/null
echo ""
echo "[*] TOP VERIFIED SUBDOMAINS:"
head -n 50 $ALIVE_FILE
echo ""
echo "[*] INFRASTRUCTURE POINTERS (CNAME/MX):"
head -n 10 $ALIVE_FILE | while read sub; do
    # Clean domain: remove http/https and trailing slash
    clean_sub=$(echo "$sub" | sed -E '"'s|https?://||; s|/.*$||'"')
    cname=$(dig CNAME +short +time=3 +tries=2 "$clean_sub")
    [ -n "$cname" ] && echo "[CNAME] $sub -> $cname"
    mx=$(dig MX +short +time=3 +tries=2 "$clean_sub")
    [ -n "$mx" ] && echo "[MX] $sub -> $mx"
done

rm $RAW_FILE $ALIVE_FILE 2>/dev/null
EOF'

sudo chmod +x /usr/local/bin/argus_recon

# --- 0. Pre-Flight Checks ---
echo "[*] Ensuring package manager is available..."
while sudo fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1 ; do
    echo "[!] Waiting for other package managers to finish..."
    sleep 2
done

# Initialize counters
INSTALLED_COUNT=0
ALREADY_COUNT=0

# ... (inside loops or installation blocks)
# Update counters as needed
# For example:
# if ... installed; then ((INSTALLED_COUNT++)); else ((ALREADY_COUNT++)); fi

# --- 7. Final Verification & Summary ---
echo ""
echo "========================================================"
echo "📊 INSTALLATION SUMMARY (KALI TOOLS)"
echo "========================================================"
echo "✅ Tools Already Present: $ALREADY_COUNT"
echo "🚀 New Tools Installed:   $INSTALLED_COUNT"
echo "--------------------------------------------------------"
echo "✅ Argus Environment is now Synchronized & Optimized."
echo "[INFO] All tools are linked to /usr/local/bin."
echo "========================================================"
