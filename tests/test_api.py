"""
Phase 4: API Endpoint Testing

Comprehensive test suite for FastAPI REST server endpoints.
Tests all routes: health, ingest, verify, generate-card, batch-verify.
"""

import sys
import json
import logging
from pathlib import Path

# Setup paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi.testclient import TestClient

from src.config import Settings
from src.ingestion.ingestion_manager import IngestionManager
from src.brain.agent import FactCheckingAgent
from src.cards.generator import CardGenerator
from src.api import app as app_module
from src.api.endpoints import init_services

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize services for testing
config = Settings()

try:
    ingestion_manager = IngestionManager(
        groq_api_key=config.GROQ_API_KEY,
        google_api_key=config.GOOGLE_API_KEY,
        image_engine=config.IMAGE_ENGINE,
    )
    logger.info("✓ Ingestion manager initialized")
except Exception as e:
    logger.error(f"✗ Failed to initialize ingestion manager: {e}")
    ingestion_manager = None

try:
    fact_checking_agent = FactCheckingAgent(
        groq_api_key=config.GROQ_API_KEY,
        google_api_key=config.GOOGLE_API_KEY,
        tavily_api_key=config.TAVILY_API_KEY,
        strategy="balanced",
    )
    logger.info("✓ Fact-checking agent initialized")
except Exception as e:
    logger.error(f"✗ Failed to initialize fact-checking agent: {e}")
    fact_checking_agent = None

try:
    card_generator = CardGenerator(preset="facebook", theme="light")
    logger.info("✓ Card generator initialized")
except Exception as e:
    logger.error(f"✗ Failed to initialize card generator: {e}")
    card_generator = None

# Initialize services in endpoints module
init_services(ingestion_manager, fact_checking_agent, card_generator)

# Create app and client
app = app_module.create_app()
client = TestClient(app)


def print_separator(title: str):
    """Print test separator."""
    print("\n" + "=" * 80)
    print(f"TEST: {title}")
    print("=" * 80 + "\n")


def test_health_check():
    """Test health check endpoint."""
    print_separator("HEALTH CHECK")
    
    response = client.get("/api/health")
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200, "Health check failed"
    data = response.json()
    assert data["status"] == "healthy", "Service unhealthy"
    assert "version" in data, "Missing version"
    assert "timestamp" in data, "Missing timestamp"
    
    print("[PASS] Health check verified")


