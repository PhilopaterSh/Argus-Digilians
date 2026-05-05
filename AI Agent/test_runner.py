from argus_agent import run_agent
import os

# Set target
target = "https://www.arrowfilms.com"

print(f"--- Automated Test Run for {target} ---")
try:
    result = run_agent(target)
    print("\n[+] Agent Execution Result:")
    print(result)
except Exception as e:
    print(f"\n[!] Error during execution: {e}")
