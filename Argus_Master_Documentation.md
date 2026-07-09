# Argus Security Framework: Master Installation and Technical Guide

> **Note:** For day-to-day installation, use `INSTALL.bat` / `scripts/ARGUS_INSTALLER.ps1`
> as described in `INSTALLATION_GUIDE.md` - it automates everything below in one command.
> This document predates that unified installer and describes the same setup manually,
> step by step; keep it as a technical reference for what the installer does under the
> hood, or for manual/offline provisioning, not as the first thing to follow.

This document provides the definitive, comprehensive guide for the Argus Security Framework, consolidating all infrastructure, AI environment, and security tooling documentation into a single reference.

---

## 1. System Requirements and Preparation

### 1.1 Hardware Requirements
- RAM: Minimum 8GB (16GB+ recommended for AI models).
- Disk Space: 20GB+ free (for WSL, models, and tools).
- OS: Windows 10 (version 2004+) or Windows 11.

### 1.2 Windows Host Preparation
Run these in an elevated PowerShell (Administrator):

```powershell
# Enable WSL and Virtual Machine Platform
wsl --install
wsl --update
wsl --set-default-version 2
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
```
*Note: Restart your computer after DISM commands.*

---

## 2. Host AI Intelligence Engine (Ollama)

### 2.1 Installation
```powershell
irm https://ollama.com/install.ps1 | iex
```

### 2.2 Model Selection and Deployment
The framework uses specialized models. Default: `WhiteRabbitNeo/WhiteRabbitNeo-V3-7B`.
- **WhiteRabbitNeo:** Fine-tuned for offensive security and penetration testing.
---

## 3. Python Environment and AI Core

### 3.1 Automated Python Setup (Winget Fix)
The installer handles common Winget certificate errors by forcing the official source:
```powershell
winget install --id Python.Python.3.12 --source winget --exact
```

### 3.2 App Execution Alias Fix
To prevent the Microsoft Store from intercepting 'python' commands:
```powershell
powershell -Command "Get-AppExecutionAlias | Where-Object { $_.Name -match 'python' } | Disable-AppExecutionAlias"
```

### 3.3 Core Libraries
- **Argus_venv:** The framework uses an isolated Python virtual environment named `Argus_venv` at the project root.
- **LangChain:** Communicates with Ollama.
- **FAISS-CPU:** Local vector storage for intelligence findings.
- **Streamlit:** Powers the graphical Multi-Agent Studio.

---

## 4. Kali Linux (WSL) Configuration

### 4.1 Repository Optimization (Fixing 403 Errors)
Ensure `/etc/apt/sources.list` uses the HTTPS download mirror to avoid forbidden errors:
```text
deb https://kali.download/kali kali-rolling main contrib non-free non-free-firmware
```

### 4.2 Base Dependencies
Essential tools required inside Kali:
```bash
sudo apt update
sudo apt install -y python3-pip python3-venv golang nodejs npm build-essential libpcap-dev pipx jq unzip ncat openssh-server
```

---

## 5. Security Tooling and Recon Engine

### 5.1 ProjectDiscovery PDTM
Automated tool management for:
- `httpx`, `nuclei`, `subfinder`, `katana`, `dnsx`.

### 5.2 Recon Arsenal
- **Passive:** Assetfinder, Findomain, Amass.
- **Active:** Nmap, Gobuster, FFuf, Nikto, WhatWeb, Wafw00f.
- **Advanced:** Ph.Sh Suite, FinalRecon, MassDNS.

### 5.3 Argus Native Recon Engine (`argus_recon`)
A custom 5-phase workflow integrated into the framework:
1. Passive OSINT (Subfinder, Findomain).
2. Active Brute-Force (Gobuster).
3. Permutations (DNSGen).
4. Validation (HTTPX/anew).
5. Deep Analysis (Nmap/WhatWeb).

---

## 6. Operation and Troubleshooting

### 6.1 Launching the System
Use `LAUNCH_STUDIO.bat` to start the AI interface at `http://localhost:12199`.

### 6.2 Troubleshooting
- **Python not found:** The installer will attempt a fallback check in LocalAppData and prioritize it in the session PATH.
- **WSL Connectivity:** If APT fails, verify the sources.list uses HTTPS.
- **SSH Bridge:** Ensure the SSH server is running inside Kali (`sudo service ssh start`).

---
Maintained by: Argus Security Framework Team
Consolidated Technical Reference: May 2026
