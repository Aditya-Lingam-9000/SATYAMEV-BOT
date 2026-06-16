# PHASE 3: CARD GENERATION ENGINE

## Overview

Phase 3 implements visual fact-checking proof cards using PIL (Pillow). Cards combine verdict, reasoning, evidence, and sources into shareable PNG images optimized for social media platforms.

**Key Features:**
- Multiple themes (light, dark, minimal, bold)
- Platform-specific presets (Facebook, Twitter, Instagram, LinkedIn)
- Customizable dimensions and styling
- High-resolution PNG export
- Full integration with Phase 2 verdicts

---

## Architecture

### 1. Card Rendering System

**CardGenerator** - Main rendering engine:

```
Input (Verdict Result)
    ↓
[1] Create Base Image
    ├→ Set background color
    └→ Initialize PIL canvas
    ↓
[2] Render Verdict Header
    ├→ Large colored badge (TRUE=green, FALSE=red, etc.)
    └→ Confidence score display
    ↓
[3] Render Claim Section
    ├→ Large title text
    └→ Word wrapping
    ↓
[4] Render Reasoning Section
    ├→ Explanation text
    └→ Optional truncation
    ↓
[5] Render Evidence Section
    ├→ Bullet points (max 3)
    └→ Secondary sources
    ↓
[6] Render Sources Section
    ├→ Source URLs
    └→ Link attribution
    ↓
[7] Add Footer/Watermark
    ↓
PNG Output
```

---

### 2. Configuration System (`config.py`)

**CardConfig** - Centralized configuration:

```python
from src.cards.config import CardConfig, get_preset_config

# Using preset
config = get_preset_config("facebook")  # 1200x630 for Facebook

# Custom configuration
config = CardConfig(
    width=1600,
    height=900,
    theme="dark",
    show_sources=True,
    max_sources_shown=5,
    font_size_title=48,
)
```

**Theme Support:**
| Theme | Background | Text Color | Use Case |
|-------|-----------|-----------|----------|
| **light** | White | Dark | Default, readable |
| **dark** | Dark gray | White | Modern, less glare |
| **minimal** | Light gray | Black | Clean, professional |
| **bold** | Very dark | White | High contrast |

**Platform Presets:**
| Preset | Size | Theme | Best For |
|--------|------|-------|----------|
| **twitter** | 1024x512 | light | Twitter/X posts |
| **facebook** | 1200x630 | light | Facebook feed |
| **instagram** | 1080x1080 | dark | Instagram posts |
| **linkedin** | 1200x627 | minimal | LinkedIn articles |
| **minimal** | 800x600 | minimal | Simple static display |
| **detailed** | 1600x900 | light | Comprehensive display |

---

### 3. Card Object

**Card** - Represents generated card:

```python
from src.cards.generator import CardGenerator

generator = CardGenerator()

card = generator.generate(
    claim="The Earth is round",
    verdict="TRUE",
    confidence=0.99,
    reasoning="Supported by centuries of observation",
    sources=["NASA", "ESA"],
    key_evidence=["Satellite imagery", "Physics"],
)

# Save to file
card.save("exports/proof_card.png")

# Export as bytes
png_bytes = card.to_bytes()
```

**Methods:**
- `save(path: str)` → bool: Save to PNG file
- `to_bytes()` → bytes: Export as PNG bytes

---

## Usage Examples

### Basic Card Generation

```python
from src.cards.generator import CardGenerator

generator = CardGenerator(preset="facebook", theme="light")

card = generator.generate(
    claim="COVID-19 vaccines contain microchips",
    verdict="FALSE",
    confidence=0.99,
    reasoning="Multiple credible sources confirm no microchips in vaccines",
    sources=["https://www.who.int", "https://www.cdc.gov"],
    key_evidence=[
        "Vaccine composition publicly documented",
        "Independent lab verification",
        "No microchip technology at vaccine scale"
    ],
)

card.save("exports/microchip_false.png")
```

### Integration with Phase 2 (Brain)

```python
from src.config import Settings
from src.brain.agent import FactCheckingAgent
from src.cards.generator import CardGenerator

settings = Settings()

# Verify claim
agent = FactCheckingAgent(
    groq_api_key=settings.GROQ_API_KEY,
    tavily_api_key=settings.TAVILY_API_KEY,
)

verdict = agent.verify_claim("The Moon orbits the Earth")

# Generate card from verdict
generator = CardGenerator(preset="twitter", theme="dark")
card = generator.generate(
    claim=verdict.claim,
    verdict=verdict.verdict,
    confidence=verdict.confidence,
    reasoning=verdict.reasoning,
    sources=verdict.sources,
    key_evidence=verdict.key_evidence,
)

card.save("exports/moon_orbit.png")
```

