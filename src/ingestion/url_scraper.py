"""
Real-Time URL Content Scraper Module
====================================

Extracts article titles, metadata, and core paragraph text from live web URLs in real time.
Zero external dependencies (uses standard library html.parser + requests).
"""

import re
import urllib.parse
import logging
import requests
from html.parser import HTMLParser
from typing import Dict, Any

logger = logging.getLogger("satyamev_bot.ingestion.url_scraper")


class SimpleArticleExtractor(HTMLParser):
    """HTML Parser to extract clean article text and titles while ignoring noise tags."""
    
    def __init__(self):
        super().__init__()
        self.title = ""
        self.in_title = False
        self.in_ignored_tag = False
        self.ignored_tags = {"script", "style", "nav", "footer", "header", "aside", "noscript", "svg"}
        self.paragraphs = []
        self.current_tag = ""
        self.current_text = []

    def handle_starttag(self, tag, attrs):
        self.current_tag = tag.lower()
        if self.current_tag in self.ignored_tags:
            self.in_ignored_tag = True
        if self.current_tag == "title":
            self.in_title = True

    def handle_endtag(self, tag):
        tag_lower = tag.lower()
        if tag_lower in self.ignored_tags:
            self.in_ignored_tag = False
        if tag_lower == "title":
            self.in_title = False
        if tag_lower in {"p", "h1", "h2", "h3", "article", "section"} and self.current_text:
            block_text = "".join(self.current_text).strip()
            if len(block_text) > 25 and not self.in_ignored_tag:
                self.paragraphs.append(block_text)
            self.current_text = []

    def handle_data(self, data):
        if self.in_ignored_tag:
            return
        if self.in_title:
            self.title += data
        else:
            cleaned_data = data.strip()
            if cleaned_data:
                self.current_text.append(" " + cleaned_data)


def scrape_url_content(url: str, timeout: int = 6, max_chars: int = 2500) -> Dict[str, Any]:
    """
    Scrape article title and main body text from a live URL in real time.
    
    Args:
        url: Raw web page URL to scrape
        timeout: HTTP request timeout in seconds (default: 6)
        max_chars: Maximum character budget for extracted body text (default: 2500)
        
    Returns:
        Dict containing success status, URL, title, formatted text content, and errors.
    """
    raw_url = url.strip()
    if not raw_url.startswith("http"):
        raw_url = "http://" + raw_url
        
    logger.info(f"[URLScraper] Scraping real-time content from URL: {raw_url}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    
    try:
        response = requests.get(raw_url, headers=headers, timeout=timeout, allow_redirects=True)
        if response.status_code != 200:
            logger.warning(f"[URLScraper] HTTP {response.status_code} when requesting {raw_url}")
            return {
                "success": False,
                "url": raw_url,
                "error": f"HTTP {response.status_code}",
                "title": "",
                "text": raw_url
            }
            
        content_type = response.headers.get("Content-Type", "")
        if "text/html" not in content_type and "application/xhtml" not in content_type:
            logger.info(f"[URLScraper] Non-HTML content-type '{content_type}' for {raw_url}")
            return {
                "success": False,
                "url": raw_url,
                "error": f"Non-HTML content type: {content_type}",
                "title": "",
                "text": raw_url
            }
            
        parser = SimpleArticleExtractor()
        parser.feed(response.text)
        
        clean_title = re.sub(r'\s+', ' ', parser.title).strip()
        
        seen_p = set()
        unique_paragraphs = []
        for p in parser.paragraphs:
            clean_p = re.sub(r'\s+', ' ', p).strip()
            if clean_p not in seen_p and len(clean_p) > 25:
                seen_p.add(clean_p)
                unique_paragraphs.append(clean_p)
                
        article_body = " ".join(unique_paragraphs)[:max_chars]
        
        if not article_body and not clean_title:
            logger.warning(f"[URLScraper] No article body or title extracted from {raw_url}")
            return {
                "success": False,
                "url": raw_url,
                "error": "No article text extracted",
                "title": "",
                "text": raw_url
            }
            
        formatted_content = f"URL Link: {raw_url}\n"
        if clean_title:
            formatted_content += f"Article Title: {clean_title}\n"
        if article_body:
            formatted_content += f"Extracted Article Content: {article_body}"
            
        logger.info(f"[URLScraper] Successfully extracted {len(formatted_content)} chars from {raw_url}")
        return {
            "success": True,
            "url": raw_url,
            "title": clean_title,
            "text": formatted_content,
            "raw_body": article_body,
            "error": None
        }
        
    except Exception as e:
        logger.warning(f"[URLScraper] Failed to scrape URL {raw_url}: {str(e)}")
        return {
            "success": False,
            "url": raw_url,
            "error": str(e),
            "title": "",
            "text": raw_url
        }
