import subprocess
import os
import paramiko
import re
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

import threading

# Load environment variables from .env file
load_dotenv()

class WSLBridgeTools:
    def __init__(self):
        # Configuration from .env or defaults
        self.host = os.getenv("WSL_HOST", "127.0.0.1")
        self.user = os.getenv("WSL_USER", "kali")
        self.password = os.getenv("WSL_PASS", "kali")
        self.port = int(os.getenv("WSL_PORT", 22))
        self.distro = os.getenv("WSL_DISTRO", "kali-linux")
        self._lock = threading.Lock()

    def _clean_ansi_codes(self, text):
        """Removes ANSI escape codes (colors, bold, etc.) from terminal output."""
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)

    def _ensure_ssh_service(self):
        """Attempts to start SSH service in WSL if it's not running with locking."""
        with self._lock:
            try:
                # Check if port is open locally
                import socket
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(1)
                    if s.connect_ex((self.host, self.port)) == 0:
                        return True
                
                # If closed, try to start it via WSL command
                print(f"[*] Starting SSH service on {self.distro}...")
                start_cmd = f"wsl -d {self.distro} -u root service ssh start"
                subprocess.run(start_cmd, shell=True, capture_output=True, timeout=10)
                # Small grace period
                import time
                time.sleep(1)
                return True
            except:
                return False

    def run(self, command, show_prompt=False):
        """Executes a command on WSL Kali via direct WSL command or SSH fallback."""
        
        # 1. Try direct WSL execution if host is local (much faster/stable)
        if self.host in ["127.0.0.1", "localhost"]:
            try:
                # We use bash -c to ensure environment variables and piping work correctly
                full_cmd = f"wsl -d {self.distro} -u {self.user} bash -c \"{command.replace('\"', '\\\"')}\""
                result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, timeout=60)
                
                final_output = result.stdout if result.stdout else result.stderr
                cleaned = self._clean_ansi_codes(final_output)
                
                if show_prompt:
                    prompt = f"┌──(kali㉿WSL)-[~]\n└─$ {command}\n"
                    return prompt + cleaned
                return cleaned
            except Exception as e:
                # If direct fails, fall back to SSH
                pass

        # 2. SSH Fallback
        max_retries = 3
        for attempt in range(max_retries):
            self._ensure_ssh_service()
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            try:
                client.connect(self.host, port=self.port, username=self.user, password=self.password, timeout=10)
                stdin, stdout, stderr = client.exec_command(command)
                output = stdout.read().decode()
                error = stderr.read().decode()
                client.close()
                
                final_output = output if output else error
                cleaned = self._clean_ansi_codes(final_output)
                
                if show_prompt:
                    prompt = f"┌──(kali㉿{os.getenv('COMPUTERNAME', 'HOST')})-[~]\n└─$ {command}\n"
                    return prompt + cleaned
                return cleaned
            except Exception as e:
                if attempt < max_retries - 1:
                    import time
                    time.sleep(2)
                    continue
                return f"Bridge Exception: {str(e)}\nHint: Try running 'sudo service ssh start' manually in WSL if self-healing failed."

    def check_reachability(self, domain):
        """Checks if a domain is reachable via WSL's network."""
        ping_res = self.run(f"ping -c 1 -W 2 {domain}")
        if "1 received" in ping_res:
            return f"[✓] {domain} is reachable from WSL (ping)"
        
        # HTTP fallback using WSL's curl
        code = self.run(f"curl -s -o /dev/null -w '%{{http_code}}' http://{domain}").strip()
        if code.startswith(('2', '3')):
            return f"[✓] {domain} reachable via WSL HTTP ({code})"
        
        return f"[✗] {domain} is unreachable from WSL"

    def enumerate_subdomains(self, domain):
        """Discovers subdomains using an exhaustive multi-tool suite in WSL."""
        # Clean domain (remove protocol, path, and wildcards)
        clean_domain = domain.replace("https://", "").replace("http://", "").replace("*.", "").split("/")[0]
        
        print(f"[*] Starting MAXIMIZED Subdomain Discovery for: {clean_domain}")
        
        # Define heavy-duty multi-tool command
        # 1. subfinder (Passive/Active)
        # 2. assetfinder (Certificates/OSINT)
        # 3. theHarvester (Search engines/OSINT) - simplified for raw extraction
        # 4. Ph.Sh-Subdomain (Specialized Discovery)
        
        cmds = [
            f"subfinder -d {clean_domain} -silent",
            f"assetfinder --subs-only {clean_domain}",
            f"theHarvester -d {clean_domain} -b crtsh,otx,google,bing -l 100 | grep '@' -v | grep '.' | awk '{{print $1}}' | grep '{clean_domain}'",
            f"Ph.Sh-Subdomain -d {clean_domain}"
        ]
        
        all_subs = []
        for cmd in cmds:
            try:
                res = self.run(cmd)
                all_subs.extend([s.strip().lower() for s in res.split('\n') if s.strip() and clean_domain in s])
            except:
                pass
        
        # Deduplicate and sort
        unique_subs = sorted(list(set(all_subs)))
        
        if not unique_subs:
            return f"[-] No subdomains found for {clean_domain} after exhaustive search."
            
        report = [f"--- 🌐 MAXIMIZED SUBDOMAIN REPORT: {clean_domain} ---"]
        report.append(f"[+] Total Unique Subdomains Found: {len(unique_subs)}")
        report.append(f"[+] Sources Used: subfinder, assetfinder, theHarvester, Ph.Sh-Subdomain")
        report.append("\n" + "\n".join(unique_subs[:40])) # Show first 40 for depth
        if len(unique_subs) > 40:
            report.append(f"\n... and {len(unique_subs) - 40} more.")
            
        return "\n".join(report)

    def recon_suite(self, url):
        """Runs expanded recon using specialized tools in WSL in PARALLEL with limited workers."""
        
        # Extract domain/IP from URL for nmap
        target = url.replace("https://", "").replace("http://", "").split("/")[0]

        # Define tasks for parallel execution
        tasks = [
            ("WAF Detection", f"wafw00f {url}"),
            ("Fingerprinting", f"whatweb -v --color=never --no-errors {url}"),
            ("HTTP Headers", f"curl -sI {url}"),
            ("Service Scan", f"nmap -F --open -sV {target}"),
            ("Content Spider", f"wget --spider --server-response --max-redirect=5 {url} 2>&1")
        ]

        results_map = {}
        
        print(f"[*] Starting Parallel Recon for: {url}")
        
        # Limit to 2 workers to avoid overwhelming the SSH server in WSL
        with ThreadPoolExecutor(max_workers=2) as executor:
            # Map each task name to its future result
            future_to_task = {
                executor.submit(self.run, cmd, True): name 
                for name, cmd in tasks
            }
            
            for future in future_to_task:
                task_name = future_to_task[future]
                try:
                    results_map[task_name] = future.result()
                except Exception as exc:
                    results_map[task_name] = f"[!] Task {task_name} generated an exception: {exc}"

        # Build final report in a logical order
        report = []
        report.append(f"--- 🛡️ PARALLEL ARGUS RECON REPORT: {url} ---")
        
        ordered_keys = ["WAF Detection", "Fingerprinting", "HTTP Headers", "Service Scan", "Content Spider"]
        for key in ordered_keys:
            report.append(f"\n[*] {key}...")
            report.append(results_map.get(key, "No data collected."))
            
        return "\n".join(report)
