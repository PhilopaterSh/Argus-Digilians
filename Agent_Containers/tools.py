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
    
    # 1. Check if the tool exists
    if shutil.which("subfinder") is None:
        return "Error: subfinder not installed."

    # 2. Construct the command
    # -d: the target domain
    # -silent: removes the banner and logs so you only get the results
    command = ["subfinder", "-d", domain, "-silent"]

    try:
        # 3. Execute the command
        # capture_output=True grabs stdout and stderr
        # text=True returns strings instead of bytes
        result = subprocess.run(
            command, 
            capture_output=True, 
            text=True, 
            check=True
        )

        # 4. Return the list of subdomains
        # Inside tools.py -> run_ffuf_discovery
        if result.stdout:
            # Adding 'Observation:' at the start of the return can sometimes help the parser
            return f"SUCCESS: FFUF discovered the following paths: {result.stdout.strip()}"
        else:
            return "COMPLETED: No hidden paths were found."

    except subprocess.CalledProcessError as e:
        # Handle cases where subfinder itself fails
        return f"Error running subfinder: {e.stderr}"
    except Exception as e:
        # Handle unexpected errors
        return f"An unexpected error occurred: {str(e)}"

@tool
def run_ffuf_discovery(domain):
    """
    Uses FFUF to brute-force subdomains within the internal network.
    """
    # FFUF replaces 'FUZZ' with words from your list
    wordlist_path = "/app/wordlists/common.txt"
    target_url = f"http://{domain}:3000/FUZZ"
    
    cmd = [
        "ffuf", 
        "-w", wordlist_path, 
        "-u", target_url,
        "-mc", "200,301,302", # Only show successful or redirecting hits
        "-s" # Silent mode so we can parse the output ourselves
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.stdout:
            return f"FFUF found the following active subdomains:\n{result.stdout}"
        else:
            return "FFUF finished scanning. No subdomains responded with 200/301/302."
    except Exception as e:
        return f"Error running FFUF: {str(e)}"