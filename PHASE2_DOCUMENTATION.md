# PHASE 2: AGENTIC RAG & WEB CONSENSUS ENGINE

## Overview

Phase 2 implements "THE BRAIN" - an intelligent fact-checking agent using **ReAct** (Reasoning + Acting) architecture with LangChain-inspired autonomous loop.

**Verdict Categories:**
- **TRUE**: Claim supported by credible evidence
- **FALSE**: Claim contradicted by evidence  
- **MISLEADING**: Partially true or lacking crucial context
- **UNVERIFIABLE**: Insufficient evidence to determine

---

## Architecture

### 1. Agent Orchestration (`brain/agent.py`)

**FactCheckingAgent** - Main orchestrator using ReAct pattern:

```
Input Claim
    ↓
[1] Parse Claim Structure
    ↓
[2] Web Search for Evidence
    ├→ Search supporting evidence
    └→ Search contradicting evidence
    ↓
[3] Analyze with LLM
    ├→ Assess credibility
    ├→ Consider specificity
    └→ Generate reasoning
    ↓
[4] Verdict Generation
    ├→ Determine verdict (TRUE/FALSE/MISLEADING/UNVERIFIABLE)
    ├→ Confidence score (0-1)
    └→ Extract sources & key facts
    ↓
VerdictResult (JSON)
```

**Methods:**
- `verify_claim(claim)` → `VerdictResult`: Single claim verification
- `batch_verify(claims)` → `List[VerdictResult]`: Multiple claims
- `_analyze_evidence()`: LLM-powered evidence analysis
- `_parse_verdict_response()`: JSON parsing with fallback handling

**LLM Models:**
- Primary: Groq's **Llama-3.3-70b-versatile** (low-cost reasoning)
- Fallback: Google's **Gemini-1.5-Flash** (multimodal capability)
- Temperature: 0.1 (deterministic fact-checking)

---

### 2. Tool Suite (`brain/tools.py`)

#### WebSearchTool (Tavily API)
Performs real-time web searches with automatic query optimization.

```python
web_search = WebSearchTool(api_key=tavily_key)

# Single search
success, results, error = web_search.search(
    query="vaccine safety studies",
    topic="general",
    include_answer=True
)

# Dual-evidence search
evidence = web_search.search_claim_evidence(
    claim="The Earth is flat"
)
# Returns: {"supporting": [...], "contradicting": [...]}
```

**Features:**
- Automatic query optimization by Tavily
- Dual search (supporting + contradicting evidence)
- Configurable result limits (1-10)
- Error handling & retry logic

---

#### VectorDatabaseTool (Placeholder)
Infrastructure for production knowledge base lookup.

```python
vector_db = VectorDatabaseTool()

success, similar_claims, error = vector_db.query(
    claim="COVID vaccines contain microchips",
    top_k=5,
    threshold=0.7
)
```

**Future Integration:**
- Connect to Pinecone/Weaviate for vector similarity
- Store verified fact-checks to avoid redundant searches
- Domain-specific knowledge graphs

---

#### ClaimParserTool
Extracts structure from raw claims.

```python
parsed = ClaimParserTool.parse_claim(
    "All vaccines cause autism (year 2024)"
)
# Returns: {
#   "claim_type": "specific",
#   "temporal_markers": ["2024"],
#   "quantifiers": ["all"],
#   "key_entities": [...]
# }
```

**Extraction:**
- Claim type (specific vs general)
- Temporal markers (dates, years)
- Quantifiers (all, some, none, etc.)
- Entity recognition (placeholder for NER)

---

### 3. Configuration System (`brain/config.py`)

**FactCheckingConfig** - Centralized agent tuning:

```python
from src.brain.config import FactCheckingConfig, get_strategy_config

# Strategy presets
config = get_strategy_config("balanced")  # or "fast", "thorough"

# Custom config
config = FactCheckingConfig(
    llm_provider="groq",
    groq_model="llama-3.3-70b-versatile",
    reasoning_temperature=0.1,
    search_depth=3,
    max_iterations=10,
    confidence_threshold=0.75,
)
```

