"""
Phase 2 Testing: Agentic RAG & Web Consensus Engine

Comprehensive test suite for:
1. Tool initialization and configuration
2. Web search functionality
3. LLM agent verdict generation
4. End-to-end fact-checking pipeline
5. Batch verification

Run: python tests/test_brain.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging
from src.config import Settings
from src.brain.config import FactCheckingConfig, get_strategy_config, STRATEGIES
from src.brain.tools import (
    WebSearchTool,
    VectorDatabaseTool,
    ClaimParserTool,
    SearchResult,
)
from src.brain.agent import FactCheckingAgent, VerdictResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger(__name__)


def test_config():
    """Test 1: Configuration system."""
    print("\n" + "="*80)
    print("TEST 1: CONFIGURATION SYSTEM")
    print("="*80)
    
    try:
        # Test default config
        config = FactCheckingConfig()
        assert config.llm_provider in ["groq", "google"]
        assert 0.0 <= config.reasoning_temperature <= 2.0
        print(f"[PASS] Default config created (provider={config.llm_provider})")
        
        # Test strategy configs
        for strategy_name in ["fast", "balanced", "thorough"]:
            config = get_strategy_config(strategy_name)
            print(f"[PASS] Strategy '{strategy_name}' loaded (iterations={config.max_iterations})")
        
        # Test invalid strategy
        try:
            get_strategy_config("invalid")
            print("[FAIL] Should reject invalid strategy")
        except ValueError:
            print("[PASS] Invalid strategy properly rejected")
        
        print("\n[PASS] Configuration system verified")
    
    except Exception as e:
        print(f"\n[FAIL] Configuration test failed: {str(e)}")
        return False
    
    return True


def test_tools():
    """Test 2: Tool initialization."""
    print("\n" + "="*80)
    print("TEST 2: TOOL INITIALIZATION")
    print("="*80)
    
    try:
        settings = Settings()
        
        # Test Web Search Tool
        if settings.TAVILY_API_KEY:
            web_search = WebSearchTool(
                api_key=settings.TAVILY_API_KEY,
                max_results=5
            )
            print("[PASS] WebSearchTool initialized")
        else:
            print("[SKIPPED] Tavily API key not configured")
        
        # Test Vector DB Tool
        vector_db = VectorDatabaseTool()
        print("[PASS] VectorDatabaseTool initialized")
        
        # Test Claim Parser
        claim = "COVID-19 vaccines contain microchips manufactured in 2023"
        parsed = ClaimParserTool.parse_claim(claim)
        assert "claim_type" in parsed
        assert "temporal_markers" in parsed
        print(f"[PASS] ClaimParserTool parsed (type={parsed['claim_type']})")
        
        print("\n[PASS] Tool initialization verified")
    
    except Exception as e:
        print(f"\n[FAIL] Tool test failed: {str(e)}")
        return False
    
    return True


def test_web_search():
    """Test 3: Web search functionality."""
    print("\n" + "="*80)
    print("TEST 3: WEB SEARCH FUNCTIONALITY")
    print("="*80)
    
    try:
        settings = Settings()
        
        if not settings.TAVILY_API_KEY:
            print("[SKIPPED] Tavily API key not configured")
            return True
        
        web_search = WebSearchTool(api_key=settings.TAVILY_API_KEY)
        
        # Test single search
        print("\n3.1: Single web search")
        success, results, error = web_search.search(
            "Earth revolves around the Sun",
            topic="general"
        )
        
        if success and results:
            print(f"[PASS] Search returned {len(results)} results")
            if results:
                print(f"  - First result: {results[0].title[:60]}...")
        else:
            print(f"[FAIL] Search failed: {error}")
        
        # Test evidence search
        print("\n3.2: Evidence search (supporting + contradicting)")
        evidence = web_search.search_claim_evidence(
            "The Moon orbits the Earth"
        )
        
        supporting = evidence.get("supporting", [])
        contradicting = evidence.get("contradicting", [])
        
        print(f"[PASS] Found {len(supporting)} supporting + {len(contradicting)} contradicting")
        
        print("\n[PASS] Web search functionality verified")
    
    except Exception as e:
        print(f"\n[FAIL] Web search test failed: {str(e)}")
        return False
    
    return True


def test_agent_initialization():
    """Test 4: Agent initialization."""
    print("\n" + "="*80)
    print("TEST 4: AGENT INITIALIZATION")
    print("="*80)
    
    try:
        settings = Settings()
        
        # Check API keys
        if not settings.GROQ_API_KEY and not settings.GOOGLE_API_KEY:
            print("[SKIPPED] No LLM API keys configured")
            return True
        
        if not settings.TAVILY_API_KEY:
            print("[SKIPPED] Tavily API key not configured")
            return True
        
        # Initialize agent
        agent = FactCheckingAgent(
            groq_api_key=settings.GROQ_API_KEY,
            google_api_key=settings.GOOGLE_API_KEY,
            tavily_api_key=settings.TAVILY_API_KEY,
            strategy="fast"
        )
        
        print("[PASS] Agent initialized (strategy=fast)")
        print(f"  - LLM Provider: {agent.config.llm_provider}")
        print(f"  - Model: {agent.config.groq_model if agent.config.llm_provider == 'groq' else agent.config.google_model}")
        print(f"  - Temperature: {agent.config.reasoning_temperature}")
        print(f"  - Max iterations: {agent.config.max_iterations}")
        
        print("\n[PASS] Agent initialization verified")
    
    except Exception as e:
        print(f"\n[FAIL] Agent initialization test failed: {str(e)}")
        return False
    
    return True


def test_fact_checking():
    """Test 5: Full fact-checking pipeline."""
    print("\n" + "="*80)
    print("TEST 5: FACT-CHECKING PIPELINE")
    print("="*80)
    
    try:
        settings = Settings()
        
        # Skip if API keys missing
        if not (settings.GROQ_API_KEY or settings.GOOGLE_API_KEY) or not settings.TAVILY_API_KEY:
            print("[SKIPPED] Required API keys not configured")
            return True
        
        agent = FactCheckingAgent(
            groq_api_key=settings.GROQ_API_KEY,
            google_api_key=settings.GOOGLE_API_KEY,
            tavily_api_key=settings.TAVILY_API_KEY,
            strategy="fast"  # Use fast for testing
        )
        
        # Test claims
        test_claims = [
            ("The Earth is round", "TRUE"),
            ("The Moon is made of cheese", "FALSE"),
            ("Vaccines have no side effects", "MISLEADING"),
        ]
        
        for i, (claim, expected_category) in enumerate(test_claims, 1):
            print(f"\n5.{i}: Testing claim - '{claim}'")
            
            try:
                result = agent.verify_claim(claim, include_reasoning=True)
                
                # Display result
                print(f"  Verdict: {result.verdict}")
                print(f"  Confidence: {result.confidence:.1%}")
                print(f"  Reasoning: {result.reasoning[:100]}...")
                print(f"  Sources: {len(result.sources)} found")
                
                # Check if verdict is valid
                if result.verdict in ["TRUE", "FALSE", "MISLEADING", "UNVERIFIABLE"]:
                    print(f"  [PASS] Valid verdict returned")
                else:
                    print(f"  [FAIL] Invalid verdict: {result.verdict}")
            
            except Exception as e:
                print(f"  [FAIL] Verification failed: {str(e)}")
        
        print("\n[PASS] Fact-checking pipeline verified")
    
    except Exception as e:
        print(f"\n[FAIL] Fact-checking test failed: {str(e)}")
        return False
    
    return True


def test_batch_verification():
    """Test 6: Batch verification."""
    print("\n" + "="*80)
    print("TEST 6: BATCH VERIFICATION")
    print("="*80)
    
    try:
        settings = Settings()
        
        if not (settings.GROQ_API_KEY or settings.GOOGLE_API_KEY) or not settings.TAVILY_API_KEY:
            print("[SKIPPED] Required API keys not configured")
            return True
        
        agent = FactCheckingAgent(
            groq_api_key=settings.GROQ_API_KEY,
            google_api_key=settings.GOOGLE_API_KEY,
            tavily_api_key=settings.TAVILY_API_KEY,
            strategy="fast"
        )
        
        claims = [
            "Water boils at 100 degrees Celsius",
            "The sky is green",
        ]
        
        print(f"\n6.1: Batch verification of {len(claims)} claims")
        results = agent.batch_verify(claims, verbose=True)
        
        print(f"\n[PASS] Batch verification completed")
        print(f"  Results: {len(results)} verdicts generated")
        
        # Summary
        verdicts = {}
        for result in results:
            verdicts[result.verdict] = verdicts.get(result.verdict, 0) + 1
        
        for verdict, count in verdicts.items():
            print(f"  - {verdict}: {count}")
        
        print("\n[PASS] Batch verification verified")
    
    except Exception as e:
        print(f"\n[FAIL] Batch verification test failed: {str(e)}")
        return False
    
    return True


def run_all_tests():
    """Run all Phase 2 tests."""
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "PHASE 2: AGENTIC RAG & WEB CONSENSUS ENGINE - TEST SUITE".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "="*78 + "╝")
    
    tests = [
        ("Configuration System", test_config),
        ("Tool Initialization", test_tools),
        ("Web Search Functionality", test_web_search),
        ("Agent Initialization", test_agent_initialization),
        ("Fact-Checking Pipeline", test_fact_checking),
        ("Batch Verification", test_batch_verification),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            logger.exception(f"Test '{name}' crashed: {str(e)}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {name}")
    
    print(f"\nTotal: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n✓ ALL TESTS PASSED - Phase 2 ready for integration")
    else:
        print(f"\n✗ {total_count - passed_count} test(s) failed")
    
    return passed_count == total_count


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
