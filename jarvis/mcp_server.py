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
                    
                    # Capture the response from Jarvis
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