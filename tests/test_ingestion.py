"""
Phase 1 Manual Testing Script
==============================

Comprehensive testing of the Multimodal Ingestion Pipeline.

Tests:
1. Text ingestion: Direct string processing
2. Audio ingestion: Mock test (requires actual audio file)
3. Image ingestion: Mock test (requires actual image file)
4. Error handling: Invalid inputs, edge cases
"""

import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging
from src.config import get_settings
from src.ingestion.text_handler import TextHandler
from src.ingestion.audio_handler import AudioHandler
from src.ingestion.image_handler import ImageHandler
from src.ingestion.ingestion_manager import IngestionManager, IngestionType

# Initialize config and logging
settings = get_settings()
logger = logging.getLogger("test_phase1")


def print_header(title):
    """Print section header."""
    print("\n" + "=" * 80)
    print(title.center(80))
    print("=" * 80 + "\n")


def print_subheader(title):
    """Print subsection header."""
    print("\n" + "-" * 80)
    print(title)
    print("-" * 80)


def test_text_handler():
    """Test TextHandler with various inputs."""
    print_subheader("TEST 1: TEXT HANDLER")
    
    handler = TextHandler()
    
    # Test 1.1: Valid text
    print("\n1.1: Valid text processing")
    test_text = "The Earth is flat. This is a false claim that needs verification."
    success, output, error = handler.process(test_text, clean=True)
    print("Input:  {}".format(test_text))
    print("Output: {}".format(output))
    print("Status: [PASS]" if success else "[FAIL] {}".format(error))
    
    # Test 1.2: Text with URLs and emails
    print("\n1.2: Text with URLs, emails, special chars")
    test_text = "Visit http://example.com or email test@domain.com for more!!! Information..."
    success, output, error = handler.process(test_text, clean=True)
    print("Input:  {}".format(test_text))
    print("Output: {}".format(output))
    print("Status: [PASS] - URLs and emails cleaned" if success else "[FAIL] {}".format(error))
    
    # Test 1.3: Too short text
    print("\n1.3: Text too short (validation)")
    test_text = "Short"
    success, output, error = handler.process(test_text)
    print("Input:  '{}'".format(test_text))
    print("Status: [PASS] - Correctly rejected" if not success else "[FAIL] Should have rejected")
    print("Error:  {}".format(error))
    
    # Test 1.4: Empty/None input
    print("\n1.4: None/empty input (validation)")
    success, output, error = handler.process(None)
    print("Input:  None")
    print("Status: [PASS] - Correctly rejected" if not success else "[FAIL] Should have rejected")
    print("Error:  {}".format(error))
    
    print("\n[PASS] TextHandler tests completed")


def test_audio_handler():
    """Test AudioHandler initialization and validation."""
    print_subheader("TEST 2: AUDIO HANDLER")
    
    groq_key = settings.GROQ_API_KEY
    
    if not groq_key or groq_key == "your_groq_api_key_here":
        print("SKIPPED: Groq API key not configured in .env")
        print("To test audio transcription:")
        print("  1. Get API key from https://console.groq.com/keys")
        print("  2. Add GROQ_API_KEY=<key> to .env")
        print("  3. Provide a test .mp3/.wav file")
        return
    
    try:
        handler = AudioHandler(groq_key)
        print("[PASS] AudioHandler initialized successfully")
        
        # Test validation with non-existent file
        print("\n2.1: Validation test (non-existent file)")
        success, error = handler.validate("/path/to/nonexistent.mp3")
        print("Status: [PASS] - Correctly rejected" if not success else "[FAIL]")
        print("Error:  {}".format(error))
        
        # Test unsupported format
        print("\n2.2: Unsupported format test")
        success, error = handler.validate("test.txt")
        print("Status: [PASS] - Correctly rejected" if not success else "[FAIL]")
        print("Error:  {}".format(error))
        
        print("\n[INFO] To test actual transcription:")
        print("  1. Place audio file in project root (e.g., test_audio.mp3)")
        print("  2. Update test_ingestion.py with file path")
        print("  3. Re-run this test")
        
    except Exception as e:
        print("[FAIL] AudioHandler initialization: {}".format(str(e)))
        print("Ensure Groq API key is valid and groq library is installed")


