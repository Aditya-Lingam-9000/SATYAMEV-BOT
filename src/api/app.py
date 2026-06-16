"""
FastAPI Application Factory

Main entry point for the Satyamev-Bot REST API.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.config import Settings
from src.ingestion.ingestion_manager import IngestionManager
from src.brain.agent import FactCheckingAgent
from src.cards.generator import CardGenerator

from .endpoints import create_router, init_services

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle (startup/shutdown).
    """
    # Startup
    logger.info("Starting Satyamev-Bot API server...")
    
    # Initialize services
    config = Settings()
    
    try:
        ingestion_manager = IngestionManager(
            groq_api_key=config.GROQ_API_KEY,
            google_api_key=config.GOOGLE_API_KEY,
            image_engine=config.IMAGE_ENGINE,
        )
        logger.info("Ingestion manager initialized")
    except Exception as e:
        logger.error(f"Failed to initialize ingestion manager: {e}")
        ingestion_manager = None
    
    try:
        fact_checking_agent = FactCheckingAgent(
            groq_api_key=config.GROQ_API_KEY,
            google_api_key=config.GOOGLE_API_KEY,
            tavily_api_key=config.TAVILY_API_KEY,
            strategy="balanced",
        )
        logger.info("Fact-checking agent initialized")
    except Exception as e:
        logger.error(f"Failed to initialize fact-checking agent: {e}")
        fact_checking_agent = None
    
    try:
        card_generator = CardGenerator(preset="facebook", theme="light")
        logger.info("Card generator initialized")
    except Exception as e:
        logger.error(f"Failed to initialize card generator: {e}")
        card_generator = None
    
    init_services(ingestion_manager, fact_checking_agent, card_generator)
    logger.info("API server ready")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Satyamev-Bot API server...")


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.
    """
    config = Settings()
    
    app = FastAPI(
        title="Satyamev-Bot",
        description="Advanced multimodal RAG-driven fact-checking engine",
        version="0.1.0",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
        redoc_url="/api/redoc",
        lifespan=lifespan,
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # TODO: Restrict in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(create_router())
    
    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "name": "Satyamev-Bot",
            "version": "0.1.0",
            "description": "Advanced multimodal fact-checking engine",
            "docs": "/api/docs",
            "health": "/api/health",
        }
    
    # Exception handlers
    @app.exception_handler(Exception)
    async def generic_exception_handler(request, exc):
        logger.error(f"Unhandled exception: {str(exc)}")
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "error_type": "InternalServerError",
                "message": "An unexpected error occurred",
            },
        )
    
    return app


# Create app instance for uvicorn
app = create_app()

if __name__ == "__main__":
    import uvicorn
    
    config = Settings()
    uvicorn.run(
        app,
        host=config.SERVER_HOST,
        port=config.SERVER_PORT,
        log_level=config.LOG_LEVEL.lower(),
    )
