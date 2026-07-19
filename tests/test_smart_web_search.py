import unittest
from unittest.mock import MagicMock, patch
from app.tools.web_search import SmartWebSearch


class TestSmartWebSearch(unittest.TestCase):
    @patch("app.tools.web_search.DDGS")
    def test_successful_search_formats_results(self, mock_ddgs_cls):
        """Verify Successful search formats results.
        
        Args:
            mock_ddgs_cls: pytest fixture (see the module's @pytest.fixture definitions).
        """
        mock_ddgs_cls.return_value.__enter__.return_value.text.return_value = [
            {"title": "Result A", "href": "http://a.example", "body": "snippet A"},
        ]
        searcher = SmartWebSearch(memory=None)
        result = searcher.smart_web_search("cve-2024-0001")
        self.assertIn("Result A", result)
        self.assertIn("http://a.example", result)

    @patch("app.tools.web_search.DDGS")
    def test_no_results_returns_explicit_message(self, mock_ddgs_cls):
        """Verify No results returns explicit message.
        
        Args:
            mock_ddgs_cls: pytest fixture (see the module's @pytest.fixture definitions).
        """
        mock_ddgs_cls.return_value.__enter__.return_value.text.return_value = []
        searcher = SmartWebSearch(memory=None)
        result = searcher.smart_web_search("no matches for this")
        self.assertEqual(result, "No results found on the web.")

    @patch("app.tools.web_search.DDGS")
    def test_attempt_limit_blocks_further_searches(self, mock_ddgs_cls):
        """Verify Attempt limit blocks further searches.
        
        Args:
            mock_ddgs_cls: pytest fixture (see the module's @pytest.fixture definitions).
        """
        mock_ddgs_cls.return_value.__enter__.return_value.text.return_value = []
        searcher = SmartWebSearch(memory=None)
        searcher._max_attempts = 1

        _ = searcher.smart_web_search("first query")
        result = searcher.smart_web_search("second query")

        self.assertIn("Maximum Smart Web Search attempts reached", result)
        self.assertEqual(mock_ddgs_cls.call_count, 1, "DDGS must not be invoked past the limit")

    @patch("app.tools.web_search.DDGS")
    def test_failed_search_still_counts_as_an_attempt(self, mock_ddgs_cls):
        """Verify Failed search still counts as an attempt.
        
        Args:
            mock_ddgs_cls: pytest fixture (see the module's @pytest.fixture definitions).
        """
        mock_ddgs_cls.return_value.__enter__.return_value.text.side_effect = RuntimeError("network down")
        searcher = SmartWebSearch(memory=None)
        searcher._max_attempts = 1

        first = searcher.smart_web_search("first query")
        second = searcher.smart_web_search("second query")

        self.assertIn("Web Search Error", first)
        self.assertIn("Maximum Smart Web Search attempts reached", second)

    @patch("app.tools.web_search.DDGS")
    def test_passes_configured_timeout_to_ddgs(self, mock_ddgs_cls):
        """Verify Passes configured timeout to ddgs.
        
        Args:
            mock_ddgs_cls: pytest fixture (see the module's @pytest.fixture definitions).
        """
        mock_ddgs_cls.return_value.__enter__.return_value.text.return_value = []
        searcher = SmartWebSearch(memory=None)
        searcher._timeout = 7
        searcher.smart_web_search("query")
        mock_ddgs_cls.assert_called_once_with(timeout=7)


if __name__ == "__main__":
    unittest.main()
