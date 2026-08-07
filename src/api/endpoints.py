"""
API Endpoint Handlers

Main route implementations for FastAPI application.
"""

import logging
from typing import Optional
from datetime import datetime
import base64

from fastapi import APIRouter, HTTPException, BackgroundTasks, Form, Request
from fastapi.responses import StreamingResponse
import io
import os
import requests

from .models import (
    HealthResponse,
    IngestionRequest,
    IngestionResponse,
    VerifyRequest,
    VerifyResponse,
    GenerateCardRequest,
    GenerateCardResponse,
    BatchVerifyRequest,
    BatchVerifyResponse,
    ErrorResponse,
)

logger = logging.getLogger(__name__)

# Global services (initialized in app.py)
ingestion_manager = None
fact_checking_agent = None
card_generator = None


def init_services(ingestion_mgr, agent, card_gen):
    """Initialize service instances."""
    global ingestion_manager, fact_checking_agent, card_generator
    ingestion_manager = ingestion_mgr
    fact_checking_agent = agent
    card_generator = card_gen
    logger.info("Services initialized")


def create_router() -> APIRouter:
    """Create API router with all endpoints."""
    router = APIRouter(prefix="/api", tags=["fact-checking"])

    @router.get("/health", response_model=HealthResponse)
    async def health_check():
        """Health check endpoint."""
        return HealthResponse(
            status="healthy",
            version="0.1.0",
            timestamp=datetime.now().isoformat(),
        )

    @router.post("/ingest", response_model=IngestionResponse)
    async def ingest_claim(request: IngestionRequest):
        """
        Ingest a claim from text, audio, or image.
        
        - **source**: Text, file path, or URL
        - **input_type**: AUTO (auto-detect), TEXT, AUDIO, or IMAGE
        - **clean**: Remove URLs, emails, phone numbers
        """
        if ingestion_manager is None:
            raise HTTPException(
                status_code=503,
                detail="Ingestion service not initialized"
            )
        
        try:
            logger.info(f"Ingesting {request.input_type}: {request.source[:50]}")
            
            success, text, error = ingestion_manager.ingest(
                source=request.source,
                input_type=request.input_type.lower(),  # Convert to lowercase for enum
                clean=request.clean,
            )
            
            if not success:
                logger.warning(f"Ingestion failed: {error}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Ingestion failed: {error}"
                )
            
            return IngestionResponse(
                success=True,
                text=text,
                character_count=len(text) if text else 0,
                input_type=request.input_type,
            )
        
        except Exception as e:
            logger.error(f"Ingestion error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Ingestion error: {str(e)}"
            )

    @router.post("/verify", response_model=VerifyResponse)
    async def verify_claim(request: VerifyRequest):
        """
        Verify a fact-checking claim.
        
        - **claim**: The claim to fact-check (10-5000 characters)
        - **strategy**: fast (quick), balanced (default), or thorough (comprehensive)
        - **include_reasoning**: Include detailed reasoning in response
        """
        if fact_checking_agent is None:
            raise HTTPException(
                status_code=503,
                detail="Fact-checking service not initialized"
            )
        
        try:
            logger.info(f"Verifying claim: {request.claim[:50]}")
            
            result = fact_checking_agent.verify_claim(
                claim=request.claim,
                include_reasoning=request.include_reasoning,
            )
            
            return VerifyResponse(
                claim=result.claim,
                verdict=result.verdict,
                confidence=result.confidence,
                reasoning=result.reasoning,
                sources=result.sources,
                key_evidence=result.key_evidence,
                timestamp=result.timestamp,
            )
        
        except Exception as e:
            logger.error(f"Verification error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Verification error: {str(e)}"
            )

    @router.post("/verify-batch", response_model=BatchVerifyResponse)
    async def batch_verify(request: BatchVerifyRequest):
        """
        Verify multiple claims in a single request.
        
        - **claims**: List of claims (1-100 claims)
        - **strategy**: fast, balanced, or thorough
        """
        if fact_checking_agent is None:
            raise HTTPException(
                status_code=503,
                detail="Fact-checking service not initialized"
            )
        
        try:
            logger.info(f"Batch verifying {len(request.claims)} claims")
            
            results = fact_checking_agent.batch_verify(request.claims)
            
            completed = sum(1 for r in results if r.verdict != "UNVERIFIABLE")
            failed = len(results) - completed
            
            return BatchVerifyResponse(
                total=len(request.claims),
                completed=completed,
                failed=failed,
                results=[
                    VerifyResponse(
                        claim=r.claim,
                        verdict=r.verdict,
                        confidence=r.confidence,
                        reasoning=r.reasoning,
                        sources=r.sources,
                        key_evidence=r.key_evidence,
                        timestamp=r.timestamp,
                    )
                    for r in results
                ],
                timestamp=datetime.now().isoformat(),
            )
        
        except Exception as e:
            logger.error(f"Batch verification error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Batch verification error: {str(e)}"
            )

    @router.post("/generate-card")
    async def generate_card(request: GenerateCardRequest):
        """
        Generate a visual proof card.
        
        - **claim**: Claim text
        - **verdict**: TRUE, FALSE, MISLEADING, or UNVERIFIABLE
        - **confidence**: Confidence score (0-1)
        - **preset**: Social media preset (facebook, twitter, instagram, linkedin, etc.)
        - **theme**: Color theme (light, dark, minimal, bold)
        
        Returns PNG image as byte stream.
        """
        if card_generator is None:
            raise HTTPException(
                status_code=503,
                detail="Card generation service not initialized"
            )
        
        try:
            logger.info(f"Generating card: {request.claim[:30]}... ({request.verdict})")
            
            generator = card_generator.__class__(
                preset=request.preset,
                theme=request.theme,
            )
            
            card = generator.generate(
                claim=request.claim,
                verdict=request.verdict,
                confidence=request.confidence,
                reasoning=request.reasoning,
                sources=request.sources,
                key_evidence=request.key_evidence,
            )
            
            card_bytes = card.to_bytes()
            
            return StreamingResponse(
                iter([card_bytes]),
                media_type="image/png",
                headers={
                    "Content-Disposition": f"attachment; filename=card_{request.verdict}.png"
                },
            )
        
        except Exception as e:
            logger.error(f"Card generation error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Card generation error: {str(e)}"
            )

    @router.get("/stats")
    async def get_stats():
        """Get service statistics."""
        return {
            "message": "Statistics endpoint",
            "timestamp": datetime.now().isoformat(),
            "version": "0.1.0",
        }

    @router.post("/v1/whatsapp")
    async def whatsapp_webhook(
        background_tasks: BackgroundTasks,
        From: str = Form(...),
        Body: str = Form(default=""),
        MediaUrl0: str = Form(default=None),
        MediaContentType0: str = Form(default=None),
        MessageSid: str = Form(default=None),
        SmsSid: str = Form(default=None),
    ):
        """
        WhatsApp webhook endpoint for Twilio integration.
        
        Receives incoming WhatsApp messages and processes them asynchronously.
        
        Flow:
        1. Acknowledge receipt immediately (avoid timeout)
        2. Schedule async processing in background
        3. Return TwiML response to WhatsApp
        """
        from twilio.twiml.messaging_response import MessagingResponse
        
        try:
            logger.info(f"Received WhatsApp message from {From}")
            
            # Get WhatsApp handler
            from src.whatsapp.handler import WhatsAppHandler
            
            if not ingestion_manager or not fact_checking_agent:
                logger.error("Pipeline services not initialized")
                twiml = MessagingResponse()
                twiml.message("⚠️ Bot services are currently unavailable. Please try again later.")
                return twiml.to_xml()
            
            # Initialize handler
            from src.config import Settings
            config = Settings()
            whatsapp_handler = WhatsAppHandler(
                ingestion_manager=ingestion_manager,
                fact_checking_agent=fact_checking_agent,
                card_generator=card_generator,
                twilio_account_sid=config.TWILIO_ACCOUNT_SID,
                twilio_auth_token=config.TWILIO_AUTH_TOKEN,
            )
            
            # Parse incoming message
            msg, error = whatsapp_handler.parse_incoming_message(
                from_number=From,
                body=Body,
                media_url=MediaUrl0,
                media_content_type=MediaContentType0,
            )
            
            if error:
                logger.error(f"Parse error: {error}")
                twiml = MessagingResponse()
                twiml.message(f"❌ Error: {error}")
                return twiml.to_xml()
            
            # Schedule background processing
            from src.config import Settings
            config = Settings()
            background_tasks.add_task(
                process_whatsapp_message,
                user_phone=From,
                message=msg,
                whatsapp_handler=whatsapp_handler,
                config=config,
                message_sid=MessageSid or SmsSid,
            )
            
            # Return empty TwiML response (we send updates via Twilio REST client in background)
            twiml = MessagingResponse()
            logger.info(f"Acknowledged message from {From}, processing in background")
            return twiml.to_xml()
        
        except Exception as e:
            logger.error(f"WhatsApp webhook error: {str(e)}")
            try:
                from twilio.twiml.messaging_response import MessagingResponse
                twiml = MessagingResponse()
                twiml.message("⚠️ An error occurred. Please try again.")
                return twiml.to_xml()
            except:
                raise HTTPException(status_code=500, detail="WhatsApp processing error")

    @router.post("/v1/whapi")
    async def whapi_webhook(
        request: Request,
        background_tasks: BackgroundTasks
    ):
        """
        WhatsApp webhook endpoint for Whapi.Cloud integration.
        Receives incoming messages from direct Indian (+91) phone numbers.
        """
        try:
            payload = await request.json()
            logger.info("Received Whapi webhook payload")
            
            messages = payload.get("messages", [])
            if not messages:
                return {"status": "ok", "message": "no messages"}
                
            from src.config import Settings
            config = Settings()
            whapi_token = config.WHAPI_API_TOKEN or os.getenv("WHAPI_API_TOKEN", "")
            
            from src.whatsapp.handler import WhatsAppHandler, WhatsAppMessage
            whatsapp_handler = WhatsAppHandler(
                ingestion_manager=ingestion_manager,
                fact_checking_agent=fact_checking_agent,
                card_generator=card_generator,
            )
            
            for msg_item in messages:
                # Ignore outgoing messages sent by the bot
                if msg_item.get("from_me"):
                    continue
                    
                raw_sender = msg_item.get("from", "")
                sender_id = raw_sender.split("@")[0].strip() if "@" in raw_sender else raw_sender.strip()
                if not sender_id:
                    continue
                    
                msg_type = msg_item.get("type", "text")
                body = ""
                media_url = None
                media_type = None
                
                if msg_type == "text":
                    body = msg_item.get("text", {}).get("body", "")
                elif msg_type == "image":
                    body = msg_item.get("caption", "") or msg_item.get("image", {}).get("caption", "")
                    media_url = msg_item.get("image", {}).get("link", "")
                    media_type = "image"
                elif msg_type in ["voice", "audio"]:
                    media_url = msg_item.get("voice", {}).get("link", "") or msg_item.get("audio", {}).get("link", "")
                    media_type = "audio"
                    
                msg = WhatsAppMessage(
                    user_phone=sender_id,
                    message_body=body,
                    media_url=media_url,
                    media_type=media_type,
                )
                
                # Send immediate acknowledgment back via Whapi API
                if whapi_token:
                    try:
                        requests.post(
                            "https://gate.whapi.cloud/messages/text",
                            headers={"Authorization": f"Bearer {whapi_token}", "Content-Type": "application/json"},
                            json={"to": f"{sender_id}@s.whatsapp.net", "body": "🔍 Satyamev-Bot is now verifying your claim. Please wait a moment..."},
                            timeout=5
                        )
                    except Exception as ack_err:
                        logger.warning(f"Failed to send Whapi ack: {ack_err}")
                
                # Schedule background processing
                background_tasks.add_task(
                    process_whapi_message,
                    user_phone=sender_id,
                    message=msg,
                    whatsapp_handler=whatsapp_handler,
                    whapi_token=whapi_token,
                )
                
            return {"status": "ok", "processed": len(messages)}
            
        except Exception as e:
            logger.error(f"Whapi webhook error: {str(e)}")
            return {"status": "error", "error": str(e)}

    return router


