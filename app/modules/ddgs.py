# Compatibility shim: prefer the new 'ddgs' package, fall back to 'duckduckgo_search'.
# Import DDGS from here in other modules: from app.modules.ddgs import DDGS
try:
    from ddgs import DDGS  # new package name
except ImportError:
    from duckduckgo_search import DDGS  # legacy fallback

__all__ = ["DDGS"]
