"""
API Client Example

Demonstrates how to use the Satyamev-Bot REST API.
"""

import requests
import json
from typing import Optional
from pathlib import Path


class SatyamevBotClient:
    """REST API client for Satyamev-Bot."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize client."""
        self.base_url = base_url
        self.session = requests.Session()
    
    def health_check(self) -> dict:
        """Check server health."""
        response = self.session.get(f"{self.base_url}/api/health")
        response.raise_for_status()
        return response.json()
    
    def ingest(
        self,
        source: str,
        input_type: str = "AUTO",
        clean: bool = True,
    ) -> dict:
        """Ingest a claim."""
        payload = {
            "source": source,
            "input_type": input_type,
            "clean": clean,
        }
        response = self.session.post(
            f"{self.base_url}/api/ingest",
            json=payload,
        )
        response.raise_for_status()
        return response.json()
    
    def verify(
        self,
        claim: str,
        strategy: str = "balanced",
        include_reasoning: bool = True,
    ) -> dict:
        """Verify a claim."""
        payload = {
            "claim": claim,
            "strategy": strategy,
            "include_reasoning": include_reasoning,
        }
        response = self.session.post(
            f"{self.base_url}/api/verify",
            json=payload,
        )
        response.raise_for_status()
        return response.json()
    
    def batch_verify(
        self,
        claims: list,
        strategy: str = "balanced",
    ) -> dict:
        """Verify multiple claims."""
        payload = {
            "claims": claims,
            "strategy": strategy,
        }
        response = self.session.post(
            f"{self.base_url}/api/verify-batch",
            json=payload,
        )
        response.raise_for_status()
        return response.json()
    
    def generate_card(
        self,
        claim: str,
        verdict: str,
        confidence: float,
        reasoning: Optional[str] = None,
        sources: Optional[list] = None,
        key_evidence: Optional[list] = None,
        preset: str = "facebook",
        theme: str = "light",
        save_path: Optional[str] = None,
    ) -> bytes:
        """Generate a proof card."""
        payload = {
            "claim": claim,
            "verdict": verdict,
            "confidence": confidence,
            "reasoning": reasoning,
            "sources": sources or [],
            "key_evidence": key_evidence or [],
            "preset": preset,
            "theme": theme,
        }
        response = self.session.post(
            f"{self.base_url}/api/generate-card",
            json=payload,
        )
        response.raise_for_status()
        
        # Save to file if path provided
        if save_path:
            Path(save_path).parent.mkdir(exist_ok=True)
            Path(save_path).write_bytes(response.content)
            print(f"Card saved to {save_path}")
        
        return response.content


def example_1_health_check():
    """Example 1: Check server health."""
    print("\n" + "=" * 80)
    print("EXAMPLE 1: HEALTH CHECK")
    print("=" * 80 + "\n")
    
    client = SatyamevBotClient()
    
    try:
        health = client.health_check()
        print("Server Status:")
        print(json.dumps(health, indent=2))
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure the API server is running: python -m src.api.app")


def example_2_ingest_claim():
    """Example 2: Ingest a claim."""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: INGEST CLAIM")
    print("=" * 80 + "\n")
    
    client = SatyamevBotClient()
    
    try:
        result = client.ingest(
            source="The Earth is a sphere, not flat.",
            input_type="TEXT",
        )
        print("Ingestion Result:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {e}")


def example_3_verify_claim():
    """Example 3: Verify a claim."""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: VERIFY CLAIM")
    print("=" * 80 + "\n")
    
    client = SatyamevBotClient()
    
    claims = [
        "The Earth is round",
        "Water boils at 100°C at sea level",
        "The moon is made of cheese",
    ]
    
    try:
        for claim in claims:
            print(f"\nVerifying: {claim}")
            result = client.verify(
                claim=claim,
                strategy="fast",
            )
            print(f"  Verdict: {result['verdict']}")
            print(f"  Confidence: {result['confidence']:.0%}")
            print(f"  Reasoning: {result['reasoning'][:100]}...")
    except Exception as e:
        print(f"Error: {e}")


