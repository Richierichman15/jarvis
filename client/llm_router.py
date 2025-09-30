"""Enhanced LLM-backed natural language routing for the Jarvis MCP client.

Converts free-text user input into concrete MCP tool calls using available
tool list and their input schemas. Improved context understanding and tool mapping.
"""

from __future__ import annotations

import re
from typing import Dict, Tuple, Optional, Any, List
import json
from datetime import datetime, timedelta

try:
    from brain.llm import generate as llm_generate
    BRAIN_AVAILABLE = True
except Exception:
    BRAIN_AVAILABLE = False


def _normalize_server_tool_name(tool_name: str) -> Tuple[str, str]:
    """Split tool into server.tool format if not already."""
    if '.' in tool_name:
        return tool_name.rsplit('.', 1)
    # Default server mappings based on tool prefixes
    if tool_name.startswith('jarvis_'):
        return 'jarvis', tool_name
    if tool_name.startswith(('fitness', 'budget', 'trading', 'system')):
        parts = tool_name.split('_', 1)
        if len(parts) == 2:
            return parts[0], tool_name
    return 'jarvis', tool_name


def _trading_symbol(match: re.Match[str]) -> Dict[str, Any]:
    """Parse trading symbols into standard format."""
    symbol = match.group(1).upper()
    # Common crypto symbols
    if symbol in {"BTC", "ETH", "SOL", "ADA", "XRP", "DOGE", "MATIC", "LINK", "DOT", "AVAX"}:
        return {"symbol": f"{symbol}/USDT"}
    # Stock symbols (typically 1-5 chars)
    if len(symbol) <= 5 and not '/' in symbol:
        # Could be stock or crypto - let the trading server decide
        return {"symbol": symbol}
    if '/' in symbol:
        return {"symbol": symbol}
    # Default to crypto pair
    return {"symbol": f"{symbol}/USDT"}


