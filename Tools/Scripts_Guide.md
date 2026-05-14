# Automation Scripts Technical Guide

This document explains how to manually create and configure the automation scripts used to bridge Windows and Kali Linux (WSL) for tool setup.

---

## 1. Linux Setup Script (check_and_install.sh)

This script is the "Advanced Installer" for the Argus environment inside Kali Linux. It performs system-level optimizations and handles complex dependency management.

### Key Features
- **System Fixes:** Optimizes Apt mirrors, fixes SMB protocol compatibility (LANMAN1), and stabilizes the Python pip environment.
- **Go Environment:** Automatically installs Golang and configures `GOPATH` for modern security tools.
- **PDTM Integration:** Uses the ProjectDiscovery Tool Manager for robust installation of tools like `subfinder`, `nuclei`, and `katana`.
- **Hybrid Installation:** Combines `APT`, `Go install`, and `Git` cloning for a complete security arsenal.

### Expanded Toolset
The script now manages over 15+ specialized tools, including:
- **Core:** `whatweb`, `nmap`, `wafw00f`, `nikto`, `curl`, `wget`.
- **Recon:** `subfinder`, `assetfinder`, `theharvester`, `recon-ng`.
- **Advanced:** `Ph.Sh_url`, `Ph.Sh-Subdomain`, `finalrecon`, `spiderfoot`.

### Script Structure (Simplified)
```bash
#!/bin/bash
# 1. System Updates & Base Dependencies
# 2. Go Environment Configuration
# 3. PDTM Deployment (subfinder, httpx, nuclei, etc.)
# 4. Specialized Utilities via APT (nmap, wafw00f, etc.)
# 5. Manual Tooling via Git/Go (Ph.Sh suite, FinalRecon, etc.)
```

### Important Note on Format
Linux scripts must use **LF** (Line Feed) line endings. If you create this file on Windows, run the following command inside Kali to fix it:
```bash
tr -d '\r' < check_and_install.sh > fixed.sh && mv fixed.sh check_and_install.sh
```

---

## 2. Windows Bridge Script (Step_3_Kali_Tools_Setup.bat)

This script runs on Windows. It triggers the Linux script inside the WSL environment.

### Script Content
```batch
@echo off
set "DISTRO_NAME=kali-linux"
set "LINUX_PATH=/mnt/c/AI_PenTest_Project/Argus/Tools/check_and_install.sh"

echo Running Linux Tool Check from Windows...
echo Target Distro: %DISTRO_NAME%

:: Execute the shell script inside WSL
wsl -d %DISTRO_NAME% bash %LINUX_PATH%

echo.
echo Process finished.
pause
```

---

## 3. Kali AI Environment Bridge (run_kali_setup.bat)

This script automates the installation of the entire Python AI ecosystem inside Kali Linux without requiring any manual interaction with the Linux terminal.

### Components:
- **setup_python_kali.sh**: The engine that handles updates, Python installation, and library setup (requirements.txt) inside Kali.
- **run_kali_setup.bat**: The Windows-side trigger.

### How to use:
Simply double-click `run_kali_setup.bat`. It will:
1. Login to Kali as root.
2. Fix the working directory automatically.
3. Install Python 3.12+ and all AI libraries.
4. Create a virtual environment named `ai_env`.

---

## 4. How they work together

1.  **The .bat file** acts as a launcher. It uses the `wsl` command to talk to your Kali Linux.
2.  **The Path Mapping**: Windows uses `C:\AI_PenTest_Project\...`, but inside Kali, this path is seen as `/mnt/c/AI_PenTest_Project/...`.
3.  **The Execution**: The batch file tells WSL to use `bash` to read and execute the instructions inside the `.sh` file.

## Manual Creation Steps
1.  Create a text file and paste the `.sh` content. Save it as `check_and_install.sh`.
2.  Create another text file and paste the `.bat` content. Save it as `Step_3_Kali_Tools_Setup.bat`.
3.  Ensure both files are in the same directory (`C:\AI_PenTest_Project\Argus\Tools`).
4.  Run the `.bat` file to start the process.
