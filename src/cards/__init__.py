"""
Card Generation Engine - Phase 3

Generates visual fact-checking proof cards with verdict, evidence, and sources.
Outputs PNG images optimized for social media sharing and web display.

Components:
- config.py: Card design configuration (colors, fonts, sizes)
- templates.py: Predefined card layouts and designs
- generator.py: Main card rendering engine using PIL
- styles.py: Theme management (light, dark, brand)

Usage:
    from src.cards.generator import CardGenerator
    from src.brain.agent import VerdictResult
    
    generator = CardGenerator(template="modern", theme="light")
    card = generator.generate_from_verdict(verdict_result)
    card.save("exports/fact_check.png")
"""

__version__ = "0.1.0"
__all__ = ["CardGenerator", "CardTemplate", "CardTheme"]
