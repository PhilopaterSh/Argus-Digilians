from app.tools.tool_registry import WSLBridgeTools
import sys

def main():
    """Run the full recon suite against a target and print the raw result.

    Target is `sys.argv[1]` if given, else "testasp.vulnweb.com"."""
    target = sys.argv[1] if len(sys.argv) > 1 else "testasp.vulnweb.com"
    bridge = WSLBridgeTools()
    print(f"[*] Starting Comprehensive Recon for: {target}")
    result = bridge.recon_suite(target)
    print(result)

if __name__ == "__main__":
    main()
