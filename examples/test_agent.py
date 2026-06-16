"""
Example: Fact-Checking CLI

Simple command-line interface for testing the fact-checking agent.
Allows users to input claims and get verdicts with evidence.

Usage:
    python examples/test_agent.py

Then type claims to verify, or type 'quit' to exit.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import json
from src.config import Settings
from src.brain.agent import FactCheckingAgent


def print_header():
    """Print CLI header."""
    print("\n" + "="*80)
    print("SATYAMEV-BOT: FACT-CHECKING ENGINE".center(80))
    print("="*80)
    print("\nEnter claims to fact-check, or type 'quit' to exit.\n")


def print_verdict(result):
    """Pretty print verdict result."""
    print("\n" + "-"*80)
    print(f"CLAIM: {result.claim}\n")
    
    # Verdict with color-like emphasis
    verdict_symbols = {
        "TRUE": "✓",
        "FALSE": "✗",
        "MISLEADING": "~",
        "UNVERIFIABLE": "?"
    }
    symbol = verdict_symbols.get(result.verdict, "?")
    
    print(f"VERDICT: [{symbol}] {result.verdict}")
    print(f"CONFIDENCE: {result.confidence:.1%}\n")
    
    print(f"REASONING:\n{result.reasoning}\n")
    
    if result.key_evidence:
        print("KEY EVIDENCE:")
        for evidence in result.key_evidence:
            print(f"  • {evidence}")
        print()
    
    if result.sources:
        print(f"SOURCES ({len(result.sources)}):")
        for i, source in enumerate(result.sources[:5], 1):
            print(f"  {i}. {source}")
        if len(result.sources) > 5:
            print(f"  ... and {len(result.sources) - 5} more")
    
    print(f"\nTimestamp: {result.timestamp}")
    print("-"*80)


def main():
    """Main CLI loop."""
    print_header()
    
    # Initialize settings
    settings = Settings()
    
    # Validate API keys
    if not settings.GROQ_API_KEY and not settings.GOOGLE_API_KEY:
        print("ERROR: No LLM API keys configured (.env)")
        print("  - Set GROQ_API_KEY or GOOGLE_API_KEY")
        sys.exit(1)
    
    if not settings.TAVILY_API_KEY:
        print("ERROR: Tavily API key not configured (.env)")
        print("  - Set TAVILY_API_KEY")
        sys.exit(1)
    
    # Initialize agent
    print("Initializing fact-checking agent...")
    try:
        agent = FactCheckingAgent(
            groq_api_key=settings.GROQ_API_KEY,
            google_api_key=settings.GOOGLE_API_KEY,
            tavily_api_key=settings.TAVILY_API_KEY,
            strategy="balanced"
        )
        print("✓ Agent ready\n")
    except Exception as e:
        print(f"ERROR: Failed to initialize agent: {str(e)}")
        sys.exit(1)
    
    # Main loop
    claim_count = 0
    try:
        while True:
            # Get input
            claim = input("Enter claim to verify (or 'quit'): ").strip()
            
            if claim.lower() == 'quit':
                break
            
            if not claim:
                print("Please enter a claim.")
                continue
            
            if len(claim) < 10:
                print("Claim too short (minimum 10 characters).")
                continue
            
            # Verify claim
            claim_count += 1
            print(f"\n[{claim_count}] Processing claim...")
            
            try:
                result = agent.verify_claim(claim, include_reasoning=True)
                print_verdict(result)
            
            except Exception as e:
                print(f"\nERROR: Failed to verify claim: {str(e)}")
                print("Please try another claim.")
    
    except KeyboardInterrupt:
        print("\n\nExiting...")
    
    # Summary
    if claim_count > 0:
        print(f"\n✓ Verified {claim_count} claim(s)")
    
    print("\nGoodbye!")


if __name__ == "__main__":
    main()
