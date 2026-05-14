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
├── LAUNCH_STUDIO.bat           # 🚀 One-click system start
├── INSTALL_EVERYTHING.bat      # 🛠️ Full environment setup
├── CHECK_HEALTH.bat            # 🔍 System health diagnostics
├── README.md                   # 📖 Documentation
├── 01_Infrastructure_Setup/    # 🌐 Host & WSL
├── 02_AI_Environment/          # 📦 Dependencies
├── core/                       # 🧠 AI Brain & WSL Bridge Logic
├── GUI/                        # 🖥️ Streamlit Web Command Center
├── Tools/                      # 🛠️ Kali Linux Automation Scripts
└── Workflows/                  # 📊 Mappings & Diagrams
```

---

## 🧩 Key Features
*   **Parallel Reconnaissance:** Executes multiple tools (WhatWeb, Wafw00f, Nikto, etc.) simultaneously for maximum speed.
*   **AI Intelligence:** Integrated with **WhiteRabbitNeo** for advanced security reasoning.
*   **WSL Bridge:** Securely executes offensive tools inside a native Linux environment via SSH.
*   **Report Export:** Download comprehensive security reports in Markdown format with one click.

---
*Maintained by: Argus Security Framework Team | May 2026*
