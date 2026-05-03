# Complete Kali Linux Setup and Optimization on WSL 2

## Requirements
- Windows 10 (version 2004 or later) or Windows 11.
- Active internet connection.
- WSL features enabled on the host system.

## Phase 1: Windows Host Preparation

Run the following commands in an elevated PowerShell terminal (Run as Administrator):

```powershell
# Install WSL and update to the latest kernel
wsl --install
wsl --update
wsl --set-default-version 2

# Enable Mandatory Windows Features for WSL 2
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
dism.exe /online /enable-feature /featurename:Microsoft-Hyper-V-All /all /norestart
```
Note: Restart your computer after running the DISM commands to finalize the feature activation.

## Phase 2: WSL Management Commands

These commands can be executed in PowerShell or Command Prompt to manage your distributions:

- **Shut Down All WSL Instances:**
  ```powershell
  wsl --shutdown
  ```
- **Terminate a Specific Distribution:**
  ```powershell
  wsl --terminate kali-linux
  ```
- **Set Kali Linux as Default:**
  ```powershell
  wsl --setdefault kali-linux
  ```
- **Check Status and Version:**
  ```powershell
  wsl -l -v
  ```
- **Reset/Reinstall Kali Linux:**
  ```powershell
  wsl --unregister kali-linux
  wsl --install -d kali-linux
  ```

## Phase 3: Kali Linux Internal Configuration

### 1. Repository Setup
Open the sources list file within Kali:
```bash
sudo nano /etc/apt/sources.list
```
Ensure it contains the following line for the rolling release:
```text
deb http://http.kali.org/kali kali-rolling main non-free contrib
```

### 2. Post-Install Optimization and Tool Installation
Run the following script block to update the keyring, fix dependencies, and install essential tools:

```bash
# Update Keyring
sudo wget https://archive.kali.org/archive-keyring.gpg -O /usr/share/keyrings/kali-archive-keyring.gpg

# System Cleanup and Repair
sudo dpkg --configure -a
sudo apt autoremove -y
sudo apt autoclean
sudo apt clean
sudo rm -rf /var/lib/apt/lists/*
sudo rm -rf /var/log/*

# Remove conflicting packages
sudo apt remove --purge python3-jwt -y

# Full System Upgrade
sudo apt update --allow-releaseinfo-change
sudo apt upgrade -y
sudo apt full-upgrade -y
sudo apt --fix-broken install -y
sudo apt install -f --fix-missing -y

# Install Core Tools and Win-KeX
sudo apt install -y kali-linux-default
sudo apt install -y kali-linux-headless
sudo apt install -y kali-tools-top10
sudo apt install -y kali-win-kex --fix-missing
sudo apt install -y libclang-cpp19 python3-fs samdump2
sudo apt install -y openssh-server

# Enable SSH Service
sudo systemctl enable ssh.service --now
```

## Phase 4: Win-KeX GUI Setup

Win-KeX provides a graphical user interface for Kali Linux on WSL. Use the following commands to launch it:

- **Window Mode (with sound support):**
  ```bash
  kex --win -s
  ```
- **Seamless Mode:**
  ```bash
  kex --sl -s
  ```
- **Enhanced Session Mode (ESM):**
  ```bash
  kex --esm --ip -s
  ```
- **Launch directly from Windows Command Prompt:**
  ```cmd
  wsl -d kali-linux kex --win -s
  ```

## Phase 5: Verification and Maintenance

### Check Installation Integrity
```bash
lsb_release -a
grep VERSION /etc/os-release
cat /etc/apt/sources.list
```

### System Monitoring
```bash
free -h
top
htop
df -h
```

### Routine Maintenance Script
```bash
sudo rm -rf /var/lib/apt/lists/*
sudo apt update --allow-releaseinfo-change
sudo apt full-upgrade -y
sudo apt install -f --fix-missing -y
sudo apt clean
```
