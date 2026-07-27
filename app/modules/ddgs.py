try:
    from ddgs import DDGS  # current package name
except ImportError:
    from duckduckgo_search import DDGS  # pre-rename compatibility fallback
