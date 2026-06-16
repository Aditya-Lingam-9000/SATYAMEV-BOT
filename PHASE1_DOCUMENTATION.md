# PHASE 1: MULTIMODAL INGESTION PIPELINE

## Overview

Phase 1 implements a complete multimodal ingestion system that accepts claims in three formats:
1. **Text**: Direct text strings
2. **Audio**: Audio files (voice notes) transcribed via Groq Whisper API
3. **Image**: Screenshots/images with text extracted via EasyOCR or Gemini Vision

All inputs are normalized, cleaned, and output as unified plain English text ready for the verification engine (Phase 2).

---

## Architecture

### Module Structure

```
src/ingestion/
├── text_handler.py        # Text processing & normalization
├── audio_handler.py       # Groq Whisper integration
├── image_handler.py       # EasyOCR + Gemini Vision (dual engine)
├── ingestion_manager.py   # Orchestrator & factory pattern
└── __init__.py
```

---

## Component Details

### 1. TextHandler (`text_handler.py`)

**Responsibility**: Text validation, normalization, and cleaning.

**Key Methods**:
- `validate(text)`: Checks for None, type, length constraints
- `normalize(text)`: Whitespace normalization, unicode handling
- `clean(text)`: Removes URLs, emails, phone numbers, repeated punctuation
- `process(text, clean=True)`: Complete pipeline

**Configuration**:
```python
MIN_LENGTH = 10 chars
MAX_LENGTH = 5000 chars
```

**Example**:
```python
handler = TextHandler()
success, output, error = handler.process(
    "Visit http://example.com!!! COVID VACCINES MICROCHIPS!!!",
    clean=True
)
# Output: "Visit [URL] COVID VACCINES MICROCHIPS"
```

---

### 2. AudioHandler (`audio_handler.py`)

**Responsibility**: Audio file transcription using Groq Whisper API.

**Supported Formats**: `.mp3`, `.wav`, `.ogg`, `.flac`, `.m4a`

**Key Methods**:
- `validate(audio_path)`: File existence, format, size checks (max 25MB)
- `transcribe(audio_path)`: Stream to Groq Whisper API
  - Model: `whisper-large-v3-turbo`
  - Language: English only (Phase 1)

**Configuration**:
```python
MAX_FILE_SIZE_MB = 25
SUPPORTED_FORMATS = {".mp3", ".wav", ".ogg", ".flac", ".m4a"}
```

**Requirements**:
- Groq API key in `.env` file: `GROQ_API_KEY=<your_key>`
- Get key from: https://console.groq.com/keys

**Example**:
```python
handler = AudioHandler(api_key="gsk_...")
success, transcription, error = handler.transcribe("voice_note.mp3")
# Output: Transcribed text from audio
```

---

### 3. ImageHandler (`image_handler.py`)

**Responsibility**: OCR text extraction from images with dual-engine support.

**Supported Formats**: `.png`, `.jpg`, `.jpeg`, `.bmp`, `.webp`

**Engines**:
1. **EasyOCR** (Default):
   - CPU-optimized (no GPU required)
   - Fast, reliable for screenshots
   - Confidence filtering (min 0.3)
   
2. **Gemini-1.5-Flash** (Fallback):
   - Multimodal vision API
   - Better at complex images
   - Requires Google API key

**Key Methods**:
- `validate(image_path)`: File existence, format, size checks (max 50MB)
- `extract(image_path)`: Extract text, with automatic fallback
- `_extract_easyocr()`: EasyOCR implementation
- `_extract_gemini()`: Gemini Vision implementation

**Configuration**:
```python
SUPPORTED_FORMATS = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}
MAX_FILE_SIZE_MB = 50
MIN_CONFIDENCE = 0.3  # EasyOCR only
```

**Requirements**:
- EasyOCR: Built-in, no API key needed (PyTorch-based)
- Gemini: Optional fallback, requires `GOOGLE_API_KEY=<your_key>`
- Get key from: https://aistudio.google.com/apikey

