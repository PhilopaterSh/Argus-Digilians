import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from app.core.memory import ArgusMemory

def populate_clean_memory():
    """Wipe the Blackboard and seed it with a fixed set of demo findings/
    entities/relations for testasp.vulnweb.com, for manual GUI testing."""
    mem = ArgusMemory()
    mem.clear_memory()
    
    target = "testasp.vulnweb.com"
    mem.upsert_target(target, priority=10)
    
    # Add Recon findings
    mem.add_finding(target, "nmap", "ports", "80/tcp open http, 8008/tcp open http", "80/tcp and 8008/tcp are open")
    mem.add_finding(target, "whatweb", "tech", "Microsoft-IIS/8.5, ASP.NET", "IIS 8.5 / ASP.NET detected")
    mem.add_finding(target, "crawler", "leak", "Templatize.asp?item=web.config", "Path Traversal confirmed! Sensitive web.config accessed.")
    mem.add_finding(target, "manual", "vulnerability", "showforum.asp?id=1", "Potential SQL Injection detected (Status 500), but blocked by WAF.")
    
    # Add Graph Entities
    mem.upsert_entity("domain", target)
    mem.upsert_entity("tech", "IIS 8.5")
    mem.upsert_entity("tech", "ASP.NET")
    mem.upsert_entity("vulnerability", "Path Traversal")
    mem.upsert_entity("vulnerability", "SQL Injection")
    
    mem.add_relation(target, "IIS 8.5", "USES_TECH")
    mem.add_relation(target, "ASP.NET", "USES_TECH")
    mem.add_relation(target, "Path Traversal", "VULNERABLE_TO")
    
    print("[+] Clean memory populated with current intelligence.")

if __name__ == "__main__":
    populate_clean_memory()
