import os
import sys
from dotenv import load_dotenv

# Ensure we can import from core
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from core.tools import WSLBridgeTools

def test_bridge():
    print("--- Testing WSL Bridge & Self-Healing ---")
    bridge = WSLBridgeTools()
    
    # Test 1: Simple command
    print("[*] Testing 'whoami' in WSL...")
    res = bridge.run("whoami")
    print(f"[RESULT] WSL User: {res.strip()}")
    
    # Test 2: Reachability
    print("\n[*] Testing reachability (google.com)...")
    reach = bridge.check_reachability("google.com")
    print(f"[RESULT] {reach}")
    
    # Test 3: Tools check
    print("\n[*] Checking if 'whatweb' is available in WSL...")
    whatweb_check = bridge.run("whatweb --version")
    if "WhatWeb" in whatweb_check:
        print("[OK] WhatWeb is installed.")
    else:
        print("[!!] WhatWeb is NOT found or SSH failed.")

if __name__ == "__main__":
    test_bridge()
