"""
Agentic RAG & Web Consensus Engine (THE BRAIN)

This module implements the intelligent fact-checking agent that orchestrates
multimodal input processing, real-time web searches, and consensus-driven
verdict generation using LLM reasoning.

Components:
- agent.py: LangChain agent orchestration (React-style autonomous agent)
- tools.py: Tool definitions (web search, vector DB placeholder)
- config.py: Agent configuration and model settings

Usage:
    from src.brain.agent import FactCheckingAgent
    
    agent = FactCheckingAgent(
        llm_provider="groq",
        model="llama-3.3-70b-versatile",
        temperature=0.1
    )
    
    result = agent.verify_claim("COVID-19 vaccines contain microchips")
    print(result.verdict)  # "FALSE"
    print(result.sources)  # ["url1", "url2", ...]
"""

__version__ = "0.1.0"
__all__ = ["FactCheckingAgent", "FactCheckingConfig"]