**Strategies:**
| Strategy | Iterations | Search Depth | Threshold | Use Case |
|----------|-----------|-------------|-----------|----------|
| **fast** | 5 | 2 | 0.70 | Quick verification |
| **balanced** | 10 | 3 | 0.75 | General purpose |
| **thorough** | 15 | 5 | 0.80 | Critical verification |

---

## Output Format

**VerdictResult** (Pydantic Model):

```json
{
  "claim": "COVID-19 vaccines contain microchips",
  "verdict": "FALSE",
  "confidence": 0.95,
  "reasoning": "Multiple credible sources (WHO, CDC, peer-reviewed studies) confirm vaccines contain no microchips. This is a widely debunked conspiracy theory.",
  "sources": [
    "https://www.snopes.com/articles/...",
    "https://www.who.int/...",
    "https://pubmed.ncbi.nlm.nih.gov/..."
  ],
  "key_evidence": [
    "Vaccine composition publicly documented",
    "Independent lab verification available",
    "No microchip technology could function at vaccine scale"
  ],
  "timestamp": "2026-06-14T11:50:40.123456"
}
```

---

## Usage Examples

### Single Claim Verification

```python
from src.config import Settings
from src.brain.agent import FactCheckingAgent

settings = Settings()

agent = FactCheckingAgent(
    groq_api_key=settings.GROQ_API_KEY,
    google_api_key=settings.GOOGLE_API_KEY,
    tavily_api_key=settings.TAVILY_API_KEY,
    strategy="balanced"
)

result = agent.verify_claim("The Moon orbits the Earth")

print(f"Verdict: {result.verdict}")
print(f"Confidence: {result.confidence:.1%}")
print(f"Reasoning: {result.reasoning}")
```

### Batch Verification

```python
claims = [
    "Water boils at 100°C at sea level",
    "The Earth is flat",
    "Vaccines are 100% safe with no side effects",
]

results = agent.batch_verify(claims, verbose=True)

for result in results:
    print(f"{result.claim}: {result.verdict}")
```

### Custom Strategy

```python
from src.brain.config import FactCheckingConfig

config = FactCheckingConfig(
    llm_provider="google",  # Use Gemini instead
    google_model="gemini-1.5-flash",
    reasoning_temperature=0.2,  # More creative
    search_depth=5,
    confidence_threshold=0.8,  # Higher threshold
)

agent = FactCheckingAgent(
    config=config,
    groq_api_key=settings.GROQ_API_KEY,
    google_api_key=settings.GOOGLE_API_KEY,
    tavily_api_key=settings.TAVILY_API_KEY,
)
```

### CLI Tool

```bash
# Run interactive CLI
python examples/test_agent.py

# Enter claims and get verdicts
Enter claim to verify (or 'quit'): The Moon is made of cheese
[1] Processing claim...

CLAIM: The Moon is made of cheese

VERDICT: [✗] FALSE
CONFIDENCE: 99.5%

REASONING:
The Moon is a rocky celestial body composed primarily of silicate minerals, iron, and other elements. Multiple credible sources including NASA, scientific studies, and physical evidence from moon rocks confirm this...

KEY EVIDENCE:
• Moon rocks analyzed by scientists
• Satellite imagery shows geological features
• No dairy composition detected in samples

SOURCES:
1. https://www.nasa.gov/...
2. https://science.nasa.gov/...
3. https://www.smithsonianmag.com/...
```

---

## Testing

### Run Test Suite

```bash
cd /path/to/SATYAMEV-BOT
.\venv\Scripts\python.exe tests/test_brain.py
```

**Test Coverage:**
1. Configuration system validation
2. Tool initialization and API integration
3. Web search functionality
4. Agent initialization
5. Fact-checking pipeline (end-to-end)
6. Batch verification

**Expected Output:**
```
[PASS] Configuration System
[PASS] Tool Initialization
[PASS] Web Search Functionality
[PASS] Agent Initialization
[PASS] Fact-Checking Pipeline
[PASS] Batch Verification

Total: 6/6 tests passed
✓ ALL TESTS PASSED - Phase 2 ready for integration
```

