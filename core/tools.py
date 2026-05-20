import subprocess
import os
import paramiko
import re
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

import threading

# Load environment variables from .env file
load_dotenv()

from core.memory import ArgusMemory

class WSLBridgeTools:
    def __init__(self):
        # Configuration from .env or defaults
        self.host = os.getenv("WSL_HOST", "127.0.0.1")
        self.user = os.getenv("WSL_USER", "kali")
        self.password = os.getenv("WSL_PASS", "kali")
        self.port = int(os.getenv("WSL_PORT", 22))
        self.distro = os.getenv("WSL_DISTRO", "kali-linux")
        self._lock = threading.Lock()
        self.last_recon_results = None
        self.memory = ArgusMemory()

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
                start_cmd = f"wsl -d {self.distro} -u root bash -c \"mkdir -p /run/sshd && /usr/sbin/sshd\""
                subprocess.run(start_cmd, shell=True, capture_output=True, timeout=10)
                # Small grace period
                import time
                time.sleep(1)
                return True
            except:
                return False

    def run(self, command, show_prompt=False):
        """Executes a command on WSL Kali with enhanced error reporting (Guided Reflection)."""
        
        # 1. Direct WSL execution
        if self.host in ["127.0.0.1", "localhost"]:
            try:
                # Use sh -c for simpler parsing
                wsl_cmd = ["wsl", "-d", self.distro, "-u", self.user, "bash", "-c", command]
                result = subprocess.run(wsl_cmd, capture_output=True, text=True, timeout=600, encoding='utf-8', errors='ignore')
                
                if result.returncode != 0:
                    error_msg = result.stderr if result.stderr else result.stdout
                    # Guided Reflection: Detect common issues
                    if "command not found" in error_msg.lower():
                        return f"Error: Tool not installed in WSL. Suggestion: Use 'apt install' to add the missing tool."
                    if "permission denied" in error_msg.lower():
                        return f"Error: Permission denied. Suggestion: Try running with 'sudo' or check file permissions."
                    return f"Error (Code {result.returncode}): {self._clean_ansi_codes(error_msg)}"

                final_output = result.stdout if result.stdout else result.stderr
                cleaned = self._clean_ansi_codes(final_output)
                
                if show_prompt:
                    return f"┌──(kali㉿WSL)-[~]\n└─$ {command}\n{cleaned}"
                return cleaned
            except subprocess.TimeoutExpired:
                return f"Error: Command timed out after 600s. Suggestion: The target might be slow or blocking the scan. Try narrowing the scope or increasing the timeout."
            except Exception as e:
                return f"Bridge Error: {str(e)}"

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
                if error and not output:
                    return f"SSH Command Error: {error}"
                return self._clean_ansi_codes(output if output else error)
            except Exception as e:
                if attempt < max_retries - 1: time.sleep(2)
                else: return f"SSH Bridge Error: {str(e)}"
                
        return "Bridge Error: Command execution failed."

    def check_reachability(self, domain):
        """Checks if a domain is reachable via WSL's network with guided failure analysis."""
        ping_res = self.run(f"ping -c 1 -W 5 {domain}")
        if "1 received" in ping_res:
            return f"[✓] {domain} is reachable from WSL (ping)"
        
        # HTTP fallback using WSL's curl
        code = self.run(f"curl -s -o /dev/null -w '%{{http_code}}' --connect-timeout 10 http://{domain}").strip()
        if code.startswith(('2', '3')):
            return f"[✓] {domain} reachable via WSL HTTP ({code})"
        
        # Guided Reflection for failure
        diagnosis = f"[✗] {domain} is unreachable.\n"
        diagnosis += "Reflection & Suggestions:\n"
        diagnosis += "1. Target may block ICMP (Ping). Try 'curl' or 'nmap -Pn'.\n"
        diagnosis += "2. Target may only allow HTTPS. Try prefixing with https://.\n"
        diagnosis += "3. DNS Resolution may be failing inside WSL."
        return diagnosis

    def enumerate_subdomains(self, domain):
        """Discovers subdomains using the native Argus Recon Engine in WSL."""
        clean_domain = domain.replace("https://", "").replace("http://", "").replace("*.", "").split("/")[0]
        
        print(f"[*] Starting MAXIMIZED Native Discovery for: {clean_domain}")
        
        # Call the native Bash engine created during installation
        check_engine = self.run("command -v argus_recon")
        
        report = ""
        if "/usr/local/bin/argus_recon" in check_engine or "argus_recon" in check_engine:
            print("[+] Using native Argus Recon Engine...")
            report = self.run(f"argus_recon {clean_domain}")
        else:
            # Emergency Fallback if engine is missing
            print("[!] Native engine not found. Running basic discovery...")
            report = self.run(f"subfinder -d {clean_domain} -silent")

        if "Total Verified Alive (Web): 0" in report:
            return f"{report}\nReflection: No subdomains found. The target might be using wildcard DNS or hiding behind a strong CDN. Suggestion: Try manual brute-force with a larger wordlist if critical."

        # Save to memory
        alive_targets = []
        capture = False
        for line in report.split('\n'):
            if "TOP VERIFIED SUBDOMAINS:" in line:
                capture = True
                continue
            if capture and "INFRASTRUCTURE POINTERS" in line:
                capture = False
                break
            if capture and line.strip() and not line.startswith("["):
                t = line.strip().replace("https://", "").replace("http://", "")
                alive_targets.append(t)
                self.memory.upsert_target(t, parent_domain=clean_domain)
        
        return report

    def prioritize_targets(self, targets):
        """Sorts targets based on security interest keywords."""
        priority_keywords = ['api', 'admin', 'portal', 'dev', 'test', 'staging', 'checkout', 'vpn', 'internal', 'v1', 'v2', 'auth', 'login']
        
        # Scoring system
        scored_targets = []
        for target in targets:
            score = 0
            # Higher score for sensitive keywords
            for kw in priority_keywords:
                if kw in target.lower():
                    score += 10
            # Lower score for common static/cdn assets
            if any(static in target.lower() for static in ['cdn', 'static', 'assets', 'images']):
                score -= 5
            scored_targets.append((score, target))
            
            # Update priority in memory
            self.memory.upsert_target(target, priority=score)
            
        # Sort by score descending
        scored_targets.sort(key=lambda x: x[0], reverse=True)
        return [t[1] for t in scored_targets]

    def save_json_report(self, domain, data):
        """Saves findings to a structured JSON file in the Reports directory."""
        import json
        from datetime import datetime
        
        report_dir = "Reports"
        if not os.path.exists(report_dir):
            os.makedirs(report_dir)
            
        clean_name = domain.replace(".", "_").replace("/", "_")
        file_path = os.path.join(report_dir, f"{clean_name}.json")
        
        report_data = {
            "domain": domain,
            "scan_time": datetime.now().isoformat(),
            "results": data
        }
        
        with open(file_path, "w") as f:
            json.dump(report_data, f, indent=4)
        return file_path

    def recon_suite(self, url, selected_targets=None):
        """Runs expanded recon with smart target prioritization and parallel execution."""
        
        # 1. Initial Target Setup
        base_target = url.replace("https://", "").replace("http://", "").split("/")[0]
        root_domain = base_target.replace("www.", "")
        
        print(f"[*] Starting Intelligence Gathering for: {root_domain}")
        
        # 2. Step 1: Deep Subdomain Discovery (if no targets provided)
        subdomain_report = ""
        if not selected_targets:
            subdomain_report = self.enumerate_subdomains(root_domain)
            
            # Parse alive subdomains
            alive_targets = []
            capture = False
            for line in subdomain_report.split('\n'):
                if "TOP VERIFIED SUBDOMAINS:" in line:
                    capture = True
                    continue
                if capture and "INFRASTRUCTURE POINTERS" in line:
                    capture = False
                    break
                if capture and line.strip() and not line.startswith("["):
                    # Clean the target (remove http/https for tool compatibility)
                    t = line.strip().replace("https://", "").replace("http://", "")
                    alive_targets.append(t)
            
            # Smart Heuristic Prioritization
            process_targets = self.prioritize_targets(list(set(alive_targets)))[:5]
            # Ensure base target is always there if not in top 5
            if base_target not in process_targets:
                process_targets.append(base_target)
        else:
            process_targets = selected_targets

        # 3. Step 2: Parallel Recon for each identified target
        intel_data = {}
        final_results = []
        final_results.append(f"--- 🛡️ COMPREHENSIVE ARGUS RECON REPORT: {root_domain} ---")
        final_results.append(f"[+] Focus Area: {', '.join(process_targets)}\n")
        
        def analyze_single_target(target):
            target_url = f"https://{target}" if not target.startswith(("http://", "https://")) else target
            
            waf_res = self.run(f"wafw00f {target_url}")
            fingerprint_res = self.run(f"whatweb -v --color=never --no-errors {target_url}")
            services_res = self.run(f"nmap -F --open -sV {target}")
            
            # Reflection for Nmap
            if "No open ports found" in services_res or "0 hosts up" in services_res:
                services_res += "\nReflection: Nmap found no open ports. This could be due to a firewall blocking pings. Suggestion: Try scanning again with the -Pn flag to skip host discovery."

            headers_res = self.run(f"curl -sI {target_url}")
            
            target_intel = {
                "waf": waf_res,
                "fingerprint": fingerprint_res,
                "services": services_res,
                "headers": headers_res
            }
            
            # Extract Summaries for Blackboard
            waf_sum = [l for l in waf_res.split('\n') if "[+]" in l]
            waf_sum = waf_sum[0] if waf_sum else "Not detected"
            self.memory.add_finding(target, "wafw00f", "waf", waf_res, waf_sum)
            
            tech_sum = [l for l in fingerprint_res.split('\n') if "Summary :" in l or "Detected Plugins:" in l]
            tech_sum = " ".join(tech_sum[:2]) if tech_sum else "Unknown"
            self.memory.add_finding(target, "whatweb", "tech", fingerprint_res, tech_sum)
            
            ports_sum = [l for l in services_res.split('\n') if "/tcp" in l and "open" in l]
            ports_sum = ", ".join(ports_sum) if ports_sum else "No open ports found"
            self.memory.add_finding(target, "nmap", "ports", services_res, ports_sum)
            
            self.memory.add_finding(target, "curl", "headers", headers_res, "HTTP Headers captured")
            
            report_section = [f"\n=== 🎯 TARGET: {target} ==="]
            report_section.append(f"\n[*] WAF Analysis...\n{waf_res}")
            report_section.append(f"\n[*] Fingerprinting...\n{fingerprint_res}")
            report_section.append(f"\n[*] Service Scan...\n{services_res}")
            
            return target, target_intel, "\n".join(report_section)

        with ThreadPoolExecutor(max_workers=3) as executor:
            future_results = list(executor.map(analyze_single_target, process_targets))
            for target_name, data, text_report in future_results:
                intel_data[target_name] = data
                final_results.append(text_report)
            
        # 4. Save Structured Data
        json_path = self.save_json_report(root_domain, intel_data)
        
        full_text_report_str = "\n".join(final_results)
        if subdomain_report:
            full_text_report_str += "\n\n=== 📋 COMPLETE SUBDOMAIN INVENTORY ===\n" + subdomain_report
        
        return full_text_report_str

    def get_intelligence_summary(self, _=None):
        """Retrieves the current state of knowledge from the Blackboard (Shared Memory)."""
        return self.memory.get_blackboard_summary()

    def suggest_payloads(self, vulnerability_type):
        """Searches PayloadsAllTheThings for relevant payloads based on the vulnerability type."""
        mapping = {
            "xss": "XSS Injection",
            "sqli": "SQL Injection",
            "nosqli": "NoSQL Injection",
            "ssrf": "Server Side Request Forgery",
            "ssti": "Server Side Template Injection",
            "lfi": "File Inclusion",
            "rfi": "File Inclusion",
            "rce": "Command Injection",
            "cmd": "Command Injection",
            "xxe": "XXE Injection",
            "traversal": "Directory Traversal",
            "csrf": "Cross-Site Request Forgery",
            "jwt": "JSON Web Token",
            "upload": "Upload Insecure Files",
            "api": "API Key Leaks",
            "headers": "Methodology and Resources"
        }
        
        # Clean input and find best match
        v_type = vulnerability_type.lower().strip()
        matched_dir = None
        for key, folder in mapping.items():
            if key in v_type:
                matched_dir = folder
                break
        
        if not matched_dir:
            # Try a fuzzy search using find
            search_res = self.run(f"find /opt/payloads/PayloadsAllTheThings -maxdepth 1 -type d -iname '*{v_type}*'").strip()
            if search_res and "/opt/payloads" in search_res:
                matched_dir = search_res.split('/')[-1]
            else:
                return f"No specific payloads found for '{vulnerability_type}'. Suggestion: Search PayloadsAllTheThings manually or check generic methodology."

        print(f"[*] Fetching payloads from: {matched_dir}")
        
        # Read the README.md or the first .md file in the directory to get "The Juice"
        # We use a smart grep to find actual code blocks/payloads
        cmd = f"cat \"/opt/payloads/PayloadsAllTheThings/{matched_dir}/README.md\" | grep -A 5 '```' | head -n 30"
        payload_data = self.run(cmd)
        
        reflection = f"--- 🛠️ SUGGESTED PAYLOADS/METHODOLOGY FOR {matched_dir} ---\n"
        reflection += payload_data if payload_data else "No sample payloads found in README. Try looking for specific bypass files in that directory."
        reflection += f"\nSource: PayloadsAllTheThings/{matched_dir}"
        
        return reflection