def example_4_batch_verify():
    """Example 4: Batch verify claims."""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: BATCH VERIFY")
    print("=" * 80 + "\n")
    
    client = SatyamevBotClient()
    
    claims = [
        "The Earth is round",
        "Water boils at 100°C",
        "The moon is made of cheese",
        "Vaccines prevent diseases",
        "The sun is hot",
    ]
    
    try:
        result = client.batch_verify(claims, strategy="balanced")
        
        print(f"Batch Verification Result:")
        print(f"  Total: {result['total']}")
        print(f"  Completed: {result['completed']}")
        print(f"  Failed: {result['failed']}")
        print(f"\nResults:")
        
        for i, verdict in enumerate(result['results']):
            print(f"  [{i+1}] {verdict['claim'][:40]}...")
            print(f"      Verdict: {verdict['verdict']} ({verdict['confidence']:.0%})")
    except Exception as e:
        print(f"Error: {e}")


def example_5_generate_card():
    """Example 5: Generate a proof card."""
    print("\n" + "=" * 80)
    print("EXAMPLE 5: GENERATE CARD")
    print("=" * 80 + "\n")
    
    client = SatyamevBotClient()
    
    try:
        # First, verify a claim
        print("Step 1: Verifying claim...")
        verdict = client.verify(
            claim="The Earth is round",
            strategy="fast",
        )
        
        print(f"  Verdict: {verdict['verdict']}")
        print(f"  Confidence: {verdict['confidence']:.0%}")
        
        # Generate a card with the verdict
        print("\nStep 2: Generating card...")
        card_bytes = client.generate_card(
            claim=verdict['claim'],
            verdict=verdict['verdict'],
            confidence=verdict['confidence'],
            reasoning=verdict['reasoning'],
            sources=verdict['sources'],
            key_evidence=verdict['key_evidence'],
            preset="facebook",
            theme="light",
            save_path="exports/example_api_card.png",
        )
        
        print(f"  Card size: {len(card_bytes):,} bytes")
    except Exception as e:
        print(f"Error: {e}")


def example_6_full_pipeline():
    """Example 6: Full pipeline - ingest, verify, generate card."""
    print("\n" + "=" * 80)
    print("EXAMPLE 6: FULL PIPELINE")
    print("=" * 80 + "\n")
    
    client = SatyamevBotClient()
    
    try:
        # Step 1: Ingest
        print("Step 1: Ingesting claim...")
        ingested = client.ingest(
            source="Water freezes at 0°C under normal atmospheric pressure.",
            input_type="TEXT",
        )
        print(f"  Extracted text: {ingested['text'][:50]}...")
        
        # Step 2: Verify
        print("\nStep 2: Verifying ingested claim...")
        verdict = client.verify(ingested['text'])
        print(f"  Verdict: {verdict['verdict']} ({verdict['confidence']:.0%})")
        
        # Step 3: Generate card
        print("\nStep 3: Generating proof card...")
        card_bytes = client.generate_card(
            claim=verdict['claim'],
            verdict=verdict['verdict'],
            confidence=verdict['confidence'],
            reasoning=verdict['reasoning'],
            sources=verdict['sources'],
            key_evidence=verdict['key_evidence'],
            preset="facebook",
            theme="bold",
            save_path="exports/full_pipeline_card.png",
        )
        print(f"  Card generated: {len(card_bytes):,} bytes")
        
        print("\n✓ Full pipeline completed successfully!")
    except Exception as e:
        print(f"Error: {e}")


def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("SATYAMEV-BOT API CLIENT EXAMPLES")
    print("=" * 80)
    
    examples = [
        example_1_health_check,
        example_2_ingest_claim,
        example_3_verify_claim,
        example_4_batch_verify,
        example_5_generate_card,
        example_6_full_pipeline,
    ]
    
    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"\nExample error: {e}")
    
    print("\n" + "=" * 80)
    print("Examples completed!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