# Enhanced keyword shortcuts with better coverage
KEYWORD_SHORTCUTS = [
    # Fitness shortcuts
    {"tool": "fitness.list_workouts", "args": {"muscle_group": "legs"}, 
     "contains": ["leg workout", "leg workouts", "legs", "lower body", "squat", "lunges"]},
    {"tool": "fitness.list_workouts", "args": {"muscle_group": "upper"}, 
     "contains": ["upper body", "upper workouts", "arm workout", "shoulder workout", 
                  "chest workout", "back workout", "biceps", "triceps"]},
    {"tool": "fitness.list_workouts", "args": {"muscle_group": "core"}, 
     "contains": ["core workout", "ab workout", "abs", "midsection", "plank", "crunches"]},
    {"tool": "fitness.list_workouts", "args": {}, 
     "contains": ["all workouts", "every workout", "full workout list", "show workouts"]},
    {"tool": "fitness.search_workouts", "args": {"query": "cardio"}, 
     "contains": ["cardio workout", "hiit", "endurance", "running", "cycling"]},
    
    # Budget shortcuts
    {"tool": "budget.get_balance", "args": {}, 
     "contains": ["budget balance", "current balance", "wallet balance", "financial overview", 
                  "how much money", "account balance", "my balance"]},
    {"tool": "budget.get_transactions", "args": {"limit": 20}, 
     "contains": ["recent transactions", "list transactions", "show expenses", 
                  "spending history", "last purchases", "transaction history"]},
    {"tool": "budget.add_transaction", 
     "pattern": re.compile(r"(?:spent|paid|bought|purchased)\s+\$?(\d+(?:\.\d{2})?)\s+(?:on|for|at)\s+(.+)", re.IGNORECASE),
     "builder": lambda m: {"amount": float(m.group(1)), "description": m.group(2).strip(), "type": "expense"}},
    {"tool": "budget.get_monthly_stats", "args": {}, 
     "contains": ["monthly spending", "month over month", "monthly stats", "this month's spend", 
                  "monthly budget", "monthly expenses"]},
    {"tool": "budget.get_category_stats", "args": {}, 
     "contains": ["category breakdown", "spending by category", "top categories", "expense categories"]},
    
    # Trading shortcuts
    {"tool": "trading.get_price", "args": {"symbol": "BTC/USDT"}, 
     "contains": ["btc price", "bitcoin price", "price of btc", "bitcoin value"]},
    {"tool": "trading.get_price", "args": {"symbol": "ETH/USDT"}, 
     "contains": ["eth price", "ethereum price", "price of eth", "ethereum value"]},
    {"tool": "trading.get_price", 
     "pattern": re.compile(r"(?:price|quote|value)\s+(?:of\s+)?([A-Za-z]{2,6}(?:/[A-Za-z]{3,4})?)", re.IGNORECASE),
     "builder": _trading_symbol},
    {"tool": "trading.get_momentum", 
     "pattern": re.compile(r"(?:momentum|trend|direction)\s+(?:of\s+)?([A-Za-z]{2,6}(?:/[A-Za-z]{3,4})?)", re.IGNORECASE),
     "builder": _trading_symbol},
    {"tool": "trading.get_analysis", 
     "pattern": re.compile(r"(?:analyze|analysis|technical analysis)\s+(?:of\s+)?([A-Za-z]{2,6}(?:/[A-Za-z]{3,4})?)", re.IGNORECASE),
     "builder": _trading_symbol},
    {"tool": "trading.list_positions", "args": {}, 
     "contains": ["my positions", "open positions", "current trades", "portfolio", "holdings"]},
    
    # System (Solo Leveling) shortcuts
    {"tool": "system.get_status", "args": {}, 
     "contains": ["quest status", "xp status", "game status", "leveling status", "my level", "player stats"]},
    {"tool": "system.list_quests", "args": {}, 
     "contains": ["list quests", "show quests", "available quests", "my quests", "quest list", 
                  "daily quests", "weekly quests"]},
    {"tool": "system.list_tasks", "args": {}, 
     "contains": ["list tasks", "show tasks", "my tasks", "task list"]},
    {"tool": "system.update_quest", 
     "pattern": re.compile(r"(?:complete|finish|done with)\s+quest\s+(?:#)?(\d+|.+)", re.IGNORECASE),
     "builder": lambda m: {"quest_id": m.group(1).strip(), "status": "completed"}},
    {"tool": "system.check_progress", 
     "pattern": re.compile(r"(?:progress|status)\s+(?:on|of)\s+(.+)", re.IGNORECASE),
     "builder": lambda m: {"title": m.group(1).strip()}},
    
    # Jarvis core shortcuts
    {"tool": "jarvis_get_status", "args": {}, 
     "contains": ["jarvis status", "system status", "overall status", "give me a status", "health check"]},
    {"tool": "jarvis_get_settings", "args": {}, 
     "contains": ["list settings", "show settings", "configuration", "jarvis settings", "preferences"]},
    {"tool": "jarvis_web_search", 
     "pattern": re.compile(r"(?:search|google|look up|find online|web search)\s+(?:for\s+)?(.+)", re.IGNORECASE),
     "builder": lambda m: {"query": m.group(1).strip()}},
    {"tool": "jarvis_get_tasks", "args": {"status": "all"}, 
     "contains": ["jarvis tasks", "todo list", "task list", "pending tasks"]},
    
    # Weather is common enough to warrant special handling
    {"tool": "jarvis_web_search", "args": {"query": "weather"}, 
     "contains": ["current weather", "today's weather", "weather report", "weather forecast"]},
]


def _match_keyword_shortcut(query: str, tools: Optional[Dict[str, Any]] = None) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """Match query against keyword shortcuts."""
    for shortcut in KEYWORD_SHORTCUTS:
        tool = shortcut["tool"]
        
        # Check if tool is available
        if tools:
            # Handle both server.tool and tool formats
            if tool not in tools and '.' not in tool:
                # Try to find it with server prefix
                found = False
                for t in tools:
                    if t.endswith(f".{tool}") or t == tool:
                        found = True
                        tool = t
                        break
                if not found:
                    continue
        
        # Check contains patterns
        contains = shortcut.get("contains", [])
        for phrase in contains:
            if phrase in query:
                args = shortcut.get("args", {}).copy()
                return tool, args
        
        # Check regex patterns
        pattern = shortcut.get("pattern")
        if pattern:
            match = pattern.search(query)
            if match:
                builder = shortcut.get("builder")
                args = builder(match) if builder else shortcut.get("args", {}).copy()
                return tool, args
    
    return None, None


