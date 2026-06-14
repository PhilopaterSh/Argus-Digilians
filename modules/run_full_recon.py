from core.tools import WSLBridgeTools
import sys

def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "testasp.vulnweb.com"
    bridge = WSLBridgeTools()
    print(f"[*] Starting Comprehensive Recon for: {target}")
    result = bridge.recon_suite(target)
    print(result)

if __name__ == "__main__":
    main()
