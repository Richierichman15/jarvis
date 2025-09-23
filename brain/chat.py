"""
FastAPI app exposing a conversational endpoint backed by brain memory + LLM.

POST /chat { input: string, project?: string }
Returns: { reply: string, used_memories: [ ... ] }
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .config import load_config
from .llm import generate
from . import memory


app = FastAPI(title="Jarvis Brain", version="0.1.0")


def _jarvis_system_prompt(used: List[str]) -> str:
    base = (
        "You are Jarvis, a concise, helpful AI assistant. "
        "Use helpful bullet points and short sentences. "
        "If the user mentions past goals or preferences, acknowledge them."
    )
    if used:
        joined = "\n- ".join(used)
        return base + f"\n\nRelevant memories:\n- {joined}"
    return base


async def _coerce_body(request: Request) -> Dict[str, Any]:
    """Leniently parse body as JSON, even if content-type is not set."""
    try:
        # Try declared JSON
        return await request.json()
    except Exception:
        # Raw body fallback
        raw = await request.body()
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            # Try form fallback
            try:
                form = await request.form()
                return dict(form)
            except Exception:
                return {}


@app.post("/chat")
async def chat(request: Request) -> JSONResponse:
    data = await _coerce_body(request)
    user_input = (data.get("input") or data.get("message") or "").strip()
    project = (data.get("project") or "global").strip() or "global"

    if not user_input:
        return JSONResponse({"error": "Missing 'input'"}, status_code=400)

    # Save the incoming user message
    memory.save_message("user", user_input)

    # Heuristic: store explicit memory statements
    lower = user_input.lower()
    if any(k in lower for k in ["remember", "save this", "note that", "my goal", "keep in mind"]):
        memory.save_memory(project, user_input)

    # Fetch context: last 20 messages + top memories related to the query
    recent = memory.recent_messages(20)
    used_memories: List[str] = []
    # Search memories using key terms from user input (very simple heuristic)
    key = user_input[:64]
    mems = memory.search_memories(key, limit=5)
    used_memories.extend([m[2] for m in mems])

    # Summarization trigger every 10 messages
    if len(recent) % 10 == 0:
        try:
            summary = memory.summarize_thread()
            if summary:
                used_memories.append(summary)
        except Exception:
            pass

    system_prompt = _jarvis_system_prompt(used_memories)
    reply = generate(system_prompt, user_input)
    # Ensure recall is visible even if the LLM is not configured
    if used_memories:
        preview = "\n\nRecall: " + "; ".join(used_memories[:2])
        reply = (reply or "").strip()
        if preview not in reply:
            reply = (reply + preview).strip()

    # Save assistant reply
    memory.save_message("assistant", reply)

    return JSONResponse({
        "reply": reply,
        "used_memories": used_memories,
    })
