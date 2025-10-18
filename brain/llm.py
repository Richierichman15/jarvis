"""
LLM adapter: supports Ollama (local) and OpenAI (if API key set).

Expose a single function:
    generate(system_prompt, user_prompt, tools_schema=None) -> str

Notes:
- For Ollama, use /api/generate with non-streaming requests.
- For OpenAI, use chat.completions if the openai package is available.
- If neither backend is usable, return a safe fallback string.
"""
from __future__ import annotations

import json
from typing import Any, Dict, Optional

import httpx

from .config import load_config


def _format_messages(system_prompt: str, user_prompt: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def _generate_ollama(system_prompt: str, user_prompt: str) -> str:
    cfg = load_config()
    url = f"{cfg.ollama_host}/api/generate"
    prompt = f"{system_prompt}\n\nUser: {user_prompt}\nAssistant:"

    try:
        with httpx.Client(timeout=120) as client:
            # First try /api/generate
            resp = client.post(
                url,
                json={
                    "model": cfg.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                },
            )
            if resp.status_code == 404:
                # Some Ollama builds prefer /api/chat; try that path
                chat_url = f"{cfg.ollama_host}/api/chat"
                chat_payload = {
                    "model": cfg.ollama_model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "stream": False,
                }
                chat_resp = client.post(chat_url, json=chat_payload)
                chat_resp.raise_for_status()
                data = chat_resp.json()
                # Newer API shape: { message: { role, content }, ... }
                msg = data.get("message") or {}
                return (msg.get("content") or "").strip()
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "") or ""
    except Exception as e:
        return f"[LLM unavailable: Ollama error {e}]"


def _generate_openai(system_prompt: str, user_prompt: str) -> str:
    cfg = load_config()
    if not cfg.openai_api_key:
        return "[LLM unavailable: OPENAI_KEY not set]"

    try:
        # Prefer OpenAI SDK if present
        try:
            from openai import OpenAI  # type: ignore
        except Exception:
            OpenAI = None  # type: ignore

        messages = _format_messages(system_prompt, user_prompt)

        if OpenAI is not None:
            client = OpenAI()
            res = client.chat.completions.create(
                model=cfg.openai_model,
                messages=messages,
                temperature=0.3,
            )
            text = res.choices[0].message.content or ""
            return text

        # Fallback: raw HTTP to OpenAI API if SDK missing
        headers = {
            "Authorization": f"Bearer {cfg.openai_api_key}",
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {
            "model": cfg.openai_model,
            "messages": messages,
            "temperature": 0.3,
        }
        with httpx.Client(timeout=120) as client:
            resp = client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"[LLM unavailable: OpenAI error {e}]"


def generate(system_prompt: str, user_prompt: str, tools_schema: Optional[dict] = None) -> str:
    """Generate a response using the configured LLM backend.

    tools_schema is accepted for future extension but not used in this minimal adapter.
    """
    cfg = load_config()

    # Prefer OpenAI if explicitly configured and key set
    if cfg.llm_provider == "openai" and cfg.openai_api_key:
        return _generate_openai(system_prompt, user_prompt)

    # Otherwise, try Ollama first, then OpenAI as a fallback if key exists
    text = _generate_ollama(system_prompt, user_prompt)
    if text.startswith("[LLM unavailable") and cfg.openai_api_key:
        return _generate_openai(system_prompt, user_prompt)

    # If both fail, provide a safe fallback so the endpoint still responds
    if text.startswith("[LLM unavailable") or not text.strip():
        # Minimal heuristic reply to keep flows unblocked
        return "I registered your message. I'll remember key details and respond succinctly."
    return text
