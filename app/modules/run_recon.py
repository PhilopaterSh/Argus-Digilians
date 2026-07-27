from app.tools.tool_registry import WSLBridgeTools
import sys

def main():
    """Run subdomain enumeration against a target and print the raw result.

    Target is `sys.argv[1]` if given, else "vulnweb.com"."""
    target = sys.argv[1] if len(sys.argv) > 1 else "vulnweb.com"
    bridge = WSLBridgeTools()
    print(f"[*] Enumerating subdomains for: {target}")
    result = bridge.enumerate_subdomains(target)
    print(result)

if __name__ == "__main__":
    main()
