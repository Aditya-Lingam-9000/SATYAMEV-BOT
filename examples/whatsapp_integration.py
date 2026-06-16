"""
WhatsApp Bot Integration Examples - Phase 5

Demonstrates how to set up and use the WhatsApp bot with Twilio.

Two modes:
1. Local Development: Test with mock messages
2. Twilio Sandbox: Live WhatsApp integration
"""

import os
import sys
from pathlib import Path

# Setup paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.whatsapp.handler import WhatsAppHandler, WhatsAppMessage
from src.whatsapp.formatter import WhatsAppFormatter
from src.config import Settings
from src.ingestion.ingestion_manager import IngestionManager
from src.brain.agent import FactCheckingAgent
from src.cards.generator import CardGenerator


def example_1_local_testing():
    """Example 1: Local testing with mock messages."""
    print("\n" + "=" * 80)
    print("EXAMPLE 1: LOCAL TESTING WITH MOCK MESSAGES")
    print("=" * 80 + "\n")
    
    config = Settings()
    
    try:
        # Initialize services
        ingestion_manager = IngestionManager(
            groq_api_key=config.GROQ_API_KEY,
            google_api_key=config.GOOGLE_API_KEY,
        )
        
        fact_checking_agent = FactCheckingAgent(
            groq_api_key=config.GROQ_API_KEY,
            google_api_key=config.GOOGLE_API_KEY,
            tavily_api_key=config.TAVILY_API_KEY,
            strategy="fast",
        )
        
        card_generator = CardGenerator(preset="instagram", theme="dark")
        
        # Initialize handler
        handler = WhatsAppHandler(
            ingestion_manager=ingestion_manager,
            fact_checking_agent=fact_checking_agent,
            card_generator=card_generator,
        )
        
        # Test messages
        test_messages = [
            "The Earth is round",
            "COVID vaccines are harmful",
            "Water boils at 100°C at sea level",
        ]
        
        for text in test_messages:
            print(f"\n📱 Incoming Message: {text}")
            print("-" * 60)
            
            # Create WhatsApp message
            msg = WhatsAppMessage(
                user_phone="+919876543210",
                message_body=text,
            )
            
            # Process through pipeline
            result = handler.process_message(msg)
            
            # Format response
            response = WhatsAppFormatter.format_verdict_message(result)
            
            print(f"\n📤 Response:\n{response}")
            print("-" * 60)
    
    except Exception as e:
        print(f"Error: {e}")


def example_2_setup_instructions():
    """Example 2: Setup instructions for Twilio WhatsApp Sandbox."""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: TWILIO WHATSAPP SANDBOX SETUP")
    print("=" * 80 + "\n")
    
    instructions = """
STEP 1: Download and Install Ngrok
────────────────────────────────────────────────────────────
1. Download ngrok from: https://ngrok.com/download
2. Extract and add to your PATH
3. Run: ngrok http 8000
4. Copy the public URL (looks like: https://abcd-123-45-67.ngrok-free.app)


STEP 2: Create Twilio Account and Set Up Sandbox
────────────────────────────────────────────────────────────
1. Create free account at: https://www.twilio.com/
2. Go to: Messaging > Try It Out > Send a WhatsApp Message
3. Click "Connect to WhatsApp Sandbox"
4. Send the code (like "join school-text") to Twilio WhatsApp number
5. Confirm your personal WhatsApp is connected


STEP 3: Configure Your Bot
────────────────────────────────────────────────────────────
1. In Twilio Console, go to Messaging > Settings > WhatsApp Sandbox
2. Update "When a message comes in":
   - URL: https://<YOUR-NGROK-URL>/api/v1/whatsapp
   - Method: POST
   - Click Save

   Example URL: https://abcd-123-45-67.ngrok-free.app/api/v1/whatsapp


STEP 4: Configure .env File
────────────────────────────────────────────────────────────
1. Get from Twilio Console:
   TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxx
   TWILIO_AUTH_TOKEN=f7xxxxxxxxxxxxxxxxxxxxxxx

2. Set in .env:
   TWILIO_ACCOUNT_SID=<YOUR-ACCOUNT-SID>
   TWILIO_AUTH_TOKEN=<YOUR-AUTH-TOKEN>
   TWILIO_PHONE_NUMBER=whatsapp:+14155238886
   NGROK_URL=https://<YOUR-NGROK-URL>


STEP 5: Start Services
────────────────────────────────────────────────────────────
Terminal 1 - FastAPI Server:
$ cd SATYAMEV-BOT
$ .\venv\Scripts\python.exe -m src.api.app

Terminal 2 - Ngrok Tunnel:
$ ngrok http 8000

Terminal 3 - Monitor Logs (optional):
$ tail -f logs/satyamev_bot.log


STEP 6: Test Your Bot
────────────────────────────────────────────────────────────
1. Send a WhatsApp message to your Twilio number
2. Bot will respond within 60 seconds
3. For media (images/audio), just forward WhatsApp media to your bot number


TROUBLESHOOTING
────────────────────────────────────────────────────────────
❌ "Connection refused": Ensure FastAPI server is running on localhost:8000
❌ "Webhook timeout": Bot processing takes up to 60s - this is normal
❌ "No response": Check logs for errors, verify .env credentials
❌ "Image not received": Ensure media is sent directly, not forwarded
"""
    
    print(instructions)


