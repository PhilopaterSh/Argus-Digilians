import subprocess
import os
import paramiko
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

    def run(self, command):
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
            
            if error and not output:
                return f"SSH Error: {error}"
            return output
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
        """Runs recon using tools already installed in WSL."""
        # Clean URL
        target = url.replace("https://", "").replace("http://", "").split("/")[0]
        
        results = []
        results.append(f"--- WSL RECON REPORT FOR {url} ---")
        
        # 1. WhatWeb (Installed in WSL)
        results.append("\n[*] Running WSL WhatWeb...")
        results.append(self.run(f"whatweb -v {url}"))
        
        # 2. HTTPX (Installed in WSL)
        results.append("\n[*] Running WSL HTTPX...")
        results.append(self.run(f"echo {url} | httpx -silent -tech-detect"))
        
        return "\n".join(results)
