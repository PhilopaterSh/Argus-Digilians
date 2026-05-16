#!/bin/bash

# --- ARGUS ADVANCED KALI INSTALLER ---
# Inspired by PhilopaterSh's Tools_Install.sh
# Optimized for WSL Kali environment

echo "--------------------------------------------------------"
echo "🛡️  ARGUS KALI ADVANCED ENVIRONMENT SETUP"
echo "--------------------------------------------------------"

# 1. System Update & Base Dependencies
echo "[*] Updating system repositories..."
sudo apt update -y
sudo apt install -y curl wget git python3-pip python3-venv golang-go nodejs npm build-essential libpcap-dev pipx jq

# 2. Go Environment Configuration
echo "[*] Configuring Go Environment..."
export GOPATH=$HOME/go
export PATH=$PATH:/usr/local/go/bin:$GOPATH/bin
mkdir -p $GOPATH/bin

# Add to shells for persistence
for shell_rc in "$HOME/.bashrc" "$HOME/.zshrc"; do
    if [ -f "$shell_rc" ]; then
        if ! grep -q 'GOPATH' "$shell_rc"; then
            echo 'export GOPATH=$HOME/go' >> "$shell_rc"
            echo 'export PATH=$PATH:$GOPATH/bin' >> "$shell_rc"
        fi
    fi
done

# 3. PDTM (ProjectDiscovery Tool Manager) Setup
echo "[*] Installing PDTM for automated tool management..."
go install -v github.com/projectdiscovery/pdtm/cmd/pdtm@latest
sudo ln -sf $GOPATH/bin/pdtm /usr/local/bin/pdtm

echo "[*] Deploying ALL ProjectDiscovery tools via PDTM..."
pdtm -ia

# Link all installed PDTM tools to /usr/local/bin for system-wide access
echo "[*] Linking ProjectDiscovery tools to /usr/local/bin..."
if [ -d "$HOME/.pdtm/go/bin" ]; then
    for tool_path in "$HOME/.pdtm/go/bin"/*; do
        if [ -f "$tool_path" ]; then
            tool_name=$(basename "$tool_path")
            sudo ln -sf "$tool_path" /usr/local/bin/"$tool_name"
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
    else
        echo "[OK] $tool is already installed."
    fi
done

# 5. Manual & Custom Tooling (Git / Go / Python)
echo "[*] Deploying specialized manual tools..."

# Go-based Tools
echo "[+] Installing Go-based utilities..."
go install github.com/tomnomnom/assetfinder@latest
go install github.com/d3mondev/puredns/v2@latest
go install github.com/subfinder/goaltdns@latest

# Linking Go tools
sudo ln -sf $GOPATH/bin/assetfinder /usr/local/bin/assetfinder
sudo ln -sf $GOPATH/bin/puredns /usr/local/bin/puredns
sudo ln -sf $GOPATH/bin/goaltdns /usr/local/bin/goaltdns

# Findomain (Binary)
if ! command -v findomain &> /dev/null; then
    echo "[+] Installing Findomain..."
    curl -LO https://github.com/Findomain/Findomain/releases/latest/download/findomain-linux.zip
    unzip findomain-linux.zip
    chmod +x findomain
    sudo mv findomain /usr/local/bin/findomain
    rm findomain-linux.zip
fi

# Python-based Tools (Permutations & OSINT)
echo "[+] Installing Python-based permutation tools..."
sudo pip3 install dnsgen pyaltdns alterx --break-system-packages

# MassDNS (Build from Source)
if [ ! -d "/opt/massdns" ]; then
    echo "[+] Installing MassDNS (High-performance DNS resolver)..."
    sudo git clone https://github.com/blechschmidt/massdns.git /opt/massdns
    cd /opt/massdns
    sudo make
    sudo ln -sf /opt/massdns/bin/massdns /usr/local/bin/massdns
    cd - >/dev/null
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
if ! command -v osmedeus &> /dev/null; then
    echo "[+] Installing Osmedeus (Offensive Framework)..."
    # Basic installation steps for Osmedeus
    curl -fsSL https://raw.githubusercontent.com/osmedeus/osmedeus-base/master/install.sh | bash
    # Osmedeus binary is usually installed in ~/osmedeus-base/ or similar, link it if found
    if [ -f "$HOME/osmedeus-base/osmedeus" ]; then
        sudo ln -sf "$HOME/osmedeus-base/osmedeus" /usr/local/bin/osmedeus
    fi
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

echo "[*] Phase 4: Resolution & Validation..."
sort -u $RAW_FILE -o $RAW_FILE
if command -v puredns &>/dev/null; then
    puredns resolve $RAW_FILE --quiet > $ALIVE_FILE
else
    cat $RAW_FILE | xargs -I{} host -W 2 {} | grep "has address" | awk "{print \$1}" > $ALIVE_FILE
fi

echo "[*] Phase 5: Deep DNS Analysis..."
ALIVE_COUNT=$(wc -l < $ALIVE_FILE)
echo "--- 🛡️ MAXIMIZED SUBDOMAIN DISCOVERY: $DOMAIN ---"
echo "[+] Total Potential: $(wc -l < $RAW_FILE)"
echo "[+] Total Verified Alive: $ALIVE_COUNT"
echo ""
echo "[*] TOP VERIFIED SUBDOMAINS:"
head -n 50 $ALIVE_FILE
echo ""
echo "[*] INFRASTRUCTURE POINTERS (CNAME/MX):"
head -n 10 $ALIVE_FILE | while read sub; do
    cname=$(dig CNAME +short +time=1 $sub)
    [ -n "$cname" ] && echo "[CNAME] $sub -> $cname"
    mx=$(dig MX +short +time=1 $sub)
    [ -n "$mx" ] && echo "[MX] $sub -> $mx"
done

rm $RAW_FILE $ALIVE_FILE 2>/dev/null
EOF'

sudo chmod +x /usr/local/bin/argus_recon

# 7. Final Verification
echo "--------------------------------------------------------"
echo "✅ Argus Environment is now Synchronized & Optimized."
echo "[INFO] All tools are linked to /usr/local/bin for maximum compatibility."
echo "--------------------------------------------------------"