def example_3_message_types():
    """Example 3: Handling different message types."""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: HANDLING DIFFERENT MESSAGE TYPES")
    print("=" * 80 + "\n")
    
    config = Settings()
    
    try:
        ingestion_manager = IngestionManager(
            groq_api_key=config.GROQ_API_KEY,
            google_api_key=config.GOOGLE_API_KEY,
        )
        
        fact_checking_agent = FactCheckingAgent(
            groq_api_key=config.GROQ_API_KEY,
            google_api_key=config.GOOGLE_API_KEY,
            tavily_api_key=config.TAVILY_API_KEY,
            strategy="fast",
        )
        
        handler = WhatsAppHandler(
            ingestion_manager=ingestion_manager,
            fact_checking_agent=fact_checking_agent,
        )
        
        # Message Type 1: Text
        print("\n1️⃣ TEXT MESSAGE")
        print("-" * 60)
        msg = WhatsAppMessage(
            user_phone="+919876543210",
            message_body="Is the moon made of cheese?",
        )
        result = handler.process_message(msg)
        print(f"Verdict: {result['verdict']} ({result['confidence']:.0%})")
        
        # Message Type 2: Image (mock)
        print("\n2️⃣ IMAGE MESSAGE (Screenshot)")
        print("-" * 60)
        msg = WhatsAppMessage(
            user_phone="+919876543210",
            message_body="Check this screenshot",
            media_url="https://example.com/fake_news.jpg",
            media_type="image",
        )
        print(f"Media Type: {msg.media_type}")
        print(f"Media URL: {msg.media_url}")
        print("(In production, bot would extract text via OCR)")
        
        # Message Type 3: Audio (mock)
        print("\n3️⃣ AUDIO MESSAGE (Voice Note)")
        print("-" * 60)
        msg = WhatsAppMessage(
            user_phone="+919876543210",
            message_body="Voice note attached",
            media_url="https://example.com/voice_note.ogg",
            media_type="audio",
        )
        print(f"Media Type: {msg.media_type}")
        print(f"Media URL: {msg.media_url}")
        print("(In production, bot would transcribe via Groq Whisper)")
        
    except Exception as e:
        print(f"Error: {e}")


def example_4_response_formatting():
    """Example 4: Different response formats."""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: RESPONSE FORMATTING")
    print("=" * 80 + "\n")
    
    # Format 1: Positive Verdict
    print("1️⃣ POSITIVE VERDICT RESPONSE")
    print("-" * 60)
    result = {
        "success": True,
        "verdict": "TRUE",
        "confidence": 0.99,
        "reasoning": "This is supported by scientific consensus and multiple peer-reviewed studies.",
        "sources": ["https://nasa.gov", "https://wikipedia.org"],
        "key_evidence": ["Satellite imagery confirms", "Thousands of scientific papers"],
        "card_bytes": None,
    }
    print(WhatsAppFormatter.format_verdict_message(result))
    
    # Format 2: Negative Verdict
    print("\n\n2️⃣ NEGATIVE VERDICT RESPONSE")
    print("-" * 60)
    result["verdict"] = "FALSE"
    result["confidence"] = 0.95
    result["reasoning"] = "There is no credible evidence supporting this claim."
    print(WhatsAppFormatter.format_verdict_message(result))
    
    # Format 3: Misleading Verdict
    print("\n\n3️⃣ MISLEADING VERDICT RESPONSE")
    print("-" * 60)
    result["verdict"] = "MISLEADING"
    result["confidence"] = 0.87
    result["reasoning"] = "This contains some truths but lacks important context."
    print(WhatsAppFormatter.format_verdict_message(result))
    
    # Format 4: Acknowledgment
    print("\n\n4️⃣ ACKNOWLEDGMENT MESSAGE")
    print("-" * 60)
    print(WhatsAppFormatter.format_acknowledgment_message())
    
    # Format 5: Error
    print("\n\n5️⃣ ERROR MESSAGE")
    print("-" * 60)
    print(WhatsAppFormatter.format_error_message("invalid_input"))


