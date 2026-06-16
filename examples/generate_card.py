"""
Example: Generate Fact-Checking Cards

Demonstrates card generation from fact-checking verdicts.
Integrates Phase 2 (brain) and Phase 3 (cards) components.

Usage:
    python examples/generate_card.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import Settings
from src.brain.agent import FactCheckingAgent
from src.cards.generator import CardGenerator


def main():
    """Main example flow."""
    print("\n" + "="*80)
    print("SATYAMEV-BOT: FACT-CHECKING WITH VISUAL PROOF CARDS".center(80))
    print("="*80)
    
    # Initialize settings
    settings = Settings()
    
    # Validate API keys
    if not (settings.GROQ_API_KEY or settings.GOOGLE_API_KEY):
        print("\nERROR: No LLM API keys configured (.env)")
        sys.exit(1)
    
    if not settings.TAVILY_API_KEY:
        print("ERROR: Tavily API key not configured (.env)")
        sys.exit(1)
    
    # Initialize agent
    print("\n1. Initializing fact-checking agent...")
    try:
        agent = FactCheckingAgent(
            groq_api_key=settings.GROQ_API_KEY,
            google_api_key=settings.GOOGLE_API_KEY,
            tavily_api_key=settings.TAVILY_API_KEY,
            strategy="balanced"
        )
        print("   ✓ Agent ready")
    except Exception as e:
        print(f"   ERROR: {str(e)}")
        sys.exit(1)
    
    # Example claims to verify and visualize
    example_claims = [
        "The Earth revolves around the Sun",
        "The Moon is made of cheese",
        "Vaccines are 100% safe with zero side effects",
    ]
    
    print(f"\n2. Verifying {len(example_claims)} claims...\n")
    
    # Verify each claim and generate card
    export_path = Path("exports")
    export_path.mkdir(exist_ok=True)
    
    for i, claim in enumerate(example_claims, 1):
        print(f"   [{i}/{len(example_claims)}] {claim}")
        
        try:
            # Verify claim
            result = agent.verify_claim(claim)
            
            # Generate card
            generator = CardGenerator(preset="facebook", theme="light")
            
            card = generator.generate(
                claim=result.claim,
                verdict=result.verdict,
                confidence=result.confidence,
                reasoning=result.reasoning,
                sources=result.sources,
                key_evidence=result.key_evidence,
            )
            
            # Save card
            sanitized_claim = "".join(
                c if c.isalnum() or c in " -" else "_"
                for c in claim
            ).replace(" ", "_")[:50]
            
            output_path = export_path / f"card_{i}_{sanitized_claim}.png"
            card.save(str(output_path))
            
            print(f"      Verdict: {result.verdict} ({result.confidence:.0%})")
            print(f"      Card: {output_path.name}")
        
        except Exception as e:
            print(f"      ERROR: {str(e)}")
    
    # Summary
    print("\n" + "="*80)
    print("CARD GENERATION COMPLETE")
    print("="*80)
    
    cards = list(export_path.glob("card_*.png"))
    if cards:
        print(f"\nGenerated {len(cards)} cards in '{export_path}/':")
        for card_path in sorted(cards):
            size_kb = card_path.stat().st_size / 1024
            print(f"  ✓ {card_path.name} ({size_kb:.1f} KB)")
    
    print("\nCards ready for social media sharing!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nFATAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
