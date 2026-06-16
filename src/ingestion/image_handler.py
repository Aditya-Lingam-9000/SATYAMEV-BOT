"""
Image Handler Module
====================

Handles image file ingestion and OCR via EasyOCR (local CPU) or
Gemini-1.5-Flash multimodal API for text extraction from screenshots.

Features:
- Multi-format support (png, jpg, jpeg, bmp, webp)
- Dual engine support: EasyOCR (CPU-optimized) or Gemini Vision
- Automatic fallback mechanism
- Text confidence filtering
"""

import logging
from pathlib import Path
from typing import Optional, Tuple, Literal, List

# Monkeypatch PIL.Image.ANTIALIAS for EasyOCR compatibility with Pillow 10+
from PIL import Image
if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = 1

from src.config import Settings
logger = logging.getLogger("satyamev_bot.ingestion.image")


class ImageHandler:
    """
    Handles image OCR via EasyOCR or Gemini multimodal API.
    
    Features:
    - CPU-optimized EasyOCR with confidence filtering
    - Gemini-1.5-Flash multimodal vision fallback
    - Automatic engine selection
    - Confidence threshold validation
    """
    
    # Configuration constants
    SUPPORTED_FORMATS = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}
    MAX_FILE_SIZE_MB = 50
    MIN_CONFIDENCE = 0.3  # EasyOCR confidence threshold
    
    def __init__(self, 
                 primary_engine: Literal["easyocr", "gemini"] = "easyocr",
                 google_api_key: Optional[str] = None,
                 languages: Optional[List[str]] = None):
        """
        Initialize ImageHandler with optional API keys.
        
        Args:
            primary_engine: Primary OCR engine ("easyocr" or "gemini")
            google_api_key: Google API key (required if using Gemini)
            languages: List of language codes for EasyOCR
        """
        self.primary_engine = primary_engine.lower()
        self.google_api_key = google_api_key
        
        # Load languages from Settings if not specified
        if languages is None:
            try:
                config = Settings()
                self.languages = [lang.strip() for lang in config.OCR_LANGUAGES.split(",") if lang.strip()]
            except Exception:
                self.languages = ["en"]
        else:
            self.languages = languages
            
        self.easyocr_reader = None
        self.gemini_client = None
        
        # Initialize primary engine
        if self.primary_engine == "easyocr":
            self._init_easyocr()
        elif self.primary_engine == "gemini":
            if not google_api_key:
                raise ValueError("Google API key required for Gemini engine")
            self._init_gemini()
        else:
            raise ValueError("Unknown engine: {}".format(self.primary_engine))
        
        logger.info("ImageHandler initialized (primary: {}, languages: {})".format(
            self.primary_engine, self.languages
        ))
    
    def _init_easyocr(self):
        """Initialize EasyOCR reader for configured languages."""
        try:
            import easyocr
            logger.info("Initializing EasyOCR reader for languages: {}...".format(self.languages))
            try:
                self.easyocr_reader = easyocr.Reader(self.languages, gpu=False)
            except Exception as e:
                # EasyOCR does not allow mixing Tamil ('ta') script with Devanagari/Telugu/Bengali.
                # If a compatibility exception occurs, fall back to initializing without Tamil.
                if "Tamil" in str(e) or "compatibility" in str(e).lower():
                    safe_languages = [lang for lang in self.languages if lang != "ta"]
                    logger.warning(
                        "EasyOCR script compatibility warning. Retrying with safe languages (excluding Tamil): {}".format(
                            safe_languages
                        )
                    )
                    self.easyocr_reader = easyocr.Reader(safe_languages, gpu=False)
                else:
                    raise e
            logger.info("EasyOCR reader initialized (CPU mode)")
        except ImportError:
            error = "EasyOCR not installed. Run: pip install easyocr"
            logger.error(error)
            raise ImportError(error)
        except Exception as e:
            error = "Failed to initialize EasyOCR: {}".format(str(e))
            logger.error(error)
            raise RuntimeError(error)
    
    def _init_gemini(self):
        """Initialize Google Generative AI client for Gemini Vision."""
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.google_api_key)
            self.gemini_client = genai
            logger.info("Gemini Vision API client initialized")
        except ImportError:
            error = "google-generativeai not installed. Run: pip install google-generativeai"
            logger.error(error)
            raise ImportError(error)
        except Exception as e:
            error = "Failed to initialize Gemini client: {}".format(str(e))
            logger.error(error)
            raise RuntimeError(error)
    
    def validate(self, image_path: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        Validate image file path and format.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if image_path is None:
            error = "Image file path is None"
            logger.warning(error)
            return False, error
        
        path = Path(image_path)
        
        if not path.exists():
            error = "Image file not found: {}".format(image_path)
            logger.warning(error)
            return False, error
        
        if not path.is_file():
            error = "Path is not a file: {}".format(image_path)
            logger.warning(error)
            return False, error
        
        file_ext = path.suffix.lower()
        if file_ext not in self.SUPPORTED_FORMATS:
            error = "Unsupported image format: {}. Supported: {}".format(
                file_ext, ', '.join(self.SUPPORTED_FORMATS)
            )
            logger.warning(error)
            return False, error
        
        file_size_mb = path.stat().st_size / (1024 * 1024)
        if file_size_mb > self.MAX_FILE_SIZE_MB:
            error = "Image file too large: {:.2f}MB (max: {}MB)".format(
                file_size_mb, self.MAX_FILE_SIZE_MB
            )
            logger.warning(error)
            return False, error
        
        return True, None
    
    def _extract_easyocr(self, image_path: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Extract text using EasyOCR.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Tuple of (success, extracted_text, error_message)
        """
        try:
            logger.debug("Running EasyOCR extraction on: {}".format(image_path))
            
            if self.easyocr_reader is None:
                self._init_easyocr()
            
            # EasyOCR returns list of [bbox, text, confidence]
            results = self.easyocr_reader.readtext(image_path)
            
            # Filter by confidence threshold and extract text
            extracted_lines = []
            for (bbox, text, confidence) in results:
                if confidence >= self.MIN_CONFIDENCE:
                    extracted_lines.append(text)
            
            if not extracted_lines:
                error = "EasyOCR extracted no text (confidence > {})".format(self.MIN_CONFIDENCE)
                logger.warning(error)
                return False, None, error
            
            extracted_text = ' '.join(extracted_lines)
            logger.info("EasyOCR extraction successful: {} chars from {} lines".format(
                len(extracted_text), len(extracted_lines)
            ))
            return True, extracted_text, None
            
        except Exception as e:
            error = "EasyOCR extraction failed: {}".format(str(e))
            logger.error(error, exc_info=True)
            return False, None, error
    
    def _extract_gemini(self, image_path: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Extract text using Gemini Vision API.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Tuple of (success, extracted_text, error_message)
        """
        try:
            logger.debug("Running Gemini Vision extraction on: {}".format(image_path))
            
            # Load image
            import base64
            with open(image_path, 'rb') as img_file:
                image_data = base64.standard_b64encode(img_file.read()).decode('utf-8')
            
            # Determine MIME type from file extension
            ext = Path(image_path).suffix.lower()
            mime_type_map = {
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".bmp": "image/bmp",
                ".webp": "image/webp"
            }
            mime_type = mime_type_map.get(ext, "image/jpeg")
            
            # Call Gemini Vision API
            model = self.gemini_client.GenerativeModel('gemini-2.5-flash')
            message = model.generate_content([
                {
                    "role": "user",
                    "parts": [
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": image_data,
                            },
                        },
                        "Extract all readable text from this image, including any Indian regional languages (e.g., Hindi, Tamil, Telugu, Marathi, Bengali) and mixed language text. Return only the text, nothing else.",
                    ],
                },
            ])
            
            extracted_text = message.text.strip() if message.text else ""
            
            if not extracted_text:
                error = "Gemini Vision extracted no text"
                logger.warning(error)
                return False, None, error
            
            logger.info("Gemini Vision extraction successful: {} chars".format(len(extracted_text)))
            return True, extracted_text, None
            
        except Exception as e:
            error = "Gemini Vision extraction failed: {}".format(str(e))
            logger.error(error, exc_info=True)
            return False, None, error
    
    def extract(self, image_path: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Extract text from image using primary or fallback engine.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Tuple of (success, extracted_text, error_message)
        """
        logger.info("Starting image text extraction: {}".format(image_path))
        
        # Step 1: Validate
        is_valid, error = self.validate(image_path)
        if not is_valid:
            logger.error("Image validation failed: {}".format(error))
            return False, None, error
        
        # Step 2: Try primary engine
        if self.primary_engine == "easyocr":
            success, text, error = self._extract_easyocr(image_path)
        else:
            success, text, error = self._extract_gemini(image_path)
        
        if success and text and len(text) >= 10:
            return True, text, None
        
        # Step 3: Attempt fallback
        logger.warning("Primary engine failed or returned insufficient text (len < 10), attempting fallback...")
        fallback_engine = "gemini" if self.primary_engine == "easyocr" else "easyocr"
        
        # Check if fallback is available
        if fallback_engine == "gemini" and not self.gemini_client:
            if self.google_api_key:
                try:
                    self._init_gemini()
                except Exception as init_err:
                    logger.error("Failed to lazy-initialize Gemini fallback: {}".format(init_err))
                    return False, None, error
            else:
                logger.error("Gemini fallback not available (no API key)")
                return False, None, error
        
        if fallback_engine == "easyocr" and not self.easyocr_reader:
            try:
                self._init_easyocr()
            except Exception as init_err:
                logger.error("Failed to lazy-initialize EasyOCR fallback: {}".format(init_err))
                return False, None, error
        
        # Try fallback
        if fallback_engine == "easyocr":
            success, text, fallback_error = self._extract_easyocr(image_path)
        else:
            success, text, fallback_error = self._extract_gemini(image_path)
        
        if success:
            logger.info("Fallback engine succeeded")
            return True, text, None
        else:
            combined_error = "Both engines failed. Primary: {}. Fallback: {}".format(error, fallback_error)
            logger.error(combined_error)
            return False, None, combined_error
