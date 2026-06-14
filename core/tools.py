import subprocess
import os
import paramiko
import re
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper

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
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.98 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Mobile/15E148 Safari/604.1"
        ]

    def _get_stealth_headers(self):
        import random
        ua = random.choice(self.user_agents)
        ip = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
        return f"-H 'User-Agent: {ua}' -H 'X-Forwarded-For: {ip}'"

    def system_self_heal(self, tool_info):
        """Attempts to autonomously install missing libraries or tools (Self-Healing)."""
        print(f"[*] [Argus-SelfHeal] AI requested repair for: {tool_info}")
        
        # 1. Check if it's a Python library
        if "pip install" in tool_info.lower() or "import" in tool_info.lower():
            package = tool_info.split("install")[-1].strip().split()[0] if "install" in tool_info else tool_info.split()[-1]
            print(f"[*] Attempting to install Python package: {package}")
            # Use sys.executable to target the correct venv
            import sys
            cmd = f"{sys.executable} -m pip install -U {package}"
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if res.returncode == 0:
                return f"Successfully installed Python package: {package}. You can now retry the failed action."
            else:
                return f"Failed to install {package}: {res.stderr}"

        # 2. Check if it's a Kali/System tool
        print(f"[*] Attempting to install Kali tool via apt: {tool_info}")
        res = self.run(f"sudo apt-get update && sudo apt-get install -y {tool_info}")
        if "Setting up" in res or "is already the newest version" in res:
            return f"Successfully installed/verified system tool: {tool_info}."
        
        return f"Self-heal failed for {tool_info}. Please check logs or install manually."

    def archive_research_subagent(self, query):
        """Invokes the archived AI_Agents_Project for deep research (CVEs, Web Search, Memory)."""
        print(f"[*] [Argus-Archive] Invoking research subagent for: {query}")
        
        # Determine paths
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        archive_script = os.path.join(project_root, "archive", "AI_Agents_Project", "smart_search_with_memory.py")
        venv_python = os.path.join(project_root, "Argus_venv", "Scripts", "python.exe")
        
        if not os.path.exists(archive_script):
            return "Error: Archive research script not found at the specified path."
            
        # Run the script and capture output
        try:
            cmd = [venv_python, archive_script, query]
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=300)
            
            if result.returncode != 0:
                return f"Archive Subagent Error: {result.stderr}"
                
            return f"--- 🧠 ARCHIVE RESEARCH REPORT ---\n{result.stdout}"
        except Exception as e:
            return f"Failed to invoke archive subagent: {str(e)}"

    def run_specialized_module(self, module_name, target=None):
        """Executes a specialized exploit or reasoning module from the 'modules/' directory."""
        print(f"[*] [Argus-Modules] Invoking specialized module: {module_name}")
        
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        module_path = os.path.join(project_root, "modules", module_name)
        venv_python = os.path.join(project_root, "Argus_venv", "Scripts", "python.exe")
        
        if not os.path.exists(module_path):
            return f"Error: Module '{module_name}' not found in modules/ directory."
            
        try:
            # Set PYTHONPATH to root to ensure imports work
            env = os.environ.copy()
            env["PYTHONPATH"] = f"{project_root};{env.get('PYTHONPATH', '')}"
            
            cmd = [venv_python, module_path]
            if target:
                # Some modules might take target as an argument or we can inject it
                # For now, most of these scripts have the target hardcoded or we can pass it
                cmd.append(target)
                
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=300, env=env)
            
            output = f"--- 🚀 SPECIALIZED MODULE OUTPUT: {module_name} ---\n"
            output += result.stdout
            if result.stderr:
                output += f"\n[!] Errors/Warnings:\n{result.stderr}"
                
            return output
        except Exception as e:
            return f"Failed to execute specialized module: {str(e)}"

    def stealth_run(self, command, delay=True):
        """Executes a command (typically curl) with stealth headers and optional delay."""
        import time
        import random
        if delay:
            time.sleep(random.uniform(1, 3))
        
        # If it's a curl command, inject stealth headers
        if "curl " in command:
            headers = self._get_stealth_headers()
            command = command.replace("curl ", f"curl {headers} ")
            
        return self.run(command)

    def crawl_target(self, url):
        """Discovers internal links and entry points to expand the attack surface."""
        print(f"[*] [Argus-Core] Crawling target: {url}")
        # Use a combination of curl and grep for a lightweight crawler inside WSL
        cmd = f"curl -s -L {url} | grep -oE 'href=\"[^\"]+\"' | cut -d'\"' -f2 | sort -u"
        res = self.run(cmd)
        
        links = [l for l in res.split('\n') if l.strip() and not l.startswith(('#', 'javascript'))]
        
        clean_target = url.replace("https://", "").replace("http://", "").split("/")[0]
        for link in links[:20]:
            self.memory.add_finding(clean_target, "crawler", "link", link, f"Discovered link: {link}")
            
        return f"--- 🕸️ CRAWLER REPORT: {url} ---\nFound {len(links)} links. Top findings:\n" + "\n".join(links[:15])

    def advanced_vuln_probe(self, url):
        """Performs targeted, WAF-evasive probes for SQLi and Path Traversal."""
        print(f"[*] [Argus-Core] Starting Advanced Evasion Probes for: {url}")
        results = []
        clean_target = url.replace("https://", "").replace("http://", "").split("/")[0]

        # 1. Path Traversal Evasion
        traversal_payloads = ["web.config", "..%2f..%2fweb.config", "..%5c..%5cweb.config"]
        for p in traversal_payloads:
            # Use stealth_run for the probe
            cmd = f"curl -s -o /dev/null -w '%{{http_code}} %{{size_download}}' '{url}?item={p}'"
            res = self.stealth_run(cmd)
            if res.startswith('200'):
                results.append(f"[!] Path Traversal Success: {p}")
                self.memory.add_finding(clean_target, "evasion_probe", "vulnerability", f"Traversal: {p}", "Path Traversal Bypass!")

        # 2. SQLi WAF Evasion
        sqli_payloads = ["%u0027", "1'/**/OR/**/1=1/**/--", "1%20OR%201=1"]
        for p in sqli_payloads:
            cmd = f"curl -s -o /dev/null -w '%{{http_code}}' '{url}?id={p}'"
            res = self.stealth_run(cmd)
            if res == "500":
                results.append(f"[!] Potential SQLi (Evasion): {p} (Server Error 500)")
                self.memory.add_finding(clean_target, "evasion_probe", "vulnerability", f"SQLi: {p}", "SQLi potential via WAF evasion")

        if not results:
            return "No vulnerabilities detected with advanced evasion probes."
        
        return "--- 🛡️ ADVANCED EVASION PROBE REPORT ---\n" + "\n".join(results)

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

    def _get_stealth_headers(self):
        import random
        # Modern, randomized User-Agents
        ua_list = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/114.0"
        ]
        ua = random.choice(ua_list)
        ip = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
        return f"-H 'User-Agent: {ua}' -H 'X-Forwarded-For: {ip}' -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8' -H 'Accept-Language: en-US,en;q=0.5'"

    def _is_waf_blocked(self, text):
        """Detects if the target has restricted access based on common block pages."""
        indicators = [
            "Access Temporarily Restricted",
            "possibly malicious",
            "automated security systems",
            "Cloudflare ray ID",
            "IP address as possibly malicious"
        ]
        for ind in indicators:
            if ind.lower() in text.lower():
                return True
        return False

    def run(self, command, show_prompt=False):
        """Executes a command on WSL Kali with enhanced error reporting and WAF protection."""
        
        # 1. Direct WSL execution
        if self.host in ["127.0.0.1", "localhost"]:
            try:
                # Use sh -c for simpler parsing
                wsl_cmd = ["wsl", "-d", self.distro, "-u", self.user, "bash", "-c", command]
                result = subprocess.run(wsl_cmd, capture_output=True, text=True, timeout=600, encoding='utf-8', errors='ignore')
                
                output = result.stdout if result.stdout else result.stderr
                cleaned = self._clean_ansi_codes(output)

                # WAF Detection: If blocked, stop and warn
                if self._is_waf_blocked(cleaned):
                    return f"🛑 [WAF ALERT] Access Restricted! The target has blocked your IP. Suggestion: STOP SCANS IMMEDIATELY and wait 15-30 mins or use a VPN/Proxy."

                if result.returncode != 0:
                    error_msg = result.stderr if result.stderr else result.stdout
                    # Guided Reflection: Detect common issues
                    if "command not found" in error_msg.lower():
                        return f"Error: Tool not installed in WSL. Suggestion: Use 'Run_Kali_Command' with 'sudo apt install -y {command.split()[0]}' to add the missing tool."
                    if "flag provided but not defined" in error_msg.lower() or "invalid option" in error_msg.lower():
                        return f"Error: Syntax Error in command. Suggestion: Use 'Run_Kali_Command' with '{command.split()[0]} --help' to verify the correct parameters for this tool."
                    if "permission denied" in error_msg.lower():
                        return f"Error: Permission denied. Suggestion: Try running with 'sudo' or check file permissions."
                    return f"Error (Code {result.returncode}): {cleaned}"

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
        # Strip protocol and path for tools that need just the hostname (like ping)
        clean_host = domain.replace("https://", "").replace("http://", "").split("/")[0].split(":")[0]
        
        print(f"[*] Checking reachability for: {clean_host}")
        ping_res = self.run(f"ping -c 1 -W 5 {clean_host}")
        if "1 received" in ping_res:
            # Graph Integration: Link Domain to IP
            ip_match = re.search(r'\((.*?)\)', ping_res)
            if ip_match:
                ip = ip_match.group(1)
                self.memory.upsert_entity("domain", clean_host)
                self.memory.upsert_entity("ip", ip)
                self.memory.add_relation(clean_host, ip, "HOSTS")
            return f"[✓] {clean_host} is reachable from WSL (ping)"
        
        # HTTP fallback using WSL's curl
        url = domain if domain.startswith(("http://", "https://")) else f"http://{domain}"
        code = self.run(f"curl -s -o /dev/null -w '%{{http_code}}' --connect-timeout 10 {url}").strip()
        if code.startswith(('2', '3')):
            self.memory.upsert_entity("domain", clean_host)
            return f"[✓] {url} reachable via WSL HTTP ({code})"
        
        # Guided Reflection for failure
        diagnosis = f"[✗] {clean_host} is unreachable.\n"
        diagnosis += "Reflection & Suggestions:\n"
        diagnosis += "1. Target may block ICMP (Ping). Try 'curl' or 'nmap -Pn'.\n"
        diagnosis += "2. Target may only allow HTTPS. Try prefixing with https://.\n"
        diagnosis += "3. DNS Resolution may be failing inside WSL."
        return diagnosis

    def fuzz_sensitive_files(self, url):
        """Perform smart fuzzing for high-value files (.env, .git, config, etc.) with logic-based selection."""
        clean_url = url.rstrip('/')
        print(f"[*] Starting Smart Fuzzing for: {clean_url}")
        
        # Define high-impact payloads for Information Disclosure
        sensitive_paths = [
            ".env", ".git/config", ".git/index", "phpinfo.php", "config.php.bak", 
            "wp-config.php.save", ".htaccess", "server-status", ".ssh/id_rsa",
            "api/.env", "backup.sql", "database.sql", ".aws/credentials",
            "composer.json", "package.json", ".npmrc"
        ]
        
        results = []
        def check_path(path):
            full_url = f"{clean_url}/{path}"
            # Use curl -I to check headers and -L to follow redirects (smart bypass check)
            cmd = f"curl -s -L -I -w '%{{http_code}} %{{size_download}}' -o /dev/null {full_url}"
            res = self.run(cmd).strip()
            if res.startswith(('200', '206')): # OK or Partial Content
                return f"[!] FOUND: {full_url} (Status: {res})"
            elif res.startswith('403'):
                return f"[?] PROTECTED: {full_url} (403 Forbidden - Potential Bypass Target)"
            return None

        with ThreadPoolExecutor(max_workers=5) as executor:
            findings = list(executor.map(check_path, sensitive_paths))
            results = [f for f in findings if f]

        if not results:
            return "No common sensitive files found. Target seems well-configured or using a WAF."
        
        report = "--- 📁 SENSITIVE FILE DISCOVERY REPORT ---\n"
        report += "\n".join(results)
        return f"```\n{report}\n```"

    def analyze_secrets(self, url):
        """Fetches the page body and JS files to look for leaked secrets using Regex."""
        print(f"[*] Analyzing for Secrets & PII in: {url}")
        
        # Fetch body
        body = self.run(f"curl -s -L {url} | head -c 50000") # Limit to 50k for context safety
        clean_target = url.replace("https://", "").replace("http://", "").split("/")[0]

        patterns = {
            "Email": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            "API Key (Generic)": r'(?:key|api|token|secret|auth)[-_=:]+([a-zA-Z0-9]{20,})',
            "Google API Key": r'AIza[0-9A-Za-z-_]{35}',
            "AWS Access Key": r'AKIA[0-9A-Z]{16}',
            "S3 Bucket": r'[a-z0-9.-]+\.s3\.amazonaws\.com',
            "Firebase URL": r'[a-z0-9-]+\.firebaseio\.com'
        }
        
        found = []
        for name, regex in patterns.items():
            matches = re.findall(regex, body, re.IGNORECASE)
            if matches:
                # Deduplicate and limit
                unique_matches = list(set(matches))[:5]
                found.append(f"[!] {name}: {', '.join(unique_matches)}")
                # Graph Integration: Link Target to Secret
                for m in unique_matches:
                    self.memory.upsert_entity("secret", m, metadata={"category": name})
                    self.memory.add_relation(clean_target, m, "EXPOSES")

        if not found:
            return "No obvious secrets or credentials leaked in the landing page HTML."
        
        report = "--- 🔍 LEAKED SECRETS ANALYSIS ---\n" + "\n".join(found)
        return f"```\n{report}\n```"

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
            process_targets = self.prioritize_targets(list(set(alive_targets)))[:3] # Reduced for deeper analysis
            # Ensure base target is always there
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
            
            # Advanced Analysis: Sensitive Files & Secrets
            fuzz_res = self.fuzz_sensitive_files(target_url)
            secrets_res = self.analyze_secrets(target_url)

            headers_res = self.run(f"curl -sI {target_url}")
            
            target_intel = {
                "waf": waf_res,
                "fingerprint": fingerprint_res,
                "services": services_res,
                "fuzzing": fuzz_res,
                "secrets": secrets_res,
                "headers": headers_res
            }
            
            # Extract Summaries for Blackboard
            waf_sum = [l for l in waf_res.split('\n') if "[+]" in l]
            waf_sum = waf_sum[0] if waf_sum else "Not detected"
            self.memory.add_finding(target, "wafw00f", "waf", waf_res, waf_sum)
            
            # Graph Integration: WAF
            if "detected" in waf_sum.lower() and "[" in waf_sum:
                waf_match = re.search(r'\[(.*?)\]', waf_sum)
                if waf_match:
                    waf_name = waf_match.group(1)
                    self.memory.upsert_entity("waf", waf_name)
                    self.memory.add_relation(target, waf_name, "PROTECTED_BY")

            tech_sum = [l for l in fingerprint_res.split('\n') if "Summary :" in l or "Detected Plugins:" in l]
            tech_sum = " ".join(tech_sum[:2]) if tech_sum else "Unknown"
            self.memory.add_finding(target, "whatweb", "tech", fingerprint_res, tech_sum)
            
            # Graph Integration: Tech
            tech_matches = re.findall(r'\[ (.*?) \]', fingerprint_res)
            if tech_matches:
                for tech_item in tech_matches[0].split(','):
                    t_name = tech_item.strip().split('[')[0].strip()
                    if t_name:
                        self.memory.upsert_entity("tech", t_name)
                        self.memory.add_relation(target, t_name, "USES_TECH")

            ports_sum = [l for l in services_res.split('\n') if "/tcp" in l and "open" in l]
            ports_sum = ", ".join(ports_sum) if ports_sum else "No open ports found"
            self.memory.add_finding(target, "nmap", "ports", services_res, ports_sum)
            
            if "FOUND:" in fuzz_res:
                self.memory.add_finding(target, "fuzzer", "leak", fuzz_res, "Sensitive files found!")
                # Graph Integration: Files
                file_matches = re.findall(r'FOUND: (.*?)\s\(', fuzz_res)
                for f_url in file_matches:
                    f_name = f_url.split('/')[-1]
                    self.memory.upsert_entity("file", f_name, metadata={"url": f_url})
                    self.memory.add_relation(target, f_name, "HAS_FILE")
            
            if "[!]" in secrets_res:
                self.memory.add_finding(target, "analyzer", "secrets", secrets_res, "Secrets leaked in HTML")

            self.memory.add_finding(target, "curl", "headers", headers_res, "HTTP Headers captured")
            
            report_section = [f"\n=== 🎯 TARGET: {target} ==="]
            report_section.append(f"\n[*] WAF Analysis...\n{waf_sum}")
            report_section.append(f"\n[*] Deep Fuzzing & Secrets...\n{fuzz_res}\n{secrets_res}")
            report_section.append(f"\n[*] Fingerprinting...\n{tech_sum}")
            
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

    def prioritize_targets(self, targets):
        """Sorts targets by potential value (shorter domains, root domains first)."""
        return sorted(targets, key=len)

    def enumerate_subdomains(self, domain):
        """Fast subdomain discovery using the internal 5-phase pipeline."""
        print(f"[*] Starting deep subdomain enumeration for: {domain}")
        # Call the native argus_recon command inside Kali
        res = self.run(f"argus_recon {domain}")
        
        # Integration: Save discovered subdomains to targets table
        if "TOP VERIFIED SUBDOMAINS:" in res:
            try:
                # Simple parser to find domains in the report
                capture = False
                for line in res.split('\n'):
                    if "TOP VERIFIED SUBDOMAINS:" in line:
                        capture = True
                        continue
                    if capture and "INFRASTRUCTURE POINTERS" in line:
                        break
                    if capture and line.strip() and not line.startswith("["):
                        sub = line.strip().replace("https://", "").replace("http://", "")
                        self.memory.upsert_target(sub, parent_domain=domain)
            except Exception as e:
                print(f"[!] Error parsing/saving subdomains: {e}")

        return f"```\n{res}\n```"

    def save_json_report(self, domain, data):
        """Saves structured intel to a JSON file for persistence."""
        os.makedirs("reports", exist_ok=True)
        # Sanitize domain for filename
        safe_domain = re.sub(r'[^\w\.-]', '_', domain)
        path = f"reports/intel_{safe_domain}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(path, "w") as f:
            json.dump(data, f, indent=4)
        print(f"[+] Structured intelligence saved to: {path}")
        return path

    def get_intelligence_summary(self, _=None):
        """Retrieves the current state of knowledge from the Blackboard (Shared Memory)."""
        summary = self.memory.get_blackboard_summary()
        return f"```json\n{summary}\n```"

    def query_knowledge_graph(self, _=None):
        """Returns complex relationships and commonalities across targets (Knowledge Graph)."""
        print("[*] Querying Knowledge Graph for cross-target insights...")
        insights = self.memory.get_graph_insights()
        return f"```\n{insights}\n```"

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
        # We use a smart grep with hex encoding to avoid shell parsing issues with backticks
        cmd = f"cat \"/opt/payloads/PayloadsAllTheThings/{matched_dir}/README.md\" | grep -A 5 -P '\\x60\\x60\\x60' | head -n 30"
        payload_data = self.run(cmd)
        
        reflection = f"--- 🛠️ SUGGESTED PAYLOADS/METHODOLOGY FOR {matched_dir} ---\n"
        reflection += payload_data if payload_data else "No sample payloads found in README. Try looking for specific bypass files in that directory."
        reflection += f"\nSource: PayloadsAllTheThings/{matched_dir}"
        
        return reflection

    def smart_web_search(self, query):
        """Performs a real-time web search for security intelligence (CVEs, exploits, tech info)."""
        print(f"[*] Searching the web for: {query}...")
        try:
            wrapper = DuckDuckGoSearchAPIWrapper(max_results=10)
            search = DuckDuckGoSearchRun(api_wrapper=wrapper)
            results = search.run(query)
            
            if not results:
                return "No search results found on the web."
            
            # Save to memory for potential future use
            self.memory.upsert_entity("web_intelligence", query, metadata={"results": results[:500]}) # Truncated for meta
            
            return f"--- 🌐 WEB INTELLIGENCE REPORT ---\n\n{results}"
        except Exception as e:
            return f"Web Search Error: {str(e)}"

    def run_nikto(self, url):
        """Runs Nikto vulnerability scanner inside Kali against a web target."""
        print(f"[*] Starting Nikto Vulnerability Scan for: {url}")
        
        # Ensure the output directory exists
        output_dir = "reports/nikto"
        os.makedirs(output_dir, exist_ok=True)
        
        # Construct filename
        clean_target = url.replace("https://", "").replace("http://", "").rstrip('/').replace("/", "_")
        timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        filename = f"nikto_{clean_target}_{timestamp}.txt"
        output_path = f"{output_dir}/{filename}"
        
        # -nointeractive: no prompts, -maxtime: safety cap
        cmd = f"nikto -h {url} -nointeractive -maxtime 120s -Format txt -o {output_path}"
        res = self.run(cmd)
        
        # Parse and save findings
        findings = [l for l in res.split('\n') if l.strip().startswith("+")]
        if findings:
            target_for_mem = url.replace("https://", "").replace("http://", "").split("/")[0]
            for f in findings:
                self.memory.add_finding(target_for_mem, "nikto", "vulnerability", f, "Potential vulnerability detected")
        
        return f"--- 🛠️ NIKTO VULNERABILITY REPORT (Saved to {output_path}) ---\n{res}"

    def run_ffuf_discovery(self, url):
        """Runs FFUF for fast directory discovery inside Kali. Optimized for 120s timeout."""
        clean_url = url.rstrip('/')
        wordlist = "/usr/share/seclists/Discovery/Web-Content/common.txt"
        
        print(f"[*] Starting FFUF Path Discovery for: {clean_url}")
        # Added -t 50 for speed and -maxtime 110 to stay within bridge timeout
        cmd = f"ffuf -w {wordlist} -u {clean_url}/FUZZ -mc 200,301,302 -s -t 50 -maxtime 110"
        res = self.run(cmd)
        
        if res.strip():
            paths = res.strip().splitlines()
            clean_target = url.replace("https://", "").replace("http://", "").split("/")[0]
            for p in paths[:20]: 
                self.memory.add_finding(clean_target, "ffuf", "path", p, "Hidden path discovered")
            return f"--- 📁 FFUF DISCOVERY REPORT ---\nDiscovered {len(paths)} paths. Top findings:\n" + "\n".join(paths[:40])
        
        return "FFUF completed. No notable paths found or timeout reached."

    def run_kali_command(self, command):
        """Executes ANY command directly in the Kali WSL environment. Use this for manual reconnaissance or fixing tool issues."""
        print(f"[*] [Argus-Kali] Executing manual command: {command}")
        
        # Ensure Go bins are in PATH for the command execution
        full_command = f"export PATH=$PATH:/home/kali/go/bin:/home/kali/.pdtm/go/bin && {command}"
        res = self.run(full_command, show_prompt=True)
        
        # Integration: If the command output looks like subdomains, attempt to save them
        if len(res.splitlines()) > 2:
            potential_subs = re.findall(r'(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}', res)
            if potential_subs:
                # Deduplicate and limit
                unique_subs = list(set(potential_subs))
                print(f"[*] [Argus-Kali] Auto-detected {len(unique_subs)} potential subdomains in output.")
                # We don't know the parent domain here easily, so we just upsert them
                for sub in unique_subs[:50]:
                    self.memory.upsert_target(sub)

        return f"--- 🖥️ KALI TERMINAL OUTPUT ---\n{res}"


