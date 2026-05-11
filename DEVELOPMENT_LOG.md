# 📓 Argus Development Log & Steps

This document tracks the technical transitions and decisions made during the Argus Security Framework setup.

---

## 🛠️ Step 1: Transitioning to Local-First Workflow
**Date:** May 11, 2026
**Action:** Refactored `core/tools.py`
**Description:** 
Changed the default `WSL_HOST` from `host.docker.internal` (Docker-specific) to `127.0.0.1`.
**Reason:** 
To ensure the Argus AI Studio can communicate with the Kali WSL environment directly via SSH when running from a local Python virtual environment (`.venv`). This removes the dependency on Docker networks for internal tool communication.

---

## 📋 Ongoing Status
- **Environment:** Local Python (`.venv` at Root)
- **Bridge:** SSH via 127.0.0.1 (WSL)
- **Primary Setup Tool:** `Master_Installer.bat` (v2.0)
- **Primary Launch Tool:** `START_Argus_AI.bat` (Root-linked)

---

## 🛠️ Step 3: Self-Healing Bridge & Diagnostic Tools
**Date:** May 11, 2026
**Action:** Updated `core/tools.py`, created `.env`, `.env.example`, and `CHECK_HEALTH.bat`.
**Description:**
1.  **Self-Healing WSL Bridge:** Implemented automated SSH service detection in `core/tools.py`. If the bridge fails to connect, it now attempts to start the SSH service in WSL automatically using background commands.
2.  **Environment Decoupling:** Integrated `python-dotenv`. Created a `.env` file to store sensitive or configurable data (SSH credentials, Distro name, Ollama host) instead of hardcoding them in the scripts.
3.  **Diagnostic Utility:** Created `CHECK_HEALTH.bat`, a standalone tool that verifies the status of Python, the `.venv`, Ollama's API, and the WSL Kali installation in seconds.
**Reason:**
To eliminate common "point-of-failure" issues (like SSH being turned off) and provide users with an easy way to verify system readiness without deep technical knowledge.

