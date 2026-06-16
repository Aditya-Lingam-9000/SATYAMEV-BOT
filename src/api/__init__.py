"""
FastAPI REST Server - Phase 4

Production-ready API for Satyamev-Bot fact-checking engine.

Components:
- app.py: Main FastAPI application
- models.py: Pydantic request/response schemas
- endpoints.py: API route handlers
- middleware.py: Custom middleware (logging, error handling)

Endpoints:
- GET /health: Health check
- POST /api/verify: Fact-check a claim
- POST /api/ingest: Multimodal ingestion
- POST /api/generate-card: Generate proof card
- GET /api/docs: OpenAPI documentation

Usage:
    uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload
"""

__version__ = "0.1.0"
__all__ = ["app", "create_app"]
