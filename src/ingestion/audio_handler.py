"""
Audio Handler Module
====================

Handles audio file ingestion via Groq Whisper API.
Supports: .mp3, .wav, .ogg, .flac, .m4a

Stream-based transcription for efficient memory usage.
"""

import logging
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger("satyamev_bot.ingestion.audio")


class AudioHandler:
    """
    Handles audio file transcription via Groq Whisper API.
    
    Features:
    - Multi-format support (mp3, wav, ogg, flac, m4a)
    - File validation and size limits
    - Stream-based processing for efficiency
    - Robust error handling
    """
    
    # Configuration constants
    SUPPORTED_FORMATS = {".mp3", ".wav", ".ogg", ".flac", ".m4a"}
    MAX_FILE_SIZE_MB = 25  # Groq Whisper limit
    
    def __init__(self, api_key: str):
        """
        Initialize AudioHandler with Groq API key.
        
        Args:
            api_key: Groq API key for Whisper access
            
        Raises:
            ValueError: If API key is empty or invalid
        """
        if not api_key or not api_key.strip():
            raise ValueError("Groq API key is required but not provided")
        
        self.api_key = api_key
        
        try:
            from groq import Groq
            self.client = Groq(api_key=api_key)
            logger.info("Groq Whisper client initialized successfully")
        except ImportError:
            error = "Groq library not installed. Run: pip install groq"
            logger.error(error)
            raise ImportError(error)
        except Exception as e:
            error = "Failed to initialize Groq client: {}".format(str(e))
            logger.error(error)
            raise RuntimeError(error)
    
    def validate(self, audio_path: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        Validate audio file path and format.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if audio_path is None:
            error = "Audio file path is None"
            logger.warning(error)
            return False, error
        
        path = Path(audio_path)
        
        if not path.exists():
            error = "Audio file not found: {}".format(audio_path)
            logger.warning(error)
            return False, error
        
        if not path.is_file():
            error = "Path is not a file: {}".format(audio_path)
            logger.warning(error)
            return False, error
        
        file_ext = path.suffix.lower()
        if file_ext not in self.SUPPORTED_FORMATS:
            error = "Unsupported audio format: {}. Supported: {}".format(
                file_ext, ', '.join(self.SUPPORTED_FORMATS)
            )
            logger.warning(error)
            return False, error
        
        file_size_mb = path.stat().st_size / (1024 * 1024)
        if file_size_mb > self.MAX_FILE_SIZE_MB:
            error = "Audio file too large: {:.2f}MB (max: {}MB)".format(
                file_size_mb, self.MAX_FILE_SIZE_MB
            )
            logger.warning(error)
            return False, error
        
        return True, None
    
    def transcribe(self, audio_path: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Transcribe audio file using Groq Whisper API.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Tuple of (success, transcription_text, error_message)
        """
        logger.info("Starting audio transcription: {}".format(audio_path))
        
        # Step 1: Validate
        is_valid, error = self.validate(audio_path)
        if not is_valid:
            logger.error("Audio validation failed: {}".format(error))
            return False, None, error
        
        try:
            path = Path(audio_path)
            
            # Step 2: Open file and send to Groq Whisper
            logger.debug("Opening audio file: {}".format(path.name))
            with open(path, 'rb') as audio_file:
                # Call Groq Whisper API
                logger.debug("Sending to Groq Whisper API...")
                transcription = self.client.audio.transcriptions.create(
                    file=(path.name, audio_file, 'audio/mpeg'),  # Let Groq detect format
                    model="whisper-large-v3-turbo"
                )
            
            # Step 3: Extract text
            if not transcription.text or not transcription.text.strip():
                error = "Transcription returned empty text"
                logger.warning(error)
                return False, None, error
            
            transcribed_text = transcription.text.strip()
            logger.info("Transcription successful: {} chars".format(len(transcribed_text)))
            return True, transcribed_text, None
            
        except FileNotFoundError as e:
            error = "Audio file not found: {}".format(str(e))
            logger.error(error)
            return False, None, error
        except IOError as e:
            error = "Failed to read audio file: {}".format(str(e))
            logger.error(error, exc_info=True)
            return False, None, error
        except Exception as e:
            error = "Groq Whisper transcription failed: {}".format(str(e))
            logger.error(error, exc_info=True)
            return False, None, error
