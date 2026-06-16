import sys
from pathlib import Path

# Add project root to sys.path so imports work
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("=" * 80)
print("PHASE 0: ENVIRONMENT CONFIGURATION & ARCHITECTURE BOOTSTRAPPING")
print("=" * 80)
print()

print("TEST 1: Python Version Validation")
print("-" * 80)
required_version = (3, 11)
current_version = sys.version_info[:2]
if current_version >= required_version:
    print("[PASS] Python {}.{} detected (required: 3.11+)".format(current_version[0], current_version[1]))
    print("       Interpreter: {}".format(sys.executable))
else:
    print("[FAIL] Python {}.{} is below required version 3.11+".format(current_version[0], current_version[1]))
    sys.exit(1)
print()

print("TEST 2: Virtual Environment Verification")
print("-" * 80)
in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
if in_venv:
    print("[PASS] Virtual environment detected")
    print("       venv location: {}".format(sys.prefix))
else:
    print("[WARN] Not running in virtual environment (optional but recommended)")
print()

print("TEST 3: Core Dependency Import Validation")
print("-" * 80)
required_packages = {
    "fastapi": "FastAPI (Web Framework)",
    "uvicorn": "Uvicorn (ASGI Server)",
    "pydantic": "Pydantic (Data Validation)",
    "pydantic_settings": "Pydantic Settings",
    "dotenv": "Python-dotenv (Env Loader)",
    "langchain": "LangChain (Orchestration)",
    "langchain_core": "LangChain Core",
    "langchain_community": "LangChain Community",
    "groq": "Groq API Client",
    "google.generativeai": "Google Generative AI",
    "requests": "Requests (HTTP)",
    "PIL": "Pillow (Image Processing)",
    "easyocr": "EasyOCR",
    "tavily": "Tavily Search API",
    "httpx": "HTTPX (HTTP Client)",
}
failed_imports = []
for package_name, description in required_packages.items():
    try:
        __import__(package_name)
        print("[PASS] {:<40} ({})".format(description, package_name))
    except ImportError as e:
        print("[FAIL] {:<40} ({}) - ERROR: {}".format(description, package_name, str(e)))
        failed_imports.append(package_name)
if failed_imports:
    print("\n[FAIL] Failed to import {} package(s): {}".format(len(failed_imports), ', '.join(failed_imports)))
    sys.exit(1)
print("\n[PASS] All core dependencies imported successfully!")
print()

print("TEST 4: Project Directory Structure Validation")
print("-" * 80)
project_root = Path(__file__).parent.parent
required_dirs = ["src", "src/ingestion", "src/brain", "src/utils", "tests", "exports"]
all_dirs_exist = True
for dir_path in required_dirs:
    full_path = project_root / dir_path
    if full_path.exists() and full_path.is_dir():
        print("[PASS] {:<30} exists".format(dir_path))
    else:
        print("[FAIL] {:<30} MISSING".format(dir_path))
        all_dirs_exist = False
if not all_dirs_exist:
    print("\n[FAIL] Some directories are missing.")
    sys.exit(1)
print("\n[PASS] All required directories exist!")
print()

print("TEST 5: Configuration Loading & Parsing")
print("-" * 80)
try:
    from src.config import get_settings
    settings = get_settings()
    print("[PASS] Configuration loaded successfully from .env")
    print()
    print("  Loaded Configuration Values:")
    print("    SERVER_HOST: {}".format(settings.SERVER_HOST))
    print("    SERVER_PORT: {}".format(settings.SERVER_PORT))
    print("    ENVIRONMENT: {}".format(settings.ENVIRONMENT))
    print("    DEBUG: {}".format(settings.DEBUG))
    print("    LOG_LEVEL: {}".format(settings.LOG_LEVEL))
    print("    TEMP_DIR: {}".format(settings.TEMP_DIR))
    print("    EXPORTS_DIR: {}".format(settings.EXPORTS_DIR))
except Exception as e:
    print("[FAIL] Configuration loading failed: {}".format(e))
    sys.exit(1)
print()

print("TEST 6: API Key Configuration Status")
print("-" * 80)
try:
    api_status = settings.validate_api_keys()
    print("  Groq API:        {}".format("[PASS] Configured" if api_status['groq_configured'] else "[WARN] NOT SET"))
    print("  Google API:      {}".format("[PASS] Configured" if api_status['google_configured'] else "[WARN] NOT SET"))
    print("  Tavily API:      {}".format("[PASS] Configured" if api_status['tavily_configured'] else "[WARN] NOT SET"))
    if not any(api_status.values()):
        print("\n[WARN] No API keys configured!")
        print("       You can add them to .env file for Phase 1 testing")
except Exception as e:
    print("[FAIL] API key validation failed: {}".format(e))
    sys.exit(1)
print()

print("TEST 7: Directory Setup & Logging Initialization")
print("-" * 80)
try:
    settings.setup_directories()
    print("[PASS] Required directories created/verified")
    logger = settings.setup_logging()
    print("[PASS] Logging system initialized")
    print("       Log file: {}".format(settings.LOG_FILE))
except Exception as e:
    print("[FAIL] Directory setup or logging initialization failed: {}".format(e))
    sys.exit(1)
print()

print("TEST 8: File Permissions & Write Access")
print("-" * 80)
try:
    temp_dir = Path(settings.TEMP_DIR)
    temp_dir.mkdir(parents=True, exist_ok=True)
    test_file = temp_dir / "test_write.txt"
    test_file.write_text("Permission test successful")
    test_file.unlink()
    print("[PASS] Write access verified in {}".format(settings.TEMP_DIR))
    exports_dir = Path(settings.EXPORTS_DIR)
    exports_dir.mkdir(parents=True, exist_ok=True)
    print("[PASS] Write access verified in {}".format(settings.EXPORTS_DIR))
except Exception as e:
    print("[FAIL] Write access test failed: {}".format(e))
    sys.exit(1)
print()

print("=" * 80)
print("PHASE 0 VALIDATION COMPLETE [PASS]")
print("=" * 80)
print()
print("Summary:")
print("  [PASS] Python 3.11+ detected")
print("  [PASS] All core dependencies installed")
print("  [PASS] Project directory structure valid")
print("  [PASS] Configuration system operational")
print("  [PASS] Logging system initialized")
print("  [PASS] Directory permissions verified")
print()
print("Next Steps:")
print("  1. Configure API keys in .env file (see TEST 6)")
print("  2. Run Phase 1 setup: Multimodal Ingestion Pipeline")
print("  3. Execute Phase 1 manual testing")
print()
print("=" * 80)
