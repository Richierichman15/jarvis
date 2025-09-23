"""
MCP (Model Context Protocol) Server for Jarvis.
This module provides MCP tools for interacting with Jarvis functionality.
"""
import asyncio
import json
import logging
import sys
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

# MCP imports
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
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
        self._register_tools()

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
            query = arguments.get("query", "")
            if not query:
                return [TextContent(type="text", text="Error: No search query provided")]
            if hasattr(self.jarvis, 'tool_manager') and 'web_search' in self.jarvis.tool_manager.tools:
                try:
                    web_search_tool = self.jarvis.tool_manager.tools['web_search']
                    results = web_search_tool.search(query)
                    return [TextContent(type="text", text=results)]
                except Exception as e:
                    return [TextContent(type="text", text=f"Web search error: {str(e)}")]
            else:
                return [TextContent(type="text", text="Web search tool not available")]

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
            """List all available Jarvis tools."""
            return [
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
                Tool(
                    name="jarvis_schedule_task",
                    description="Schedule a new task or reminder with Jarvis.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "description": {
                                "type": "string",
                                "description": "Description of the task"
                            },
                            "priority": {
                                "type": "string",
                                "enum": ["low", "medium", "high", "urgent"],
                                "description": "Priority level of the task",
                                "default": "medium"
                            },
                            "category": {
                                "type": "string",
                                "description": "Category of the task (work, personal, learning, health, general)",
                                "default": "general"
                            },
                            "deadline": {
                                "type": "string",
                                "description": "Deadline for the task (ISO format)",
                                "default": None
                            },
                            "duration": {
                                "type": "integer",
                                "description": "Estimated duration in minutes",
                                "default": None
                            }
                        },
                        "required": ["description"]
                    }
                ),
                Tool(
                    name="jarvis_get_tasks",
                    description="Get all tasks from Jarvis, including pending and completed tasks.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "status": {
                                "type": "string",
                                "enum": ["all", "pending", "completed"],
                                "description": "Filter tasks by status",
                                "default": "all"
                            }
                        }
                    }
                ),
                Tool(
                    name="jarvis_complete_task",
                    description="Mark a task as completed by its index number.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "task_index": {
                                "type": "integer",
                                "description": "Index number of the task to complete (1-based)"
                            }
                        },
                        "required": ["task_index"]
                    }
                ),
                Tool(
                    name="jarvis_delete_task",
                    description="Delete a task by its index number.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "task_index": {
                                "type": "integer",
                                "description": "Index number of the task to delete (1-based)"
                            }
                        },
                        "required": ["task_index"]
                    }
                ),
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
                    description="Perform a web search using Jarvis's web search tool.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query"
                            }
                        },
                        "required": ["query"]
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
                            response = self.jarvis.chat(message)
                            return [TextContent(type="text", text=response)]

                    # Fallback if brain package is not available
                    response = self.jarvis.chat(message)
                    return [TextContent(type="text", text=response)]
                
                elif name == "jarvis_schedule_task":
                    description = arguments.get("description", "")
                    priority = arguments.get("priority", "medium")
                    category = arguments.get("category", "general")
                    deadline = arguments.get("deadline")
                    duration = arguments.get("duration")
                    
                    if not description:
                        return [TextContent(type="text", text="Error: No task description provided")]
                    
                    # Schedule the task
                    self.jarvis.schedule_task(description, priority, category, deadline, duration)
                    return [TextContent(type="text", text=f"Task scheduled successfully: {description}")]
                
                elif name == "jarvis_get_tasks":
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
                    
                    # Format tasks for display
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
                
                elif name == "jarvis_complete_task":
                    task_index = arguments.get("task_index")
                    if not task_index:
                        return [TextContent(type="text", text="Error: No task index provided")]
                    
                    try:
                        self.jarvis.complete_task(task_index)
                        return [TextContent(type="text", text=f"Task {task_index} completed successfully!")]
                    except (IndexError, ValueError) as e:
                        return [TextContent(type="text", text=f"Error: {str(e)}")]
                
                elif name == "jarvis_delete_task":
                    task_index = arguments.get("task_index")
                    if not task_index:
                        return [TextContent(type="text", text="Error: No task index provided")]
                    
                    try:
                        self.jarvis.delete_task(task_index)
                        return [TextContent(type="text", text=f"Task {task_index} deleted successfully!")]
                    except (IndexError, ValueError) as e:
                        return [TextContent(type="text", text=f"Error: {str(e)}")]
                
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
                    query = arguments.get("query", "")
                    if not query:
                        return [TextContent(type="text", text="Error: No search query provided")]
                    
                    # Use the web search tool if available
                    if hasattr(self.jarvis, 'tool_manager') and 'web_search' in self.jarvis.tool_manager.tools:
                        try:
                            web_search_tool = self.jarvis.tool_manager.tools['web_search']
                            results = web_search_tool.search(query)
                            return [TextContent(type="text", text=results)]
                        except Exception as e:
                            return [TextContent(type="text", text=f"Web search error: {str(e)}")]
                    else:
                        return [TextContent(type="text", text="Web search tool not available")]
                
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
                    return [TextContent(type="text", text=f"Unknown tool: {name}")]
                    
            except Exception as e:
                logger.error(f"Error in tool call {name}: {e}")
                return [TextContent(type="text", text=f"Error executing {name}: {str(e)}")]
    
    async def run(self):
        """Run the MCP server."""
        logger.info("Starting Jarvis MCP Server...")
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
