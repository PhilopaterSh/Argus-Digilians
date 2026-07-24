from app.tools.tool_registry import WSLBridgeTools
import sys

def main():
    """Probe a fixed list of common ASP endpoints on testasp.vulnweb.com via
    curl, printing each path's HTTP status code."""
    bridge = WSLBridgeTools()
    target = "testasp.vulnweb.com"
    paths = ["index.aspx", "login.aspx", "admin.aspx", "config.aspx", "search.aspx", "categories.aspx", "product.aspx"]
    print(f"[*] Mapping entry points for {target}...")
    for p in paths:
        res = bridge.run(f"curl -o /dev/null -s -w '%{{http_code}}' http://{target}/{p}")
        print(f"{p}: {res}")

if __name__ == "__main__":
    main()
