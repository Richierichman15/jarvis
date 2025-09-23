"""
Brain package: conversational hub with short- and long-term memory for Jarvis.

Components:
- config: environment-driven configuration
- llm: simple LLM adapter (Ollama/OpenAI) with safe fallbacks
- memory: SQLite-backed short/long-term memory utilities
- chat: FastAPI app exposing a /chat endpoint
"""

__all__ = [
    "config",
    "llm",
    "memory",
]

