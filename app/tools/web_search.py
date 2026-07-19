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
        """Deeper background/OSINT research beyond a quick search.

        Rewritten 2026-07-19: previously shelled out to a standalone script in
        archive/AI_Agents_Project/ (the only subprocess-based tool in the
        suite - fragile process/encoding handling, a hard dependency on a
        local Ollama model with no guarantee it's running, Arabic-only
        output). That script's own session log showed it failing on most
        real invocations. Now delegates to smart_web_search() in-process -
        strictly more reliable, though it no longer does LLM summarization or
        keeps its own session memory the old script did. Kept as a distinct
        tool name (not merged into Smart_Web_Search) since it is already
        registered and referenced by name in app/core/prompts.py's tool
        guide and covered by tests/test_agent/test_brain_tools.py's expected
        tool-name set.
        """
        return self.smart_web_search(query)