def example_5_production_deployment():
    """Example 5: Production deployment checklist."""
    print("\n" + "=" * 80)
    print("EXAMPLE 5: PRODUCTION DEPLOYMENT CHECKLIST")
    print("=" * 80 + "\n")
    
    checklist = """
PRE-DEPLOYMENT CHECKLIST
════════════════════════════════════════════════════════════

✅ SECURITY
  ☐ All API keys stored in secure environment (.env)
  ☐ Twilio credentials never hardcoded
  ☐ HTTPS enabled (ngrok provides this automatically)
  ☐ Request validation implemented
  ☐ Rate limiting configured
  ☐ Error messages don't expose sensitive info

✅ PERFORMANCE
  ☐ Background task processing prevents timeouts
  ☐ Async/await properly implemented
  ☐ Database connection pooling (if using DB)
  ☐ Cache configured for frequently verified claims
  ☐ Load testing completed (recommended: 100+ concurrent)

✅ RELIABILITY
  ☐ Error handling for all edge cases
  ☐ Graceful degradation if services unavailable
  ☐ Logging configured and monitored
  ☐ Health check endpoints working
  ☐ Fallback LLM (Google Gemini) configured

✅ COMPLIANCE
  ☐ WhatsApp terms of service reviewed
  ☐ Privacy policy in place
  ☐ Data retention policy defined
  ☐ GDPR compliance if handling EU users
  ☐ Terms of service displayed to users

✅ TESTING
  ☐ All unit tests passing
  ☐ Integration tests for full pipeline
  ☐ WhatsApp webhook tests done
  ☐ Long-running claim processing tested (60s timeout)
  ☐ Media handling tested (images, audio)

✅ DEPLOYMENT
  ☐ Docker image created and tested
  ☐ Production environment variables configured
  ☐ Database migrations run (if applicable)
  ☐ Monitoring and alerting set up
  ☐ Backup strategy in place
  ☐ Rollback procedure documented


PRODUCTION SETUP (AWS, Google Cloud, or Digital Ocean)
════════════════════════════════════════════════════════════

1. Deploy Docker container:
   docker build -t satyamev-bot:prod .
   docker run -p 8000:8000 --env-file .env.prod satyamev-bot:prod

2. Set Twilio webhook to production URL:
   https://your-production-domain.com/api/v1/whatsapp

3. Configure monitoring:
   - CloudWatch / Stackdriver / Datadog
   - Alert on errors, timeouts, high latency

4. Set up CI/CD pipeline:
   - GitHub Actions / GitLab CI
   - Auto-deploy on merge to main
   - Run tests before deployment


UPGRADE PATH (From Sandbox to Production)
════════════════════════════════════════════════════════════

Sandbox (Free - Unlimited):
  ✓ For hackathons and testing
  ✓ Limited to 1 phone number
  ✓ Twilio number: +14155238886
  ✓ Full access to all bot features

Production (Paid):
  1. Register business with Meta
  2. Get verified business account
  3. Request WhatsApp Business API access
  4. Get dedicated business phone number
  5. Update TWILIO_PHONE_NUMBER in .env
  6. Test thoroughly before switching


MONITORING & LOGGING
════════════════════════════════════════════════════════════

1. Application logs:
   logs/satyamev_bot.log

2. Key metrics to track:
   - Message processing time (target: <60s)
   - Error rate (target: <1%)
   - Verdict distribution (TRUE/FALSE/MISLEADING/UNVERIFIABLE)
   - API response times
   - Twilio webhook failures

3. Recommended alerts:
   - Error rate > 5%
   - Processing time > 70s
   - Twilio failures > 0
   - Low disk space
   - High memory usage
"""
    
    print(checklist)


def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("SATYAMEV-BOT WHATSAPP INTEGRATION EXAMPLES - PHASE 5")
    print("=" * 80)
    
    examples = [
        ("Local Testing", example_1_local_testing),
        ("Setup Instructions", example_2_setup_instructions),
        ("Message Types", example_3_message_types),
        ("Response Formatting", example_4_response_formatting),
        ("Production Deployment", example_5_production_deployment),
    ]
    
    print("\n" + "=" * 80)
    print("AVAILABLE EXAMPLES:")
    print("=" * 80)
    
    for i, (name, _) in enumerate(examples, 1):
        print(f"{i}. {name}")
    
    print("\n" + "=" * 80)
    
    # Run all examples
    for i, (name, example_func) in enumerate(examples, 1):
        try:
            example_func()
        except Exception as e:
            print(f"\n❌ Example {i} error: {e}")
    
    print("\n" + "=" * 80)
    print("Examples completed!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
