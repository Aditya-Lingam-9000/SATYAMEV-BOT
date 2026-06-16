"""
Card Design Configuration

Centralized configuration for card appearance, fonts, colors, sizes,
and layout parameters.
"""

import logging
from dataclasses import dataclass
from typing import Dict, Tuple, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class VerdictColor(str, Enum):
    """Color assignments for verdicts."""
    TRUE = "#27AE60"  # Green
    FALSE = "#E74C3C"  # Red
    MISLEADING = "#F39C12"  # Orange
    UNVERIFIABLE = "#95A5A6"  # Gray


class CardTheme(str, Enum):
    """Available card themes."""
    LIGHT = "light"
    DARK = "dark"
    MINIMAL = "minimal"
    BOLD = "bold"


@dataclass
class ColorScheme:
    """Color scheme for a theme."""
    background: str
    text_primary: str
    text_secondary: str
    accent: str
    border: str
    
    def get_verdict_color(self, verdict: str) -> str:
        """Get color for verdict."""
        verdict_colors = {
            "TRUE": VerdictColor.TRUE.value,
            "FALSE": VerdictColor.FALSE.value,
            "MISLEADING": VerdictColor.MISLEADING.value,
            "UNVERIFIABLE": VerdictColor.UNVERIFIABLE.value,
        }
        return verdict_colors.get(verdict, VerdictColor.UNVERIFIABLE.value)


# Theme Definitions
THEMES = {
    "light": ColorScheme(
        background="#FFFFFF",
        text_primary="#1C1C1C",
        text_secondary="#555555",
        accent="#007AFF",
        border="#E0E0E0",
    ),
    "dark": ColorScheme(
        background="#1E1E1E",
        text_primary="#FFFFFF",
        text_secondary="#B0B0B0",
        accent="#0A84FF",
        border="#404040",
    ),
    "minimal": ColorScheme(
        background="#F8F8F8",
        text_primary="#000000",
        text_secondary="#666666",
        accent="#000000",
        border="#CCCCCC",
    ),
    "bold": ColorScheme(
        background="#0F1419",
        text_primary="#FFFFFF",
        text_secondary="#D0D0D0",
        accent="#FF6B6B",
        border="#333333",
    ),
}


@dataclass
class CardDimensions:
    """Card dimensions in pixels."""
    width: int = 1200
    height: int = 630  # Standard social media aspect ratio
    padding: int = 40
    margin: int = 20
    
    # Typography
    font_size_title: int = 48
    font_size_verdict: int = 72
    font_size_body: int = 24
    font_size_small: int = 16
    
    # Spacing
    line_height: float = 1.5
    section_gap: int = 30
    
    @property
    def content_width(self) -> int:
        """Usable content width."""
        return self.width - (2 * self.padding)
    
    @property
    def content_height(self) -> int:
        """Usable content height."""
        return self.height - (2 * self.padding)


@dataclass
class CardConfig:
    """Complete card configuration."""
    
    # Dimensions
    width: int = 1200
    height: int = 630
    padding: int = 40
    
    # Theme
    theme: str = "light"
    
    # Branding
    logo_path: Optional[str] = None
    watermark: str = "SATYAMEV-BOT"
    brand_color: Optional[str] = None
    
    # Text rendering
    title_color: Optional[str] = None
    body_color: Optional[str] = None
    verdict_bold: bool = True
    
    # Layout
    show_confidence: bool = True
    show_sources: bool = True
    max_sources_shown: int = 3
    truncate_reasoning: bool = True
    max_reasoning_chars: int = 200
    
    # Spacing
    section_gap: int = 30
    line_height: float = 1.3
    
    # Font
    font_size_title: int = 48
    font_size_verdict: int = 72
    font_size_body: int = 24
    font_size_small: int = 16
    
    @property
    def content_width(self) -> int:
        """Usable content width."""
        return self.width - (2 * self.padding)
    
    @property
    def content_height(self) -> int:
        """Usable content height."""
        return self.height - (2 * self.padding)
    
    def __post_init__(self):
        """Validate config after initialization."""
        if self.theme not in THEMES:
            raise ValueError(
                f"Theme '{self.theme}' not found. "
                f"Available: {list(THEMES.keys())}"
            )
        
        logger.info(
            f"CardConfig initialized: "
            f"size={self.width}x{self.height}, theme={self.theme}"
        )
    
    def get_color_scheme(self) -> ColorScheme:
        """Get color scheme for theme."""
        return THEMES[self.theme]


# Preset configurations for common use cases
PRESETS = {
    "twitter": CardConfig(
        width=1024,
        height=512,
        theme="light",
        show_sources=True,
        max_sources_shown=2,
    ),
    "facebook": CardConfig(
        width=1200,
        height=630,
        theme="light",
        show_sources=True,
        max_sources_shown=3,
    ),
    "instagram": CardConfig(
        width=1080,
        height=1080,
        theme="dark",
        show_sources=True,
        max_sources_shown=2,
    ),
    "linkedin": CardConfig(
        width=1200,
        height=627,
        theme="minimal",
        show_sources=True,
        max_sources_shown=3,
    ),
    "minimal": CardConfig(
        width=800,
        height=600,
        theme="minimal",
        show_sources=False,
        max_sources_shown=0,
    ),
    "detailed": CardConfig(
        width=1600,
        height=900,
        theme="light",
        show_sources=True,
        max_sources_shown=5,
        truncate_reasoning=False,
    ),
}


def get_preset_config(preset: str = "facebook") -> CardConfig:
    """
    Get predefined card configuration.
    
    Args:
        preset: One of "twitter", "facebook", "instagram", "linkedin", 
                "minimal", "detailed"
    
    Returns:
        CardConfig instance
    
    Raises:
        ValueError: If preset not found
    """
    if preset not in PRESETS:
        raise ValueError(
            f"Preset '{preset}' not found. "
            f"Available: {list(PRESETS.keys())}"
        )
    
    logger.info(f"Using preset config: {preset}")
    return PRESETS[preset]
