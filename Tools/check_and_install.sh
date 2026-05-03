#!/bin/bash

# List of core tools to check and install
TOOLS=("whatweb" "curl" "wget")

echo "[*] Fixing potential 403 Forbidden errors (User-Agent fix)..."
sudo bash -c "echo 'Acquire::http::User-Agent \"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36\";' > /etc/apt/apt.conf.d/99useragent"

echo "[*] Ensuring official Kali repositories are used..."
sudo bash -c "echo 'deb http://http.kali.org/kali kali-rolling main non-free contrib' > /etc/apt/sources.list"

echo "[*] Updating package lists to ensure everything is fresh..."
sudo apt update -y

echo "Checking core web analysis tools..."
for tool in "${TOOLS[@]}"; do
    if ! command -v "$tool" &> /dev/null; then
        echo "[!] $tool is not installed. Installing..."
        sudo apt install -y "$tool"
        
        if command -v "$tool" &> /dev/null; then
            echo "[+] $tool installed successfully."
        else
            echo "[-] Failed to install $tool. Please check your internet connection."
        fi
    else
        echo "[+] $tool is already installed."
    fi
done

echo "Verification complete."
