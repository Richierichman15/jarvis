"""LLM-backed natural language routing for the Jarvis client.

Converts free-text user input into a concrete MCP tool call using the
available tool list and their input schemas.

Fallbacks:
- If LLM is unavailable or parsing fails, return a default chat call.
- We also keep a few deterministic keyword routes for resilience.
"""

from __future__ import annotations

import re
from typing import Dict, Tuple, Optional, Any, List
import json
import re
from datetime import datetime, timedelta

try:
    # Use the in-repo brain LLM adapter (Ollama/OpenAI)
    from brain.llm import generate as llm_generate
    BRAIN_AVAILABLE = True
except Exception:
    BRAIN_AVAILABLE = False


def route_natural_language(query: str, tools: Optional[Dict[str, Any]] = None, allow_multi: bool = True) -> Tuple[Optional[str], Optional[Dict]]:
    """Route a free-text query to a tool name and args.

    Returns (tool_name, args) on match. Falls back to ("jarvis_chat", {"message": query}).
    """
    q = (query or "").strip()
    if not q:
        return "jarvis_chat", {"message": ""}

    ql = q.lower()

    # Multi-intent detection FIRST so it doesn't get short-circuited by single-intent heuristics
    multi_intent = bool(re.search(r"\b(and|then|;|,\s*then)\b", ql))
    if allow_multi and multi_intent and tools and "orchestrator.run_plan" in tools:
        # Build a concise tool catalog for the LLM
        tool_specs: List[Dict[str, Any]] = []
        if tools:
            for name, t in tools.items():
                schema = getattr(t, 'inputSchema', None)
                if schema is not None and not isinstance(schema, dict):
                    schema = {
                        "properties": getattr(schema, 'properties', None) or {},
                        "required": getattr(schema, 'required', None) or [],
                    }
                tool_specs.append({
                    "name": name,
                    "description": getattr(t, 'description', '') or '',
                    "inputSchema": schema or {},
                })
        # Try LLM plan only if brain LLM is available; otherwise skip to heuristics
        if BRAIN_AVAILABLE:
            system = (
                "You create execution plans for an MCP client. "
                "Return ONLY JSON of the form {\"steps\": [{\"tool\": <name>, \"args\": {...}, \"parallel\": <bool>?}, ...]}. "
                "Use only tools from the list provided. Prefer minimal, valid args per schema. "
                "Include parallel=true when independent steps can run together."
            )
            user = json.dumps({"tools": tool_specs, "query": query})
            try:
                raw = llm_generate(system, user)
                payload = _extract_json_object(raw)
                if isinstance(payload, dict) and isinstance(payload.get("steps"), list):
                    return "orchestrator.run_plan", {"steps": payload["steps"]}
            except Exception:
                pass
        # Heuristic split into steps (works even without LLM)
        try:
            parts = re.split(r"\s*(?:;|,?\s*then\s+|\s+and\s+)\s*", q.strip(), flags=re.IGNORECASE)
        except Exception:
            parts = []
        step_list: List[Dict[str, Any]] = []
        for part in parts:
            part = part.strip()
            if not part:
                continue
            t, a = route_natural_language(part, tools, allow_multi=False)
            if not t:
                continue
            step_list.append({"tool": t, "args": a or {}})
        # Prefer concrete tool steps, but fall back if necessary
        concrete = [s for s in step_list if s["tool"] != "jarvis_chat"]
        steps_out = concrete if concrete else step_list
        if len(steps_out) >= 2:
            return "orchestrator.run_plan", {"steps": steps_out}

    # Simple deterministic routes as a first pass (fast and reliable)
    # Tasks: list
    if (
        "list tasks" in ql or ql.startswith("get tasks") or ql in {"tasks", "show tasks"}
        or "list task" in ql or ql.startswith("get task")
    ):
        return "jarvis_get_tasks", {"status": "all"}
    m = re.search(r"complete\s+task\s+(\d+)", ql)
    if m:
        return "jarvis_complete_task", {"task_index": int(m.group(1))}
    m = re.search(r"delete\s+task\s+(\d+)", ql)
    if m:
        return "jarvis_delete_task", {"task_index": int(m.group(1))}

    # Heuristic scheduling: trigger jarvis_schedule_task on common phrasing
    schedule_keywords = [
        "schedule", "remind", "set reminder", "appointment", "meeting", "call",
    ]
    if any(k in ql for k in schedule_keywords) and (tools is None or "jarvis_schedule_task" in tools):
        args: Dict[str, Any] = {"description": query, "priority": "medium"}
        # Try a very light deadline parse: "tomorrow at 9am/pm"
        try:
            if "tomorrow" in ql:
                tm = datetime.now() + timedelta(days=1)
                m = re.search(r"at\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", ql)
                hour = 9
                minute = 0
                if m:
                    hour = int(m.group(1))
                    minute = int(m.group(2) or 0)
                    mer = (m.group(3) or '').lower()
                    if mer == 'pm' and hour < 12:
                        hour += 12
                    if mer == 'am' and hour == 12:
                        hour = 0
                deadline = tm.replace(hour=hour, minute=minute, second=0, microsecond=0).isoformat()
                args["deadline"] = deadline
        except Exception:
            pass
        return "jarvis_schedule_task", args

    # Status and system info
    if ("status" in ql or "health" in ql or "uptime" in ql) and (tools is None or "jarvis_get_status" in tools):
        return "jarvis_get_status", {}
    if ("system info" in ql or "system information" in ql or re.search(r"\b(cpu|memory|disk|ram)\b", ql)) and (tools is None or "jarvis_get_system_info" in tools):
        return "jarvis_get_system_info", {}

    # Settings: get
    if any(p in ql for p in ["show settings", "list settings", "get settings", "what are your settings"]) and (tools is None or "jarvis_get_settings" in tools):
        return "jarvis_get_settings", {}

    # Settings: update (set/change/update <key> to <value>)
    m = re.search(r"\b(set|change|update)\s+([a-zA-Z0-9_\- ]+?)\s+(?:to|as|=)\s+(.+)$", q, flags=re.IGNORECASE)
    if m and (tools is None or "jarvis_update_setting" in tools):
        key = m.group(2).strip().lower().replace(" ", "_")
        value = m.group(3).strip()
        return "jarvis_update_setting", {"key": key, "value": value}

    # Web search
    m = re.search(r"^(?:search|google|look\s*up|lookup|find|web\s*search)\s+(?:for\s+)?(.+)$", q, flags=re.IGNORECASE)
    if m and (tools is None or "jarvis_web_search" in tools):
        query_str = m.group(1).strip()
        return "jarvis_web_search", {"query": query_str}

    # Calculator
    m = re.search(r"^(?:calculate|calc|what\s+is|what's)\s+(.+)$", q, flags=re.IGNORECASE)
    math_expr = None
    if m:
        math_expr = m.group(1).strip()
    else:
        # If the whole input looks like a math expression, use it directly
        if re.fullmatch(r"[0-9\s\+\-\*\/\(\)\.\^%]+", q):
            math_expr = q
    if math_expr and (tools is None or "jarvis_calculate" in tools):
        return "jarvis_calculate", {"expression": math_expr}

    # Memory recall
    if any(p in ql for p in ["what did i say", "what did i tell you", "conversation history", "show memory", "what do you remember", "recall"]):
        # Optional: parse limit like "last 5"
        m = re.search(r"last\s+(\d+)", ql)
        limit = int(m.group(1)) if m else 10
        if tools is None or "jarvis_get_memory" in tools:
            return "jarvis_get_memory", {"limit": limit}

    # Build a concise tool catalog for the LLM
    tool_specs: List[Dict[str, Any]] = []
    if tools:
        for name, t in tools.items():
            schema = getattr(t, 'inputSchema', None)
            # Normalize schema shape for prompting
            if schema is not None and not isinstance(schema, dict):
                schema = {
                    "properties": getattr(schema, 'properties', None) or {},
                    "required": getattr(schema, 'required', None) or [],
                }
            tool_specs.append({
                "name": name,
                "description": getattr(t, 'description', '') or '',
                "inputSchema": schema or {},
            })

    # Detect multi-intent requests heuristically
    multi_intent = bool(re.search(r"\b(and|then|;|,\s+then)\b", ql))

    if multi_intent and tools and "orchestrator.run_plan" in tools:
        # Ask LLM for a plan when multiple intents detected
        system = (
            "You create execution plans for an MCP client. "
            "Return ONLY JSON of the form {\"steps\": [{\"tool\": <name>, \"args\": {...}, \"parallel\": <bool>?}, ...]}. "
            "Use only tools from the list provided. Prefer minimal, valid args per schema. "
            "Include parallel=true when independent steps can run together."
        )
        user = json.dumps({"tools": tool_specs, "query": query})
        try:
            raw = llm_generate(system, user)
            payload = _extract_json_object(raw)
            if not isinstance(payload, dict) or not isinstance(payload.get("steps"), list):
                raise ValueError("No steps array found")
            return "orchestrator.run_plan", {"steps": payload["steps"]}
        except Exception:
            # Fall through to single-tool routing below
            pass

    # Single-tool routing via LLM
    system = (
        "You are a router that maps user requests to MCP tools. "
        "Respond ONLY with a compact JSON object of the form {\"tool\": <name>, \"args\": {..}}. "
        "Choose the best tool from the list. If the user is just chatting, pick 'jarvis_chat' with {message}. "
        "Never invent tools not in the list. Prefer minimal, valid args matching each tool's schema."
    )
    user = json.dumps({"tools": tool_specs, "query": query})

    try:
        raw = llm_generate(system, user)
        payload = _extract_json_object(raw)
        if not isinstance(payload, dict):
            raise ValueError("No JSON object found")
        tool = payload.get("tool")
        args = payload.get("args") or {}
        if not isinstance(args, dict):
            args = {}
        if tools and tool not in tools:
            return "jarvis_chat", {"message": query}
        if tool == "jarvis_chat" and "message" not in args:
            args["message"] = query
        return tool, args
    except Exception:
        return "jarvis_chat", {"message": query}


def _extract_json_object(text: str) -> Any:
    """Extract the first top-level JSON object from text.

    Handles code fences and extra prose. Returns parsed JSON or raises.
    """
    if not text:
        raise ValueError("empty response")
    # Strip code fences if present
    text = text.strip()
    fence_match = re.search(r"```(json)?\s*(\{[\s\S]*?\})\s*```", text)
    if fence_match:
        candidate = fence_match.group(2)
        return json.loads(candidate)
    # Fallback: find first {...} block
    brace_match = re.search(r"\{[\s\S]*\}", text)
    if brace_match:
        return json.loads(brace_match.group(0))
    # Try direct parse last
    return json.loads(text)
