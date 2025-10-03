"""
MCP (Model Context Protocol) Server for Jarvis.
This module provides MCP tools for interacting with Jarvis functionality.
"""
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple
from datetime import datetime
import os

# MCP imports
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    from mcp.types import (
        Tool, 
        TextContent, 
        ImageContent, 
        EmbeddedResource,
        LoggingLevel
    )
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("Warning: MCP library not available. Install with: pip install mcp")

from .jarvis import Jarvis
from .config import PROJECT_ROOT
from .tools.fitness import list_workouts as fitness_list_workouts, search_workouts as fitness_search_workouts
try:
    # Use the new brain package for memory + LLM
    from brain import memory as brain_memory
    from brain.llm import generate as brain_generate
    BRAIN_AVAILABLE = True
except Exception:
    BRAIN_AVAILABLE = False

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JarvisMCPServer:
    """MCP Server that exposes Jarvis functionality as tools."""
    
    def __init__(self, user_name: str = "Boss"):
        """Initialize the MCP server with a Jarvis instance."""
        if not MCP_AVAILABLE:
            raise ImportError("MCP library is required. Install with: pip install mcp")
            
        self.jarvis = Jarvis(user_name=user_name)
        self.server = Server("jarvis-mcp-server")
        
        # Initialize optional external MCP session manager so this server can act as a client
        # to other MCP servers (e.g., system, finance) and aggregate their tools.
        self._session_manager = None
        self._external_initialized = False
        self._namespace_remote = os.environ.get("NAMESPACE_REMOTE_TOOLS", "true").lower() in ("1", "true", "yes", "on")
        # tool name -> (alias, remote_tool_name)
        self._remote_tool_index: Dict[str, Tuple[str, str]] = {}
        try:
            # Lazy import to avoid a hard dependency for users not using multi-server mode
            from client.api import SessionManager  # type: ignore
            # Build a dummy default parameter (not used to start Jarvis here) and pass saved servers
            default_path = PROJECT_ROOT / "run_mcp_server.py"
            default_params = StdioServerParameters(command=sys.executable, args=["-u", str(default_path), user_name])
            self._session_manager = SessionManager(default_params, saved_servers=self._load_saved_external_servers())
        except Exception as e:
            logger.info("Multi-server session manager unavailable: %s", e)
        self._register_tools()

    # -------- External servers management --------
    def _load_saved_external_servers(self) -> Dict[str, Dict[str, Any]]:
        """Load external MCP servers from env or saved client storage.

        Supports env var MCP_EXTERNAL_SERVERS as JSON array of entries:
        [{"alias": "system", "command": "python", "args": ["path/to/server.py"]}, ...]
        """
        # Highest priority: env configuration
        raw = os.environ.get("MCP_EXTERNAL_SERVERS")
        if raw:
            try:
                data = json.loads(raw)
                out: Dict[str, Dict[str, Any]] = {}
                if isinstance(data, list):
                    for entry in data:
                        if not isinstance(entry, dict):
                            continue
                        alias = str(entry.get("alias") or "").strip()
                        command = str(entry.get("command") or "").strip()
                        if not alias or not command:
                            continue
                        rec: Dict[str, Any] = {"command": command, "args": list(entry.get("args") or [])}
                        if entry.get("cwd"):
                            rec["cwd"] = entry.get("cwd")
                        if entry.get("env"):
                            rec["env"] = entry.get("env")
                        out[alias] = rec
                if out:
                    return out
            except Exception as e:
                logger.warning("Failed to parse MCP_EXTERNAL_SERVERS: %s", e)

        # Fallback: use saved servers from client.storage if present
        try:
            from client.storage import load_servers as _load_servers  # type: ignore
            saved = _load_servers()
            if isinstance(saved, dict):
                saved.pop("jarvis", None)  # never include default jarvis here
                return saved
        except Exception:
            pass
        return {}

    async def _ensure_external_sessions(self) -> None:
        if self._external_initialized or not self._session_manager:
            return
        try:
            # Connect all known servers from saved configuration
            for alias, entry in (self._session_manager.saved_servers or {}).items():
                if not isinstance(entry, dict) or not entry.get("command"):
                    continue
                try:
                    await self._session_manager.connect_server(
                        alias=alias,
                        command=entry.get("command"),
                        args=entry.get("args") or [],
                        save=False,
                        cwd=entry.get("cwd"),
                        env=entry.get("env"),
                    )
                    logger.info("Connected external MCP server '%s'", alias)
                except Exception as exc:
                    logger.warning("Failed to connect external server '%s': %s", alias, exc)
            self._external_initialized = True
        except Exception as e:
            logger.warning("External session init failed: %s", e)

    async def _index_remote_tools(self) -> None:
        if not self._session_manager:
            return
        await self._ensure_external_sessions()
        index: Dict[str, Tuple[str, str]] = {}
        try:
            aliases = [a for a in self._session_manager.list_aliases() if a != getattr(self._session_manager, "default_alias", "jarvis")]
        except Exception:
            aliases = []
        for alias in aliases:
            try:
                tools = await self._session_manager.list_tools_cached(alias)
            except Exception:
                continue
            for t in tools or []:
                rname = getattr(t, "name", None) or (t.get("name") if isinstance(t, dict) else None)
                if not rname:
                    continue
                exposed = f"{alias}.{rname}" if self._namespace_remote else rname
                if exposed not in index:
                    index[exposed] = (alias, rname)
                if self._namespace_remote and rname not in index:
                    index[rname] = (alias, rname)
        self._remote_tool_index = index

    @staticmethod
    def _as_text(value: Any) -> str:
        """Ensure tool responses are serialized to a safe string."""
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        if isinstance(value, (dict, list)):
            try:
                return json.dumps(value, ensure_ascii=False)
            except Exception:
                pass
        return str(value)

    def _active_sessions_path(self) -> Path:
        return PROJECT_ROOT / ".jarvis_active_sessions.json"

    def _saved_servers_path(self) -> Path:
        return PROJECT_ROOT / ".jarvis_servers.json"

    def _is_external_server_connected(self, alias: str) -> bool:
        try:
            data = json.loads(self._active_sessions_path().read_text())
            return alias in data
        except Exception:
            return False

    def _load_saved_server_command(self, alias: str) -> Optional[StdioServerParameters]:
        try:
            data = json.loads(self._saved_servers_path().read_text())
        except Exception:
            return None

        entry = data.get(alias)
        if not isinstance(entry, dict):
            return None

        command = entry.get("command")
        args = entry.get("args") or []
        if not command:
            return None

        return StdioServerParameters(command=command, args=args)

    async def _invoke_external_tool(
        self,
        params: StdioServerParameters,
        tool: str,
        args: Dict[str, Any],
    ) -> Any:
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                return await session.call_tool(tool, args)

    def _extract_text_content(self, result: Any) -> str:
        if isinstance(result, str):
            return result
        if hasattr(result, "content") and getattr(result, "content") is not None:
            texts: List[str] = []
            for content in result.content:
                if hasattr(content, "text"):
                    texts.append(getattr(content, "text") or "")
                elif isinstance(content, dict) and "text" in content:
                    texts.append(str(content.get("text") or ""))
            return "\n".join(t for t in texts if t)
        return str(result)

    async def _dispatch_tool(self, name: str, arguments: Dict[str, Any]) -> List[Union[TextContent, ImageContent, EmbeddedResource]]:
        """Internal dispatcher to invoke a tool by name.
        Covers commonly used tools to enable server-side orchestration.
        """
        # Minimal coverage; extend as needed
        if name == "jarvis_chat":
            message = arguments.get("message", "")
            if not message:
                return [TextContent(type="text", text="Error: No message provided")]
            # Prefer brain-backed chat if available
            if BRAIN_AVAILABLE:
                try:
                    brain_memory.save_message("user", message)
                    mems = brain_memory.search_memories(message, limit=5)
                    used_memories = [m[2] for m in mems]
                    base = (
                        "You are Jarvis, a concise, helpful AI assistant. "
                        "Use short sentences and helpful bullet points when useful."
                    )
                    if used_memories:
                        joined = "\n- ".join(used_memories)
                        system_prompt = base + f"\n\nRelevant memories:\n- {joined}"
                    else:
                        system_prompt = base
                    reply = brain_generate(system_prompt, message)
                    if not reply or reply.startswith("[LLM unavailable"):
                        reply = "I registered your message. I'll remember key details and respond succinctly."
                    brain_memory.save_message("assistant", reply)
                    try:
                        recent = brain_memory.recent_messages(100)
                        if len(recent) % 10 == 0:
                            brain_memory.summarize_thread()
                    except Exception:
                        pass
                    if used_memories:
                        preview = "\n\nRecall: " + "; ".join(used_memories[:2])
                        if preview not in reply:
                            reply = (reply or "").strip() + preview
                    return [TextContent(type="text", text=reply)]
                except Exception:
                    pass
            response = self.jarvis.chat(message)
            return [TextContent(type="text", text=response)]

        if name == "jarvis_get_tasks":
            status_filter = arguments.get("status", "all")
            if status_filter == "all":
                tasks = self.jarvis.tasks
            elif status_filter == "pending":
                tasks = [t for t in self.jarvis.tasks if t.status == "pending"]
            elif status_filter == "completed":
                tasks = [t for t in self.jarvis.tasks if t.status == "completed"]
            else:
                tasks = self.jarvis.tasks
            if not tasks:
                return [TextContent(type="text", text="No tasks found.")]
            task_list = []
            for i, task in enumerate(tasks, 1):
                task_dict = task.to_dict() if hasattr(task, 'to_dict') else task
                priority_icon = {"urgent": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(task_dict.get("priority", "medium"), "⚪")
                status_icon = "✅" if task_dict.get("status") == "completed" else "⏳"
                task_info = f"{i}. {priority_icon} {status_icon} {task_dict.get('name', 'Unknown')}"
                if task_dict.get('description'):
                    task_info += f"\n   📝 {task_dict['description']}"
                if task_dict.get('category'):
                    task_info += f"\n   🏷️ Category: {task_dict['category']}"
                if task_dict.get('deadline'):
                    task_info += f"\n   ⏰ Deadline: {task_dict['deadline']}"
                task_list.append(task_info)
            return [TextContent(type="text", text="\n\n".join(task_list))]

        if name == "jarvis_get_status":
            import io, contextlib
            f = io.StringIO()
            with contextlib.redirect_stdout(f):
                self.jarvis.show_status()
            system_output = f.getvalue()
            return [TextContent(type="text", text=system_output)]

        if name == "jarvis_schedule_task":
            description = arguments.get("description", "")
            priority = arguments.get("priority", "medium")
            category = arguments.get("category", "general")
            deadline = arguments.get("deadline")
            duration = arguments.get("duration")
            if not description:
                return [TextContent(type="text", text="Error: No task description provided")]
            self.jarvis.schedule_task(description, priority, category, deadline, duration)
            return [TextContent(type="text", text=f"Task scheduled successfully: {description}")]

        if name == "jarvis_complete_task":
            task_index = arguments.get("task_index")
            if not task_index:
                return [TextContent(type="text", text="Error: No task index provided")]
            try:
                self.jarvis.complete_task(task_index)
                return [TextContent(type="text", text=f"Task {task_index} completed successfully!")]
            except (IndexError, ValueError) as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]

        if name == "jarvis_delete_task":
            task_index = arguments.get("task_index")
            if not task_index:
                return [TextContent(type="text", text="Error: No task index provided")]
            try:
                self.jarvis.delete_task(task_index)
                return [TextContent(type="text", text=f"Task {task_index} deleted successfully!")]
            except (IndexError, ValueError) as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]

        if name == "jarvis_get_system_info":
            import io, contextlib
            f = io.StringIO()
            with contextlib.redirect_stdout(f):
                self.jarvis.show_system_info()
            system_output = f.getvalue()
            return [TextContent(type="text", text=system_output)]

        if name == "jarvis_update_setting":
            key = arguments.get("key")
            value = arguments.get("value")
            if not key or not value:
                return [TextContent(type="text", text="Error: Both key and value are required")]
            try:
                self.jarvis.update_setting(key, value)
                return [TextContent(type="text", text=f"Setting '{key}' updated to '{value}'")]
            except Exception as e:
                return [TextContent(type="text", text=f"Error updating setting: {str(e)}")]

        if name == "jarvis_get_settings":
            settings = self.jarvis.preferences
            settings_text = "Current Jarvis Settings:\n\n"
            for key, value in settings.items():
                settings_text += f"• {key.replace('_', ' ').title()}: {value}\n"
            return [TextContent(type="text", text=settings_text)]

        if name == "jarvis_web_search":
            query = (arguments or {}).get("query", "")
            if not query:
                return [TextContent(type="text", text="Error: No search query provided")]
            if not self._is_external_server_connected("search"):
                return [TextContent(type="text", text="Search server not connected. Run: connect search python3 search/mcp_server.py")]
            params = self._load_saved_server_command("search")
            if params is None:
                return [TextContent(type="text", text="Search server command not configured. Reconnect the 'search' server from the client.")]
            try:
                response = await self._invoke_external_tool(params, "web.search", {"query": query})
                text = self._extract_text_content(response)
                
                # Parse JSON results
                try:
                    results = json.loads(text)
                    if not isinstance(results, list):
                        results = []
                except (json.JSONDecodeError, TypeError):
                    results = []
                
                # Format top 5 results into readable context
                context_parts = []
                for i, result in enumerate(results[:5], 1):
                    if isinstance(result, dict):
                        title = result.get("title", "No title")
                        url = result.get("url", "No URL")
                        snippet = result.get("snippet", "No snippet")
                        context_parts.append(f"{i}. **{title}**\n   URL: {url}\n   {snippet}")
                
                if context_parts:
                    context = "\n\n".join(context_parts)
                    prompt = f"Based on these search results for '{query}':\n\n{context}\n\nPlease provide a helpful summary and analysis."
                else:
                    prompt = f"I searched for '{query}' but didn't find any structured results. The raw response was: {text[:500]}..."
                
                # Send to jarvis_chat tool
                chat_response = await self._dispatch_tool("jarvis_chat", {"message": prompt})
                chat_text = self._extract_text_content(chat_response[0]) if chat_response else "No response from chat"
                
                return [TextContent(type="text", text=f"🔎 Results for '{query}':\n\n{chat_text}")]
            except Exception as e:
                logger.error("Proxy search failed: %s", e)
                return [TextContent(type="text", text=f"Search proxy failed: {e}")]

        if name == "jarvis_calculate":
            expression = arguments.get("expression", "")
            if not expression:
                return [TextContent(type="text", text="Error: No expression provided")]
            if hasattr(self.jarvis, 'tool_manager') and 'calculator' in self.jarvis.tool_manager.tools:
                try:
                    calc_tool = self.jarvis.tool_manager.tools['calculator']
                    result = calc_tool.calculate(expression)
                    return [TextContent(type="text", text=f"Result: {result}")]
                except Exception as e:
                    return [TextContent(type="text", text=f"Calculation error: {str(e)}")]
            else:
                return [TextContent(type="text", text="Calculator tool not available")]

        if name == "jarvis_get_memory":
            limit = arguments.get("limit", 10)
            conversations = self.jarvis.conversation_history[-limit:] if self.jarvis.conversation_history else []
            if not conversations:
                return [TextContent(type="text", text="No conversation history found.")]
            memory_text = f"Recent Conversations (last {len(conversations)}):\n\n"
            for i, msg in enumerate(conversations, 1):
                role = "🤖 JARVIS" if msg['role'] == "assistant" else f"👤 {self.jarvis.user_name}"
                content = msg['content'][:200] + "..." if len(msg['content']) > 200 else msg['content']
                memory_text += f"{i}. {role}: {content}\n\n"
            return [TextContent(type="text", text=memory_text)]

        # Fallback
        return [TextContent(type="text", text=f"Error: Orchestrator cannot dispatch unknown tool '{name}'")]
        
    def _register_tools(self):
        """Register all Jarvis tools with the MCP server."""

        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List all available Jarvis tools aggregated with connected servers."""
            local_tools: List[Tool] = [
                Tool(
                    name="jarvis_chat",
                    description="Chat with Jarvis AI assistant. Send a message and get an intelligent response.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": "The message to send to Jarvis"
                            }
                        },
                        "required": ["message"]
                    }
                ),
                # Task management tools have been removed from Jarvis to avoid
                # redundancy with the dedicated 'system' server.
                Tool(
                    name="jarvis_get_status",
                    description="Get current system status and overview from Jarvis.",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="jarvis_get_system_info",
                    description="Get detailed system information from Jarvis.",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="jarvis_update_setting",
                    description="Update a user preference setting in Jarvis.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "key": {
                                "type": "string",
                                "description": "Setting key to update"
                            },
                            "value": {
                                "type": "string",
                                "description": "New value for the setting"
                            }
                        },
                        "required": ["key", "value"]
                    }
                ),
                Tool(
                    name="jarvis_get_settings",
                    description="Get current user settings and preferences from Jarvis.",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="jarvis_web_search",
                    description="Proxy web search via the external 'search' MCP server.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query"
                            }
                        },
                        "required": ["query"],
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="jarvis_calculate",
                    description="Perform mathematical calculations using Jarvis's calculator tool.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "expression": {
                                "type": "string",
                                "description": "Mathematical expression to calculate"
                            }
                        },
                        "required": ["expression"]
                    }
                ),
                Tool(
                    name="jarvis_get_memory",
                    description="Get recent conversation history from Jarvis memory.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of conversations to return",
                                "default": 10
                            }
                        }
                    }
                ),
                Tool(
                    name="orchestrator.run_plan",
                    description="Execute a multi-step plan of tool calls, with optional parallel steps and retries.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "steps": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "tool": {"type": "string"},
                                        "args": {"type": "object"},
                                        "parallel": {"type": "boolean"}
                                    },
                                    "required": ["tool"]
                                },
                                "description": "Ordered list of steps to execute"
                            }
                        },
                        "required": ["steps"]
                    }
                ),
                Tool(
                    name="fitness.list_workouts",
                    description="List workouts from the fitness library; optionally filter by muscle group.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "muscle_group": {"type": "string", "description": "Optional muscle group to filter by"}
                        }
                    }
                ),
                Tool(
                    name="fitness.search_workouts",
                    description="Search workouts by keyword in the fitness library.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"}
                        },
                        "required": ["query"]
                    }
                )
            ]

            # Append remote tools if any external servers are connected
            try:
                if self._session_manager is not None:
                    await self._index_remote_tools()
                    aggregated: List[Tool] = list(local_tools)
                    aliases = [a for a in self._session_manager.list_aliases() if a != getattr(self._session_manager, "default_alias", "jarvis")]
                    for alias in aliases:
                        try:
                            remote_tools = await self._session_manager.list_tools_cached(alias)
                        except Exception:
                            continue
                        for rt in remote_tools or []:
                            rname = getattr(rt, "name", None) or (rt.get("name") if isinstance(rt, dict) else None)
                            if not rname:
                                continue
                            desc = getattr(rt, "description", None) or (rt.get("description") if isinstance(rt, dict) else None) or ""
                            schema = getattr(rt, "inputSchema", None) or (rt.get("inputSchema") if isinstance(rt, dict) else None) or {"type": "object", "properties": {}}
                            exposed_name = f"{alias}.{rname}" if self._namespace_remote else rname
                            if any(t.name == exposed_name for t in aggregated):
                                continue
                            try:
                                aggregated.append(Tool(name=exposed_name, description=desc, inputSchema=schema))
                            except Exception:
                                aggregated.append(Tool(name=exposed_name, description=desc, inputSchema={"type": "object", "properties": {}}))
                    return aggregated
            except Exception as e:
                logger.warning("Remote tool aggregation failed: %s", e)

            return local_tools
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[Union[TextContent, ImageContent, EmbeddedResource]]:
            """Handle tool calls."""
            try:
                if name == "jarvis_chat":
                    message = arguments.get("message", "")
                    if not message:
                        return [TextContent(type="text", text="Error: No message provided")]

                    # If brain is available, use it as the chat backend (memory + LLM)
                    if BRAIN_AVAILABLE:
                        try:
                            # Save user message
                            brain_memory.save_message("user", message)

                            # Retrieve relevant memories (simple LIKE search)
                            mems = brain_memory.search_memories(message, limit=5)
                            used_memories = [m[2] for m in mems]

                            # Build a concise Jarvis persona prompt with surfaced memories
                            base = (
                                "You are Jarvis, a concise, helpful AI assistant. "
                                "Use short sentences and helpful bullet points when useful."
                            )
                            if used_memories:
                                joined = "\n- ".join(used_memories)
                                system_prompt = base + f"\n\nRelevant memories:\n- {joined}"
                            else:
                                system_prompt = base

                            reply = brain_generate(system_prompt, message)
                            # Hard fallback if brain returns unavailability marker
                            if not reply or reply.startswith("[LLM unavailable"):
                                reply = "I registered your message. I'll remember key details and respond succinctly."

                            # Save assistant reply
                            brain_memory.save_message("assistant", reply)

                            # Periodically summarize to long-term memory
                            try:
                                recent = brain_memory.recent_messages(100)
                                if len(recent) % 10 == 0:
                                    brain_memory.summarize_thread()
                            except Exception:
                                pass

                            # Include a small recall preview to make memory use visible
                            if used_memories:
                                preview = "\n\nRecall: " + "; ".join(used_memories[:2])
                                if preview not in reply:
                                    reply = (reply or "").strip() + preview

                            return [TextContent(type="text", text=reply)]
                        except Exception as e:
                            # Fall back to legacy Jarvis chat on any brain error
                            logger.warning(f"Brain chat failed, falling back to Jarvis.chat: {e}")
                            response = self._as_text(self.jarvis.chat(message))
                            if not response:
                                response = "I heard you. Let's keep chatting!"
                            return [TextContent(type="text", text=response)]

                    # Fallback if brain package is not available
                    response = self._as_text(self.jarvis.chat(message))
                    if not response:
                        response = "I heard you. Let's keep chatting!"
                    return [TextContent(type="text", text=response)]
                
                elif name in ("jarvis_schedule_task", "jarvis_get_tasks", "jarvis_complete_task", "jarvis_delete_task"):
                    return [TextContent(
                        type="text",
                        text=(
                            "These task tools are deprecated in Jarvis. "
                            "Use the 'system' server instead:\n"
                            "- system.create_task\n"
                            "- system.list_tasks\n"
                            "- system.complete_task\n"
                            "- system.set_task_completed"
                        ),
                    )]
                
                elif name == "jarvis_get_status":
                    # Capture the status output
                    import io
                    import contextlib
                    
                    f = io.StringIO()
                    with contextlib.redirect_stdout(f):
                        self.jarvis.show_status()
                    status_output = f.getvalue()
                    
                    return [TextContent(type="text", text=status_output)]
                
                elif name == "jarvis_get_system_info":
                    # Capture the system info output
                    import io
                    import contextlib
                    
                    f = io.StringIO()
                    with contextlib.redirect_stdout(f):
                        self.jarvis.show_system_info()
                    system_output = f.getvalue()
                    
                    return [TextContent(type="text", text=system_output)]
                
                elif name == "jarvis_update_setting":
                    key = arguments.get("key")
                    value = arguments.get("value")
                    
                    if not key or not value:
                        return [TextContent(type="text", text="Error: Both key and value are required")]
                    
                    try:
                        self.jarvis.update_setting(key, value)
                        return [TextContent(type="text", text=f"Setting '{key}' updated to '{value}'")]
                    except Exception as e:
                        return [TextContent(type="text", text=f"Error updating setting: {str(e)}")]
                
                elif name == "jarvis_get_settings":
                    settings = self.jarvis.preferences
                    settings_text = "Current Jarvis Settings:\n\n"
                    for key, value in settings.items():
                        settings_text += f"• {key.replace('_', ' ').title()}: {value}\n"
                    
                    return [TextContent(type="text", text=settings_text)]
                
                elif name == "jarvis_web_search":
                    query = (arguments or {}).get("query", "")
                    if not query:
                        return [TextContent(type="text", text="Error: No search query provided")]

                    if not self._is_external_server_connected("search"):
                        return [TextContent(type="text", text="Search server not connected. Run: connect search python3 search/mcp_server.py")]

                    params = self._load_saved_server_command("search")
                    if params is None:
                        return [TextContent(type="text", text="Search server command not configured. Reconnect the 'search' server from the client.")]

                    try:
                        response = await self._invoke_external_tool(params, "web.search", {"query": query})
                        text = self._extract_text_content(response)
                        
                        # Parse JSON results
                        try:
                            results = json.loads(text)
                            if not isinstance(results, list):
                                results = []
                        except (json.JSONDecodeError, TypeError):
                            results = []
                        
                        # Format top 5 results into readable context
                        context_parts = []
                        for i, result in enumerate(results[:5], 1):
                            if isinstance(result, dict):
                                title = result.get("title", "No title")
                                url = result.get("url", "No URL")
                                snippet = result.get("snippet", "No snippet")
                                context_parts.append(f"{i}. **{title}**\n   URL: {url}\n   {snippet}")
                        
                        if context_parts:
                            context = "\n\n".join(context_parts)
                            prompt = f"Based on these search results for '{query}':\n\n{context}\n\nPlease provide a helpful summary and analysis."
                        else:
                            prompt = f"I searched for '{query}' but didn't find any structured results. The raw response was: {text[:500]}..."
                        
                        # Send to jarvis_chat tool
                        chat_response = await self._dispatch_tool("jarvis_chat", {"message": prompt})
                        chat_text = self._extract_text_content(chat_response[0]) if chat_response else "No response from chat"
                        
                        return [TextContent(type="text", text=f"🔎 Results for '{query}':\n\n{chat_text}")]
                    except Exception as e:
                        logger.error("Proxy search failed: %s", e)
                        return [TextContent(type="text", text=f"Search proxy failed: {e}")]
                
                elif name == "jarvis_calculate":
                    expression = arguments.get("expression", "")
                    if not expression:
                        return [TextContent(type="text", text="Error: No expression provided")]
                    
                    # Use the calculator tool if available
                    if hasattr(self.jarvis, 'tool_manager') and 'calculator' in self.jarvis.tool_manager.tools:
                        try:
                            calc_tool = self.jarvis.tool_manager.tools['calculator']
                            result = calc_tool.calculate(expression)
                            return [TextContent(type="text", text=f"Result: {result}")]
                        except Exception as e:
                            return [TextContent(type="text", text=f"Calculation error: {str(e)}")]
                    else:
                        return [TextContent(type="text", text="Calculator tool not available")]
                
                elif name == "jarvis_get_memory":
                    limit = arguments.get("limit", 10)
                    conversations = self.jarvis.conversation_history[-limit:] if self.jarvis.conversation_history else []
                    
                    if not conversations:
                        return [TextContent(type="text", text="No conversation history found.")]
                    
                    memory_text = f"Recent Conversations (last {len(conversations)}):\n\n"
                    for i, msg in enumerate(conversations, 1):
                        role = "🤖 JARVIS" if msg['role'] == "assistant" else f"👤 {self.jarvis.user_name}"
                        content = msg['content'][:200] + "..." if len(msg['content']) > 200 else msg['content']
                        memory_text += f"{i}. {role}: {content}\n\n"
                    
                    return [TextContent(type="text", text=memory_text)]
                
                elif name == "orchestrator.run_plan":
                    try:
                        from orchestrator.executor import execute_plan
                    except Exception as e:
                        return [TextContent(type="text", text=f"Error: Orchestrator not available: {e}")]

                    steps = arguments.get("steps") or []
                    if not isinstance(steps, list) or not steps:
                        return [TextContent(type="text", text="Error: 'steps' must be a non-empty array")]

                    class _LocalClient:
                        async def call_tool(self_inner, tool_name: str, args: Dict[str, Any]):
                            return await self._dispatch_tool(tool_name, args)

                    plan_results = await execute_plan(steps, _LocalClient())
                    import json as _json
                    return [TextContent(type="text", text=_json.dumps({"results": plan_results}, indent=2))]

                elif name == "fitness.list_workouts":
                    mg = arguments.get("muscle_group")
                    import json as _json
                    payload = fitness_list_workouts(mg)
                    return [TextContent(type="text", text=_json.dumps(payload, indent=2))]

                elif name == "fitness.search_workouts":
                    q = arguments.get("query", "")
                    if not q:
                        return [TextContent(type="text", text="Error: No query provided")]
                    import json as _json
                    payload = fitness_search_workouts(q)
                    return [TextContent(type="text", text=_json.dumps(payload, indent=2))]
                
                else:
                    # Attempt to route unknown tools to connected external servers
                    if self._session_manager is not None:
                        await self._index_remote_tools()
                        alias: Optional[str] = None
                        remote_tool: Optional[str] = None
                        if "." in name:
                            prefix, _, tool_part = name.partition(".")
                            if prefix and tool_part:
                                alias, remote_tool = prefix, tool_part
                        if alias is None or remote_tool is None:
                            mapped = self._remote_tool_index.get(name)
                            if mapped:
                                alias, remote_tool = mapped
                        if alias and remote_tool:
                            try:
                                result = await self._session_manager.call_tool(alias, remote_tool, arguments or {})
                                text = self._extract_text_content(result)
                                return [TextContent(type="text", text=text)]
                            except Exception as e:
                                return [TextContent(type="text", text=f"Error routing to {alias}.{remote_tool}: {e}")]
                    return [TextContent(type="text", text=f"Unknown tool: {name}")]
                    
            except Exception as e:
                logger.error(f"Error in tool call {name}: {e}")
                return [TextContent(type="text", text=f"Error executing {name}: {str(e)}")]
    
    async def run(self):
        """Run the MCP server."""
        logger.info("Starting Jarvis MCP Server...")
        # Proactively connect external MCP servers before accepting requests
        try:
            await self._ensure_external_sessions()
        except Exception as e:
            logger.warning("External servers pre-connect failed: %s", e)
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


def create_mcp_server(user_name: str = "Boss") -> JarvisMCPServer:
    """Create and return a new Jarvis MCP server instance."""
    return JarvisMCPServer(user_name)


async def main():
    """Main entry point for the MCP server."""
    if not MCP_AVAILABLE:
        print("Error: MCP library is required. Install with: pip install mcp")
        sys.exit(1)
    
    # Get user name from command line or use default
    user_name = "Boss"
    if len(sys.argv) > 1:
        user_name = sys.argv[1]
    
    server = create_mcp_server(user_name)
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
