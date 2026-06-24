import os
import socket
import subprocess
import warnings
import yaml
# Updated import: prefer ddgs, fallback to duckduckgo_search if needed
try:
    from ddgs import DDGS  # ddgs is the new package name
except ImportError:
    from duckduckgo_search import DDGS  # backward compatibility
# Suppress repetitive RuntimeWarning about package rename
warnings.filterwarnings(
    "ignore",
    message=r".*duckduckgo_search.*has been renamed to ddgs.*",
    category=RuntimeWarning,
)

# ── Load config & apply socket timeout ────────────────────────────────────────────
_CFG_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'config.yaml')
_cfg: dict = {}
if os.path.exists(_CFG_PATH):
    try:
        with open(_CFG_PATH, 'r') as _f:
            _cfg = yaml.safe_load(_f) or {}
    except Exception:
        pass
_WEB_TIMEOUT: int = int(_cfg.get("web_search_timeout_seconds", 10))
socket.setdefaulttimeout(_WEB_TIMEOUT)

class SmartWebSearch:
    """Provides internet search capabilities for CVEs and security research.
    Limits the number of search attempts to avoid endless retries.
    """

    def __init__(self, memory):
        self.memory = memory
        self._attempts = 0
        self._max_attempts = 3



    def smart_web_search(self, query):
        """Search internet for CVEs/Exploits/Security info using DuckDuckGo (ddgs).
        Returns result or a message if maximum attempts are exceeded.
        """
        # Enforce attempt limit
        if self._attempts >= self._max_attempts:
            return "Maximum Smart Web Search attempts reached; skipping further searches."
        self._attempts += 1
        print(f"[*] Searching internet for: {query}")
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=5))
                if not results:
                    return "No results found on the web."
                
                formatted = [f"- {r['title']}: {r['href']}\n  {r['body']}" for r in results]
                return "\n\n".join(formatted)
        except Exception as e:
            return f"Web Search Error: {e}"

    def archive_research_subagent(self, query):
        """Invokes the archived AI_Agents_Project for deep research."""
        print("[*] [Argus-Archive]    agent = create_react_agent(")
        # The actual creation of the agent would require proper imports and context.
        # For now, we keep this as a placeholder.
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        archive_script = os.path.join(project_root, "archive", "AI_Agents_Project", "smart_search_with_memory.py")
        venv_python = os.path.join(project_root, "Argus_venv", "Scripts", "python.exe")
        archive_script = os.path.join(project_root, "archive", "AI_Agents_Project", "smart_search_with_memory.py")
        venv_python = os.path.join(project_root, "Argus_venv", "Scripts", "python.exe")
        
        if not os.path.exists(archive_script):
            return "Error: Archive research script not found at the specified path."

        try:
            cmd = [venv_python, archive_script, query]
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=300)

            if result.returncode != 0:
                return f"Archive Subagent Error: {result.stderr}"

            return f"--- 🧠 ARCHIVE RESEARCH REPORT ---\n{result.stdout}"
        except Exception as e:
            return f"Failed to invoke archive subagent: {str(e)}"