### Custom Card Configuration

```python
from src.cards.config import CardConfig
from src.cards.generator import CardGenerator

# Create custom config
custom_config = CardConfig(
    width=1600,
    height=900,
    theme="bold",
    font_size_title=64,
    font_size_verdict=96,
    font_size_body=32,
    max_reasoning_chars=300,
    max_sources_shown=5,
)

# Use custom config
generator = CardGenerator(custom_config=custom_config)

card = generator.generate(
    claim="Test claim",
    verdict="TRUE",
    confidence=0.95,
)

card.save("exports/custom_card.png")
```

### Batch Card Generation

```python
from src.cards.generator import CardGenerator

# List of verdicts from Phase 2
verdicts = [
    # ... VerdictResult objects from agent.batch_verify()
]

generator = CardGenerator(preset="facebook")

for i, verdict in enumerate(verdicts, 1):
    card = generator.generate(
        claim=verdict.claim,
        verdict=verdict.verdict,
        confidence=verdict.confidence,
        reasoning=verdict.reasoning,
        sources=verdict.sources,
        key_evidence=verdict.key_evidence,
    )
    
    output_path = f"exports/card_{i:03d}.png"
    card.save(output_path)
    print(f"Generated: {output_path}")
```

### Theme Selection

```python
from src.cards.generator import CardGenerator

themes = ["light", "dark", "minimal", "bold"]

for theme in themes:
    generator = CardGenerator(preset="facebook", theme=theme)
    
    card = generator.generate(
        claim="Example claim",
        verdict="TRUE",
        confidence=0.85,
    )
    
    card.save(f"exports/theme_{theme}.png")
```

---

## Output Specifications

### Verdict Colors

```
TRUE       → #27AE60 (Green)      ✓
FALSE      → #E74C3C (Red)        ✗
MISLEADING → #F39C12 (Orange)     ~
UNVERIFIABLE → #95A5A6 (Gray)     ?
```

### Card Dimensions

**Standard Presets:**
- Twitter: 1024×512 px (2:1 aspect ratio)
- Facebook: 1200×630 px (1.9:1 aspect ratio)
- Instagram: 1080×1080 px (1:1 aspect ratio, square)
- LinkedIn: 1200×627 px (1.9:1 aspect ratio)

**Default:** 1200×630 px (Facebook standard)

### Text Hierarchy

```
Verdict Badge (72pt, white text)
    ↓
Claim Title (48pt, primary text)
    ↓
Reasoning (24pt, secondary text)
    ↓
Evidence Bullets (16pt, secondary text)
    ↓
Sources Link (16pt, secondary text)
    ↓
Watermark (12pt, subtle text)
```

---

## Testing

### Run Test Suite

```bash
cd /path/to/SATYAMEV-BOT
.\venv\Scripts\python.exe tests/test_cards.py
```

**Test Coverage:**
1. Configuration system validation
2. Preset loading and validation
3. Generator initialization
4. Card generation for all verdict types
5. Theme rendering (light, dark, minimal, bold)
6. Preset rendering (Twitter, Facebook, Instagram, LinkedIn)
7. Export functionality (PNG, bytes)

**Expected Output:**
```
[PASS] Configuration System
[PASS] Preset System
[PASS] Generator Initialization
[PASS] Basic Card Generation
[PASS] Theme Rendering
[PASS] Preset Rendering
[PASS] Export Functionality

Total: 7/7 tests passed
✓ ALL TESTS PASSED - Phase 3 ready for integration
```

**Generated Test Cards:**
```
exports/
├── test_true.png
├── test_false.png
├── test_misleading.png
├── test_unverifiable.png
├── test_theme_light.png
├── test_theme_dark.png
├── test_theme_minimal.png
├── test_theme_bold.png
├── test_preset_twitter.png
├── test_preset_facebook.png
├── test_preset_instagram.png
├── test_preset_linkedin.png
└── test_preset_minimal.png
```

---

## API Reference

### CardGenerator

```python
class CardGenerator:
    def __init__(
        self,
        preset: str = "facebook",
        theme: Optional[str] = None,
        custom_config: Optional[CardConfig] = None,
    ) -> None:
        """Initialize card generator."""
    
    def generate(
        self,
        claim: str,
        verdict: str,
        confidence: float,
        reasoning: Optional[str] = None,
        sources: Optional[List[str]] = None,
        key_evidence: Optional[List[str]] = None,
    ) -> Card:
        """Generate a fact-checking card."""
```

### Card

```python
class Card:
    def save(self, path: str) -> bool:
        """Save card to PNG file."""
    
    def to_bytes(self) -> bytes:
        """Export as PNG bytes."""
```

### Configuration

