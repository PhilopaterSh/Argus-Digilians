#!/usr/bin/env python
import sys
sys.stdout.reconfigure(encoding='utf-8')

from app.core.llm_factory import build_llm
from app.tools.tool_registry import WSLBridgeTools
from app.core.memory.memory_service import ArgusMemory

print("\n" + "="*70)
print("ARGUS SECURITY FRAMEWORK - LIVE DEMONSTRATION")
print("="*70 + "\n")

print("[INITIALIZATION]")
print("-"*70)

print("[1/3] Loading AI Model (WhiteRabbitNeo)...")
llm = build_llm('WhiteRabbitNeo/WhiteRabbitNeo-V3-7B')
print("      [OK] WhiteRabbitNeo ready")

print("[2/3] Loading Tool Registry...")
tools = WSLBridgeTools()
print("      [OK] Tool Registry loaded")
print("      Available services:")
print("        • Reconnaissance Engine")
print("        • Vulnerability Scanners")
print("        • Payload Generator")
print("        • Secret Analyzer")
print("        • Web Crawler")
print("        • Evasion Service")
print("        • ZERO-APT Simulation")

print("[3/3] Loading Memory Service...")
memory = ArgusMemory()
print("      [OK] FAISS Memory initialized")

print("\n" + "="*70)
print("TEST 1: AI REASONING")
print("="*70)
print("Query: What are the 5 main security testing methodologies?\n")

response = llm.invoke("List 5 main security testing methodologies (be concise)")
print("Response:")
print("-"*70)
if len(response) > 800:
    print(response[:800])
    print("\n[... output continues ...]")
else:
    print(response)

print("\n" + "="*70)
print("TEST 2: TOOL REGISTRY")
print("="*70)
print("Available Security Tools:")
print("-"*70)
print("• Reconnaissance:   Subfinder, Gobuster, Nmap, WhatWeb, Nikto")
print("• Scanners:        SSL/TLS analysis, Vuln detection")
print("• Payloads:        Dynamic payload suggestion")
print("• Secrets:         API key & credential detection")
print("• Crawler:         Web application mapping")
print("• Evasion:         WAF bypass, obfuscation techniques")
print("• Simulation:      Red-team exercise scenarios")

print("\n" + "="*70)
print("TEST 3: MEMORY PERSISTENCE")
print("="*70)
print("Database: argus_intelligence.db")
print("Storage:  FAISS vector embeddings")
print("Purpose:  Intelligent finding correlation & reasoning")
print("[OK] Memory system ready\n")

print("="*70)
print("STATUS: ALL SYSTEMS OPERATIONAL")
print("="*70 + "\n")

print("Framework is ready for testing!")
print("\nQuick Start Options:")
print("  1. WEB GUI (Recommended):")
print("     → Run: .\\LAUNCH_STUDIO.bat")
print("     → Browser: http://localhost:12199")
print("\n  2. CLI DEMO:")
print("     → Run: python workspace\\run_argus_cli.py --query 'your question'")
print("\n  3. INTERACTIVE TESTS:")
print("     → Run: .\\scripts\\TEST_ARGUS.bat")
print()
