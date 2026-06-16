---
title: Satyamev-Bot
emoji: 🛡️
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# Satyamev-Bot: Advanced Multimodal RAG-Driven Fact-Checking Engine

A production-grade, CPU-optimized fact-checking system leveraging LangChain agentic workflows, multimodal ingestion, and real-time web consensus verification.


## 📋 Project Overview

**Satyamev-Bot** is designed to automatically verify claims across text, audio, and images using:
- **Multimodal Ingestion**: Text processing, audio transcription (Whisper), and OCR/image understanding
- **Agentic Verification**: LangChain-based autonomous agent using Llama-3.3-70b or Gemini-1.5-Flash
- **Web Consensus**: Real-time fact-checking via Tavily Search API
- **Visual Defusing**: Automatic infographic card generation for viral claim countermeasures

## 🏗️ Architecture Phases

| Phase | Focus | Status |
|-------|-------|--------|
| **Phase 0** | Environment & Config Setup | 🔨 Current |
| **Phase 1** | Multimodal Ingestion Pipeline | ⏳ Pending |
| **Phase 2** | Agentic RAG & Web Consensus | ⏳ Pending |
| **Phase 3** | Dynamic Card Generation | ⏳ Pending |
| **Phase 4** | FastAPI Gateway Integration | ⏳ Pending |

## 🚀 Quick Start (Phase 0)

### 1. Create Virtual Environment
```powershell
cd c:\Users\ADITYA LINGAM\Desktop\SATYAMEV-BOT
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. Install Dependencies
```powershell
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### 3. Configure Environment
```powershell
Copy-Item .env.example .env
# Edit .env with your API keys:
# - GROQ_API_KEY (for Llama & Whisper)
# - GOOGLE_API_KEY (for Gemini)
# - TAVILY_API_KEY (for web search)
```

### 4. Verify Configuration
```powershell
python src/config.py
```

Expected output:
```
✓ Settings loaded successfully
  Environment: development
  Debug Mode: true
  Server: 0.0.0.0:8000

API Key Status:
  Groq: ✓ Configured
  Google: ✓ Configured
  Tavily: ✓ Configured

✓ Directories and logging initialized
```

## 📁 Project Structure

```
SATYAMEV-BOT/
├── src/
│   ├── config.py                 # Pydantic configuration loader
│   ├── app.py                    # FastAPI main (Phase 4)
│   ├── ingestion/                # Phase 1: Multimodal processing
│   │   ├── text_handler.py
│   │   ├── audio_handler.py
│   │   ├── image_handler.py
│   │   └── ingestion_manager.py
│   ├── brain/                    # Phase 2: Agentic engine
│   │   ├── agent.py
│   │   └── tools.py
│   └── utils/                    # Phase 3: Card generation
│       └── card_generator.py
├── tests/                        # Test suites
├── exports/                      # Generated verification cards
├── .env.example                  # Environment template
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

## 🔧 Tech Stack

- **Framework**: FastAPI + Uvicorn
- **Orchestration**: LangChain + LangGraph
- **LLM**: Llama-3.3-70b via Groq API
- **Alt LLM**: Gemini-1.5-Flash via Google AI Studio
- **ASR**: Whisper-large-v3-turbo via Groq API
- **OCR**: EasyOCR (local) or Gemini Multimodal API
- **Search**: Tavily Search API
- **Image Gen**: Pillow (PIL)
- **Environment**: Python 3.11+ with venv

## 📝 Development Standards

- ✅ No generic `except: pass` - all exceptions logged explicitly
- ✅ Structured logging with file & console outputs
- ✅ Pydantic models for strict input/output validation
- ✅ Incremental phase-by-phase development
- ✅ Manual testing blueprint for each phase
- ✅ Clean HTTP error responses (400/500 with JSON payloads)

## ⚠️ Important Notes

1. **No Local GPU**: All heavy computation routed through cloud APIs
2. **Phase 1 English Only**: Architecture modular for regional ASR/OCR later
3. **Incremental Development**: Each phase must be fully working before advancing
4. **Security**: Never commit `.env` file with real API keys

## 📚 Next Steps

After verifying Phase 0 runs successfully:
1. Proceed to **Phase 1: Multimodal Ingestion Pipeline**
2. Implement text, audio, and image handlers
3. Build ingestion manager orchestrator
4. Create comprehensive test suite

---

**Status**: Phase 0 - Environment Configuration ✅