```python
CardConfig(
    width: int = 1200,
    height: int = 630,
    padding: int = 40,
    theme: str = "light",
    logo_path: Optional[str] = None,
    watermark: str = "SATYAMEV-BOT",
    show_confidence: bool = True,
    show_sources: bool = True,
    max_sources_shown: int = 3,
    truncate_reasoning: bool = True,
    max_reasoning_chars: int = 200,
    font_size_title: int = 48,
    font_size_verdict: int = 72,
    font_size_body: int = 24,
    font_size_small: int = 16,
)
```

---

## Performance

| Operation | Duration |
|-----------|----------|
| Card generation (simple) | 500-800ms |
| Card generation (complex) | 1-2 seconds |
| PNG export | 200-400ms |
| Batch (10 cards) | 8-15 seconds |

**Optimization Tips:**
- Reuse generator instance for batch operations
- Use simpler themes (minimal) for faster rendering
- Reduce max sources if not needed
- Pre-generate common cards

---

## Font Support

**Automatic Font Detection:**
1. Attempts Arial.ttf (Windows)
2. Falls back to DejaVuSans (Linux)
3. Final fallback to PIL default font

**Custom Fonts:**
```python
# Not yet implemented - future enhancement
# config.custom_font_path = "/path/to/font.ttf"
```

---

## Social Media Optimization

### Twitter/X
- Preset: `twitter` (1024×512)
- Theme: `light` or `dark`
- Best for: Quick fact-checks, breaking news
- File size: ~50-80 KB

### Facebook
- Preset: `facebook` (1200×630)
- Theme: `light` (high visibility)
- Best for: Detailed fact-checks, articles
- File size: ~80-120 KB

### Instagram
- Preset: `instagram` (1080×1080)
- Theme: `dark` (Instagram aesthetic)
- Best for: Vertical story format, reels
- File size: ~70-100 KB

### LinkedIn
- Preset: `linkedin` (1200×627)
- Theme: `minimal` (professional)
- Best for: Corporate/organizational sharing
- File size: ~60-90 KB

---

## File Structure

```
src/cards/
├── __init__.py          # Module initialization
├── config.py            # Configuration system
├── generator.py         # Main card rendering engine
│
tests/
├── test_cards.py        # Comprehensive test suite
│
examples/
├── generate_card.py     # Integrated Phase 2+3 example
│
exports/
└── *.png                # Generated cards
```

---

## Known Limitations

1. **Font Rendering**: Limited to system fonts; custom fonts not yet supported
2. **Complex Layouts**: No multi-column or advanced grid layouts
3. **Images**: Cannot embed external images in cards
4. **Transparency**: Alpha channel not supported (opaque PNG only)
5. **RTL Languages**: Left-to-right only; RTL not supported

---

## Future Enhancements (Phase 3.5+)

- [ ] Custom font support (upload TTF/OTF)
- [ ] Embedded images/logos in cards
- [ ] QR code linking to full fact-check
- [ ] Multiple language support
- [ ] Template system (user-defined layouts)
- [ ] Dynamic color adjustment based on contrast
- [ ] SVG export option
- [ ] Batch watermarking
- [ ] Card animation support (GIF)
- [ ] Brand customization profiles

---

## Integration with Other Phases

### Phase 1 → Phase 3
Ingestion extracts claim → directly pass to CardGenerator

### Phase 2 → Phase 3 (Full Pipeline)
```
Input Claim (text/audio/image)
    ↓ [Phase 1: Ingestion]
Extracted Text
    ↓ [Phase 2: Brain]
VerdictResult {verdict, confidence, reasoning, sources}
    ↓ [Phase 3: Cards]
Visual Proof Card (PNG)
    ↓
Export & Share
```

### Phase 3 → Phase 4 (API)
```python
# FastAPI endpoint (Phase 4)
@app.post("/api/generate-card")
async def generate_card(verdict: VerdictResult):
    generator = CardGenerator()
    card = generator.generate(
        claim=verdict.claim,
        verdict=verdict.verdict,
        ...
    )
    return card.to_bytes()
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Font not found | Check system fonts; PIL will fallback to default |
| Image too large | Reduce dimensions or use minimal theme |
| Slow rendering | Reuse generator; reduce source count |
| Text cut off | Increase height or use simpler claim |
| Colors look wrong | Check theme name and THEMES dict |
| Export failed | Ensure exports/ directory exists and is writable |

---

## Support & Debugging

**Enable debug logging:**
```python
import logging
logging.getLogger("src.cards").setLevel(logging.DEBUG)
```

**Test font rendering:**
```python
from PIL import ImageFont
font = ImageFont.truetype("arial.ttf", 48)
# If fails, PIL will use default font
```

---

**Status**: Phase 3 COMPLETE ✓  
**Last Updated**: 2026-06-14  
**Version**: 0.1.0
