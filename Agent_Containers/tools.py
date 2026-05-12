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