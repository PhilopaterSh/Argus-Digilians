# Argus-Digilians Project Setup Guide

This project is a comprehensive security analysis and AI Agent system.

---

## Quick Start (Recommended)
For the easiest and fastest setup, use the Master Installer. This single file will automatically run all three setup phases for you.

**Path:** Master_Installer.bat (Found in the root directory)
- Action: Right-click and "Run as Administrator".
- Purpose: Automatically executes Step 1, Step 2, and Step 3 in sequence.

---

## Automated Synchronization: The Intelligence Loop (V9.0)
To ensure all team members are working on the latest version and to secure your findings automatically, use the Argus Secure Sync tool.

**Path:** Argus_Secure_Sync.exe
- Action: Double-click to run.
- Workflow: 
  1. Secure and Transmit: Automatically saves your local work and uploads it to your private device branch (e.g., argus/Your-PC-Name). This keeps your work safe in your personal cloud vault.
  2. Global Integration: Automatically downloads and merges the latest updates from the global main branch into your workspace.
  3. Smart Conflict Resolution: If a file is modified by both you and a teammate, the system intelligently prioritizes your local findings to prevent data loss.
- Note: You MUST run this file regularly to maintain synchronization and avoid data divergence.

### Example Scenario:
Imagine you write a new SQL Injection script on your PC. At the same time, a teammate uploads a new Password Wordlist to the main project.
- When you run the sync tool:
  - Your SQL script is instantly backed up to your private branch.
  - The Wordlist is downloaded to your PC.
  - Result: You now have the latest version of everything (your script + their wordlist) ready for use!

---

## Manual Setup Steps
If you prefer to run the setup phases individually, follow these steps in order:

### Step 1: Host Preparation and Kali Linux Installation
Run the following script to prepare your Windows host. This script fixes potential system corruption, enables required Windows features (WSL, Virtual Machine Platform), and installs the Kali Linux distribution.

**Path:** How to satup/setup_kali.bat
- Action: Right-click and "Run as Administrator".
- Purpose: Ensures the Windows foundation is ready for WSL 2 and Kali Linux.

---

## Step 2: Web Analysis Tools Verification
Once Kali Linux is installed and running, use this script to verify and install the essential web scanning tools (WhatWeb, Curl, Wget) inside the Linux environment.

**Path:** Tools/run_check.bat
- Action: Double-click to run.
- Purpose: Automates the internal configuration of Kali Linux and ensures all core tools are present.

---

## Step 3: Python AI Environment Setup
This final step prepares the Python environment required for the AI Agents. It will automatically check for Python 3.12, install it if missing, create an isolated virtual environment, and install all necessary AI libraries (LangChain, FAISS, etc.).

**Path:** Library_Python_Requirements/Universal_AI_Setup.bat
- Action: Double-click to run.
- Purpose: Creates a "Zero-Touch" environment for the AI Agent to function on the Windows host or within WSL.

---

## Summary of Components
- How to satup: Contains scripts for initial OS and WSL configuration.
- Tools: Contains web scanning scripts and technical documentation.
- Library_Python_Requirements: Contains the universal installer and the list of Python dependencies.

For more technical details on the scripts or libraries, refer to the .md files within the respective folders.

---
Maintained by: Argus Security Framework Team
Last Documentation Update: May 2026
