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

Not covered by a script in this directory - `ARGUS_INSTALLER.ps1` installs security
tools (nmap, gobuster, subfinder, etc.) and configures the SSH daemon directly via
its own embedded WSL provisioning logic. There is no `Step_3_Kali_Tools_Setup.bat`
or `check_and_install.sh` here to run manually for this step - use the master
installer, or provision Kali tools by hand inside WSL.

---

## Files in This Directory

| File | Purpose | Status |
|------|---------|--------|
| `Step_1_Core_Foundation.bat` | WSL2 + Kali + Ollama setup | Legacy |
| `Step_2_AI_Python_Env.bat` | Python venv + AI model | Legacy |
| `requirements.txt` | Python package dependencies | **Active** - used by CI (`.github/workflows/ci.yml`); the master installer embeds its own copy of these dependencies rather than reading this file at runtime |
| `README.md` | This file | - |

> Corrected 2026-07-19: this table previously listed 5 files that do not exist in
> this directory (`Step_3_Kali_Tools_Setup.bat`, `check_and_install.sh`,
> `setup_python_kali.sh`, `argus_recon_fixed.sh`, `run_kali_setup.bat`) - found
> during a fresh, no-assumptions audit of the whole repo. `requirements.txt` remains
> the authoritative source for Python runtime dependencies.

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
- `../docs/Argus_Master_Documentation.md` - Full technical documentation
