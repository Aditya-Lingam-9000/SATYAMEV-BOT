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
    relevance_score: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Relevance score (0-1)"
    )


class WebSearchTool:
    """
    Real-time web search tool via Tavily API.
    
    Used by agent to find supporting/contradicting evidence for claims.
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
        logger.info(f"WebSearchTool initialized (max_results={self.max_results})")
    
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
        try:
            # Truncate query if it exceeds 390 characters to avoid Tavily API constraints
            if len(query) > 390:
                query = query[:390]
                logger.warning(f"[WebSearchTool] Query truncated to 390 characters: {query}")
                
            logger.info(f"[WebSearchTool] Searching: {query}")
            
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
                        relevance_score=0.5  # Tavily doesn't return scores
                    )
                    results.append(result)
                    logger.debug(f"  - Found: {result.title} ({result.url})")
            
            logger.info(f"[WebSearchTool] Found {len(results)} results")
            return True, results, None
        
        except Exception as e:
            error_msg = f"Web search failed: {str(e)}"
            logger.error(f"[WebSearchTool] {error_msg}")
            return False, None, error_msg
    
    def search_claim_evidence(self, claim: str) -> Dict[str, Any]:
        """
        Search for both supporting and contradicting evidence.
        
        Args:
            claim: Claim to investigate
        
        Returns:
            Dict with "supporting" and "contradicting" evidence lists
        """
        logger.info(f"[WebSearchTool] Investigating: {claim}")
        
        # Search for supporting evidence
        success_support, supporting, error_support = self.search(
            query=f"evidence supporting {claim}",
            topic="general"
        )
        
        # Search for contradicting evidence
        success_contra, contradicting, error_contra = self.search(
            query=f"evidence against {claim}",
            topic="general"
        )
        
        return {
            "claim": claim,
            "supporting": supporting if success_support else [],
            "contradicting": contradicting if success_contra else [],
            "errors": {
                "supporting": error_support,
                "contradicting": error_contra
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
