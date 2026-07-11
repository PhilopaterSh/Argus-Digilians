"""Manual live-network integration check for CrawlerService/EvasionService
via the WSLBridgeTools facade. Needs a real target and, for advanced_vuln_probe,
live WSL/Kali - not part of the pytest suite (see tests/manual/README.md).

Fixed 2026-07-10: `from core.tools import WSLBridgeTools` was a pre-reorg
import path that no longer exists (`ModuleNotFoundError: No module named
'core'`, confirmed live) - the real path is `app.tools.tool_registry`.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.tools.tool_registry import WSLBridgeTools


def test_integration():
    bridge = WSLBridgeTools()
    target = "http://testasp.vulnweb.com"
    
    print("--- Testing Crawl_Target ---")
    crawl_res = bridge.crawl_target(target)
    print(crawl_res)
    
    print("\n--- Testing Advanced_Vuln_Probe ---")
    probe_res = bridge.advanced_vuln_probe(target)
    print(probe_res)

if __name__ == "__main__":
    test_integration()