---

## Error Handling

### API Failures

```python
try:
    result = agent.verify_claim("Some claim")
except Exception as e:
    # Fallback: returns UNVERIFIABLE verdict
    result = VerdictResult(
        claim="Some claim",
        verdict="UNVERIFIABLE",
        confidence=0.0,
        reasoning=f"Verification failed: {str(e)}"
    )
```

### LLM Parsing Errors

If LLM returns malformed JSON:
1. Attempt regex extraction of JSON block
2. Fallback to UNVERIFIABLE verdict
3. Log full response for debugging

### Web Search Timeouts

- Retry logic: up to 3 attempts
- Timeout: 60 seconds (configurable)
- Fallback: proceed with limited evidence

---

## Performance Characteristics

| Metric | Value |
|--------|-------|
| Web Search (per claim) | 5-15 seconds |
| LLM Reasoning | 2-8 seconds |
| Total (single claim) | 7-25 seconds |
| Batch (10 claims) | 70-250 seconds |
| Temperature overhead | <100ms |

**Optimization Tips:**
- Use "fast" strategy for real-time requirements
- Batch process at scale (10+ claims)
- Cache results for duplicate claims
- Use Groq (cheaper) before Gemini fallback

---

## Integration with Phase 1 & Phase 3

### With Phase 1 (Multimodal Ingestion)

```python
from src.ingestion.ingestion_manager import IngestionManager
from src.brain.agent import FactCheckingAgent

# Ingest claim from any source
manager = IngestionManager(...)
success, claim_text, error = manager.ingest("claim_audio.mp3", input_type="AUDIO")

# Verify extracted claim
if success:
    agent = FactCheckingAgent(...)
    result = agent.verify_claim(claim_text)
```

### With Phase 3 (Card Generation)

```python
# Generate visual proof card after verification
result = agent.verify_claim("Some claim")

from src.cards.generator import CardGenerator
card = CardGenerator().generate(
    claim=result.claim,
    verdict=result.verdict,
    confidence=result.confidence,
    sources=result.sources,
)
card.save("exports/fact_check_card.png")
```

---

## Known Limitations

1. **Evidence Quality**: Depends on Tavily search results; misinformation may appear in results
2. **Language**: Currently English-only; multilingual support in Phase 4
3. **Real-time Bias**: Recent events may have limited evidence
4. **Context Loss**: LLM may miss subtle nuances in complex topics
5. **Determinism**: Low temperature (0.1) ensures consistency but sacrifices diversity

---

## Future Enhancements (Phase 3+)

- [ ] Vector DB integration (Pinecone/Weaviate)
- [ ] Claim deduplication & caching
- [ ] Multi-language support
- [ ] Image/audio claim analysis
- [ ] Source credibility scoring
- [ ] Temporal claim tracking
- [ ] Interactive UI for evidence review
- [ ] API endpoint integration (Phase 4)

---

## Files & Structure

```
src/brain/
├── __init__.py          # Module initialization
├── config.py            # Configuration & strategies
├── tools.py             # Web search, vector DB, parsers
├── agent.py             # Main orchestration engine
│
tests/
├── test_brain.py        # Comprehensive test suite
│
examples/
├── test_agent.py        # Interactive CLI tool
```

---

## Support & Debugging

**Enable debug logging:**
```python
config = FactCheckingConfig(debug_mode=True)
agent = FactCheckingAgent(config=config, ...)
```

**Common Issues:**

| Issue | Solution |
|-------|----------|
| "Tavily API key required" | Verify `TAVILY_API_KEY` in `.env` |
| "At least one LLM API key required" | Set `GROQ_API_KEY` or `GOOGLE_API_KEY` |
| Slow verification | Use "fast" strategy or batch processing |
| Malformed verdict | Check LLM response format; fallback to UNVERIFIABLE |

---

**Status**: Phase 2 COMPLETE ✓  
**Last Updated**: 2026-06-14  
**Version**: 0.1.0
