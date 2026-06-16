"""
Fact-Checking Agent Implementation

Core LangChain agent using ReAct (Reasoning + Acting) pattern.
Uses Llama-3.3-70b (via Groq) or Gemini-1.5-Flash for reasoning
and Tavily API for real-time web search.

Verdict Categories:
- TRUE: Claim supported by evidence
- FALSE: Claim contradicted by evidence
- MISLEADING: Partially true or lacking context
- UNVERIFIABLE: Insufficient evidence
"""

import logging
import json
import re
from typing import Optional, List, Dict, Any, Literal, Tuple
from datetime import datetime
from pydantic import BaseModel, Field

from groq import Groq
import google.generativeai as genai

from .config import FactCheckingConfig, get_strategy_config
from .tools import create_tools, WebSearchTool

logger = logging.getLogger(__name__)


class VerdictResult(BaseModel):
    """Structured verdict result from fact-checking agent."""
    
    claim: str = Field(description="Original claim")
    verdict: Literal["TRUE", "FALSE", "MISLEADING", "UNVERIFIABLE"] = Field(
        description="Fact-check verdict"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score (0-1)"
    )
    reasoning: str = Field(description="Explanation for verdict")
    sources: List[str] = Field(
        default_factory=list,
        description="URLs of supporting evidence"
    )
    key_evidence: List[str] = Field(
        default_factory=list,
        description="Key facts supporting the verdict"
    )
    language: str = Field(
        default="English",
        description="Detected language of the claim"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Timestamp of verdict"
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Export as dictionary."""
        return self.model_dump()
    
    def to_json(self) -> str:
        """Export as JSON string."""
        return self.model_dump_json(indent=2)


class FactCheckingAgent:
    """
    Main fact-checking agent orchestrator.
    
    Uses LangChain-inspired ReAct pattern with tool integration:
    1. Claim parsing (structure extraction)
    2. Web search for evidence (via Tavily)
    3. Evidence analysis (LLM reasoning)
    4. Verdict generation (TRUE/FALSE/MISLEADING/UNVERIFIABLE)
    """
    
    def __init__(
        self,
        config: Optional[FactCheckingConfig] = None,
        groq_api_key: Optional[str] = None,
        google_api_key: Optional[str] = None,
        tavily_api_key: Optional[str] = None,
        strategy: str = "balanced",
    ):
        """
        Initialize fact-checking agent.
        
        Args:
            config: FactCheckingConfig instance (overrides strategy)
            groq_api_key: Groq API key for Llama models
            google_api_key: Google API key for Gemini
            tavily_api_key: Tavily API key for web search
            strategy: Predefined config strategy ("fast", "balanced", "thorough")
        
        Raises:
            ValueError: If required API keys missing
        """
        # Load config
        if config is None:
            config = get_strategy_config(strategy)
        self.config = config
        
        # Initialize LLMs
        self.groq_client = None
        self.google_client = None
        
        if groq_api_key:
            self.groq_client = Groq(api_key=groq_api_key)
            logger.info("Groq client initialized")
        
        if google_api_key:
            genai.configure(api_key=google_api_key)
            self.google_client = genai.GenerativeModel(self.config.google_model)
            logger.info("Google Gemini client initialized")
        
        # Ensure at least one LLM is available
        if not self.groq_client and not self.google_client:
            raise ValueError("At least one LLM API key required (Groq or Google)")
        
        # Initialize tools
        if not tavily_api_key:
            raise ValueError("Tavily API key required for web search")
        
        self.tools = create_tools(tavily_api_key)
        self.web_search = self.tools["web_search"]
        
        logger.info(
            f"FactCheckingAgent initialized: "
            f"provider={self.config.llm_provider}, "
            f"strategy={strategy}"
        )
    
    def verify_claim(
        self,
        claim: str,
        include_reasoning: bool = True,
    ) -> VerdictResult:
        """
        Main entry point: verify a claim end-to-end.
        
        Args:
            claim: Claim to fact-check
            include_reasoning: Include detailed reasoning in response
        
        Returns:
            VerdictResult with verdict, confidence, evidence
        """
        logger.info(f"=== Starting fact-check: {claim} ===")
        
        # Detect input language and translate for search indexing
        detected_lang = self._detect_language(claim)
        is_english = detected_lang.lower() in ["english", "en"]
        
        search_query_base = claim if is_english else self._translate_to_english(claim)
        
        # Step 1: Parse claim using the English search query base
        parsed = self.tools["claim_parser"].parse_claim(search_query_base)
        logger.info(f"Claim type: {parsed['claim_type']}")
        
        # Step 2: Web search for evidence
        logger.info("Step 2: Searching for evidence...")
        search_evidence = self.web_search.search_claim_evidence(search_query_base)
        
        supporting = search_evidence.get("supporting", [])
        contradicting = search_evidence.get("contradicting", [])
        
        logger.info(
            f"Found {len(supporting)} supporting + "
            f"{len(contradicting)} contradicting sources"
        )
        
        # Step 3: Analyze with LLM
        logger.info("Step 3: Analyzing evidence with LLM...")
        verdict_result = self._analyze_evidence(
            claim=claim,
            supporting_sources=supporting,
            contradicting_sources=contradicting,
            include_reasoning=include_reasoning,
            target_language=detected_lang,
        )
        
        # Step 4: Extract sources
        all_sources = []
        if supporting:
            all_sources.extend([s.url for s in supporting[:3]])
        if contradicting:
            all_sources.extend([s.url for s in contradicting[:3]])
        
        verdict_result.sources = all_sources
        
        logger.info(f"Verdict: {verdict_result.verdict} (confidence: {verdict_result.confidence})")
        
        return verdict_result
    
    def _analyze_evidence(
        self,
        claim: str,
        supporting_sources: List[Any],
        contradicting_sources: List[Any],
        include_reasoning: bool = True,
        target_language: str = "English",
    ) -> VerdictResult:
        """
        Analyze search results with LLM to generate verdict.
        
        Args:
            claim: Original claim
            supporting_sources: List of supporting SearchResult objects
            contradicting_sources: List of contradicting SearchResult objects
            include_reasoning: Include detailed reasoning
            target_language: Target language for reasoning and evidence text
        
        Returns:
            VerdictResult
        """
        # Format evidence for LLM
        evidence_text = self._format_evidence(
            supporting_sources,
            contradicting_sources
        )
        
        # Construct prompt
        prompt = self._construct_verdict_prompt(
            claim=claim,
            evidence=evidence_text,
            include_reasoning=include_reasoning,
            target_language=target_language,
        )
        
        # Get LLM response
        response_text = self._call_llm(prompt)
        
        # Parse verdict
        verdict_result = self._parse_verdict_response(response_text, claim)
        verdict_result.language = target_language
        
        return verdict_result
    
    def _format_evidence(
        self,
        supporting: List[Any],
        contradicting: List[Any],
    ) -> str:
        """Format search results for LLM."""
        evidence = "EVIDENCE SUMMARY:\n\n"
        
        if supporting:
            evidence += f"SUPPORTING EVIDENCE ({len(supporting)} sources):\n"
            for i, source in enumerate(supporting[:5], 1):
                title = source.title if hasattr(source, 'title') else source.get('title', 'N/A')
                snippet = source.snippet if hasattr(source, 'snippet') else source.get('content', '')[:200]
                evidence += f"{i}. {title}\n   {snippet}\n\n"
        
        if contradicting:
            evidence += f"\nCONTRADICTING EVIDENCE ({len(contradicting)} sources):\n"
            for i, source in enumerate(contradicting[:5], 1):
                title = source.title if hasattr(source, 'title') else source.get('title', 'N/A')
                snippet = source.snippet if hasattr(source, 'snippet') else source.get('content', '')[:200]
                evidence += f"{i}. {title}\n   {snippet}\n\n"
        
        if not supporting and not contradicting:
            evidence += "No evidence found in web search.\n"
        
        return evidence
    
    def _construct_verdict_prompt(
        self,
        claim: str,
        evidence: str,
        include_reasoning: bool = True,
        target_language: str = "English",
    ) -> str:
        """Construct prompt for LLM verdict generation."""
        prompt = f"""You are an expert fact-checker. Analyze the following claim and evidence.

CLAIM: {claim}

{evidence}

TASK: Determine if the claim is TRUE, FALSE, MISLEADING, or UNVERIFIABLE.

INSTRUCTIONS:
1. Analyze the evidence carefully
2. Assess the credibility and relevance of sources
3. Consider the claim's specificity and verifiability
4. Provide a clear verdict with reasoning
5. IMPORTANT: The "verdict" key value MUST be one of the English keys: "TRUE", "FALSE", "MISLEADING", or "UNVERIFIABLE".
6. IMPORTANT: The "reasoning" and "key_evidence" text values MUST be written in the user's original language: {target_language}.

REQUIRED RESPONSE FORMAT (JSON):
{{
    "verdict": "TRUE|FALSE|MISLEADING|UNVERIFIABLE",
    "confidence": <float 0-1>,
    "reasoning": "<explanation written in {target_language}>",
    "key_evidence": ["<fact1 written in {target_language}>", "<fact2 written in {target_language}>", ...]
}}

DEFINITIONS:
- TRUE: Claim is supported by credible evidence
- FALSE: Claim is contradicted by credible evidence
- MISLEADING: Claim is partially true or taken out of context
- UNVERIFIABLE: Insufficient evidence to verify

Respond ONLY with valid JSON, no other text."""
        
        return prompt
    
    def _call_llm(self, prompt: str) -> str:
        """Call configured LLM with prompt."""
        try:
            if self.config.llm_provider == "groq" and self.groq_client:
                logger.info(f"Calling Groq ({self.config.groq_model})...")
                response = self.groq_client.chat.completions.create(
                    model=self.config.groq_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=self.config.reasoning_temperature,
                    max_tokens=1000,
                    timeout=self.config.api_timeout_seconds,
                )
                return response.choices[0].message.content
            
            elif self.config.llm_provider == "google" and self.google_client:
                logger.info(f"Calling Google ({self.config.google_model})...")
                response = self.google_client.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=self.config.reasoning_temperature,
                        max_output_tokens=1000,
                    )
                )
                return response.text
            
            else:
                # Fallback to available client
                if self.groq_client:
                    logger.warning("Falling back to Groq")
                    response = self.groq_client.chat.completions.create(
                        model=self.config.groq_model,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=self.config.reasoning_temperature,
                        max_tokens=1000,
                    )
                    return response.choices[0].message.content
                elif self.google_client:
                    logger.warning("Falling back to Google")
                    response = self.google_client.generate_content(prompt)
                    return response.text
        
        except Exception as e:
            logger.error(f"LLM call failed: {str(e)}")
            raise
            
    def _detect_language(self, text: str) -> str:
        """Detect the language of the text using LLM."""
        prompt = (
            f"Identify the language of the following text (e.g., English, Hindi, Tamil, Telugu, Bengali, Marathi, Kannada, Malayalam, Gujarati, etc.). "
            f"Return only the name of the language, nothing else.\n\nText: {text}"
        )
        try:
            lang = self._call_llm(prompt).strip().strip('"').strip("'").strip()
            logger.info(f"Detected language: {lang}")
            return lang
        except Exception as e:
            logger.warning(f"Language detection failed: {e}, defaulting to English")
            return "English"

    def _translate_to_english(self, text: str) -> str:
        """Translate text to English using LLM if it's not already in English."""
        prompt = (
            f"Translate the following text to English. If it is already in English, return it exactly as is. "
            f"Return only the translated text, nothing else.\n\nText: {text}"
        )
        try:
            translation = self._call_llm(prompt).strip().strip('"').strip("'").strip()
            logger.info(f"Translated query to English: {translation}")
            return translation
        except Exception as e:
            logger.warning(f"Translation to English failed: {e}, using original text")
            return text
    
    def _parse_verdict_response(
        self,
        response_text: str,
        claim: str,
    ) -> VerdictResult:
        """Parse LLM JSON response into VerdictResult."""
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                data = json.loads(json_str)
            else:
                data = json.loads(response_text)
            
            # Extract fields
            verdict = data.get("verdict", "UNVERIFIABLE").upper()
            confidence = float(data.get("confidence", 0.5))
            reasoning = data.get("reasoning", "No reasoning provided")
            key_evidence = data.get("key_evidence", [])
            
            # Validate verdict
            valid_verdicts = ["TRUE", "FALSE", "MISLEADING", "UNVERIFIABLE"]
            if verdict not in valid_verdicts:
                logger.warning(f"Invalid verdict '{verdict}', defaulting to UNVERIFIABLE")
                verdict = "UNVERIFIABLE"
            
            # Clamp confidence
            confidence = max(0.0, min(1.0, confidence))
            
            return VerdictResult(
                claim=claim,
                verdict=verdict,
                confidence=confidence,
                reasoning=reasoning,
                key_evidence=key_evidence,
            )
        
        except Exception as e:
            logger.error(f"Failed to parse verdict response: {str(e)}")
            logger.debug(f"Response text: {response_text}")
            
            # Return unverifiable as fallback
            return VerdictResult(
                claim=claim,
                verdict="UNVERIFIABLE",
                confidence=0.0,
                reasoning=f"Unable to parse agent response: {str(e)}",
            )
    
    def batch_verify(
        self,
        claims: List[str],
        verbose: bool = False,
    ) -> List[VerdictResult]:
        """
        Verify multiple claims in sequence.
        
        Args:
            claims: List of claims to verify
            verbose: Print progress
        
        Returns:
            List of VerdictResult objects
        """
        results = []
        for i, claim in enumerate(claims, 1):
            if verbose:
                print(f"[{i}/{len(claims)}] Verifying: {claim}")
            
            try:
                result = self.verify_claim(claim)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to verify claim: {claim}")
                results.append(VerdictResult(
                    claim=claim,
                    verdict="UNVERIFIABLE",
                    confidence=0.0,
                    reasoning=f"Verification failed: {str(e)}",
                ))
        
        return results
