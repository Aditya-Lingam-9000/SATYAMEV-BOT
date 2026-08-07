import unittest
from src.ingestion.url_scraper import scrape_url_content
from src.ingestion.ingestion_manager import IngestionManager

class TestLiveURLVerification(unittest.TestCase):
    """Test suite for Real-Time URL Scraping & Ingestion."""
    
    def test_scrape_wikipedia_url(self):
        """Test real-time scraping of a live Wikipedia URL."""
        res = scrape_url_content("https://en.wikipedia.org/wiki/India")
        self.assertTrue(res["success"])
        self.assertIn("India", res["title"])
        self.assertGreater(len(res["text"]), 100)
        self.assertIn("URL Link:", res["text"])
        
    def test_ingestion_manager_with_url(self):
        """Test IngestionManager auto-scraping of standalone URL claims."""
        manager = IngestionManager()
        success, text, error = manager.ingest_text("https://en.wikipedia.org/wiki/ISRO")
        self.assertTrue(success)
        self.assertIsNotNone(text)
        self.assertGreater(len(text), 100)
        self.assertIn("ISRO", text)

if __name__ == "__main__":
    unittest.main()
