"""
Tool Definitions for Fact-Checking Agent

Implements the tools available to the agent:
1. Web search tool (via Tavily API) - for real-time fact verification
2. Vector database tool (placeholder) - for knowledge base retrieval
3. Claim parser tool - for structured claim extraction
"""

import logging
import json
from typing import Optional, List, Dict, Any
from tavily import TavilyClient
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class SearchResult(BaseModel):
    """Single search result from web search."""
    title: str = Field(description="Result title")
    url: str = Field(description="Result URL")
    snippet: str = Field(description="Content snippet")
    source_engine: str = Field(default="Tavily", description="Search provider engine name")
    relevance_score: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Relevance score (0-1)"
    )


class WebSearchTool:
    """
    Multi-Engine Real-Time Web Search Tool.
    
    Combines Tavily API with free, non-API key search providers:
    - Tavily API
    - Google News RSS (Free Indian & Global headlines)
    - Wikipedia REST API (Free background facts)
    - DuckDuckGo Search (Free web search)
    
    Executes all searches concurrently in parallel via ThreadPoolExecutor for minimal latency.
    """
    
    def __init__(self, api_key: str, max_results: int = 5):
        """
        Initialize web search tool.
        
        Args:
            api_key: Tavily API key
            max_results: Maximum results per search (5-10 recommended)
        """
        if not api_key:
            raise ValueError("Tavily API key is required")
        
        self.client = TavilyClient(api_key=api_key)
        self.max_results = min(max(max_results, 1), 10)  # Clamp to 1-10
        logger.info(f"WebSearchTool initialized with Parallel Multi-Engine search (max_results={self.max_results})")
    
    def search(
        self,
        query: str,
        topic: str = "general",
        include_answer: bool = True
    ) -> tuple[bool, Optional[List[SearchResult]], Optional[str]]:
        """
        Perform web search with Tavily API.
        
        Args:
            query: Search query (will be automatically optimized by Tavily)
            topic: Search topic - "general" or "news"
            include_answer: Whether to include AI-generated answer
        
        Returns:
            Tuple: (success: bool, results: Optional[List[SearchResult]], error: Optional[str])
        """
        import time
        max_retries = 3
        backoff_factor = 2
        last_exception = None
        
        # Truncate query if it exceeds 390 characters to avoid Tavily API constraints
        if len(query) > 390:
            query = query[:390]
            logger.warning(f"[WebSearchTool] Query truncated to 390 characters: {query}")
            
        logger.info(f"[WebSearchTool] Searching Tavily: {query}")
        
        for attempt in range(max_retries):
            try:
                response = self.client.search(
                    query=query,
                    topic=topic,
                    max_results=self.max_results,
                    include_answer=include_answer
                )
                
                results = []
                
                # Extract search results
                if "results" in response:
                    for item in response["results"]:
                        result = SearchResult(
                            title=item.get("title", "N/A"),
                            url=item.get("url", ""),
                            snippet=item.get("content", ""),
                            source_engine="Tavily",
                            relevance_score=0.5
                        )
                        results.append(result)
                        logger.debug(f"  - Found: {result.title} ({result.url})")
                
                logger.info(f"[WebSearchTool] Tavily found {len(results)} results")
                return True, results, None
                
            except Exception as e:
                last_exception = e
                wait_time = backoff_factor ** attempt
                logger.warning(
                    f"[WebSearchTool] Attempt {attempt + 1}/{max_retries} failed: {str(e)}. "
                    f"Retrying in {wait_time}s..."
                )
                time.sleep(wait_time)
                
        error_msg = f"Web search failed after {max_retries} attempts: {str(last_exception)}"
        logger.error(f"[WebSearchTool] {error_msg}")
        return False, None, error_msg

    def _search_google_news(self, query: str, max_results: int = 4) -> List[SearchResult]:
        """Fetch real-time news headlines via Google News RSS feed (No API Key required)."""
        import urllib.parse
        import xml.etree.ElementTree as ET
        import requests
        
        results = []
        try:
            encoded_query = urllib.parse.quote(query[:300])
            rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-IN&gl=IN&ceid=IN:en"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            
            resp = requests.get(rss_url, headers=headers, timeout=4)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                for item in root.findall("./channel/item")[:max_results]:
                    title = item.findtext("title", "N/A")
                    link = item.findtext("link", "")
                    pub_date = item.findtext("pubDate", "")
                    snippet = f"News Article ({pub_date}): {title}"
                    results.append(SearchResult(
                        title=title,
                        url=link,
                        snippet=snippet,
                        source_engine="Google News RSS"
                    ))
                logger.info(f"[Google News RSS] Retrieved {len(results)} items")
        except Exception as e:
            logger.warning(f"[Google News RSS] Search failed: {e}")
        return results

    def _search_wikipedia(self, query: str, max_results: int = 2) -> List[SearchResult]:
        """Fetch background facts via Wikipedia REST API (No API Key required)."""
        import urllib.parse
        import requests
        
        results = []
        try:
            encoded_query = urllib.parse.quote(query[:300])
            wiki_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={encoded_query}&format=json"
            headers = {"User-Agent": "SatyamevBotFactChecker/1.0"}
            
            resp = requests.get(wiki_url, headers=headers, timeout=4)
            if resp.status_code == 200:
                data = resp.json()
                search_items = data.get("query", {}).get("search", [])[:max_results]
                for item in search_items:
                    title = item.get("title", "")
                    snippet_raw = item.get("snippet", "")
                    snippet = snippet_raw.replace('<span class="searchmatch">', '').replace('</span>', '').replace('&quot;', '"')
                    url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"
                    results.append(SearchResult(
                        title=f"Wikipedia: {title}",
                        url=url,
                        snippet=snippet,
                        source_engine="Wikipedia"
                    ))
                logger.info(f"[Wikipedia API] Retrieved {len(results)} items")
        except Exception as e:
            logger.warning(f"[Wikipedia API] Search failed: {e}")
        return results

    def _search_duckduckgo(self, query: str, max_results: int = 3) -> List[SearchResult]:
        """Fetch web search results via DuckDuckGo (No API Key required)."""
        import urllib.parse
        import re
        import requests
        
        results = []
        try:
            try:
                from duckduckgo_search import DDGS
                with DDGS() as ddgs:
                    ddg_results = list(ddgs.text(query[:300], max_results=max_results))
                    for item in ddg_results:
                        results.append(SearchResult(
                            title=item.get("title", "N/A"),
                            url=item.get("href", ""),
                            snippet=item.get("body", ""),
                            source_engine="DuckDuckGo"
                        ))
                logger.info(f"[DuckDuckGo] Retrieved {len(results)} items via DDGS")
                return results
            except Exception:
                pass
                
            encoded_query = urllib.parse.quote(query[:300])
            html_url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            resp = requests.get(html_url, headers=headers, timeout=4)
            if resp.status_code == 200:
                matches = re.findall(r'<a class="result__url" href="([^"]+)".*?>(.*?)</a>', resp.text, re.DOTALL)
                snippets = re.findall(r'<a class="result__snippet".*?>(.*?)</a>', resp.text, re.DOTALL)
                for i, (url, domain) in enumerate(matches[:max_results]):
                    snip = snippets[i] if i < len(snippets) else ""
                    clean_snip = re.sub(r'<[^>]+>', '', snip).strip()
                    clean_domain = re.sub(r'<[^>]+>', '', domain).strip()
                    if url.startswith("//duckduckgo.com/l/?uddg="):
                        url = urllib.parse.unquote(url.split("uddg=")[1].split("&")[0])
                    results.append(SearchResult(
                        title=clean_domain or "DuckDuckGo Result",
                        url=url,
                        snippet=clean_snip,
                        source_engine="DuckDuckGo"
                    ))
                logger.info(f"[DuckDuckGo] Retrieved {len(results)} items via HTML")
        except Exception as e:
            logger.warning(f"[DuckDuckGo] Search failed: {e}")
        return results

    @staticmethod
    def _optimize_url_query(claim: str) -> str:
        """Extract domain and path keywords from a URL to create an optimized search query."""
        import urllib.parse
        import re
        if re.match(r'^(https?://|www\.)', claim.strip(), re.IGNORECASE):
            raw_url = claim.strip()
            if not raw_url.startswith("http"):
                raw_url = "http://" + raw_url
            try:
                parsed = urllib.parse.urlparse(raw_url)
                domain = parsed.netloc.replace("www.", "")
                path = parsed.path.replace("/", " ")
                path_words = re.sub(r'\.(html|php|aspx|jsp)$', '', path, flags=re.IGNORECASE)
                keywords = f"{domain} {path_words}".strip()
                clean_keywords = re.sub(r'[-_]+', ' ', keywords)
                return f"{clean_keywords} scam fact check".strip()
            except Exception:
                pass
        return claim

    def search_claim_evidence(self, claim: str) -> Dict[str, Any]:
        """
        Search for both supporting and contradicting evidence in parallel using 4 search engines:
        1. Tavily API (Supporting query)
        2. Tavily API (Contradicting query)
        3. Google News RSS Feed (No API Key - Real-time Indian & global news)
        4. Wikipedia REST API (No API Key - Encylopedic background facts)
        5. DuckDuckGo Search (No API Key - Free web index)
        """
        import concurrent.futures
        logger.info(f"[WebSearchTool] Parallel Multi-Engine Investigation starting for: '{claim}'")
        
        search_query = self._optimize_url_query(claim)
        logger.info(f"[WebSearchTool] Optimized search query: '{search_query}'")
        
        supporting: List[SearchResult] = []
        contradicting: List[SearchResult] = []
        seen_urls = set()

        def _run_tavily_support():
            ok, res, err = self.search(query=f"evidence supporting {search_query}", topic="general")
            return res if ok and res else []

        def _run_tavily_contra():
            ok, res, err = self.search(query=f"evidence against {search_query}", topic="general")
            return res if ok and res else []

        def _run_google_news():
            return self._search_google_news(search_query, max_results=4)

        def _run_wikipedia():
            return self._search_wikipedia(search_query, max_results=2)

        def _run_duckduckgo():
            return self._search_duckduckgo(search_query, max_results=3)

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            fut_t_sup = executor.submit(_run_tavily_support)
            fut_t_con = executor.submit(_run_tavily_contra)
            fut_g_news = executor.submit(_run_google_news)
            fut_wiki = executor.submit(_run_wikipedia)
            fut_ddg = executor.submit(_run_duckduckgo)

            t_sup_results = fut_t_sup.result()
            t_con_results = fut_t_con.result()
            g_news_results = fut_g_news.result()
            wiki_results = fut_wiki.result()
            ddg_results = fut_ddg.result()

        # Deduplicate and organize supporting / general news
        for res in t_sup_results:
            if res.url and res.url not in seen_urls:
                seen_urls.add(res.url)
                supporting.append(res)

        for res in g_news_results + wiki_results + ddg_results:
            if res.url and res.url not in seen_urls:
                seen_urls.add(res.url)
                supporting.append(res)

        for res in t_con_results:
            if res.url and res.url not in seen_urls:
                seen_urls.add(res.url)
                contradicting.append(res)

        logger.info(
            f"[WebSearchTool] Parallel Multi-Engine search completed: "
            f"{len(supporting)} supporting/general + {len(contradicting)} contradicting items aggregated across engines"
        )

        return {
            "claim": claim,
            "supporting": supporting,
            "contradicting": contradicting,
            "errors": {
                "supporting": None,
                "contradicting": None
            }
        }


