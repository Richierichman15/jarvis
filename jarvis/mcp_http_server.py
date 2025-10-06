"""
HTTP/WebSocket MCP Server for Jarvis.
This module provides an HTTP-based MCP server that can be accessed via localhost:3010.
"""
import asyncio
import json
import logging
import sys
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import aiohttp
from aiohttp import web, WSMsgType
import uuid

from .jarvis import Jarvis
from .config import PROJECT_ROOT

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JarvisHTTPMCPServer:
    """HTTP/WebSocket MCP Server that exposes Jarvis functionality as tools."""
    
    def __init__(self, user_name: str = "Boss", host: str = "0.0.0.0", port: int = 3010):
        """Initialize the HTTP MCP server with a Jarvis instance."""
        self.jarvis = Jarvis(user_name=user_name)
        self.host = host
        self.port = port
        self.app = web.Application()
        self.setup_middleware()
        self.setup_routes()
    
    def setup_middleware(self):
        """Set up middleware for CORS, logging, and security."""
        
        # CORS middleware
        @web.middleware
        async def cors_middleware(request, handler):
            # Handle preflight requests
            if request.method == 'OPTIONS':
                response = web.Response()
            else:
                response = await handler(request)
            
            # Add CORS headers
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
            response.headers['Access-Control-Max-Age'] = '86400'
            
            return response
        
        # Logging middleware
        @web.middleware
        async def logging_middleware(request, handler):
            start_time = datetime.now()
            client_ip = request.remote or request.headers.get('X-Forwarded-For', 'unknown')
            
            logger.info(f"{start_time.strftime('%Y-%m-%d %H:%M:%S')} - {request.method} {request.path} from {client_ip}")
            
            try:
                response = await handler(request)
                duration = (datetime.now() - start_time).total_seconds()
                logger.info(f"Response: {response.status} in {duration:.3f}s")
                return response
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                logger.error(f"Error: {str(e)} in {duration:.3f}s")
                raise
        
        # Add middleware to the app
        self.app.middlewares.append(logging_middleware)
        self.app.middlewares.append(cors_middleware)
        
    def setup_routes(self):
        """Set up HTTP routes for the MCP server."""
        
        # Health check endpoint
        self.app.router.add_get('/health', self.health_check)
        self.app.router.add_get('/status', self.health_check)  # Alternative endpoint
        
        # Help/endpoints list
        self.app.router.add_get('/help', self.help_endpoint)
        
        # MCP endpoints
        self.app.router.add_get('/mcp/tools', self.list_tools)
        self.app.router.add_post('/mcp/tools/call', self.call_tool)
        self.app.router.add_get('/mcp/tools/call', self.call_tool_get)  # Support GET requests
        self.app.router.add_get('/mcp/status', self.get_status)
        
        # n8n integration endpoints
        self.app.router.add_post('/tool/jarvis_scan_news', self.n8n_scan_news)
        self.app.router.add_post('/tool/jarvis_trigger_n8n', self.n8n_trigger_n8n)
        
        # WebSocket endpoint for real-time MCP communication
        self.app.router.add_get('/mcp/ws', self.websocket_handler)
        
        # Static file serving for documentation
        self.app.router.add_get('/', self.index_page)
        self.app.router.add_get('/docs', self.docs_page)
        
        # Add OPTIONS handlers for CORS preflight
        self.app.router.add_options('/mcp/tools/call', self.options_handler)
        self.app.router.add_options('/mcp/tools', self.options_handler)
        self.app.router.add_options('/tool/jarvis_scan_news', self.options_handler)
        self.app.router.add_options('/tool/jarvis_trigger_n8n', self.options_handler)
    
    async def health_check(self, request):
        """Health check endpoint."""
        return web.json_response({
            "status": "healthy",
            "server": "Jarvis MCP HTTP Server",
            "user": self.jarvis.user_name,
            "host": self.host,
            "port": self.port,
            "timestamp": datetime.now().isoformat()
        })
    
    async def help_endpoint(self, request):
        """Help endpoint listing all available endpoints."""
        endpoints = [
            {"path": "/", "method": "GET", "description": "Home page with server info"},
            {"path": "/health", "method": "GET", "description": "Health check endpoint"},
            {"path": "/status", "method": "GET", "description": "Alternative health check"},
            {"path": "/help", "method": "GET", "description": "This help endpoint"},
            {"path": "/docs", "method": "GET", "description": "Documentation page"},
            {"path": "/mcp/tools", "method": "GET", "description": "List all available MCP tools"},
            {"path": "/mcp/tools/call", "method": "POST", "description": "Call a Jarvis tool"},
            {"path": "/mcp/status", "method": "GET", "description": "MCP server status"},
            {"path": "/mcp/ws", "method": "GET", "description": "WebSocket endpoint for real-time communication"}
        ]
        
        return web.json_response({
            "server": "Jarvis MCP HTTP Server",
            "user": self.jarvis.user_name,
            "host": self.host,
            "port": self.port,
            "endpoints": endpoints,
            "timestamp": datetime.now().isoformat()
        })
    
    async def options_handler(self, request):
        """Handle OPTIONS requests for CORS preflight."""
        return web.Response(status=200)
    
    async def list_tools(self, request):
        """List all available Jarvis tools."""
        tools = [
            {
                "name": "jarvis_chat",
                "description": "Chat with Jarvis AI assistant. Send a message and get an intelligent response.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "The message to send to Jarvis"
                        }
                    },
                    "required": ["message"]
                }
            },
            {
                "name": "jarvis_schedule_task",
                "description": "Schedule a new task or reminder with Jarvis.",
                "inputSchema": {
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
            },
            {
                "name": "jarvis_get_tasks",
                "description": "Get all tasks from Jarvis, including pending and completed tasks.",
                "inputSchema": {
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
            },
            {
                "name": "jarvis_complete_task",
                "description": "Mark a task as completed by its index number.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "task_index": {
                            "type": "integer",
                            "description": "Index number of the task to complete (1-based)"
                        }
                    },
                    "required": ["task_index"]
                }
            },
            {
                "name": "jarvis_delete_task",
                "description": "Delete a task by its index number.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "task_index": {
                            "type": "integer",
                            "description": "Index number of the task to delete (1-based)"
                        }
                    },
                    "required": ["task_index"]
                }
            },
            {
                "name": "jarvis_get_status",
                "description": "Get current system status and overview from Jarvis.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "jarvis_get_system_info",
                "description": "Get detailed system information from Jarvis.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "jarvis_update_setting",
                "description": "Update a user preference setting in Jarvis.",
                "inputSchema": {
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
            },
            {
                "name": "jarvis_get_settings",
                "description": "Get current user settings and preferences from Jarvis.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "jarvis_web_search",
                "description": "Perform a web search using Jarvis's web search tool.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "jarvis_calculate",
                "description": "Perform mathematical calculations using Jarvis's calculator tool.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "Mathematical expression to calculate"
                        }
                    },
                    "required": ["expression"]
                }
            },
            {
                "name": "jarvis_get_memory",
                "description": "Get recent conversation history from Jarvis memory.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of conversations to return",
                            "default": 10
                        }
                    }
                }
            },
            {
                "name": "jarvis_scan_news",
                "description": "Scan news across multiple tech topics (AI, Crypto, Finance, Automation, Emerging Tech, Economics) and provide AI-powered summaries.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "jarvis_trigger_n8n",
                "description": "Trigger an n8n workflow by sending a webhook to localhost:5678/webhook/d3a372f9-f7c5-41aa-b217-8e1f961f4e7d.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]
        
        return web.json_response({
            "tools": tools,
            "count": len(tools),
            "timestamp": datetime.now().isoformat()
        })
    
    async def call_tool(self, request):
        """Call a Jarvis tool via POST."""
        try:
            data = await request.json()
            tool_name = data.get("name")
            arguments = data.get("arguments", {})
            
            if not tool_name:
                return web.json_response({
                    "error": "Tool name is required"
                }, status=400)
            
            # Execute the tool
            result = await self.execute_tool(tool_name, arguments)
            
            return web.json_response({
                "result": result,
                "tool": tool_name,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error calling tool: {e}")
            return web.json_response({
                "error": str(e)
            }, status=500)
    
    async def call_tool_get(self, request):
        """Call a Jarvis tool via GET (for MCP compatibility)."""
        try:
            # Get parameters from query string
            tool_name = request.query.get("name")
            arguments_str = request.query.get("arguments", "{}")
            
            if not tool_name:
                return web.json_response({
                    "error": "Tool name is required as 'name' parameter"
                }, status=400)
            
            # Parse arguments if provided
            try:
                import json
                arguments = json.loads(arguments_str) if arguments_str else {}
            except json.JSONDecodeError:
                arguments = {}
            
            # Execute the tool
            result = await self.execute_tool(tool_name, arguments)
            
            return web.json_response({
                "result": result,
                "tool": tool_name,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error calling tool via GET: {e}")
            return web.json_response({
                "error": str(e)
            }, status=500)
    
    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Jarvis tool."""
        try:
            if name == "jarvis_chat":
                message = arguments.get("message", "")
                if not message:
                    return {"error": "No message provided"}
                
                response = self.jarvis.chat(message)
                return {"response": response}
            
            elif name == "jarvis_schedule_task":
                description = arguments.get("description", "")
                priority = arguments.get("priority", "medium")
                category = arguments.get("category", "general")
                deadline = arguments.get("deadline")
                duration = arguments.get("duration")
                
                if not description:
                    return {"error": "No task description provided"}
                
                self.jarvis.schedule_task(description, priority, category, deadline, duration)
                return {"message": f"Task scheduled successfully: {description}"}
            
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
                    return {"message": "No tasks found."}
                
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
                
                return {"tasks": task_list, "count": len(tasks)}
            
            elif name == "jarvis_complete_task":
                task_index = arguments.get("task_index")
                if not task_index:
                    return {"error": "No task index provided"}
                
                try:
                    self.jarvis.complete_task(task_index)
                    return {"message": f"Task {task_index} completed successfully!"}
                except (IndexError, ValueError) as e:
                    return {"error": str(e)}
            
            elif name == "jarvis_delete_task":
                task_index = arguments.get("task_index")
                if not task_index:
                    return {"error": "No task index provided"}
                
                try:
                    self.jarvis.delete_task(task_index)
                    return {"message": f"Task {task_index} deleted successfully!"}
                except (IndexError, ValueError) as e:
                    return {"error": str(e)}
            
            elif name == "jarvis_get_status":
                import io
                import contextlib
                
                f = io.StringIO()
                with contextlib.redirect_stdout(f):
                    self.jarvis.show_status()
                status_output = f.getvalue()
                
                return {"status": status_output}
            
            elif name == "jarvis_get_system_info":
                import io
                import contextlib
                
                f = io.StringIO()
                with contextlib.redirect_stdout(f):
                    self.jarvis.show_system_info()
                system_output = f.getvalue()
                
                return {"system_info": system_output}
            
            elif name == "jarvis_update_setting":
                key = arguments.get("key")
                value = arguments.get("value")
                
                if not key or not value:
                    return {"error": "Both key and value are required"}
                
                try:
                    self.jarvis.update_setting(key, value)
                    return {"message": f"Setting '{key}' updated to '{value}'"}
                except Exception as e:
                    return {"error": str(e)}
            
            elif name == "jarvis_get_settings":
                settings = self.jarvis.preferences
                return {"settings": settings}
            
            elif name == "jarvis_web_search":
                query = arguments.get("query", "")
                if not query:
                    return {"error": "No search query provided"}
                
                # Use the web search tool if available
                if hasattr(self.jarvis, 'tool_manager') and 'web_search' in self.jarvis.tool_manager.tools:
                    try:
                        web_search_tool = self.jarvis.tool_manager.tools['web_search']
                        results = web_search_tool.search(query)
                        return {"results": results}
                    except Exception as e:
                        return {"error": f"Web search error: {str(e)}"}
                else:
                    return {"error": "Web search tool not available"}
            
            elif name == "jarvis_calculate":
                expression = arguments.get("expression", "")
                if not expression:
                    return {"error": "No expression provided"}
                
                # Use the calculator tool if available
                if hasattr(self.jarvis, 'tool_manager') and 'calculator' in self.jarvis.tool_manager.tools:
                    try:
                        calc_tool = self.jarvis.tool_manager.tools['calculator']
                        result = calc_tool.calculate(expression)
                        return {"result": result}
                    except Exception as e:
                        return {"error": f"Calculation error: {str(e)}"}
                else:
                    return {"error": "Calculator tool not available"}
            
            elif name == "jarvis_get_memory":
                limit = arguments.get("limit", 10)
                conversations = self.jarvis.conversation_history[-limit:] if self.jarvis.conversation_history else []
                
                if not conversations:
                    return {"message": "No conversation history found."}
                
                return {"conversations": conversations, "count": len(conversations)}
            
            elif name == "jarvis_scan_news":
                # Import the MCP server to use its dispatch functionality
                from .mcp_server import JarvisMCPServer
                mcp_server = JarvisMCPServer(user_name=self.jarvis.user_name)
                
                try:
                    result = await mcp_server._dispatch_tool("jarvis_scan_news", {})
                    if result and len(result) > 0:
                        return {"result": result[0].text, "status": "success"}
                    else:
                        return {"error": "No result from news scan", "status": "error"}
                except Exception as e:
                    logger.error(f"News scan failed: {e}")
                    return {"error": f"News scan failed: {str(e)}", "status": "error"}
            
            elif name == "jarvis_trigger_n8n":
                # Import the MCP server to use its dispatch functionality
                from .mcp_server import JarvisMCPServer
                mcp_server = JarvisMCPServer(user_name=self.jarvis.user_name)
                
                try:
                    result = await mcp_server._dispatch_tool("jarvis_trigger_n8n", {})
                    if result and len(result) > 0:
                        return {"result": result[0].text, "status": "success"}
                    else:
                        return {"error": "No result from n8n trigger", "status": "error"}
                except Exception as e:
                    logger.error(f"n8n trigger failed: {e}")
                    return {"error": f"n8n trigger failed: {str(e)}", "status": "error"}
            
            else:
                return {"error": f"Unknown tool: {name}"}
                
        except Exception as e:
            logger.error(f"Error executing tool {name}: {e}")
            return {"error": f"Error executing {name}: {str(e)}"}
    
    async def get_status(self, request):
        """Get server status."""
        return web.json_response({
            "server": "Jarvis MCP HTTP Server",
            "user": self.jarvis.user_name,
            "host": self.host,
            "port": self.port,
            "status": "running",
            "timestamp": datetime.now().isoformat()
        })
    
    async def n8n_scan_news(self, request):
        """Dedicated endpoint for n8n to trigger news scanning."""
        try:
            # Execute the news scan tool
            result = await self.execute_tool("jarvis_scan_news", {})
            
            # Return the result in a format that n8n can easily process
            return web.json_response({
                "success": result.get("status") == "success",
                "data": result.get("result", result.get("error", "Unknown error")),
                "timestamp": datetime.now().isoformat(),
                "tool": "jarvis_scan_news"
            })
            
        except Exception as e:
            logger.error(f"Error in n8n_scan_news endpoint: {e}")
            return web.json_response({
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "tool": "jarvis_scan_news"
            }, status=500)
    
    async def n8n_trigger_n8n(self, request):
        """Dedicated endpoint for n8n to trigger itself (for testing/loops)."""
        try:
            # Execute the n8n trigger tool
            result = await self.execute_tool("jarvis_trigger_n8n", {})
            
            # Return the result in a format that n8n can easily process
            return web.json_response({
                "success": result.get("status") == "success",
                "data": result.get("result", result.get("error", "Unknown error")),
                "timestamp": datetime.now().isoformat(),
                "tool": "jarvis_trigger_n8n"
            })
            
        except Exception as e:
            logger.error(f"Error in n8n_trigger_n8n endpoint: {e}")
            return web.json_response({
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "tool": "jarvis_trigger_n8n"
            }, status=500)
    
    async def websocket_handler(self, request):
        """Handle WebSocket connections for real-time MCP communication."""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        logger.info(f"WebSocket connection established from {request.remote}")
        
        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        response = await self.handle_websocket_message(data)
                        await ws.send_str(json.dumps(response))
                    except json.JSONDecodeError:
                        await ws.send_str(json.dumps({"error": "Invalid JSON"}))
                    except Exception as e:
                        await ws.send_str(json.dumps({"error": str(e)}))
                elif msg.type == WSMsgType.ERROR:
                    logger.error(f"WebSocket error: {ws.exception()}")
                    break
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            logger.info("WebSocket connection closed")
        
        return ws
    
    async def handle_websocket_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle WebSocket messages."""
        message_type = data.get("type")
        
        if message_type == "list_tools":
            tools = await self.list_tools(None)
            return {"type": "tools_list", "data": await tools.json()}
        
        elif message_type == "call_tool":
            tool_name = data.get("tool")
            arguments = data.get("arguments", {})
            result = await self.execute_tool(tool_name, arguments)
            return {"type": "tool_result", "tool": tool_name, "result": result}
        
        elif message_type == "ping":
            return {"type": "pong", "timestamp": datetime.now().isoformat()}
        
        else:
            return {"error": f"Unknown message type: {message_type}"}
    
    async def index_page(self, request):
        """Serve the index page."""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Jarvis MCP HTTP Server</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .header { color: #2c3e50; }
                .endpoint { background: #f8f9fa; padding: 10px; margin: 10px 0; border-radius: 5px; }
                .method { color: #27ae60; font-weight: bold; }
            </style>
        </head>
        <body>
            <h1 class="header">🤖 Jarvis MCP HTTP Server</h1>
            <p>Welcome to the Jarvis MCP HTTP Server running on port 3010!</p>
            
            <h2>Available Endpoints:</h2>
            
            <div class="endpoint">
                <span class="method">GET</span> /health - Health check
            </div>
            
            <div class="endpoint">
                <span class="method">GET</span> /mcp/tools - List all available tools
            </div>
            
            <div class="endpoint">
                <span class="method">POST</span> /mcp/tools/call - Call a tool
            </div>
            
            <div class="endpoint">
                <span class="method">GET</span> /mcp/status - Get server status
            </div>
            
            <div class="endpoint">
                <span class="method">GET</span> /mcp/ws - WebSocket endpoint
            </div>
            
            <h2>Quick Test:</h2>
            <p>Try calling: <code>curl http://localhost:3010/health</code></p>
            
            <h2>Documentation:</h2>
            <p><a href="/docs">View full documentation</a></p>
        </body>
        </html>
        """
        return web.Response(text=html, content_type='text/html')
    
    async def docs_page(self, request):
        """Serve the documentation page."""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Jarvis MCP HTTP Server - Documentation</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .header { color: #2c3e50; }
                .tool { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; }
                .tool-name { color: #e74c3c; font-weight: bold; }
                .example { background: #2c3e50; color: white; padding: 10px; border-radius: 3px; font-family: monospace; }
            </style>
        </head>
        <body>
            <h1 class="header">📚 Jarvis MCP HTTP Server Documentation</h1>
            
            <h2>Available Tools:</h2>
            
            <div class="tool">
                <div class="tool-name">jarvis_chat</div>
                <p>Chat with Jarvis AI assistant.</p>
                <div class="example">
POST /mcp/tools/call
{
  "name": "jarvis_chat",
  "arguments": {
    "message": "Hello Jarvis!"
  }
}
                </div>
            </div>
            
            <div class="tool">
                <div class="tool-name">jarvis_schedule_task</div>
                <p>Schedule a new task or reminder.</p>
                <div class="example">
POST /mcp/tools/call
{
  "name": "jarvis_schedule_task",
  "arguments": {
    "description": "Call the dentist",
    "priority": "medium",
    "category": "personal"
  }
}
                </div>
            </div>
            
            <div class="tool">
                <div class="tool-name">jarvis_get_tasks</div>
                <p>Get all tasks from Jarvis.</p>
                <div class="example">
POST /mcp/tools/call
{
  "name": "jarvis_get_tasks",
  "arguments": {
    "status": "pending"
  }
}
                </div>
            </div>
            
            <p><a href="/">← Back to Home</a></p>
        </body>
        </html>
        """
        return web.Response(text=html, content_type='text/html')
    
    async def run(self):
        """Run the HTTP MCP server."""
        logger.info(f"Starting Jarvis MCP HTTP Server on {self.host}:{self.port}")
        
        runner = web.AppRunner(self.app)
        await runner.setup()
        
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        
        logger.info(f"🚀 Jarvis MCP HTTP Server is running!")
        logger.info(f"📍 Local endpoint: http://{self.host}:{self.port}")
        logger.info(f"🔧 Health check: http://{self.host}:{self.port}/health")
        logger.info(f"📋 List tools: http://{self.host}:{self.port}/mcp/tools")
        logger.info(f"📚 Documentation: http://{self.host}:{self.port}/docs")
        logger.info(f"Press Ctrl+C to stop the server")
        
        try:
            # Keep the server running
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down server...")
        finally:
            await runner.cleanup()


def create_http_mcp_server(user_name: str = "Boss", host: str = "0.0.0.0", port: int = 3010) -> JarvisHTTPMCPServer:
    """Create and return a new Jarvis HTTP MCP server instance."""
    return JarvisHTTPMCPServer(user_name, host, port)


async def main():
    """Main entry point for the HTTP MCP server."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Jarvis MCP HTTP Server')
    parser.add_argument('--user', default='Boss', help='User name for Jarvis')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=3010, help='Port to bind to')
    
    args = parser.parse_args()
    
    server = create_http_mcp_server(args.user, args.host, args.port)
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
