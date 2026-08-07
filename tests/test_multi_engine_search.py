import unittest
import os
from src.brain.tools import WebSearchTool

class TestMultiEngineSearch(unittest.TestCase):
    """Test suite for Parallel Multi-Engine WebSearchTool."""
    
    def setUp(self):
        self.api_key = os.getenv("TAVILY_API_KEY", "tvly-test-key")
        self.search_tool = WebSearchTool(api_key=self.api_key)
        
    def test_google_news_rss(self):
        """Test Google News RSS search without API key."""
        results = self.search_tool._search_google_news("India budget 2026", max_results=3)
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0].source_engine, "Google News RSS")
        self.assertTrue(results[0].url.startswith("http"))
        
    def test_wikipedia_api(self):
        """Test Wikipedia REST API search without API key."""
        results = self.search_tool._search_wikipedia("Indian Space Research Organisation", max_results=2)
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0].source_engine, "Wikipedia")
        self.assertIn("wikipedia.org", results[0].url)
        
    def test_duckduckgo_search(self):
        """Test DuckDuckGo search fallback without API key."""
        results = self.search_tool._search_duckduckgo("Reserve Bank of India interest rates", max_results=2)
        self.assertIsInstance(results, list)
        
    def test_parallel_claim_evidence(self):
        """Test multi-engine parallel search aggregation."""
        evidence = self.search_tool.search_claim_evidence("ISRO Chandrayaan mission")
        self.assertIn("supporting", evidence)
        self.assertIn("contradicting", evidence)
        self.assertGreater(len(evidence["supporting"]), 0)
        print(f"\n[Test Success] Total supporting/news items retrieved: {len(evidence['supporting'])}")
        for item in evidence["supporting"][:4]:
            print(f"  - [{item.source_engine}] {item.title} -> {item.url}")

if __name__ == "__main__":
    unittest.main()
