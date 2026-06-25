# 🛡️ Argus-Digilians Security Framework

Argus is a professional-grade security analysis system and an autonomous AI Agent studio, bridging Windows accessibility with Kali Linux's offensive power.

---

## 🚀 QUICK START
If you have just cloned this repository, follow these two steps:

### 1. Full Installation (First Time Only)
Run the **Master Installer** as Administrator to set up WSL, Kali, Python, and AI Models.
- **File:** `INSTALL_EVERYTHING.bat`
- **Note:** A system restart may be required after WSL installation.

### 2. Launch the Studio (Daily Use)
Start the entire ecosystem with a single click.
- **File:** `LAUNCH_STUDIO.bat`
- **Action:** Launches the AI engine, activates the SSH bridge, and opens your browser at `http://localhost:12199`.

---

## 🔍 SYSTEM DIAGNOSTICS
Not sure if everything is working? Run the health check:
- **File:** `CHECK_HEALTH.bat`
- **Verified Components:** Python Environment, Ollama (AI Engine), WSL (Kali Linux), and SSH Bridge.

---

## 📂 Project Structure

```text
Argus/
├── 📄 README.md                           # Project overview
├── 📄 Argus_Master_Documentation.md       # Technical reference
├── .env.example                           # Environment template
├── .gitignore                             # Git ignore rules
│
├── 📁 scripts/                            # Operational scripts & launchers
│   ├── LAUNCH_STUDIO.bat                  # 🚀 One-click system start
│   ├── LAUNCH_CLI.bat                     # CLI agent launcher
│   ├── CHECK_HEALTH.bat                   # 🔍 System health diagnostics
│   ├── INSTALL_EVERYTHING.ps1             # Master installer
│   └── run_argus_cli.py                   # CLI entry point
│
├── 📁 app/                                # Main application core
│   ├── GUI/                               # 🖥️ Streamlit Web Command Center
│   ├── core/                              # 🧠 AI Brain & Memory Logic
│   ├── tools/                             # Security tools & modules
│   └── modules/                           # Specialized exploit scripts
│
├── 📁 Setup/                              # 🌐 Installation scripts & resources
│   ├── Step_1_Host_Setup.bat
│   ├── Step_2_Python_AI.bat
│   ├── Step_3_Kali_Tools.bat
│   └── helpers/
│
├── 📁 docs/                               # Documentation
│   ├── README.md                          # Doc index
│   ├── STRUCTURE_GUIDE.md                 # Organization guide
│   ├── GEMINI.md                          # Development standards
│   └── arc42.md                           # Architecture documentation
│
├── 📁 tests/                              # 🧪 Test suites
│   └── test_*.py                          # Test modules
│
├── 📁 data/                               # Data & databases
│   └── argus_intelligence.db              # AI cache database
│
├── 📁 bin/                                # Executables
│   └── Argus_Secure_Sync.exe
│
├── 📁 logs/                               # Application logs
│   └── .gitkeep
│
└── 📁 archive/                            # Legacy/deprecated code
```

---

## 🧩 Key Features
*   **Parallel Reconnaissance:** Executes multiple tools (WhatWeb, Wafw00f, Nikto, etc.) simultaneously for maximum speed.
*   **AI Intelligence:** Integrated with **WhiteRabbitNeo** for advanced security reasoning.
*   **WSL Bridge:** Securely executes offensive tools inside a native Linux environment via SSH.
*   **Report Export:** Download comprehensive security reports in Markdown format with one click.

---
*Maintained by: Argus Security Framework Team | May 2026*
