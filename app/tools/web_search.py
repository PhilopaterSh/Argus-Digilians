from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper


class SmartWebSearch:
    """Responsible only for real-time security web intelligence search."""

    def __init__(self, memory):
        self.memory = memory

    def smart_web_search(self, query: str) -> str:
        print(f"[*] Searching the web for: {query}...")

        try:
            wrapper = DuckDuckGoSearchAPIWrapper(max_results=10)
            search = DuckDuckGoSearchRun(api_wrapper=wrapper)
            results = search.run(query)

            if not results:
                return "No search results found on the web."

            self.memory.upsert_entity(
                "web_intelligence",
                query,
                metadata={"results": results[:500]},
            )

            return f"--- 🌐 WEB INTELLIGENCE REPORT ---\n\n{results}"
        except Exception as exc:
            return f"Web Search Error: {exc}"
