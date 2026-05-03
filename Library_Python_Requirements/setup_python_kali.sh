#!/bin/bash

# Change directory to the script's location
cd "$(dirname "$0")"

echo "========================================================"
echo "       Kali Linux Python AI Environment Setup"
echo "========================================================"

# 1. Update and install Python core components
echo "[*] Updating package lists..."
sudo apt update -y

echo "[*] Installing Python3 and Pip..."
sudo apt install -y python3 python3-pip python3-venv

# 2. Check Version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "[+] Found Python version: $PYTHON_VERSION"

# 3. Create and Activate Virtual Environment (Recommended for Linux)
echo "[*] Setting up a virtual environment (ai_env)..."
python3 -m venv ai_env
source ai_env/bin/activate

# 4. Install Requirements
if [ -f "requirements.txt" ]; then
    echo "[*] Installing requirements from requirements.txt..."
    pip install --upgrade pip
    pip install -r requirements.txt
    
    if [ $? -eq 0 ]; then
        echo "========================================================"
        echo "[OK] Environment is ready inside Kali Linux!"
        echo "To activate it later, run: source ai_env/bin/activate"
        echo "========================================================"
    else
        echo "[!] Error occurred during library installation."
    fi
else
    echo "[!] Error: requirements.txt not found in this directory."
fi
