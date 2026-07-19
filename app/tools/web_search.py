import os
import subprocess
try:
    from ddgs import DDGS  # current package name
except ImportError:
    from duckduckgo_search import DDGS  # pre-rename compatibility fallback

from app.core.config import ArgusConfig

class SmartWebSearch:
    """Provides internet search capabilities for CVEs and security research."""

    def __init__(self, memory):
        self.memory = memory
        self._attempts = 0
        cfg = ArgusConfig.load()
        self._max_attempts = cfg.max_web_search_attempts
        self._timeout = cfg.web_search_timeout_seconds

    def smart_web_search(self, query):
        """Search internet for CVEs/Exploits/Security info using DuckDuckGo.

        Bounded by ``max_web_search_attempts`` (config.yaml) for the
        lifetime of this instance - counts failed searches too, so a
        persistent upstream/network failure can't retry indefinitely.
        """
        if self._attempts >= self._max_attempts:
            return "Maximum Smart Web Search attempts reached; skipping further searches."
        self._attempts += 1
        print(f"[*] Searching internet for: {query}")
        try:
            with DDGS(timeout=self._timeout) as ddgs:
                results = list(ddgs.text(query, max_results=5))
                if not results:
                    return "No results found on the web."

                formatted = [f"- {r['title']}: {r['href']}\n  {r['body']}" for r in results]
                return "\n\n".join(formatted)
        except Exception as e:
            return f"Web Search Error: {e}"

    def archive_research_subagent(self, query):
        """Invokes the archived AI_Agents_Project for deep research."""
        print(f"[*] [Argus-Archive] Invoking research subagent for: {query}")
        
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        archive_script = os.path.join(project_root, "archive", "AI_Agents_Project", "smart_search_with_memory.py")
        venv_python = os.path.join(project_root, "Argus_venv", "Scripts", "python.exe")
        
        if not os.path.exists(archive_script):
            return "Error: Archive research script not found at the specified path."

        try:
            cmd = [venv_python, archive_script, query]
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=300)

            if result.returncode != 0:
                return f"Archive Subagent Error: {result.stderr}"

            return f"--- [BRAIN] ARCHIVE RESEARCH REPORT ---\n{result.stdout}"
        except Exception as e:
            return f"Failed to invoke archive subagent: {str(e)}"
