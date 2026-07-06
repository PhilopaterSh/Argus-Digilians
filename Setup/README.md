# Setup & Installation Scripts (Legacy Reference)

> **NOTE:** These scripts are now **legacy / manual fallback**. The supported
> installation path is the self-contained installer at `scripts\ARGUS_INSTALLER.ps1`
> which embeds all dependencies internally. See `scripts/README.md` for details.

---

## When to Use These Scripts Manually

Use these individual step scripts only if you are:

- Debugging a specific installation failure
- Running a CI/CD pipeline that needs granular control
- Customizing a single setup step
- Working in an air-gapped environment with manual provisioning

---

## Legacy Three-Step Installation Process

### Step 1: Host Environment Setup
**File:** `Step_1_Core_Foundation.bat`

- Checks Admin privileges
- Enables WSL2 and Virtual Machine Platform
- Installs Kali Linux distribution
- Installs Ollama (AI engine)

### Step 2: Python & AI Environment
**File:** `Step_2_AI_Python_Env.bat`

- Verifies Python 3.12
- Starts Ollama engine
- Creates `Argus_venv/` virtual environment at project root
- Installs Python packages from `requirements.txt`
- Pulls the AI model (WhiteRabbitNeo-V3-7B)

### Step 3: Kali Linux Tools
**File:** `Step_3_Kali_Tools_Setup.bat`

- Verifies Kali WSL distro
- Runs `check_and_install.sh` inside WSL as root
- Installs security tools (nmap, gobuster, subfinder, etc.)
- Configures SSH daemon

---

## Files in This Directory

| File | Purpose | Status |
|------|---------|--------|
| `Step_1_Core_Foundation.bat` | WSL2 + Kali + Ollama setup | Legacy |
| `Step_2_AI_Python_Env.bat` | Python venv + AI model | Legacy |
| `Step_3_Kali_Tools_Setup.bat` | Kali tools via WSL | Legacy |
| `check_and_install.sh` | Kali tools installer (run inside WSL) | **Active** (used by master installer) |
| `requirements.txt` | Python package dependencies | **Active** |
| `setup_python_kali.sh` | Python setup inside Kali | Legacy |
| `argus_recon_fixed.sh` | Recon engine script (Linux) | Legacy |
| `run_kali_setup.bat` | Manual Kali setup trigger | Legacy |
| `README.md` | This file | - |

> `check_and_install.sh` and `requirements.txt` remain the authoritative source
> for Kali tool installation and Python dependencies respectively. The master
> installer references them directly.

---

## System Requirements

- **OS:** Windows 10 (build 19041+) or Windows 11
- **RAM:** 8 GB minimum (16 GB+ recommended for AI models)
- **Disk:** 20 GB+ free
- **Privileges:** Administrator / elevated

---

## See Also

- `scripts/README.md` - Master installer and launch scripts guide
- `INSTALLATION_GUIDE.md` - Detailed installation reference
- `Argus_Master_Documentation.md` - Full technical documentation
