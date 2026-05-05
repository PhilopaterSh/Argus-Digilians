import requests
import shutil
import subprocess
from langchain.tools import tool

@tool
def check_web_headers(url: str) -> str:
    """Checks security headers of a URL."""
    try:
        response = requests.get(url, timeout=5, verify=False)
        headers = response.headers
        security_headers = {h: headers.get(h) for h in ["Server", "X-Powered-By", "Content-Security-Policy"] if h in headers}
        return str(security_headers) if security_headers else "No security headers found."
    except Exception as e:
        return f"Error: {str(e)}"

@tool
def run_subfinder(domain: str) -> str:
    """Runs subfinder on a domain. Ensure subfinder is installed in the container."""
    if shutil.which("subfinder") is None:
        return "Error: subfinder not installed."
    # ... (rest of your subfinder logic)