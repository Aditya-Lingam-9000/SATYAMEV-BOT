"""
Brain Module Configuration

Handles LLM model selection, temperature settings, retry policies,
and agent behavior tuning for the fact-checking engine.
"""

import logging
from typing import Literal
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class FactCheckingConfig(BaseModel):
    """Configuration for fact-checking agent behavior and LLM settings."""
    
    # LLM Provider Selection
    llm_provider: Literal["groq", "google"] = Field(
        default="groq",
        description="Primary LLM provider (Groq for Llama, Google for Gemini)"
    )
    
    # Model Names
    groq_model: str = Field(
        default="llama-3.3-70b-versatile",
        description="Groq model for reasoning"
    )
    google_model: str = Field(
        default="gemini-2.5-flash",
        description="Google model for fallback/multimodal"
    )
    
    # Temperature Controls
    reasoning_temperature: float = Field(
        default=0.1,
        ge=0.0,
        le=2.0,
        description="Low temp (0.1) for consistent fact-checking; higher for diversity"
    )
    search_temperature: float = Field(
        default=0.3,
        ge=0.0,
        le=2.0,
        description="Temperature for search query generation"
    )
    
    # Agent Behavior
    max_iterations: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum ReAct agent iterations before fallback"
    )
    search_depth: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of web searches per claim"
    )
    confidence_threshold: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="Confidence threshold for verdict certainty"
    )
    
    # Retry & Timeout
    max_retries: int = Field(
        default=3,
        ge=1,
        description="Max retries for API calls"
    )
    api_timeout_seconds: int = Field(
        default=60,
        ge=10,
        description="Timeout for API requests"
    )
    
    # Logging
    debug_mode: bool = Field(
        default=False,
        description="Enable verbose agent thinking/reasoning logs"
    )
    
    @field_validator("reasoning_temperature", "search_temperature")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        """Validate temperature is in valid range."""
        if not (0.0 <= v <= 2.0):
            raise ValueError("Temperature must be between 0.0 and 2.0")
        return v
    
    @field_validator("confidence_threshold")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        """Validate confidence threshold."""
        if not (0.0 <= v <= 1.0):
            raise ValueError("Confidence threshold must be between 0.0 and 1.0")
        return v
    
    class Config:
        """Pydantic config."""
        validate_assignment = True
        json_schema_extra = {
            "example": {
                "llm_provider": "groq",
                "groq_model": "llama-3.3-70b-versatile",
                "reasoning_temperature": 0.1,
                "max_iterations": 10,
                "search_depth": 3,
            }
        }
    
    def __init__(self, **data):
        """Initialize config with logging."""
        super().__init__(**data)
        logger.info(
            f"FactCheckingConfig initialized: provider={self.llm_provider}, "
            f"model={self.groq_model if self.llm_provider == 'groq' else self.google_model}, "
            f"temp={self.reasoning_temperature}"
        )
    
    def to_dict(self) -> dict:
        """Export config as dictionary."""
        return self.model_dump()


# Default configurations for different verification strategies
STRATEGIES = {
    "fast": FactCheckingConfig(
        reasoning_temperature=0.1,
        search_depth=2,
        max_iterations=5,
        confidence_threshold=0.7,
    ),
    "balanced": FactCheckingConfig(
        reasoning_temperature=0.1,
        search_depth=3,
        max_iterations=10,
        confidence_threshold=0.75,
    ),
    "thorough": FactCheckingConfig(
        reasoning_temperature=0.2,
        search_depth=5,
        max_iterations=15,
        confidence_threshold=0.8,
    ),
}


def get_strategy_config(strategy: str = "balanced") -> FactCheckingConfig:
    """
    Get predefined configuration strategy.
    
    Args:
        strategy: One of "fast", "balanced", "thorough"
    
    Returns:
        FactCheckingConfig instance
    
    Raises:
        ValueError: If strategy not recognized
    """
    if strategy not in STRATEGIES:
        raise ValueError(
            f"Strategy '{strategy}' not found. "
            f"Available: {list(STRATEGIES.keys())}"
        )
    
    logger.info(f"Using '{strategy}' strategy config")
    return STRATEGIES[strategy]
