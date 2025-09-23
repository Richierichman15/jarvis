"""
Configuration loader for the brain package.

Environment variables (with defaults):
- LLM_PROVIDER: one of ["ollama", "openai"], default "ollama"
- OLLAMA_MODEL: default "llama3.1"
- OPENAI_MODEL: default "gpt-4o-mini"
- MEMORY_DB_PATH: default "./data/memory.sqlite"
"""
from __future__ import annotations

import os
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class BrainConfig:
    llm_provider: str
    ollama_host: str
    ollama_model: str
    openai_model: str
    openai_api_key: str | None
    memory_db_path: Path


def load_config() -> BrainConfig:
    llm_provider = os.getenv("LLM_PROVIDER", "ollama").strip().lower()
    ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
    ollama_model = os.getenv("OLLAMA_MODEL", "llama3.1").strip()
    openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
    openai_api_key = os.getenv("OPENAI_API_KEY") or None
    memory_db_path = Path(os.getenv("MEMORY_DB_PATH", "./data/memory.sqlite")).resolve()

    # Ensure data dir exists
    if not memory_db_path.parent.exists():
        memory_db_path.parent.mkdir(parents=True, exist_ok=True)

    return BrainConfig(
        llm_provider=llm_provider,
        ollama_host=ollama_host,
        ollama_model=ollama_model,
        openai_model=openai_model,
        openai_api_key=openai_api_key,
        memory_db_path=memory_db_path,
    )

