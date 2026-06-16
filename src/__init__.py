"""
Satyamev-Bot - Advanced Multimodal RAG-Driven Fact-Checking Engine
Version: 0.1.0-alpha
"""

__version__ = "0.1.0-alpha"
__author__ = "Satyamev-Bot Development Team"

from src.config import get_settings

settings = get_settings()
settings.setup_logging()
