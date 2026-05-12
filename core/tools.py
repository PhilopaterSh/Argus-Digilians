import subprocess
import os
import paramiko
import re
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

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

    def _clean_ansi_codes(self, text):
        """Removes ANSI escape codes (colors, bold, etc.) from terminal output."""
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)

    def _ensure_ssh_service(self):
        """Attempts to start SSH service in WSL if it's not running."""
        try:
            # Check if port is open locally
            import socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2)
                if s.connect_ex((self.host, self.port)) == 0:
                    return True
            
            # If closed, try to start it via WSL command
            print(f"[*] SSH service appears down. Attempting self-healing on {self.distro}...")
            start_cmd = f"wsl -d {self.distro} -u root service ssh start"
            subprocess.run(start_cmd, shell=True, capture_output=True)
            return True
        except:
            return False

    def run(self, command, show_prompt=False):
        """Executes a command on WSL Kali via SSH with self-healing."""
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

    def recon_suite(self, url):
        """Runs expanded recon using specialized tools in WSL in PARALLEL."""
        
        # Define tasks for parallel execution (Nikto removed for speed)
        tasks = [
            ("WAF Detection", f"wafw00f {url}"),
            ("Fingerprinting", f"whatweb -v --color=never --no-errors {url}"),
            ("HTTP Headers", f"curl -sI {url}"),
            ("Content Spider", f"wget --spider --server-response --max-redirect=5 {url} 2>&1")
        ]

        results_map = {}
        
        print(f"[*] Starting Parallel Recon for: {url}")
        
        with ThreadPoolExecutor(max_workers=len(tasks)) as executor:
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
        
        ordered_keys = ["WAF Detection", "Fingerprinting", "HTTP Headers", "Content Spider"]
        for key in ordered_keys:
            report.append(f"\n[*] {key}...")
            report.append(results_map.get(key, "No data collected."))
            
        return "\n".join(report)