def _build_tool_catalog(tools: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Build a concise tool catalog for LLM prompting."""
    if not tools:
        return []
    
    tool_specs = []
    for name, t in tools.items():
        # Extract description
        desc = getattr(t, 'description', '') or ''
        
        # Extract and normalize schema
        schema = getattr(t, 'inputSchema', None)
        if schema is not None and not isinstance(schema, dict):
            schema = {
                "properties": getattr(schema, 'properties', None) or {},
                "required": getattr(schema, 'required', None) or [],
            }
        
        # Add server context to description if not obvious
        server, tool_name = _normalize_server_tool_name(name)
        if server != 'jarvis' and server not in desc.lower():
            desc = f"[{server}] {desc}"
        
        tool_specs.append({
            "name": name,
            "description": desc,
            "inputSchema": schema or {},
            "server": server
        })
    
    return tool_specs


def _detect_multi_intent(query: str) -> bool:
    """Detect if query contains multiple intents."""
    ql = query.lower()
    
    # Look for explicit conjunctions
    if re.search(r'\b(and then|then|after that|also|additionally|plus)\b', ql):
        return True
    
    # Look for semicolons or multiple sentences
    if ';' in query or re.search(r'[.!?]\s+[A-Z]', query):
        return True
    
    # Look for numbered lists
    if re.search(r'^\s*\d+[.)]\s+', query, re.MULTILINE):
        return True
    
    # Look for multiple action verbs
    action_verbs = ['list', 'show', 'get', 'find', 'search', 'check', 'calculate', 
                    'complete', 'update', 'add', 'delete', 'analyze']
    verb_count = sum(1 for verb in action_verbs if verb in ql)
    if verb_count >= 2:
        return True
    
    return False


def route_natural_language(query: str, tools: Optional[Dict[str, Any]] = None, 
                          allow_multi: bool = True, context: Optional[str] = None) -> Tuple[Optional[str], Optional[Dict]]:
    """Route a free-text query to a tool name and args.
    
    Args:
        query: User's natural language input
        tools: Available tools dictionary
        allow_multi: Whether to allow multi-step plans
        context: Optional context about the conversation
    
    Returns:
        (tool_name, args) tuple, falls back to ("jarvis_chat", {"message": query})
    """
    q = (query or "").strip()
    if not q:
        return "jarvis_chat", {"message": ""}
    
    ql = q.lower()
    
    # First, try keyword shortcuts for speed
    tool_shortcut, args_shortcut = _match_keyword_shortcut(ql, tools)
    if tool_shortcut:
        return tool_shortcut, args_shortcut
    
    # Detect multi-intent queries
    if allow_multi and _detect_multi_intent(query) and tools and "orchestrator.run_plan" in tools:
        if BRAIN_AVAILABLE:
            tool_specs = _build_tool_catalog(tools)
            system = """You are a task planner for Jarvis MCP client. Create execution plans from user requests.

Available servers:
- jarvis: Core assistant, chat, status, settings, web search
- system: Quest/leveling system (Solo Leveling style), tracks quests and progress
- fitness: Workout management and search
- budget: Financial tracking and statistics  
- trading: Crypto/stock prices, analysis, portfolio

Return ONLY JSON: {"steps": [{"server": "...", "tool": "...", "args": {...}, "parallel": true/false}, ...]}

Rules:
- Use exact tool names from the provided list
- Set parallel=true for independent steps
- Include server field for each step
- Minimal valid args per schema
- Order steps logically"""
            
            user = json.dumps({
                "tools": tool_specs,
                "query": query,
                "context": context or "No additional context"
            })
            
            try:
                raw = llm_generate(system, user)
                payload = _extract_json_object(raw)
                if isinstance(payload, dict) and isinstance(payload.get("steps"), list):
                    steps = payload["steps"]
                    # Validate and fix server fields
                    for step in steps:
                        if isinstance(step, dict):
                            if "server" not in step and "tool" in step:
                                server, _ = _normalize_server_tool_name(step["tool"])
                                step["server"] = server
                    return "orchestrator.run_plan", {"steps": steps}
            except Exception:
                pass
    
    # Single-tool routing with better context
    if BRAIN_AVAILABLE:
        tool_specs = _build_tool_catalog(tools)
        
        # Enhanced system prompt with better context
        system = """You are a router for Jarvis MCP client. Map user requests to the BEST matching tool.

Available servers and their purposes:
- jarvis: Core assistant functions (chat, status, settings, web search, tasks)
- system: Quest and leveling system (list quests, update progress, check status)
- fitness: Workout management (list by muscle group, search exercises)
- budget: Financial management (balance, transactions, statistics)
- trading: Market data (prices, momentum, analysis, portfolio)

Important mappings:
- "quests" or "leveling" → system.list_quests or system.get_status
- "tasks" or "todo" → jarvis_get_tasks
- Price/momentum/analysis of symbols → trading tools
- Financial/spending/budget → budget tools
- Workouts/exercises → fitness tools

Return ONLY JSON: {"tool": "<exact_tool_name>", "args": {...}}

If just chatting or unclear, use jarvis_chat with message.
NEVER invent tools. Match schema requirements."""
        
        user = json.dumps({
            "tools": tool_specs,
            "query": query,
            "context": context or "User is asking about system capabilities",
            "examples": {
                "list quests": "system.list_quests",
                "show tasks": "jarvis_get_tasks", 
                "btc price": "trading.get_price",
                "my balance": "budget.get_balance"
            }
        })
        
        try:
            raw = llm_generate(system, user)
            payload = _extract_json_object(raw)
            
            if not isinstance(payload, dict):
                raise ValueError("Invalid response format")
            
            tool = payload.get("tool")
            args = payload.get("args", {})
            
            if not isinstance(args, dict):
                args = {}
            
            # Validate tool exists
            if tools and tool not in tools:
                # Try to find with fuzzy matching
                for t in tools:
                    if t.endswith(tool) or tool.endswith(t):
                        tool = t
                        break
                else:
                    # Default to chat if tool not found
                    return "jarvis_chat", {"message": query}
            
            # Ensure chat messages have content
            if tool == "jarvis_chat" and "message" not in args:
                args["message"] = query
            
            return tool, args
            
        except Exception as e:
            # Fallback to chat on any error
            return "jarvis_chat", {"message": query}
    
    # Final fallback: deterministic patterns
    
    # System/Quest patterns
    if any(word in ql for word in ["quest", "quests", "leveling", "xp", "level up"]):
        if "list" in ql or "show" in ql or "what" in ql:
            return "system.list_quests", {}
        if "status" in ql:
            return "system.get_status", {}
    
    # Task patterns (different from quests!)
    if any(phrase in ql for phrase in ["list tasks", "show tasks", "my tasks", "todo"]):
        return "jarvis_get_tasks", {"status": "all"}
    
    # Budget patterns  
    if any(word in ql for word in ["budget", "spending", "expense", "financial"]):
        if "balance" in ql:
            return "budget.get_balance", {}
        if "transaction" in ql or "history" in ql:
            return "budget.get_transactions", {"limit": 20}
        if "month" in ql:
            return "budget.get_monthly_stats", {}
        if "category" in ql:
            return "budget.get_category_stats", {}
    
    # Trading patterns
    if any(word in ql for word in ["price", "value", "worth", "trading", "crypto", "stock"]):
        # Try to extract symbol
        symbols = re.findall(r'\b([A-Z]{2,6})\b', q)  # Use original case
        if symbols:
            return "trading.get_price", {"symbol": f"{symbols[0]}/USDT"}
    
    # Default fallback
    return "jarvis_chat", {"message": query}


def _extract_json_object(text: str) -> Any:
    """Extract the first valid JSON object from text.
    
    Handles code fences, extra prose, and various formatting issues.
    """
    if not text:
        raise ValueError("Empty response")
    
    text = text.strip()
    
    # Try multiple extraction strategies
    strategies = [
        # Strategy 1: Code fence with optional language
        lambda t: re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", t),
        # Strategy 2: Raw JSON block
        lambda t: re.search(r"(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})", t),
        # Strategy 3: Array format (for steps)
        lambda t: re.search(r"(\[[^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*\])", t),
    ]
    
    for strategy in strategies:
        match = strategy(text)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                continue
    
    # Last resort: try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to clean common issues
        cleaned = text.replace("'", '"').replace('True', 'true').replace('False', 'false')
        return json.loads(cleaned)