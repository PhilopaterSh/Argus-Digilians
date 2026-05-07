# 🛡️ Argus-Digilians Project Framework

This project is a comprehensive security analysis system and an autonomous AI Agent studio.

---

## 🚀 THE MASTER BUTTON (Start Here)
To start the entire system with one click, use the Master Launcher:

**Path:** `START_Argus_AI.bat` (Root Directory)
- **Action:** Double-click to run.
- **Purpose:** 
  1. Checks and starts the AI Engine (Ollama).
  2. Activates the Python environment.
  3. Launches the Security Studio in your browser on `http://localhost:12189`.

---

## 📂 Complete Project Structure (Project Map)

```text
Argus/
├── START_Argus_AI.bat          # 🚀 MASTER BUTTON (Single-click Start)
├── Master_Installer.bat        # 🛠️ Main Setup Utility (Full Installation)
├── Argus_Secure_Sync.exe       # 🔄 Synchronization & Backup Tool
├── README.md                   # 📖 Main Project Documentation
├── core/                       # 🧠 Modular Intelligence (The "Brain")
├── GUI/                        # 🖥️ Graphical Interfaces & Launchers
├── AI Agent/                   # 🤖 Original AI Logic & Prototypes
├── Tools/                      # 🛠️ WSL Bridge & Automation Scripts
├── How to satup/               # 📖 Documentation & Installation Guides
└── Library_Python_Requirements/ # 📦 Dependencies & Environment
```

---

## 🛠️ Installation & Setup
If this is your first time, run the **Master Installer** (`Master_Installer.bat`) as Administrator to prepare the system.

---

## 🔄 Synchronization
Use **Argus_Secure_Sync.exe** to keep your work updated with the GitHub repository.

---

## 🧩 Component Breakdown
*   **core/**: Handles AI reasoning (LangChain) and advanced reconnaissance. Now includes an **Advanced Recon Suite**:
    *   **Reachability Check:** Ping + HTTP fallback verification.
    *   **Dual Protocol:** Automatic analysis of both HTTP and HTTPS versions.
    *   **Tooling:** Verbose WhatWeb, HTTPX Tech Detection, and Wget redirection mapping.
*   **GUI/**: Web-based Command Center for real-time monitoring and AI report generation.

---

## 🛡️ Agent Protocols & Safety
To ensure efficiency and accuracy, the Argus AI Agent follows a strict execution protocol:

1.  **Reachability First (Mandatory):** Before any analysis, the Agent MUST execute the `Check_Reachability` tool. 
2.  **Conditional Execution:** If the target is unreachable (Ping fails and HTTP status is non-2xx/3xx), the Agent will terminate the mission immediately to save resources.
3.  **Local Execution:** All tools and LLM inferences are performed on the local host/WSL environment.

---
*Maintained by: Argus Security Framework Team | May 2026*