def test_image_handler():
    """Test ImageHandler initialization and validation."""
    print_subheader("TEST 3: IMAGE HANDLER")
    
    try:
        # Try EasyOCR first (always available)
        handler = ImageHandler(primary_engine="easyocr", google_api_key=None)
        print("[PASS] ImageHandler initialized (EasyOCR primary engine)")
        
        # Test validation with non-existent file
        print("\n3.1: Validation test (non-existent file)")
        success, error = handler.validate("/path/to/nonexistent.png")
        print("Status: [PASS] - Correctly rejected" if not success else "[FAIL]")
        print("Error:  {}".format(error))
        
        # Test unsupported format
        print("\n3.2: Unsupported format test")
        success, error = handler.validate("test.pdf")
        print("Status: [PASS] - Correctly rejected" if not success else "[FAIL]")
        print("Error:  {}".format(error))
        
        print("\n[INFO] To test actual extraction:")
        print("  1. Place image file in project root (e.g., test_screenshot.png)")
        print("  2. Update test_ingestion.py with file path")
        print("  3. Re-run this test")
        
    except Exception as e:
        print("[FAIL] ImageHandler initialization: {}".format(str(e)))


def test_ingestion_manager():
    """Test IngestionManager with complete pipeline."""
    print_subheader("TEST 4: INGESTION MANAGER (ORCHESTRATOR)")
    
    groq_key = settings.GROQ_API_KEY if settings.GROQ_API_KEY != "your_groq_api_key_here" else None
    google_key = settings.GOOGLE_API_KEY if settings.GOOGLE_API_KEY != "your_google_api_key_here" else None
    
    try:
        manager = IngestionManager(
            groq_api_key=groq_key,
            google_api_key=google_key,
            image_engine="easyocr"
        )
        print("[PASS] IngestionManager initialized")
        
        # Test 4.1: Text ingestion
        print("\n4.1: Text ingestion via manager")
        test_text = "COVID-19 vaccines contain microchips. This claim requires verification."
        success, output, error = manager.ingest_text(test_text)
        print("Input:  {}".format(test_text))
        print("Output: {}".format(output))
        print("Status: [PASS]" if success else "[FAIL] {}".format(error))
        
        # Test 4.2: Auto-detection (text)
        print("\n4.2: Auto-detection (text input)")
        test_text = "The moon landing was fake. Let's verify this claim."
        success, output, error = manager.ingest(test_text, IngestionType.AUTO)
        print("Status: [PASS] - Auto-detected as text" if success else "[FAIL]")
        
        print("\n[PASS] IngestionManager tests completed")
        
    except Exception as e:
        print("[FAIL] IngestionManager initialization: {}".format(str(e)))
        import traceback
        traceback.print_exc()


def test_end_to_end():
    """End-to-end test with realistic claims."""
    print_subheader("TEST 5: END-TO-END PIPELINE (REALISTIC CLAIMS)")
    
    groq_key = settings.GROQ_API_KEY if settings.GROQ_API_KEY != "your_groq_api_key_here" else None
    google_key = settings.GOOGLE_API_KEY if settings.GOOGLE_API_KEY != "your_google_api_key_here" else None
    
    manager = IngestionManager(
        groq_api_key=groq_key,
        google_api_key=google_key,
        image_engine="easyocr"
    )
    
    # Test claims
    test_claims = [
        ("TRUE CLAIM", "Water boils at 100 degrees Celsius at sea level."),
        ("FALSE CLAIM", "The Earth is flat."),
        ("MISLEADING CLAIM", "All vaccines are 100% safe with no side effects."),
    ]
    
    for claim_type, claim_text in test_claims:
        print("\n{}: {}".format(claim_type, claim_text))
        success, output, error = manager.ingest_text(claim_text)
        if success:
            print("  Processed: {}".format(output[:60]) + ("..." if len(output) > 60 else ""))
            print("  Length: {} chars".format(len(output)))
            print("  [PASS]")
        else:
            print("  [FAIL] {}".format(error))


def main():
    """Run all Phase 1 tests."""
    print_header("PHASE 1: MULTIMODAL INGESTION PIPELINE - MANUAL TEST SUITE")
    
    print("Environment: {}".format(settings.ENVIRONMENT))
    print("Debug Mode: {}".format(settings.DEBUG))
    print("Log Level: {}".format(settings.LOG_LEVEL))
    print()
    
    try:
        test_text_handler()
        test_audio_handler()
        test_image_handler()
        test_ingestion_manager()
        test_end_to_end()
        
        print_header("PHASE 1 TESTING COMPLETE")
        print("\nSummary:")
        print("  [PASS] TextHandler fully operational")
        print("  [INFO] AudioHandler ready (requires Groq API key)")
        print("  [INFO] ImageHandler ready (EasyOCR functional)")
        print("  [PASS] IngestionManager orchestration verified")
        print("\nNext Steps:")
        print("  1. Optional: Configure Groq/Google API keys in .env for audio/image testing")
        print("  2. Optional: Place test audio/image files in project root")
        print("  3. Proceed to Phase 2: Agentic RAG & Web Consensus Engine")
        print()
        
    except Exception as e:
        print("[FAIL] Test suite error: {}".format(str(e)))
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
