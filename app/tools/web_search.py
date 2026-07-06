import os
import subprocess
from duckduckgo_search import DDGS

class SmartWebSearch:
    """Provides internet search capabilities for CVEs and security research."""

    def __init__(self, memory):
        self.memory = memory

    def smart_web_search(self, query):
        """Search internet for CVEs/Exploits/Security info using DuckDuckGo."""
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