class VectorDatabaseTool:
    """
    Vector database placeholder for knowledge base retrieval.
    
    In production, this would connect to:
    - Pinecone/Weaviate for vector similarity search
    - Internal knowledge base of fact-checks
    - Domain-specific knowledge graphs
    
    For Phase 2, this is a placeholder that returns structured format.
    """
    
    def __init__(self):
        """Initialize vector database tool."""
        self.knowledge_base = {}
        logger.info("VectorDatabaseTool initialized (placeholder mode)")
    
    def query(
        self,
        claim: str,
        top_k: int = 5,
        threshold: float = 0.7
    ) -> tuple[bool, Optional[List[Dict]], Optional[str]]:
        """
        Query vector database for similar claims.
        
        Args:
            claim: Claim to find similar entries for
            top_k: Number of results to return
            threshold: Similarity threshold (0-1)
        
        Returns:
            Tuple: (success: bool, results: Optional[List[Dict]], error: Optional[str])
        
        Note:
            Current implementation returns empty list (placeholder).
            Production would perform vector similarity search.
        """
        try:
            logger.info(f"[VectorDatabaseTool] Query: {claim} (k={top_k})")
            
            # Placeholder: return empty list
            # In production, this would:
            # 1. Embed the claim using sentence-transformers
            # 2. Search vector DB for similar embeddings
            # 3. Return top_k results with similarity scores
            
            results = []
            logger.info(f"[VectorDatabaseTool] Found {len(results)} similar claims")
            
            return True, results, None
        
        except Exception as e:
            error_msg = f"Vector DB query failed: {str(e)}"
            logger.error(f"[VectorDatabaseTool] {error_msg}")
            return False, None, error_msg


