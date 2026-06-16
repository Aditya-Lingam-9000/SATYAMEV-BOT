"""
WhatsApp Message Handler

Processes incoming WhatsApp messages and routes them through the ingestion,
verification, and card generation pipeline.
"""

import logging
import os
import tempfile
import requests
from pathlib import Path
from typing import Optional, Dict, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class WhatsAppMessage:
    """Represents an incoming WhatsApp message."""
    
    def __init__(
        self,
        user_phone: str,
        message_body: str,
        media_url: Optional[str] = None,
        media_type: Optional[str] = None,
    ):
        """
        Initialize WhatsApp message.
        
        Args:
            user_phone: Sender's WhatsApp phone number (with country code)
            message_body: Text content of message
            media_url: URL of media attachment (image, audio, etc.)
            media_type: Type of media (image, audio, etc.)
        """
        self.user_phone = user_phone
        self.message_body = message_body.strip() if message_body else ""
        self.media_url = media_url
        self.media_type = media_type
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "user_phone": self.user_phone,
            "message_body": self.message_body,
            "media_url": self.media_url,
            "media_type": self.media_type,
            "timestamp": self.timestamp,
        }


class WhatsAppHandler:
    """
    Handles incoming WhatsApp messages and routes them through the pipeline.
    
    Pipeline Flow:
    1. Parse incoming message
    2. Detect media type (text, audio, image)
    3. Ingest using appropriate handler
    4. Verify claim with agent
    5. Generate visual card
    6. Format response for WhatsApp
    7. Send back asynchronously
    """
    
    def __init__(
        self,
        ingestion_manager=None,
        fact_checking_agent=None,
        card_generator=None,
        twilio_account_sid: Optional[str] = None,
        twilio_auth_token: Optional[str] = None,
    ):
        """Initialize handler with pipeline components and Twilio credentials."""
        self.ingestion_manager = ingestion_manager
        self.fact_checking_agent = fact_checking_agent
        self.card_generator = card_generator
        self.twilio_account_sid = twilio_account_sid
        self.twilio_auth_token = twilio_auth_token
    
    @staticmethod
    def _detect_media_type_from_url(media_url: str) -> str:
        """
        Detect media type from URL file extension.
        Falls back to 'document' if unknown.
        """
        if any(x in media_url.lower() for x in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
            return "image"
        elif any(x in media_url.lower() for x in ['.mp3', '.wav', '.ogg', '.m4a', '.flac']):
            return "audio"
        else:
            return "document"
    
    def _download_twilio_media(self, media_url: str, media_type: str) -> Optional[str]:
        """
        Download media file from Twilio URL to temporary location.
        
        Args:
            media_url: Twilio media URL
            media_type: Type of media (image, audio)
            
        Returns:
            Local file path or None if download failed
        """
        try:
            # Create temp directory if it doesn't exist
            temp_dir = Path(tempfile.gettempdir()) / "satyamev_media"
            temp_dir.mkdir(exist_ok=True, parents=True)
            
            # Determine file extension based on media type
            if media_type == "image":
                # Default to jpg for images
                file_ext = ".jpg"
            elif media_type == "audio":
                # Default to ogg for audio (Twilio's default format)
                file_ext = ".ogg"
            else:
                file_ext = ".tmp"
            
            # Create temp file path
            temp_file = temp_dir / f"media_{int(datetime.now().timestamp())}{file_ext}"
            
            # Download file with Twilio auth
            logger.info(f"Downloading Twilio media to {temp_file}")
            
            auth = (self.twilio_account_sid, self.twilio_auth_token) if self.twilio_account_sid else None
            response = requests.get(media_url, auth=auth, timeout=30)
            response.raise_for_status()
            
            # Save to temp file
            with open(temp_file, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Media downloaded successfully: {temp_file}")
            return str(temp_file)
            
        except Exception as e:
            logger.error(f"Failed to download Twilio media: {str(e)}")
            return None
    
    def parse_incoming_message(
        self,
        from_number: str,
        body: str,
        media_url: Optional[str] = None,
        media_content_type: Optional[str] = None,
    ) -> Tuple[WhatsAppMessage, Optional[str]]:
        """
        Parse incoming Twilio message.
        
        Args:
            from_number: Sender's phone (with 'whatsapp:' prefix from Twilio)
            body: Message text
            media_url: Media attachment URL
            media_content_type: MIME type from Twilio (e.g., 'image/jpeg', 'audio/ogg')
        
        Returns:
            (WhatsAppMessage, error_message)
        """
        try:
            # Remove 'whatsapp:' prefix if present
            phone = from_number.replace("whatsapp:", "").strip()
            
            if not phone:
                return None, "Invalid phone number"
            
            # Detect media type from Twilio's Content-Type or URL
            media_type = None
            if media_url:
                # First, try to use Twilio's Content-Type header
                if media_content_type:
                    if media_content_type.startswith('image/'):
                        media_type = "image"
                    elif media_content_type.startswith('audio/'):
                        media_type = "audio"
                    else:
                        # For other types, try to infer from URL
                        media_type = self._detect_media_type_from_url(media_url)
                else:
                    # Fallback to URL-based detection
                    media_type = self._detect_media_type_from_url(media_url)
            
            msg = WhatsAppMessage(
                user_phone=phone,
                message_body=body,
                media_url=media_url,
                media_type=media_type,
            )
            
            logger.info(f"Parsed message from {phone}: {body[:50]}..." if body else f"Media: {media_type}")
            return msg, None
        
        except Exception as e:
            error_msg = f"Failed to parse message: {str(e)}"
            logger.error(error_msg)
            return None, error_msg
    
    def process_message(self, message: WhatsAppMessage, status_callback=None) -> Dict:
        """
        Process WhatsApp message through complete pipeline.
        
        Args:
            message: WhatsAppMessage object
            status_callback: Optional callback function(text, percent) to report progress
        
        Returns:
            Dict with verdict, reasoning, sources, card_bytes
        """
        result = {
            "success": False,
            "verdict": None,
            "confidence": None,
            "reasoning": None,
            "sources": [],
            "key_evidence": [],
            "card_bytes": None,
            "error": None,
        }
        
        try:
            # Step 1: Determine input source (text or media)
            if message.media_url and message.media_type:
                if status_callback:
                    status_callback("Downloading media file", 15)
                # Download media from Twilio to local temp storage
                local_path = self._download_twilio_media(message.media_url, message.media_type)
                if not local_path:
                    result["error"] = f"Failed to download media file from URL: {message.media_url}"
                    logger.error(result["error"])
                    return result
                source = local_path
                input_type = message.media_type.upper()
            elif message.message_body:
                source = message.message_body
                input_type = "TEXT"
            else:
                result["error"] = "No text or media provided"
                return result
            
            logger.info(f"Processing {input_type} input from {message.user_phone}")
            
            if status_callback:
                status_callback("Extracting text content from claim", 30)
            
            # Step 2: Ingest claim
            if not self.ingestion_manager:
                result["error"] = "Ingestion service not available"
                return result
            
            success, text, error = self.ingestion_manager.ingest(
                source=source,
                input_type=input_type.lower(),
                clean=True,
            )
            
            if not success:
                result["error"] = f"Failed to ingest: {error}"
                logger.error(f"Ingestion failed: {error}")
                return result
            
            if not text or len(text) < 10:
                result["error"] = "No valid text extracted from input (minimum 10 characters required)"
                return result
            
            logger.info(f"Extracted text: {text[:100]}")
            
            if status_callback:
                status_callback("Searching trusted web databases and consensus", 55)
            
            # Step 3: Verify claim
            if not self.fact_checking_agent:
                result["error"] = "Verification service not available"
                return result
            
            if status_callback:
                status_callback("Analyzing evidence and synthesizing verdict", 75)
            
            verdict_result = self.fact_checking_agent.verify_claim(text)
            
            result["verdict"] = verdict_result.verdict
            result["confidence"] = verdict_result.confidence
            result["reasoning"] = verdict_result.reasoning
            result["sources"] = verdict_result.sources
            result["key_evidence"] = verdict_result.key_evidence
            result["language"] = getattr(verdict_result, "language", "English")
            
            logger.info(f"Verdict: {verdict_result.verdict} ({verdict_result.confidence:.0%})")
            
            # Step 4: Generate visual card
            if self.card_generator:
                if status_callback:
                    status_callback("Rendering final visual verdict card", 90)
                try:
                    generator = self.card_generator.__class__(
                        preset="instagram",  # Square for WhatsApp
                        theme="dark",
                    )
                    
                    card = generator.generate(
                        claim=text,
                        verdict=verdict_result.verdict,
                        confidence=verdict_result.confidence,
                        reasoning=verdict_result.reasoning[:100],  # Truncate for card
                        sources=verdict_result.sources[:3],  # Limit to 3 sources
                        key_evidence=verdict_result.key_evidence[:2],  # Limit to 2 evidence
                    )
                    
                    result["card_bytes"] = card.to_bytes()
                    logger.info(f"Card generated: {len(result['card_bytes'])} bytes")
                
                except Exception as e:
                    logger.warning(f"Card generation failed: {e}")
            
            if status_callback:
                status_callback("Fact-check report compiled successfully", 100)
            
            result["success"] = True
            return result
        
        except Exception as e:
            error_msg = f"Pipeline error: {str(e)}"
            logger.error(error_msg)
            result["error"] = error_msg
            return result
    
    def get_processing_status(self) -> Dict:
        """Get handler status and available services."""
        return {
            "ingestion_available": self.ingestion_manager is not None,
            "verification_available": self.fact_checking_agent is not None,
            "card_generation_available": self.card_generator is not None,
            "timestamp": datetime.now().isoformat(),
        }
