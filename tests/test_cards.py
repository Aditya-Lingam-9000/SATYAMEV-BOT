"""
Phase 3 Testing: Card Generation Engine

Comprehensive test suite for:
1. Card configuration system
2. Card generation with various templates
3. Visual output validation
4. Theme support
5. Integration with Phase 2 verdicts

Run: python tests/test_cards.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging
import json
from src.cards.config import CardConfig, get_preset_config, PRESETS, THEMES
from src.cards.generator import CardGenerator, Card

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger(__name__)


def test_config():
    """Test 1: Configuration system."""
    print("\n" + "="*80)
    print("TEST 1: CARD CONFIGURATION SYSTEM")
    print("="*80)
    
    try:
        # Test default config
        config = CardConfig()
        assert config.width == 1200
        assert config.height == 630
        print("[PASS] Default config created")
        
        # Test theme validation
        for theme_name in THEMES.keys():
            config = CardConfig(theme=theme_name)
            assert config.theme == theme_name
            print(f"[PASS] Theme '{theme_name}' validated")
        
        # Test invalid theme
        try:
            config = CardConfig(theme="invalid")
            print("[FAIL] Should reject invalid theme")
            return False
        except ValueError:
            print("[PASS] Invalid theme properly rejected")
        
        # Test color scheme
        config = CardConfig(theme="light")
        scheme = config.get_color_scheme()
        assert scheme.background == "#FFFFFF"
        print("[PASS] Color scheme retrieved successfully")
        
        print("\n[PASS] Configuration system verified")
    
    except Exception as e:
        print(f"\n[FAIL] Configuration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def test_presets():
    """Test 2: Preset configurations."""
    print("\n" + "="*80)
    print("TEST 2: CARD PRESETS")
    print("="*80)
    
    try:
        print("\nAvailable presets:")
        for preset_name, preset_config in PRESETS.items():
            print(
                f"  - {preset_name}: "
                f"{preset_config.width}x{preset_config.height}, "
                f"theme={preset_config.theme}"
            )
        
        # Test each preset
        for preset_name in PRESETS.keys():
            config = get_preset_config(preset_name)
            assert config is not None
            print(f"[PASS] Preset '{preset_name}' loaded")
        
        # Test invalid preset
        try:
            get_preset_config("invalid")
            print("[FAIL] Should reject invalid preset")
            return False
        except ValueError:
            print("[PASS] Invalid preset properly rejected")
        
        print("\n[PASS] Preset system verified")
    
    except Exception as e:
        print(f"\n[FAIL] Preset test failed: {str(e)}")
        return False
    
    return True


def test_generator_initialization():
    """Test 3: Card generator initialization."""
    print("\n" + "="*80)
    print("TEST 3: CARD GENERATOR INITIALIZATION")
    print("="*80)
    
    try:
        # Test default initialization
        generator = CardGenerator()
        assert generator.config is not None
        print("[PASS] Generator initialized with defaults")
        
        # Test with preset
        generator = CardGenerator(preset="twitter")
        assert generator.config.width == 1024
        print("[PASS] Generator initialized with 'twitter' preset")
        
        # Test with custom theme
        generator = CardGenerator(preset="facebook", theme="dark")
        assert generator.config.theme == "dark"
        print("[PASS] Generator initialized with custom theme")
        
        # Test with custom config
        custom_config = CardConfig(width=800, height=600, theme="minimal")
        generator = CardGenerator(custom_config=custom_config)
        assert generator.config.width == 800
        print("[PASS] Generator initialized with custom config")
        
        print("\n[PASS] Generator initialization verified")
    
    except Exception as e:
        print(f"\n[FAIL] Generator initialization test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def test_card_generation():
    """Test 4: Basic card generation."""
    print("\n" + "="*80)
    print("TEST 4: BASIC CARD GENERATION")
    print("="*80)
    
    try:
        # Ensure exports directory exists
        export_path = Path("exports")
        export_path.mkdir(exist_ok=True)
        
        generator = CardGenerator(preset="facebook", theme="light")
        
        # Test TRUE verdict
        print("\n4.1: Generating TRUE verdict card")
        card = generator.generate(
            claim="The Earth revolves around the Sun",
            verdict="TRUE",
            confidence=0.99,
            reasoning="Supported by centuries of astronomical observation and physics",
            sources=["NASA", "ESA", "Physics textbooks"],
            key_evidence=["Kepler's laws", "Observable parallax", "Seasons"],
        )
        
        assert card is not None
        assert card.verdict == "TRUE"
        assert card.confidence == 0.99
        print("[PASS] TRUE card generated")
        
        # Save card
        output_path = export_path / "test_true.png"
        success = card.save(str(output_path))
        assert success
        assert output_path.exists()
        print(f"[PASS] Card saved: {output_path}")
        
        # Test FALSE verdict
        print("\n4.2: Generating FALSE verdict card")
        card = generator.generate(
            claim="The Moon is made of cheese",
            verdict="FALSE",
            confidence=0.99,
            reasoning="Scientific analysis of moon rocks shows silicate composition",
            sources=["NASA Apollo missions", "Lunar samples"],
            key_evidence=["Geological composition", "Satellite imagery"],
        )
        
        assert card.verdict == "FALSE"
        print("[PASS] FALSE card generated")
        
        output_path = export_path / "test_false.png"
        success = card.save(str(output_path))
        assert success
        print(f"[PASS] Card saved: {output_path}")
        
        # Test MISLEADING verdict
        print("\n4.3: Generating MISLEADING verdict card")
        card = generator.generate(
            claim="Vaccines are completely safe with no side effects",
            verdict="MISLEADING",
            confidence=0.85,
            reasoning="While vaccines are safe overall, minor side effects can occur",
            sources=["CDC", "WHO", "Medical journals"],
            key_evidence=["Rigorous testing", "Minor side effects documented"],
        )
        
        assert card.verdict == "MISLEADING"
        print("[PASS] MISLEADING card generated")
        
        output_path = export_path / "test_misleading.png"
        success = card.save(str(output_path))
        assert success
        print(f"[PASS] Card saved: {output_path}")
        
        # Test UNVERIFIABLE verdict
        print("\n4.4: Generating UNVERIFIABLE verdict card")
        card = generator.generate(
            claim="Aliens visited Earth in 1987",
            verdict="UNVERIFIABLE",
            confidence=0.2,
            reasoning="Insufficient credible evidence",
            sources=[],
        )
        
        assert card.verdict == "UNVERIFIABLE"
        print("[PASS] UNVERIFIABLE card generated")
        
        output_path = export_path / "test_unverifiable.png"
        success = card.save(str(output_path))
        assert success
        print(f"[PASS] Card saved: {output_path}")
        
        print("\n[PASS] Card generation verified")
    
    except Exception as e:
        print(f"\n[FAIL] Card generation test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def test_card_themes():
    """Test 5: Theme rendering."""
    print("\n" + "="*80)
    print("TEST 5: CARD THEMES")
    print("="*80)
    
    try:
        export_path = Path("exports")
        
        themes_to_test = ["light", "dark", "minimal", "bold"]
        
        for i, theme in enumerate(themes_to_test, 1):
            print(f"\n5.{i}: Generating card with '{theme}' theme")
            
            generator = CardGenerator(preset="facebook", theme=theme)
            
            card = generator.generate(
                claim="Test claim for theme rendering",
                verdict="TRUE",
                confidence=0.90,
                reasoning=f"Testing {theme} theme rendering",
                sources=["Source 1", "Source 2"],
            )
            
            output_path = export_path / f"test_theme_{theme}.png"
            success = card.save(str(output_path))
            assert success
            print(f"[PASS] {theme} theme card saved")
        
        print("\n[PASS] Theme rendering verified")
    
    except Exception as e:
        print(f"\n[FAIL] Theme test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def test_card_presets_rendering():
    """Test 6: Preset rendering."""
    print("\n" + "="*80)
    print("TEST 6: PRESET RENDERING")
    print("="*80)
    
    try:
        export_path = Path("exports")
        
        presets_to_test = ["twitter", "facebook", "instagram", "linkedin", "minimal"]
        
        for preset in presets_to_test:
            print(f"\n6.{presets_to_test.index(preset)+1}: Rendering with '{preset}' preset")
            
            generator = CardGenerator(preset=preset)
            
            card = generator.generate(
                claim=f"Card generated for {preset} social platform",
                verdict="TRUE",
                confidence=0.85,
                reasoning="Testing preset-specific rendering",
                sources=["Source A"],
            )
            
            output_path = export_path / f"test_preset_{preset}.png"
            success = card.save(str(output_path))
            assert success
            print(f"[PASS] {preset} preset card saved")
        
        print("\n[PASS] Preset rendering verified")
    
    except Exception as e:
        print(f"\n[FAIL] Preset rendering test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def test_card_export():
    """Test 7: Card export functionality."""
    print("\n" + "="*80)
    print("TEST 7: CARD EXPORT FUNCTIONALITY")
    print("="*80)
    
    try:
        export_path = Path("exports")
        
        generator = CardGenerator()
        card = generator.generate(
            claim="Testing export functionality",
            verdict="TRUE",
            confidence=0.95,
        )
        
        # Test PNG export
        png_path = export_path / "test_export.png"
        success = card.save(str(png_path))
        assert success
        assert png_path.exists()
        assert png_path.stat().st_size > 0
        print(f"[PASS] PNG export successful ({png_path.stat().st_size} bytes)")
        
        # Test bytes export
        png_bytes = card.to_bytes()
        assert len(png_bytes) > 0
        print(f"[PASS] Bytes export successful ({len(png_bytes)} bytes)")
        
        print("\n[PASS] Export functionality verified")
    
    except Exception as e:
        print(f"\n[FAIL] Export test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def run_all_tests():
    """Run all Phase 3 tests."""
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "PHASE 3: CARD GENERATION ENGINE - TEST SUITE".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "="*78 + "╝")
    
    tests = [
        ("Configuration System", test_config),
        ("Preset System", test_presets),
        ("Generator Initialization", test_generator_initialization),
        ("Basic Card Generation", test_card_generation),
        ("Theme Rendering", test_card_themes),
        ("Preset Rendering", test_card_presets_rendering),
        ("Export Functionality", test_card_export),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            logger.exception(f"Test '{name}' crashed: {str(e)}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {name}")
    
    print(f"\nTotal: {passed_count}/{total_count} tests passed")
    
    # List generated cards
    export_path = Path("exports")
    if export_path.exists():
        cards = list(export_path.glob("test_*.png"))
        if cards:
            print(f"\nGenerated {len(cards)} test cards:")
            for card_path in sorted(cards):
                size_mb = card_path.stat().st_size / (1024 * 1024)
                print(f"  - {card_path.name} ({size_mb:.2f} MB)")
    
    if passed_count == total_count:
        print("\n✓ ALL TESTS PASSED - Phase 3 ready for integration")
    else:
        print(f"\n✗ {total_count - passed_count} test(s) failed")
    
    return passed_count == total_count


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
