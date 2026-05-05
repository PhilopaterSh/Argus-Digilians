# Argus AI Agent

This directory contains the first AI Agent model for the Argus framework.

## Overview
`argus_agent.py` is a LangChain-based agent that uses **Ollama** as its brain and **Kali WSL** as its toolset. It can automatically perform web reconnaissance using tools like `WhatWeb`, `curl`, and `wget`.

## Prerequisites
1. **Ollama**: Must be installed and running on your Windows host.
2. **Models**: Ensure you have the models pulled (e.g., `ollama pull dolphin-llama3` or `ollama pull WhiteRabbitNeo/WhiteRabbitNeo-V3-7B`).
3. **Python Environment**: The `ai_env` virtual environment should be set up (run `Library_Python_Requirements\Universal_AI_Setup.bat`).
4. **Kali WSL**: The `kali-linux` distribution must be installed and tools verified (run `Tools\run_check.bat`).

## How to Run
1. Open a terminal (CMD or PowerShell).
2. Activate the virtual environment:
   ```powershell
   # If using the provided ai_env
   .\Library_Python_Requirements\ai_env\Scripts\activate
   ```
3. Navigate to this directory:
   ```powershell
   cd "AI Agent"
   ```
4. Run the agent:
   ```powershell
   python argus_agent.py
   ```

## Example Usage
- "Analyze the technologies used by http://example.com"
- "Fetch the headers of http://google.com"
- "Download the landing page of http://example.org"
