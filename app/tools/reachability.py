import re

from tools.utils import clean_host


class ReachabilityService:
    """Responsible only for target reachability checks."""

    def __init__(self, runner, memory):
        self.runner = runner
        self.memory = memory

    def check_reachability(self, domain: str) -> str:
        clean_target = clean_host(domain)

        print(f"[*] Checking reachability for: {clean_target}")
        ping_res = self.runner.run(f"ping -c 1 -W 5 {clean_target}")

        if "1 received" in ping_res:
            ip_match = re.search(r"\((.*?)\)", ping_res)
            if ip_match:
                ip_address = ip_match.group(1)
                self.memory.upsert_entity("domain", clean_target)
                self.memory.upsert_entity("ip", ip_address)
                self.memory.add_relation(clean_target, ip_address, "HOSTS")
            return f"[✓] {clean_target} is reachable from WSL (ping)"

        url = domain if domain.startswith(("http://", "https://")) else f"http://{domain}"
        code = self.runner.run(
            f"curl -s -o /dev/null -w '%{{http_code}}' --connect-timeout 10 {url}"
        ).strip()

        if code.startswith(("2", "3")):
            self.memory.upsert_entity("domain", clean_target)
            return f"[✓] {url} reachable via WSL HTTP ({code})"

        diagnosis = f"[✗] {clean_target} is unreachable.\n"
        diagnosis += "Reflection & Suggestions:\n"
        diagnosis += "1. Target may block ICMP (Ping). Try 'curl' or 'nmap -Pn'.\n"
        diagnosis += "2. Target may only allow HTTPS. Try prefixing with https://.\n"
        diagnosis += "3. DNS Resolution may be failing inside WSL."
        return diagnosis
