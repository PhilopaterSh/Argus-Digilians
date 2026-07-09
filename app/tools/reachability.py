import os
import json
import re
from datetime import datetime

from app.tools.utils import normalize_domain_for_memory

class ReachabilityService:
    def __init__(self, runner, memory):
        self.runner = runner
        self.memory = memory

    def check_reachability(self, domain):
        """Verifies if a target is reachable using ping from WSL."""
        print(f"[*] Checking reachability for: {domain}")
        # ping needs a bare host, not a scheme/port/path-qualified URL - a
        # target like "https://scanme.nmap.org" was passed to ping as-is,
        # which always failed with "Name or service not known" regardless
        # of whether the host was actually reachable, misleading the agent
        # into reporting a live target as "DOWN".
        host = normalize_domain_for_memory(domain)
        res = self.runner.run(f"ping -c 4 {host}")
        if "4 received" in res or "3 received" in res:
            self.memory.upsert_target(domain)
            return f"Target {domain} is REACHABLE.\n{res}"
        return f"Target {domain} seems DOWN or unreachable.\n{res}"

class JSONReportWriter:
    def save_json_report(self, domain, data):
        """Saves structured intel to a JSON file for persistence."""
        os.makedirs("reports", exist_ok=True)
        safe_domain = re.sub(r'[^\w\.-]', '_', domain)
        path = f"reports/intel_{safe_domain}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(path, "w") as f:
            json.dump(data, f, indent=4)
        print(f"[+] Structured intelligence saved to: {path}")
        return path
