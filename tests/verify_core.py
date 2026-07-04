from core.tools import WSLBridgeTools

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