**Example**:
```python
handler = ImageHandler(primary_engine="easyocr")
success, extracted_text, error = handler.extract("screenshot.png")
# Output: Text extracted from image
```

---

### 4. IngestionManager (`ingestion_manager.py`)

**Responsibility**: Unified orchestrator routing inputs to appropriate handlers.

**Key Methods**:
- `__init__(groq_api_key, google_api_key, image_engine)`: Initialize all handlers
- `ingest(source, input_type, clean=True)`: Main entry point
- `ingest_text(text, clean=True)`: Convenience method
- `ingest_audio(audio_path)`: Convenience method
- `ingest_image(image_path)`: Convenience method
- `_detect_type(source)`: Auto-detect input type from file extension

**Auto-Detection Logic**:
- File exists + `.mp3/.wav/.ogg/.flac/.m4a` → Audio
- File exists + `.png/.jpg/.jpeg/.bmp/.webp` → Image
- String or non-existent file → Text

**Example**:
```python
manager = IngestionManager(
    groq_api_key="gsk_...",
    google_api_key="AIzaSy...",
    image_engine="easyocr"
)

# Text
success, output, error = manager.ingest_text("COVID vaccines have microchips")

# Audio
success, output, error = manager.ingest_audio("voice_claim.mp3")

# Image
success, output, error = manager.ingest_image("screenshot.png")

# Auto-detect
success, output, error = manager.ingest("unknown_input.wav")
```

---

## Error Handling

All handlers implement **strict, non-silent error handling**:

```python
# Pattern used throughout Phase 1
success, output, error = handler.method(input)

if not success:
    logger.error("Operation failed: {}".format(error))
    # Handle specific error...
```

**Example Errors**:
- `"Text input is None"`
- `"Audio file too large: 30.5MB (max: 25MB)"`
- `"Unsupported image format: .pdf. Supported: .png, .jpg, .jpeg, .bmp, .webp"`
- `"Groq Whisper transcription failed: Connection timeout"`
- `"Both engines failed. Primary: EasyOCR error. Fallback: Gemini error"`

---

## Logging

All modules use structured logging:

```
[timestamp] [module_name] [LEVEL] [message]
```

**Example Output**:
```
[2026-06-14 10:30:45] [satyamev_bot.ingestion.text] [INFO] Text processing successful: 150 chars
[2026-06-14 10:30:46] [satyamev_bot.ingestion.audio] [DEBUG] Opening audio file: voice.mp3
[2026-06-14 10:30:47] [satyamev_bot.ingestion.image] [WARNING] Primary engine failed, attempting fallback...
```

---

## Testing

### Run Phase 1 Manual Test Suite

```powershell
cd c:\Users\ADITYA LINGAM\Desktop\SATYAMEV-BOT
.\venv\Scripts\python.exe tests/test_ingestion.py
```

### Test Coverage

| Test | Type | Status |
|------|------|--------|
| Text validation (empty, short, long) | Unit | ✓ Always runs |
| Text normalization (URLs, emails) | Unit | ✓ Always runs |
| Audio handler init | Integration | ⚠ Optional (requires key) |
| Audio transcription | Integration | ⚠ Optional (requires file + key) |
| Image handler init | Integration | ✓ Always runs (EasyOCR) |
| Image extraction | Integration | ⚠ Optional (requires file) |
| Manager orchestration | Integration | ✓ Always runs |
| End-to-end pipeline | Integration | ✓ Always runs |

### Expected Output Example