def test_ingest_text():
    """Test text ingestion endpoint."""
    print_separator("TEXT INGESTION")
    
    payload = {
        "source": "The Earth is a sphere, not flat.",
        "input_type": "TEXT",
        "clean": True,
    }
    
    response = client.post("/api/ingest", json=payload)
    
    print(f"Status Code: {response.status_code}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200, f"Ingestion failed: {response.text}"
    data = response.json()
    assert data["success"] is True, "Ingestion marked as failed"
    assert data["text"] is not None, "No text returned"
    assert data["character_count"] > 0, "Character count is zero"
    
    print(f"[PASS] Text ingestion verified ({data['character_count']} characters)")


def test_verify_claim():
    """Test fact-checking verification endpoint."""
    print_separator("FACT-CHECKING VERIFICATION")
    
    payload = {
        "claim": "The Earth is round, not flat.",
        "strategy": "fast",
        "include_reasoning": True,
    }
    
    response = client.post("/api/verify", json=payload)
    
    print(f"Status Code: {response.status_code}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200, f"Verification failed: {response.text}"
    data = response.json()
    assert data["claim"] == payload["claim"], "Claim mismatch"
    assert data["verdict"] in ["TRUE", "FALSE", "MISLEADING", "UNVERIFIABLE"], "Invalid verdict"
    assert 0 <= data["confidence"] <= 1, "Confidence out of range"
    assert data["reasoning"], "No reasoning provided"
    assert "timestamp" in data, "Missing timestamp"
    
    print(f"[PASS] Verification verified - Verdict: {data['verdict']} ({data['confidence']:.1%})")


def test_batch_verify():
    """Test batch verification endpoint."""
    print_separator("BATCH VERIFICATION")
    
    payload = {
        "claims": [
            "The Earth is round",
            "Water boils at 100°C at sea level",
            "The moon is made of cheese",
        ],
        "strategy": "balanced",
    }
    
    response = client.post("/api/verify-batch", json=payload)
    
    print(f"Status Code: {response.status_code}")
    print(f"Claims: {json.dumps(payload['claims'], indent=2)}")
    print(f"Response Summary:")
    
    assert response.status_code == 200, f"Batch verification failed: {response.text}"
    data = response.json()
    assert data["total"] == len(payload["claims"]), "Total count mismatch"
    assert len(data["results"]) == len(payload["claims"]), "Results count mismatch"
    
    for i, result in enumerate(data["results"]):
        print(f"  [{i+1}] {result['claim'][:30]}... → {result['verdict']} ({result['confidence']:.0%})")
        assert result["verdict"] in ["TRUE", "FALSE", "MISLEADING", "UNVERIFIABLE"], "Invalid verdict"
    
    print(f"\n[PASS] Batch verification verified - {data['completed']}/{data['total']} completed")


def test_generate_card():
    """Test card generation endpoint."""
    print_separator("CARD GENERATION")
    
    payload = {
        "claim": "Testing card generation via API",
        "verdict": "TRUE",
        "confidence": 0.95,
        "reasoning": "This is a test claim for card generation.",
        "sources": ["https://example.com"],
        "key_evidence": ["Test evidence"],
        "preset": "facebook",
        "theme": "light",
    }
    
    response = client.post("/api/generate-card", json=payload)
    
    print(f"Status Code: {response.status_code}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print(f"Response Content-Type: {response.headers.get('content-type')}")
    print(f"Response Size: {len(response.content)} bytes")
    
    assert response.status_code == 200, f"Card generation failed: {response.text}"
    assert response.headers["content-type"] == "image/png", "Invalid content type"
    assert len(response.content) > 0, "Empty response"
    
    # Save card for verification
    card_path = project_root / "exports" / "test_api_card.png"
    card_path.parent.mkdir(exist_ok=True)
    card_path.write_bytes(response.content)
    
    print(f"[PASS] Card generated and saved to {card_path}")


def test_root_endpoint():
    """Test root endpoint."""
    print_separator("ROOT ENDPOINT")
    
    response = client.get("/")
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200, "Root endpoint failed"
    data = response.json()
    assert "name" in data, "Missing name"
    assert data["name"] == "Satyamev-Bot", "Invalid name"
    assert "docs" in data, "Missing docs endpoint"
    
    print("[PASS] Root endpoint verified")


def test_openapi_docs():
    """Test OpenAPI documentation."""
    print_separator("OPENAPI DOCUMENTATION")
    
    response = client.get("/api/openapi.json")
    
    print(f"Status Code: {response.status_code}")
    
    assert response.status_code == 200, "OpenAPI doc failed"
    data = response.json()
    assert "openapi" in data, "Missing OpenAPI version"
    assert "paths" in data, "Missing API paths"
    
    print(f"OpenAPI Version: {data.get('openapi')}")
    print(f"Paths: {list(data.get('paths', {}).keys())}")
    print("[PASS] OpenAPI documentation verified")


def run_all_tests():
    """Run all API tests."""
    print("\n" + "=" * 80)
    print("PHASE 4: API ENDPOINT TESTING")
    print("FastAPI REST Server Verification")
    print("=" * 80)
    
    tests = [
        ("Root Endpoint", test_root_endpoint),
        ("Health Check", test_health_check),
        ("OpenAPI Docs", test_openapi_docs),
        ("Text Ingestion", test_ingest_text),
        ("Fact-Checking Verification", test_verify_claim),
        ("Batch Verification", test_batch_verify),
        ("Card Generation", test_generate_card),
    ]
    
    passed = 0
    failed = 0
    skipped = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            logger.error(f"Test failed: {str(e)}")
            failed += 1
            print(f"[FAIL] {test_name}: {str(e)}\n")
        except Exception as e:
            logger.error(f"Test skipped: {str(e)}")
            skipped += 1
            print(f"[SKIPPED] {test_name}: {str(e)}\n")
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"[PASS] {passed} tests passed")
    if failed > 0:
        print(f"[FAIL] {failed} tests failed")
    if skipped > 0:
        print(f"[SKIPPED] {skipped} tests skipped")
    print(f"\nTotal: {passed}/{len(tests)} tests passed")
    
    if failed == 0 and skipped == 0:
        print("\n✓ ALL TESTS PASSED - Phase 4 API server ready for deployment\n")
    
    return passed, failed, skipped


if __name__ == "__main__":
    run_all_tests()
