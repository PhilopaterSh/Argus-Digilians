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
        """Executes a command on WSL Kali using the most direct and stable method."""
        
        # We simplify the command execution to avoid complex escaping issues from Windows to Linux
        # The PATH is now handled inside the native argus_recon script itself
        
        # 1. Direct WSL execution
        if self.host in ["127.0.0.1", "localhost"]:
            try:
                # Use sh -c for simpler parsing
                wsl_cmd = ["wsl", "-d", self.distro, "-u", self.user, "bash", "-c", command]
                result = subprocess.run(wsl_cmd, capture_output=True, text=True, timeout=120, encoding='utf-8', errors='ignore')
                
                final_output = result.stdout if result.stdout else result.stderr
                cleaned = self._clean_ansi_codes(final_output)
                
                if show_prompt:
                    return f"┌──(kali㉿WSL)-[~]\n└─$ {command}\n{cleaned}"
                return cleaned
            except Exception as e:
                pass

        # 2. SSH Fallback
        max_retries = 2
        for attempt in range(max_retries):
            self._ensure_ssh_service()
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                client.connect(self.host, port=self.port, username=self.user, password=self.password, timeout=15)
                stdin, stdout, stderr = client.exec_command(command)
                output = stdout.read().decode()
                error = stderr.read().decode()
                client.close()
                cleaned = self._clean_ansi_codes(output if output else error)
                return cleaned
            except:
                if attempt < max_retries - 1: time.sleep(2)
                
        return "Bridge Error: Command execution failed."

    def check_reachability(self, domain):
        """Checks if a domain is reachable via WSL's network."""
        ping_res = self.run(f"ping -c 1 -W 5 {domain}")
        if "1 received" in ping_res:
            return f"[✓] {domain} is reachable from WSL (ping)"
        
        # HTTP fallback using WSL's curl
        code = self.run(f"curl -s -o /dev/null -w '%{{http_code}}' --connect-timeout 5 http://{domain}").strip()
        if code.startswith(('2', '3')):
            return f"[✓] {domain} reachable via WSL HTTP ({code})"
        
        return f"[✗] {domain} is unreachable or timed out from WSL"

    def enumerate_subdomains(self, domain):
        """Discovers subdomains using the native Argus Recon Engine in WSL."""
        clean_domain = domain.replace("https://", "").replace("http://", "").replace("*.", "").split("/")[0]
        
        print(f"[*] Starting MAXIMIZED Native Discovery for: {clean_domain}")
        
        # Call the native Bash engine created during installation
        # We ensure the script exists first, if not we fall back to a simple check
        check_engine = self.run("command -v argus_recon")
        
        if "/usr/local/bin/argus_recon" in check_engine or "argus_recon" in check_engine:
            print("[+] Using native Argus Recon Engine...")
            return self.run(f"argus_recon {clean_domain}")
        else:
            # Emergency Fallback if engine is missing
            print("[!] Native engine not found. Running basic discovery...")
            return self.run(f"subfinder -d {clean_domain} -silent")

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
