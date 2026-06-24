import unittest
from app.tools.web_search import SmartWebSearch

class TestSmartWebSearch(unittest.TestCase):
    def test_attempt_limit(self):
        # Initialize with dummy memory (None) and set max attempts to 1 for quick test
        searcher = SmartWebSearch(memory=None)
        searcher._max_attempts = 1
        # First call may attempt a real search; we ignore its result.
        try:
            _ = searcher.smart_web_search("dummy query")
        except Exception:
            pass
        # Second call should hit the attempt limit and return the limit message.
        result = searcher.smart_web_search("dummy query")
        self.assertIn("Maximum Smart Web Search attempts reached", result)

if __name__ == "__main__":
    unittest.main()
