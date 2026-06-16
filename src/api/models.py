"""
API Data Models

Pydantic schemas for request/response validation.
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(description="Service status (healthy/unhealthy)")
    version: str = Field(description="API version")
    timestamp: str = Field(description="Current timestamp")


class IngestionRequest(BaseModel):
    """Ingestion request payload."""
    source: str = Field(
        description="Text, file path, or URL to ingest"
    )
    input_type: Literal["TEXT", "AUDIO", "IMAGE", "AUTO"] = Field(
        default="AUTO",
        description="Input type"
    )
    clean: bool = Field(
        default=True,
        description="Clean text (remove URLs, emails, etc.)"
    )


class IngestionResponse(BaseModel):
    """Ingestion response payload."""
    success: bool = Field(description="Whether ingestion succeeded")
    text: Optional[str] = Field(
        default=None,
        description="Extracted/processed text"
    )
    character_count: int = Field(
        default=0,
        description="Length of extracted text"
    )
    input_type: str = Field(description="Detected input type")
    error: Optional[str] = Field(
        default=None,
        description="Error message if failed"
    )


class VerifyRequest(BaseModel):
    """Fact-checking verification request."""
    claim: str = Field(
        min_length=10,
        max_length=5000,
        description="Claim to verify"
    )
    strategy: Literal["fast", "balanced", "thorough"] = Field(
        default="balanced",
        description="Verification strategy"
    )
    include_reasoning: bool = Field(
        default=True,
        description="Include detailed reasoning"
    )


class VerifyResponse(BaseModel):
    """Fact-checking verdict response."""
    claim: str = Field(description="Original claim")
    verdict: Literal["TRUE", "FALSE", "MISLEADING", "UNVERIFIABLE"] = Field(
        description="Verdict"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score (0-1)"
    )
    reasoning: str = Field(description="Explanation of verdict")
    sources: List[str] = Field(
        default_factory=list,
        description="Evidence sources"
    )
    key_evidence: List[str] = Field(
        default_factory=list,
        description="Key supporting facts"
    )
    timestamp: str = Field(description="Timestamp of verdict")


class GenerateCardRequest(BaseModel):
    """Card generation request."""
    claim: str = Field(description="Claim text")
    verdict: Literal["TRUE", "FALSE", "MISLEADING", "UNVERIFIABLE"] = Field(
        description="Verdict"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score"
    )
    reasoning: Optional[str] = Field(
        default=None,
        description="Explanation"
    )
    sources: Optional[List[str]] = Field(
        default=None,
        description="Evidence sources"
    )
    key_evidence: Optional[List[str]] = Field(
        default=None,
        description="Key facts"
    )
    preset: Literal["twitter", "facebook", "instagram", "linkedin", "minimal", "detailed"] = Field(
        default="facebook",
        description="Card preset"
    )
    theme: Literal["light", "dark", "minimal", "bold"] = Field(
        default="light",
        description="Card theme"
    )


class GenerateCardResponse(BaseModel):
    """Card generation response."""
    success: bool = Field(description="Whether generation succeeded")
    card_url: Optional[str] = Field(
        default=None,
        description="URL to generated card (if stored)"
    )
    card_bytes: Optional[str] = Field(
        default=None,
        description="Base64-encoded PNG image"
    )
    size_bytes: int = Field(
        default=0,
        description="Card file size in bytes"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if failed"
    )


class BatchVerifyRequest(BaseModel):
    """Batch verification request."""
    claims: List[str] = Field(
        min_items=1,
        max_items=100,
        description="List of claims to verify"
    )
    strategy: Literal["fast", "balanced", "thorough"] = Field(
        default="balanced",
        description="Verification strategy"
    )


class BatchVerifyResponse(BaseModel):
    """Batch verification response."""
    total: int = Field(description="Total claims submitted")
    completed: int = Field(description="Successfully completed")
    failed: int = Field(description="Failed verifications")
    results: List[VerifyResponse] = Field(description="Verification results")
    timestamp: str = Field(description="Completion timestamp")


class ErrorResponse(BaseModel):
    """Error response."""
    status_code: int = Field(description="HTTP status code")
    error_type: str = Field(description="Error category")
    message: str = Field(description="Error message")
    details: Optional[dict] = Field(
        default=None,
        description="Additional error details"
    )
    timestamp: str = Field(description="Error timestamp")


class WebhookRequest(BaseModel):
    """Webhook callback for async operations."""
    claim: str = Field(description="Claim to verify")
    callback_url: str = Field(description="URL to POST result to")
    callback_secret: Optional[str] = Field(
        default=None,
        description="Secret for HMAC signature"
    )


class WebhookResponse(BaseModel):
    """Webhook registration response."""
    webhook_id: str = Field(description="Unique webhook ID")
    status: str = Field(description="Webhook status")
    callback_url: str = Field(description="Registered callback URL")
    message: str = Field(description="Status message")
