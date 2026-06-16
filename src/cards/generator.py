"""
Card Generator

Main engine for rendering fact-checking cards using PIL (Pillow).
Supports multiple templates and themes with full customization.
"""

import logging
from typing import Optional, List, Tuple
from pathlib import Path
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont

from .config import CardConfig, get_preset_config, THEMES, VerdictColor

logger = logging.getLogger(__name__)


class Card:
    """Represents a generated fact-checking card."""
    
    def __init__(self, image: Image.Image, verdict: str, confidence: float):
        """
        Initialize card.
        
        Args:
            image: PIL Image object
            verdict: Verdict string
            confidence: Confidence score
        """
        self.image = image
        self.verdict = verdict
        self.confidence = confidence
    
    def save(self, path: str) -> bool:
        """
        Save card to file.
        
        Args:
            path: Output file path (PNG)
        
        Returns:
            True if successful
        """
        try:
            output_path = Path(path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            self.image.save(output_path, format="PNG", quality=95)
            logger.info(f"Card saved: {output_path}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to save card: {str(e)}")
            return False
    
    def to_bytes(self) -> bytes:
        """Export as PNG bytes."""
        buffer = BytesIO()
        self.image.save(buffer, format="PNG")
        return buffer.getvalue()


class CardGenerator:
    """
    Generate fact-checking proof cards.
    
    Supports multiple templates and themes with customizable styling.
    """
    
    def __init__(
        self,
        preset: str = "facebook",
        theme: Optional[str] = None,
        custom_config: Optional[CardConfig] = None,
    ):
        """
        Initialize card generator.
        
        Args:
            preset: Predefined size/layout ("facebook", "twitter", etc.)
            theme: Color theme ("light", "dark", "minimal", "bold")
            custom_config: Custom CardConfig to override preset/theme
        """
        if custom_config:
            self.config = custom_config
        else:
            self.config = get_preset_config(preset)
            if theme:
                self.config.theme = theme
        
        logger.info(
            f"CardGenerator initialized: "
            f"{self.config.width}x{self.config.height}, "
            f"theme={self.config.theme}"
        )
    
    def generate(
        self,
        claim: str,
        verdict: str,
        confidence: float,
        reasoning: Optional[str] = None,
        sources: Optional[List[str]] = None,
        key_evidence: Optional[List[str]] = None,
    ) -> Card:
        """
        Generate a fact-checking card.
        
        Args:
            claim: Original claim
            verdict: Verdict ("TRUE", "FALSE", "MISLEADING", "UNVERIFIABLE")
            confidence: Confidence score (0-1)
            reasoning: Explanation text
            sources: List of source URLs
            key_evidence: List of key facts
        
        Returns:
            Card object
        """
        logger.info(f"Generating card: {claim[:50]}... (verdict={verdict})")
        
        # Create base image
        image = self._create_base_image()
        draw = ImageDraw.Draw(image)
        
        # Render sections
        y_offset = self.config.padding
        
        # Header (verdict)
        y_offset = self._render_verdict_header(draw, verdict, confidence, y_offset)
        
        # Claim section
        y_offset = self._render_claim_section(draw, claim, y_offset)
        
        # Reasoning section
        if reasoning:
            y_offset = self._render_reasoning_section(draw, reasoning, y_offset)
        
        # Evidence section
        if key_evidence:
            y_offset = self._render_evidence_section(draw, key_evidence, y_offset)
        
        # Sources section
        if sources and self.config.show_sources:
            y_offset = self._render_sources_section(draw, sources, y_offset)
        
        # Footer
        self._render_footer(draw)
        
        return Card(image, verdict, confidence)
    
    def _create_base_image(self) -> Image.Image:
        """Create base image with background."""
        scheme = self.config.get_color_scheme()
        
        # Convert hex to RGB
        bg_rgb = self._hex_to_rgb(scheme.background)
        
        image = Image.new(
            "RGB",
            (self.config.width, self.config.height),
            bg_rgb
        )
        
        return image
    
    def _render_verdict_header(
        self,
        draw: ImageDraw.ImageDraw,
        verdict: str,
        confidence: float,
        y_offset: int,
    ) -> int:
        """Render verdict header with large badge."""
        scheme = self.config.get_color_scheme()
        verdict_rgb = self._hex_to_rgb(scheme.get_verdict_color(verdict))
        text_rgb = self._hex_to_rgb(scheme.text_primary)
        
        # Verdict badge background
        badge_height = 100
        draw.rectangle(
            [0, y_offset, self.config.width, y_offset + badge_height],
            fill=verdict_rgb
        )
        
        # Verdict text
        verdict_text = verdict
        if self.config.show_confidence:
            verdict_text += f"\n{confidence:.0%} Confidence"
        
        font = self._get_font(self.config.font_size_verdict)
        
        # Draw verdict text
        text_bbox = draw.textbbox((0, 0), verdict, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_x = (self.config.width - text_width) // 2
        
        draw.text(
            (text_x, y_offset + 15),
            verdict,
            fill=(255, 255, 255),
            font=font,
            anchor="lm"
        )
        
        return y_offset + badge_height + self.config.section_gap
    
    def _render_claim_section(
        self,
        draw: ImageDraw.ImageDraw,
        claim: str,
        y_offset: int,
    ) -> int:
        """Render claim text."""
        scheme = self.config.get_color_scheme()
        text_rgb = self._hex_to_rgb(scheme.text_primary)
        
        font = self._get_font(self.config.font_size_title)
        
        # Wrap text
        wrapped = self._wrap_text(claim, self.config.content_width, font)
        
        for line in wrapped:
            draw.text(
                (self.config.padding, y_offset),
                line,
                fill=text_rgb,
                font=font
            )
            y_offset += int(self.config.font_size_title * 1.3)
        
        return y_offset + self.config.section_gap
    
    def _render_reasoning_section(
        self,
        draw: ImageDraw.ImageDraw,
        reasoning: str,
        y_offset: int,
    ) -> int:
        """Render reasoning section."""
        scheme = self.config.get_color_scheme()
        text_rgb = self._hex_to_rgb(scheme.text_secondary)
        
        # Truncate if needed
        if self.config.truncate_reasoning:
            reasoning = reasoning[:self.config.max_reasoning_chars]
            if len(reasoning) == self.config.max_reasoning_chars:
                reasoning += "..."
        
        font = self._get_font(self.config.font_size_body)
        
        # Wrap text
        wrapped = self._wrap_text(reasoning, self.config.content_width, font)
        
        # Limit lines
        wrapped = wrapped[:3]  # Max 3 lines
        
        for line in wrapped:
            draw.text(
                (self.config.padding, y_offset),
                line,
                fill=text_rgb,
                font=font
            )
            y_offset += int(self.config.font_size_body * 1.3)
        
        return y_offset + self.config.section_gap
    
    def _render_evidence_section(
        self,
        draw: ImageDraw.ImageDraw,
        key_evidence: List[str],
        y_offset: int,
    ) -> int:
        """Render key evidence as bullet points."""
        scheme = self.config.get_color_scheme()
        text_rgb = self._hex_to_rgb(scheme.text_secondary)
        
        font = self._get_font(self.config.font_size_small)
        
        for evidence in key_evidence[:3]:  # Max 3 bullets
            bullet = "• " + evidence[:60]
            if len(evidence) > 60:
                bullet += "..."
            
            draw.text(
                (self.config.padding + 10, y_offset),
                bullet,
                fill=text_rgb,
                font=font
            )
            y_offset += int(self.config.font_size_small * 1.5)
        
        return y_offset + self.config.section_gap
    
    def _render_sources_section(
        self,
        draw: ImageDraw.ImageDraw,
        sources: List[str],
        y_offset: int,
    ) -> int:
        """Render sources section."""
        scheme = self.config.get_color_scheme()
        text_rgb = self._hex_to_rgb(scheme.text_secondary)
        
        font = self._get_font(self.config.font_size_small)
        
        sources_text = "Sources: " + ", ".join(
            sources[:self.config.max_sources_shown]
        )
        
        # Truncate if too long
        if len(sources_text) > 100:
            sources_text = sources_text[:97] + "..."
        
        draw.text(
            (self.config.padding, y_offset),
            sources_text,
            fill=text_rgb,
            font=font
        )
        
        return y_offset + self.config.font_size_small + 20
    
    def _render_footer(self, draw: ImageDraw.ImageDraw) -> None:
        """Render footer with watermark."""
        scheme = self.config.get_color_scheme()
        text_rgb = self._hex_to_rgb(scheme.text_secondary)
        
        font = self._get_font(self.config.font_size_small - 4)
        
        # Watermark at bottom right
        watermark = self.config.watermark or "SATYAMEV-BOT"
        
        draw.text(
            (
                self.config.width - self.config.padding - 100,
                self.config.height - 30
            ),
            watermark,
            fill=text_rgb,
            font=font
        )
    
    def _get_font(self, size: int) -> ImageFont.FreeTypeFont:
        """
        Get font for rendering.
        
        Falls back to default font if TrueType unavailable.
        """
        font_paths = [
            "Nirmala.ttc",
            "Nirmala.ttf",
            "arial.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
        
        for path in font_paths:
            try:
                font = ImageFont.truetype(path, size)
                return font
            except (OSError, IOError):
                continue
                
        # Final fallback to default
        return ImageFont.load_default()
    
    def _wrap_text(
        self,
        text: str,
        max_width: int,
        font: ImageFont.FreeTypeFont,
    ) -> List[str]:
        """Wrap text to fit width."""
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + " " + word if current_line else word
            bbox = ImageDraw.ImageDraw(
                Image.new("RGB", (1, 1))
            ).textbbox((0, 0), test_line, font=font)
            
            if bbox[2] - bbox[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines
    
    @staticmethod
    def _hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
