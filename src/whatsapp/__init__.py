"""
WhatsApp Bot Integration - Phase 5

Async WhatsApp bot using Twilio Sandbox with background task processing.

Components:
- handler.py: Message processing and routing
- formatter.py: Response formatting for WhatsApp
- webhook: FastAPI endpoint for incoming messages

Architecture:
- Webhook receives message instantly
- Returns TwiML acknowledgment immediately
- Processes claim in background (up to 60s)
- Sends result back asynchronously via Twilio API
"""

__version__ = "0.1.0"
__all__ = ["handler", "formatter"]
