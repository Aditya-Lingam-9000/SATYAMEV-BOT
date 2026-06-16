"""
Satyamev-Bot Configuration Module
Uses Pydantic Settings for environment variable parsing and validation.
"""

import logging
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Validates all required API keys and configurations at startup.
    """

    # ============================================
    # SERVER CONFIGURATION
    # ============================================
    SERVER_HOST: str = Field(default="0.0.0.0", description="FastAPI server host")
    SERVER_PORT: int = Field(default=8000, description="FastAPI server port")
    ENVIRONMENT: str = Field(default="development", description="Environment: development or production")
    DEBUG: bool = Field(default=False, description="Enable debug mode")

    # ============================================
    # LLM & AI MODEL APIs
    # ============================================
    GROQ_API_KEY: str = Field(default="", description="Groq API key for Llama and Whisper models")
    GOOGLE_API_KEY: str = Field(default="", description="Google Generative AI API key")
    TAVILY_API_KEY: str = Field(default="", description="Tavily Search API key")

    # ============================================
    # LOCAL CONFIGURATION
    # ============================================
    OCR_LANGUAGES: str = Field(default="en,hi,te,ta,mr,bn", description="EasyOCR languages (comma-separated)")
    MAX_UPLOAD_SIZE_MB: int = Field(default=50, description="Maximum file upload size in MB")
    TEMP_DIR: str = Field(default="./temp", description="Temporary files directory")
    EXPORTS_DIR: str = Field(default="./exports", description="Generated cards export directory")

    # ============================================
    # LOGGING
    # ============================================
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FILE: str = Field(default="./logs/satyamev_bot.log", description="Log file path")

    # ============================================
    # TWILIO WHATSAPP CONFIGURATION (Phase 5)
    # ============================================
    TWILIO_ACCOUNT_SID: Optional[str] = Field(default="", description="Twilio Account SID")
    TWILIO_AUTH_TOKEN: Optional[str] = Field(default="", description="Twilio Auth Token")
    TWILIO_PHONE_NUMBER: Optional[str] = Field(
        default="whatsapp:+14155238886",
        description="Twilio WhatsApp phone number"
    )
    NGROK_URL: Optional[str] = Field(default="http://localhost:8000", description="Ngrok public URL")

    # ============================================
    # WHATSAPP BOT CONFIGURATION
    # ============================================
    WHATSAPP_BOT_ENABLED: bool = Field(default=True, description="Enable WhatsApp bot")
    WHATSAPP_STRATEGY: str = Field(default="balanced", description="WhatsApp fact-checking strategy")
    WHATSAPP_MAX_MESSAGE_LENGTH: int = Field(default=1000, description="Max message length")
    WHATSAPP_CARD_PRESET: str = Field(default="instagram", description="WhatsApp card preset")
    WHATSAPP_CARD_THEME: str = Field(default="dark", description="WhatsApp card theme")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    @validator("ENVIRONMENT")
    def validate_environment(cls, v):
        if v not in ["development", "production"]:
            raise ValueError("ENVIRONMENT must be 'development' or 'production'")
        return v

    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v

    def validate_api_keys(self) -> dict:
        """
        Validates that required API keys are configured.
        Returns a dictionary of validation status.
        """
        validation_status = {
            "groq_configured": bool(self.GROQ_API_KEY),
            "google_configured": bool(self.GOOGLE_API_KEY),
            "tavily_configured": bool(self.TAVILY_API_KEY),
        }
        return validation_status

    def setup_directories(self):
        """Creates necessary directories if they don't exist."""
        dirs_to_create = [
            Path(self.TEMP_DIR),
            Path(self.EXPORTS_DIR),
            Path(self.LOG_FILE).parent,
        ]
        for directory in dirs_to_create:
            directory.mkdir(parents=True, exist_ok=True)

    def setup_logging(self):
        """Configures the root logger with file and console handlers."""
        self.setup_directories()

        logger = logging.getLogger("satyamev_bot")
        logger.setLevel(getattr(logging, self.LOG_LEVEL))

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, self.LOG_LEVEL))
        console_format = logging.Formatter(
            "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console_handler.setFormatter(console_format)

        # File handler
        file_handler = logging.FileHandler(self.LOG_FILE, encoding="utf-8")
        file_handler.setLevel(getattr(logging, self.LOG_LEVEL))
        file_format = logging.Formatter(
            "[%(asctime)s] [%(name)s] [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_format)

        # Add handlers to logger
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

        return logger


# ============================================
# SINGLETON INSTANCE
# ============================================
def get_settings() -> Settings:
    """Lazy-load settings singleton."""
    return Settings()


if __name__ == "__main__":
    # Quick validation test
    try:
        settings = get_settings()
        print("✓ Settings loaded successfully")
        print(f"  Environment: {settings.ENVIRONMENT}")
        print(f"  Debug Mode: {settings.DEBUG}")
        print(f"  Server: {settings.SERVER_HOST}:{settings.SERVER_PORT}")
        
        api_status = settings.validate_api_keys()
        print("\nAPI Key Status:")
        print(f"  Groq: {'✓ Configured' if api_status['groq_configured'] else '✗ Missing'}")
        print(f"  Google: {'✓ Configured' if api_status['google_configured'] else '✗ Missing'}")
        print(f"  Tavily: {'✓ Configured' if api_status['tavily_configured'] else '✗ Missing'}")
        
        settings.setup_directories()
        settings.setup_logging()
        print("\n✓ Directories and logging initialized")
    except Exception as e:
        print(f"✗ Configuration Error: {e}")
        exit(1)
