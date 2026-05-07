import subprocess
import os
import re

class WSLTools:
    def __init__(self, distro="kali-linux"):
        self.distro = distro

    def run(self, command):
        try:
            full_cmd = f"wsl -d {self.distro} bash -c \"{command}\""
            res = subprocess.run(full_cmd, capture_output=True, text=True, shell=True)
            output = res.stdout if res.returncode == 0 else f"Error: {res.stderr}"
            return output
        except Exception as e:
            return f"Exception: {str(e)}"

    def check_reachability(self, domain):
        """Checks if a domain is reachable via ping or HTTP."""
        # Ping check
        ping_res = self.run(f"ping -c 1 -W 2 {domain}")
        if "1 packets transmitted, 1 received" in ping_res:
            return f"[✓] {domain} is reachable (ping)"
        
        # HTTP fallback check
        code = self.run(f"curl -s -o /dev/null -w '%{{http_code}}' http://{domain}").strip()
        if code.startswith(('2', '3')):
            return f"[✓] {domain} reachable via HTTP ({code})"
        
        return f"[✗] {domain} is unreachable"

    def analyze_target(self, domain):
        """Advanced analysis logic translated from Bash."""
        reach_status = self.check_reachability(domain)
        if "[✗]" in reach_status:
            return reach_status

        results = [reach_status]
        urls = [f"http://{domain}", f"https://{domain}"]

        for url in urls:
            proto = "http" if url.startswith("http://") else "https"
            clean_name = f"{proto}_{domain.replace('/', '').replace(':', '_')}"
            
            results.append(f"\n--- Analyzing {url} ---")

            # 1. WhatWeb
            results.append("[*] Running WhatWeb...")
            ww_cmd = f"whatweb -v --color=never --no-errors {url} | tee whatweb_{clean_name}.txt"
            results.append(self.run(ww_cmd))

            # 2. HTTPX
            results.append("[*] Running HTTPX...")
            httpx_cmd = f"echo {url} | httpx -silent -title -tech-detect -status-code -location -json -o httpx_{clean_name}.json"
            self.run(httpx_cmd)
            results.append(f"HTTPX analysis saved to httpx_{clean_name}.json")

            # 3. Curl headers
            results.append("[*] Fetching Curl headers...")
            curl_cmd = f"curl -sI {url} > Curl_{clean_name}.txt"
            self.run(curl_cmd)
            results.append(f"Headers saved to Curl_{clean_name}.txt")

            # 4. Wget redirection
            results.append("[*] Analyzing Wget redirection...")
            wget_cmd = f"wget --spider --server-response --max-redirect=5 {url} 2>&1 | tee wget_{clean_name}.txt"
            results.append(self.run(wget_cmd))

        return "\n".join(results)

    def recon_suite(self, url_or_domain):
        """Wrapper to maintain compatibility while using the new advanced logic."""
        # Extract domain if a full URL was provided
        domain = url_or_domain.replace("https://", "").replace("http://", "").split("/")[0]
        return self.analyze_target(domain)