class ClaimParserTool:
    """
    Utility tool for parsing and structuring claims.
    
    Extracts key entities, dates, specific vs general claims,
    and prepares structured data for fact-checking.
    """
    
    @staticmethod
    def parse_claim(claim: str) -> Dict[str, Any]:
        """
        Parse claim into structured components.
        
        Args:
            claim: Raw claim text
        
        Returns:
            Dict with parsed structure:
            {
                "original": str,
                "clean": str,
                "claim_type": "specific|general|temporal|comparison",
                "key_entities": list,
                "temporal_markers": list,
                "quantifiers": list,  # "all", "some", "none", etc.
            }
        """
        logger.info(f"[ClaimParserTool] Parsing: {claim}")
        
        # Simple heuristic parsing (in production, use NLP)
        claim_type = "general"
        
        temporal_markers = []
        if any(word in claim.lower() for word in ["today", "yesterday", "year", "month", "date"]):
            claim_type = "temporal"
            temporal_markers = [w for w in claim.split() if w.isdigit()]
        
        # Quantifier detection
        quantifiers = []
        for q in ["all", "some", "none", "most", "many", "few", "any"]:
            if q in claim.lower():
                quantifiers.append(q)
        
        if quantifiers or claim_type == "temporal":
            claim_type = "specific"
        
        parsed = {
            "original": claim,
            "clean": claim.strip().lower(),
            "claim_type": claim_type,
            "key_entities": [],  # Would be extracted via NER
            "temporal_markers": temporal_markers,
            "quantifiers": quantifiers,
        }
        
        logger.debug(f"[ClaimParserTool] Parsed type: {claim_type}")
        return parsed


# Tool Factory
def create_tools(tavily_api_key: str) -> Dict[str, Any]:
    """
    Create all available tools for the agent.
    
    Args:
        tavily_api_key: Tavily API key for web search
    
    Returns:
        Dictionary of tool instances
    """
    logger.info("Creating agent tools...")
    
    tools = {
        "web_search": WebSearchTool(api_key=tavily_api_key),
        "vector_db": VectorDatabaseTool(),
        "claim_parser": ClaimParserTool(),
    }
    
    logger.info("Tools created successfully")
    return tools
