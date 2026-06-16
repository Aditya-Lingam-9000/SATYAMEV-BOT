"""
Text Handler Module
===================

Handles text input validation, normalization, and preprocessing.
Includes: lowercasing, whitespace normalization, special character handling,
and length validation.
"""

import re
import logging
from typing import Optional, Tuple

logger = logging.getLogger("satyamev_bot.ingestion.text")


class TextHandler:
    """
    Handles text ingestion, validation, and normalization.
    
    Features:
    - Unicode normalization
    - Whitespace standardization
    - Special character handling
    - Length validation
    - Empty/null checking
    """
    
    # Configuration constants
    MIN_LENGTH = 10  # Minimum characters for a valid claim
    MAX_LENGTH = 5000  # Maximum characters
    
    def __init__(self, min_length: int = MIN_LENGTH, max_length: int = MAX_LENGTH):
        """
        Initialize TextHandler.
        
        Args:
            min_length: Minimum text length (default: 10)
            max_length: Maximum text length (default: 5000)
        """
        self.min_length = min_length
        self.max_length = max_length
        logger.info("TextHandler initialized (min={}, max={})".format(min_length, max_length))
    
    def validate(self, text: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        Validate raw text input.
        
        Args:
            text: Raw text input
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if text is None:
            error = "Text input is None"
            logger.warning(error)
            return False, error
        
        if not isinstance(text, str):
            error = "Text input must be string, got {}".format(type(text).__name__)
            logger.warning(error)
            return False, error
        
        if len(text.strip()) == 0:
            error = "Text input is empty"
            logger.warning(error)
            return False, error
        
        if len(text) < self.min_length:
            error = "Text too short: {} chars (minimum: {})".format(len(text), self.min_length)
            logger.warning(error)
            return False, error
        
        if len(text) > self.max_length:
            error = "Text too long: {} chars (maximum: {})".format(len(text), self.max_length)
            logger.warning(error)
            return False, error
        
        return True, None
    
    def normalize(self, text: str) -> str:
        """
        Normalize text: whitespace, unicode, special chars.
        
        Args:
            text: Raw text input
            
        Returns:
            Normalized text string
        """
        # Strip leading/trailing whitespace
        text = text.strip()
        
        # Replace multiple spaces/tabs with single space
        text = re.sub(r'\s+', ' ', text)
        
        # Remove control characters but keep newlines temporarily
        text = ''.join(char for char in text if ord(char) >= 32 or char == '\n')
        
        # Convert newlines to spaces (flatten to single line)
        text = text.replace('\n', ' ').replace('\r', ' ')
        
        # Remove extra spaces again after newline conversion
        text = re.sub(r'\s+', ' ', text).strip()
        
        logger.debug("Text normalized: {} chars -> {} chars".format(len(text), len(text)))
        return text
    
    def clean(self, text: str) -> str:
        """
        Deep clean: normalize + remove URLs, emails, special patterns.
        
        Args:
            text: Text to clean
            
        Returns:
            Cleaned text
        """
        # First normalize
        text = self.normalize(text)
        
        # Remove URLs (http, https, ftp)
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '[URL]', text)
        
        # Remove email addresses
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)
        
        # Remove phone numbers (various formats)
        text = re.sub(r'(\+\d{1,3}[- ]?)?\d{10}', '[PHONE]', text)
        
        # Remove repeated punctuation (e.g., !!! -> !)
        text = re.sub(r'([!?.,-])\1{2,}', r'\1', text)
        
        # Normalize punctuation spacing
        text = re.sub(r'\s+([.,!?;:])', r'\1', text)
        text = re.sub(r'([.,!?;:])\s*', r'\1 ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        logger.debug("Text cleaned: removed URLs, emails, special patterns")
        return text
    
    def process(self, text: Optional[str], clean: bool = True) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Complete text processing pipeline.
        
        Args:
            text: Raw text input
            clean: Whether to perform deep cleaning (default: True)
            
        Returns:
            Tuple of (success, processed_text, error_message)
        """
        logger.info("Starting text processing")
        
        # Step 1: Validate
        is_valid, error = self.validate(text)
        if not is_valid:
            logger.error("Validation failed: {}".format(error))
            return False, None, error
        
        try:
            # Step 2: Normalize (always)
            normalized = self.normalize(text)
            
            # Step 3: Deep clean (optional)
            if clean:
                processed = self.clean(normalized)
            else:
                processed = normalized
            
            logger.info("Text processing successful: {} chars".format(len(processed)))
            return True, processed, None
            
        except Exception as e:
            error_msg = "Text processing failed: {}".format(str(e))
            logger.error(error_msg, exc_info=True)
            return False, None, error_msg
