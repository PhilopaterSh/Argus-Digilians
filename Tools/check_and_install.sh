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
APT_TOOLS=("nmap" "whatweb" "wafw00f" "whois" "nikto" "theharvester" "recon-ng" "spiderfoot")
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

# 6. Final Verification
echo "--------------------------------------------------------"
echo "✅ Argus Environment is now Synchronized & Optimized."
echo "[INFO] All tools are linked to /usr/local/bin for maximum compatibility."
echo "--------------------------------------------------------"