async def process_whapi_message(user_phone: str, message, whatsapp_handler, whapi_token: str):
    """
    Background task: Process Whapi message through pipeline and send verdict back.
    """
    try:
        logger.info(f"Background Whapi processing started for {user_phone}")
        result = whatsapp_handler.process_message(message)
        
        from src.whatsapp.formatter import WhatsAppFormatter
        response_text = WhatsAppFormatter.format_verdict_message(result)
        
        if whapi_token:
            resp = requests.post(
                "https://gate.whapi.cloud/messages/text",
                headers={"Authorization": f"Bearer {whapi_token}", "Content-Type": "application/json"},
                json={"to": f"{user_phone}@s.whatsapp.net", "body": response_text},
                timeout=10
            )
            logger.info(f"Whapi response sent to {user_phone}: HTTP {resp.status_code}")
    except Exception as e:
        logger.error(f"Whapi background processing error: {str(e)}")


# Global reference to Twilio client for background task
_twilio_client = None


def set_twilio_client(client):
    """Set Twilio client for background processing."""
    global _twilio_client
    _twilio_client = client
    logger.info("Twilio client configured")


async def process_whatsapp_message(user_phone: str, message, whatsapp_handler, config=None, message_sid: str = None):
    """
    Background task: Process WhatsApp message through full pipeline.
    
    This runs asynchronously without blocking the webhook response.
    """
    from twilio.rest import Client
    
    try:
        logger.info(f"Background processing started for {user_phone} (message_sid={message_sid})")
        
        # Initialize Twilio client for sending response
        if config is None:
            from src.config import Settings
            config = Settings()
        
        account_sid = config.TWILIO_ACCOUNT_SID
        auth_token = config.TWILIO_AUTH_TOKEN
        twilio_phone = config.TWILIO_PHONE_NUMBER or "whatsapp:+14155238886"
        
        if not account_sid or not auth_token:
            logger.error("Twilio credentials not configured")
            return
        
        client = Client(account_sid, auth_token)
        
        # Send initial status receipt message
        client.messages.create(
            from_=twilio_phone,
            body="🔍 Satyamev-Bot is now verifying your claim. Please wait a moment...",
            to=user_phone,
        )
        
        # Define status callback function to send native WhatsApp typing indicator
        def update_status(text: str, percent: int):
            logger.info(f"Pipeline status update [{percent}%]: {text}")
            if message_sid:
                try:
                    url = "https://messaging.twilio.com/v3/Indicators/Typing.json"
                    import requests
                    requests.post(
                        url,
                        data={"messageId": message_sid, "channel": "whatsapp"},
                        auth=(account_sid, auth_token),
                        timeout=3
                    )
                except Exception as indicator_err:
                    logger.debug(f"Failed to send typing indicator: {indicator_err}")

        # Process message through pipeline with status updates
        result = whatsapp_handler.process_message(message, status_callback=update_status)
        
        # Format response (WhatsAppFormatter guarantees clean formatting under 1500 chars)
        from src.whatsapp.formatter import WhatsAppFormatter
        response_text = WhatsAppFormatter.format_verdict_message(result)
        
        # Send response message with retry fallback
        try:
            message_sent = client.messages.create(
                from_=twilio_phone,
                body=response_text,
                to=user_phone,
            )
            logger.info(f"Response sent to {user_phone}: {message_sent.sid}")
        except Exception as send_err:
            err_str = str(send_err)
            if "1600" in err_str or "exceeds" in err_str.lower() or "limit" in err_str.lower():
                logger.warning(f"Twilio 1600 char limit triggered on send ({err_str}), applying section-aware trim...")
                # Cut at section boundary (newline) before 1400 chars to avoid breaking URLs
                cut_idx = response_text[:1350].rfind("\n\n")
                trimmed_text = response_text[:cut_idx if cut_idx > 300 else 1350] + "\n\n..."
                message_sent = client.messages.create(
                    from_=twilio_phone,
                    body=trimmed_text,
                    to=user_phone,
                )
                logger.info(f"Trimmed response successfully sent to {user_phone}: {message_sent.sid}")
            else:
                raise send_err
        
        # Send card image if available (as separate message)
        if result.get("card_bytes"):
            try:
                # For now, we'll skip the image sending as it requires file hosting
                # In production, you would:
                # 1. Upload card_bytes to cloud storage (S3, etc.)
                # 2. Get public URL
                # 3. Send media message with media_url
                logger.info(f"Card generated ({len(result['card_bytes'])} bytes) but image sending requires cloud storage setup")
            except Exception as e:
                logger.warning(f"Failed to send card image: {e}")
    
    except Exception as e:
        logger.error(f"Background processing error: {str(e)}")
        
        try:
            from twilio.rest import Client
            
            if config is None:
                from src.config import Settings
                config = Settings()
            
            account_sid = config.TWILIO_ACCOUNT_SID
            auth_token = config.TWILIO_AUTH_TOKEN
            twilio_phone = config.TWILIO_PHONE_NUMBER or "whatsapp:+14155238886"
            
            if account_sid and auth_token:
                client = Client(account_sid, auth_token)
                from src.whatsapp.formatter import WhatsAppFormatter
                error_msg = WhatsAppFormatter.format_error_message("service_error")
                
                client.messages.create(
                    from_=twilio_phone,
                    body=error_msg,
                    to=user_phone,
                )
        except Exception as fallback_error:
            logger.error(f"Failed to send error message: {fallback_error}")
