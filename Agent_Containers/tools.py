import requests
import shutil
import subprocess
from langchain.tools import tool


@tool
def check_web_headers(url: str) -> str:
    """
    Checks the HTTP security headers of a target URL.
    Returns relevant headers like Server, X-Powered-By, and Content-Security-Policy.
    Input: full URL with port, e.g. 'http://juice-shop:3000'
    """
    try:
        response = requests.get(url, timeout=5, verify=False)
        headers = response.headers
        interesting = ["Server", "X-Powered-By", "Content-Security-Policy",
                       "X-Frame-Options", "Strict-Transport-Security", "X-XSS-Protection"]
        found = {h: headers[h] for h in interesting if h in headers}
        if found:
            lines = [f"  {k}: {v}" for k, v in found.items()]
            return "Security headers found:\n" + "\n".join(lines)
        return "No notable security headers found."
    except Exception as e:
        return f"Error checking headers: {str(e)}"


@tool
def run_subfinder(domain: str) -> str:
    """
    Runs subfinder to enumerate subdomains of a given domain.
    Only works on bare domain names (e.g. 'example.com'), not URLs with ports.
    Input: bare domain name only, e.g. 'juice-shop'
    """
    if shutil.which("subfinder") is None:
        return "Error: subfinder binary not found in PATH. Ensure it is installed in the Dockerfile."

    command = ["subfinder", "-d", domain, "-silent"]

    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=60)
        if result.stdout.strip():
            return f"Subfinder discovered the following subdomains:\n{result.stdout.strip()}"
        return "Subfinder completed. No subdomains were discovered."
    except subprocess.TimeoutExpired:
        return "Error: subfinder timed out after 60 seconds."
    except subprocess.CalledProcessError as e:
        return f"Error running subfinder: {e.stderr}"
    except Exception as e:
        return f"Unexpected error running subfinder: {str(e)}"


@tool
def run_ffuf_discovery(domain: str) -> str:
    """
    Uses FFUF to brute-force directories and hidden paths on a web server.
    Input: bare domain name only, e.g. 'juice-shop'. Port 3000 is used automatically.
    """
    wordlist_path = "/app/wordlists/common.txt"
    target_url = f"http://{domain}:3000/FUZZ"

    cmd = [
        "ffuf",
        "-w", wordlist_path,
        "-u", target_url,
        "-mc", "200,301,302",
        "-s"  # Silent: output discovered paths only, one per line
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.stdout.strip():
            paths = result.stdout.strip().splitlines()
            # Cap at 40 results so the LLM context doesn't overflow
            capped = paths[:40]
            summary = f"FFUF discovered {len(paths)} active path(s) (showing first {len(capped)}):"
            formatted = "\n".join(f"  - /{p}" for p in capped)
            return f"{summary}\n{formatted}"
        return "FFUF completed. No paths responded with HTTP 200/301/302."
    except subprocess.TimeoutExpired:
        return "Error: FFUF timed out after 120 seconds."
    except Exception as e:
        return f"Error running FFUF: {str(e)}"

# ── 4. Nmap Port & Service Scan ───────────────────────────────────────────────
 
@tool
def run_nmap(host: str) -> str:
    """
    Runs an Nmap scan to discover open ports, services, and versions on the target host.
    Input: bare hostname or IP, e.g. 'juice-shop' (no http://, no port suffix).
    """
    if shutil.which("nmap") is None:
        return "Error: nmap binary not found in PATH. Ensure it is installed in the Dockerfile."
 
    # -sV: version detection  -T4: faster timing  --open: only open ports
    # -p-: all 65535 ports would be too slow in a lab; common ports is fine
    cmd = ["nmap", "-sV", "-T4", "--open", "-p", "1-10000", host]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        output = result.stdout.strip()
        if not output:
            return "Nmap produced no output."
        # Trim to keep the LLM context manageable: skip Nmap header boilerplate
        lines = output.splitlines()
        relevant = [l for l in lines if not l.startswith("Starting Nmap") and not l.startswith("Nmap done")]
        return "Nmap scan results:\n" + "\n".join(relevant[:60])
    except subprocess.TimeoutExpired:
        return "Error: Nmap timed out after 180 seconds."
    except Exception as e:
        return f"Error running Nmap: {str(e)}"
 
 
# ── 5. Nikto Web Server Scanner ───────────────────────────────────────────────
 
@tool
def run_nikto(url: str) -> str:
    """
    Runs Nikto to scan a web server for common vulnerabilities and misconfigurations.
    Input: full URL with port, e.g. 'http://juice-shop:3000'
    """
    if shutil.which("nikto") is None:
        return "Error: nikto binary not found in PATH. Ensure it is installed in the Dockerfile."
 
    # -nointeractive: no prompts  -maxtime: safety cap  -output -: stdout
    cmd = ["nikto", "-h", url, "-nointeractive", "-maxtime", "90s", "-Format", "txt"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        output = (result.stdout + result.stderr).strip()
        if not output:
            return "Nikto produced no output."
        # Keep the most interesting lines; skip Nikto banner clutter
        lines = output.splitlines()
        findings = [l for l in lines if l.strip().startswith("+")]
        if findings:
            return "Nikto findings:\n" + "\n".join(findings[:50])
        return "Nikto completed. No notable findings flagged."
    except subprocess.TimeoutExpired:
        return "Error: Nikto timed out after 120 seconds."
    except Exception as e:
        return f"Error running Nikto: {str(e)}"
 
 
# ── 6. Gobuster Directory Brute-Force ─────────────────────────────────────────
 
@tool
def run_gobuster(domain: str) -> str:
    """
    Runs Gobuster in directory mode to enumerate hidden paths on the web server.
    Complements FFUF with a different engine and user-agent.
    Input: bare domain name only, e.g. 'juice-shop'. Port 3000 is used automatically.
    """
    if shutil.which("gobuster") is None:
        return "Error: gobuster binary not found in PATH. Ensure it is installed in the Dockerfile."
 
    wordlist_path = "/app/wordlists/common.txt"
    target_url = f"http://{domain}:3000"
 
    cmd = [
        "gobuster", "dir",
        "-u", target_url,
        "-w", wordlist_path,
        "-s", "200,301,302,403",   # status codes to flag
        "-t", "30",                # 30 threads
        "-q",                      # quiet: findings only
        "--no-error",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        output = result.stdout.strip()
        if not output:
            return "Gobuster completed. No paths found."
        lines = output.splitlines()
        capped = lines[:40]
        return (
            f"Gobuster found {len(lines)} path(s) (showing first {len(capped)}):\n"
            + "\n".join(f"  {l}" for l in capped)
        )
    except subprocess.TimeoutExpired:
        return "Error: Gobuster timed out after 180 seconds."
    except Exception as e:
        return f"Error running Gobuster: {str(e)}"
 
 
# ── 7. run_whatweb Tech-Stack Fingerprinting ───────────────────────────────
 
@tool
def run_whatweb(url: str) -> str:
    """
    Fingerprints the technology stack using WhatWeb.
    Identifies frameworks, CMS, servers, JS libraries, and more.
    Input: full URL with port, e.g. 'http://juice-shop:3000'
    """
    if shutil.which("whatweb") is None:
        return "Error: whatweb not found in PATH. Ensure it is installed in the Dockerfile."

    cmd = ["whatweb", "--color=never", "-a", "3", url]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        output = result.stdout.strip()
        return f"WhatWeb results:\n{output}" if output else "WhatWeb returned no results."
    except subprocess.TimeoutExpired:
        return "Error: WhatWeb timed out after 60 seconds."
    except Exception as e:
        return f"Error running WhatWeb: {str(e)}"
 