```
================================================================================
          PHASE 1: MULTIMODAL INGESTION PIPELINE - MANUAL TEST SUITE
================================================================================

Environment: development
Debug Mode: True
Log Level: INFO

================================================================================
                         TEST 1: TEXT HANDLER
================================================================================

1.1: Valid text processing
Input:  The Earth is flat. This is a false claim that needs verification.
Output: The Earth is flat. This is a false claim that needs verification.
Status: [PASS]

1.2: Text with URLs, emails, special chars
Input:  Visit http://example.com or email test@domain.com for more!!! Information...
Output: Visit [URL] or email [EMAIL] for more! Information.
Status: [PASS] - URLs and emails cleaned

...

================================================================================
                      PHASE 1 TESTING COMPLETE
================================================================================

Summary:
  [PASS] TextHandler fully operational
  [INFO] AudioHandler ready (requires Groq API key)
  [INFO] ImageHandler ready (EasyOCR functional)
  [PASS] IngestionManager orchestration verified

Next Steps:
  1. Optional: Configure Groq/Google API keys in .env
  2. Proceed to Phase 2: Agentic RAG & Web Consensus Engine
```

---

## Configuration

### .env Requirements

**Required for Phase 1**:
```env
# Existing (Phase 0)
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# Optional for audio transcription
GROQ_API_KEY=gsk_...  # From https://console.groq.com/keys

# Optional for image extraction fallback
GOOGLE_API_KEY=AIzaSy...  # From https://aistudio.google.com/apikey
```

---

## Performance Characteristics

### Text Processing
- **Speed**: < 10ms (no API calls)
- **Memory**: O(n) where n = text length
- **Max input**: 5000 chars

### Audio Transcription (Groq Whisper)
- **Speed**: ~30-60s for 5min audio (depends on file size)
- **Latency**: ~1-2s initial, then streaming
- **Max file size**: 25MB
- **Formats**: MP3, WAV, OGG, FLAC, M4A

### Image Extraction (EasyOCR)
- **Speed**: ~2-10s first run (model load), ~100-500ms subsequent
- **Speed**: Gemini Vision: ~2-5s (API call)
- **Memory**: ~1-2GB (first run for model loading)
- **Max file size**: 50MB
- **Formats**: PNG, JPG, BMP, WEBP

---

## Next Steps (Phase 2)

Phase 1 output (normalized English text) feeds into:

1. **Agentic Verification Engine** (LangChain)
   - Analyze claim using LLM
   - Execute strategic web searches
   - Cross-reference sources
   - Generate verdict (TRUE/FALSE/MISLEADING)

2. **Web Consensus Layer** (Tavily Search API)
   - Real-time fact verification
   - Source credibility assessment
   - Multi-source cross-validation

---

## Troubleshooting

### "No module named 'src'"
**Solution**: Run tests from project root, not subdirectories
```powershell
cd c:\Users\ADITYA LINGAM\Desktop\SATYAMEV-BOT
.\venv\Scripts\python.exe tests/test_ingestion.py  # Correct
```

### "Groq API key not configured"
**Solution**: Add valid API key to `.env`
```
GROQ_API_KEY=gsk_your_actual_key_here
```
Get key from: https://console.groq.com/keys

### "EasyOCR model not found"
**Solution**: First run downloads model (~200MB), requires internet
```
# First run may take 5-10 minutes for model download
# Subsequent runs use cached model
```

### "Audio handler not available"
**Solution**: Either add Groq key to `.env`, or use text/image only
```python
# Will still work (text & image only)
manager = IngestionManager(groq_api_key=None)
```

---

## Files Created

```
src/ingestion/
├── text_handler.py              (~260 lines)
├── audio_handler.py             (~180 lines)
├── image_handler.py             (~280 lines)
├── ingestion_manager.py         (~200 lines)
└── __init__.py

tests/
└── test_ingestion.py            (~400 lines)

Total: ~1320 lines of production code + tests
```

---

## Phase 1 Completion Checklist

- [x] TextHandler: Text normalization & cleaning
- [x] AudioHandler: Groq Whisper integration
- [x] ImageHandler: EasyOCR + Gemini dual engine
- [x] IngestionManager: Orchestrator & factory pattern
- [x] Comprehensive error handling & logging
- [x] Manual test suite with 5 test categories
- [x] Documentation with examples & troubleshooting

**Status**: Ready for Phase 2 🚀
