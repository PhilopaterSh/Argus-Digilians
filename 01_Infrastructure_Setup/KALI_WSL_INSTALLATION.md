# Argus Security Framework: Kali Linux and AI Foundation Setup on WSL 2

This document provides a comprehensive guide for setting up the technical foundation required for the Argus Security Framework.

## Requirements
- Windows 10 (version 2004 or later) or Windows 11.
- Active internet connection.
- Administrator privileges on the host system.

## Phase 1: Windows Host Preparation

Run the following commands in an elevated PowerShell terminal (Run as Administrator):

### 1.1 Enable WSL and Features
```powershell
# Install WSL and update to the latest kernel
wsl --install
wsl --update
wsl --set-default-version 2

# Enable Mandatory Windows Features
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
dism.exe /online /enable-feature /featurename:Microsoft-Hyper-V-All /all /norestart
```
Note: Restart your computer after running the DISM commands to finalize feature activation.

### 1.2 Install Ollama (AI Intelligence Engine)
The Argus framework requires Ollama to run local LLMs. Install it using the following command:
```powershell
irm https://ollama.com/install.ps1 | iex
```

## Phase 2: WSL Management Commands

Manage your distributions using these standard commands in PowerShell or Command Prompt:

- Shut Down All WSL Instances:
  ```powershell
  wsl --shutdown
  ```
- Terminate Kali Distribution:
  ```powershell
  wsl --terminate kali-linux
  ```
- Set Kali Linux as Default:
  ```powershell
  wsl --setdefault kali-linux
  ```
- Check Status and Version:
  ```powershell
  wsl -l -v
  ```

## Phase 3: Kali Linux Internal Configuration

### 3.1 Repository Setup
Ensure the official Kali rolling repositories are configured:
```bash
sudo nano /etc/apt/sources.list
```
The file must contain:
```text
deb http://http.kali.org/kali kali-rolling main non-free contrib
```

### 3.2 System Optimization and Tool Installation
Execute the following block to prepare the internal Kali environment:

```bash
# Update Keyring
sudo wget https://archive.kali.org/archive-keyring.gpg -O /usr/share/keyrings/kali-archive-keyring.gpg

# System Cleanup
sudo dpkg --configure -a
sudo apt autoremove -y
sudo apt clean
sudo rm -rf /var/lib/apt/lists/*

# Full System Upgrade
sudo apt update --allow-releaseinfo-change
sudo apt full-upgrade -y
sudo apt --fix-broken install -y

# Install Argus Core Tools
sudo apt install -y kali-linux-default
sudo apt install -y kali-linux-headless
sudo apt install -y kali-tools-top10
sudo apt install -y ncat openssh-server
```

## Phase 4: GUI Access (Win-KeX)

If a graphical interface is required, use Win-KeX:

- Window Mode:
  ```bash
  kex --win -s
  ```
- Seamless Mode:
  ```bash
  kex --sl -s
  ```
- Launch from Windows Command Prompt:
  ```cmd
  wsl -d kali-linux kex --win -s
  ```

## Phase 5: Verification

Verify the installation integrity with these commands:

```bash
# Check Version
lsb_release -a

# Check Resource Usage
free -h
df -h
```

---
Maintained by: Argus Security Framework Team
Last Update: May 2026
