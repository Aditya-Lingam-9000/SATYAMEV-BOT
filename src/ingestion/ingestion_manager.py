"""
Ingestion Manager Module
=======================

Unified orchestrator for multimodal ingestion.
Routes files based on type to appropriate handler (text, audio, image).
Returns normalized, clean text output ready for verification engine.
"""

import logging
from pathlib import Path
from typing import Optional, Tuple, Literal
from enum import Enum

from .text_handler import TextHandler
from .audio_handler import AudioHandler
from .image_handler import ImageHandler

logger = logging.getLogger("satyamev_bot.ingestion.manager")


class IngestionType(str, Enum):
    """Supported ingestion types."""
    TEXT = "text"
    AUDIO = "audio"
    IMAGE = "image"
    AUTO = "auto"  # Auto-detect from file extension


class IngestionManager:
    """
    Unified multimodal ingestion orchestrator.
    
    Routes ingestion based on input type:
    - Text: Direct text string
    - Audio: Audio file (via Groq Whisper)
    - Image: Image file (via EasyOCR or Gemini Vision)
    
    Returns unified, normalized text output.
    """
    
    def __init__(self, 
                 groq_api_key: Optional[str] = None,
                 google_api_key: Optional[str] = None,
                 image_engine: Literal["easyocr", "gemini"] = "easyocr"):
        """
        Initialize IngestionManager with API keys.
        
        Args:
            groq_api_key: Groq API key (for audio transcription)
            google_api_key: Google API key (for image extraction fallback)
            image_engine: Primary image OCR engine ("easyocr" or "gemini")
        """
        logger.info("Initializing IngestionManager")
        
        # Text handler (always available)
        self.text_handler = TextHandler()
        
        # Audio handler (optional)
        self.audio_handler = None
        if groq_api_key:
            try:
                self.audio_handler = AudioHandler(groq_api_key)
                logger.info("Audio handler initialized")
            except Exception as e:
                logger.warning("Audio handler not available: {}".format(str(e)))
        else:
            logger.warning("Groq API key not provided; audio ingestion disabled")
        
        # Image handler (optional)
        self.image_handler = None
        try:
            self.image_handler = ImageHandler(
                primary_engine=image_engine,
                google_api_key=google_api_key
            )
            logger.info("Image handler initialized (engine: {})".format(image_engine))
        except Exception as e:
            logger.warning("Image handler not available: {}".format(str(e)))
        
        logger.info("IngestionManager ready")
    
    def _detect_type(self, source: str) -> IngestionType:
        """
        Auto-detect ingestion type from source.
        
        Args:
            source: Text string or file path
            
        Returns:
            IngestionType enum value
        """
        path = Path(source)
        
        # If it's a file that exists, check extension
        if path.exists() and path.is_file():
            ext = path.suffix.lower()
            
            # Audio formats
            if ext in {".mp3", ".wav", ".ogg", ".flac", ".m4a"}:
                return IngestionType.AUDIO
            
            # Image formats
            if ext in {".png", ".jpg", ".jpeg", ".bmp", ".webp"}:
                return IngestionType.IMAGE
        
        # Default to text
        return IngestionType.TEXT
    
    def ingest(self, 
               source: str, 
               input_type: IngestionType = IngestionType.AUTO,
               clean: bool = True) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Unified ingestion pipeline for all modalities.
        
        Args:
            source: Input source (text string or file path)
            input_type: Type of ingestion (auto-detect if AUTO)
            clean: Whether to perform deep text cleaning
            
        Returns:
            Tuple of (success, processed_text, error_message)
        """
        logger.info("Starting ingestion: type={}, clean={}".format(input_type, clean))
        
        # Step 1: Detect type if AUTO
        if input_type == IngestionType.AUTO:
            input_type = self._detect_type(source)
            logger.debug("Auto-detected type: {}".format(input_type))
        
        # Step 2: Route to appropriate handler
        if input_type == IngestionType.TEXT:
            logger.debug("Routing to text handler")
            success, text, error = self.text_handler.process(source, clean=clean)
        
        elif input_type == IngestionType.AUDIO:
            if not self.audio_handler:
                error = "Audio ingestion disabled (Groq API key not configured)"
                logger.error(error)
                return False, None, error
            
            logger.debug("Routing to audio handler")
            # Get transcription
            success, transcription, error = self.audio_handler.transcribe(source)
            if not success:
                return False, None, error
            
            # Clean the transcription
            logger.debug("Cleaning audio transcription")
            success, text, error = self.text_handler.process(transcription, clean=clean)
        
        elif input_type == IngestionType.IMAGE:
            if not self.image_handler:
                error = "Image ingestion disabled (handlers not available)"
                logger.error(error)
                return False, None, error
            
            logger.debug("Routing to image handler")
            # Extract text from image
            success, extracted, error = self.image_handler.extract(source)
            if not success:
                return False, None, error
            
            # Clean the extracted text
            logger.debug("Cleaning OCR output")
            success, text, error = self.text_handler.process(extracted, clean=clean)
        
        else:
            error = "Unknown ingestion type: {}".format(input_type)
            logger.error(error)
            return False, None, error
        
        # Step 3: Return result
        if success:
            logger.info("Ingestion successful: {} chars".format(len(text)))
        else:
            logger.error("Ingestion failed: {}".format(error))
        
        return success, text, error
    
    def ingest_text(self, text: str, clean: bool = True) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Convenience method for text ingestion.
        
        Args:
            text: Raw text string
            clean: Whether to perform deep text cleaning
            
        Returns:
            Tuple of (success, processed_text, error_message)
        """
        return self.ingest(text, IngestionType.TEXT, clean=clean)
    
    def ingest_audio(self, audio_path: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Convenience method for audio ingestion.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Tuple of (success, transcribed_text, error_message)
        """
        return self.ingest(audio_path, IngestionType.AUDIO, clean=True)
    
    def ingest_image(self, image_path: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Convenience method for image ingestion.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Tuple of (success, extracted_text, error_message)
        """
        return self.ingest(image_path, IngestionType.IMAGE, clean=True)
