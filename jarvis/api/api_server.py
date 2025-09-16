"""
API server for Jarvis.
This module provides a RESTful API for interacting with Jarvis.
"""
import os
import re
import sys
import json
import time
import logging
import threading
import secrets
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime, timedelta

from flask import Flask, request, jsonify, send_from_directory, abort
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
import jwt

# Add parent directory to path to import goal_manager
sys.path.append(str(Path(__file__).parent.parent))
from goal_manager import GoalManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JarvisAPIServer:
    """API server for Jarvis."""
    
    def __init__(self, jarvis_instance: Any, host: str = "127.0.0.1", port: int = 5000,
                 enable_cors: bool = True, api_key: Optional[str] = None, 
                 enable_jwt: bool = True, jwt_secret: Optional[str] = None,
                 jwt_expiration: int = 24, ssl_cert: Optional[str] = None, 
                 ssl_key: Optional[str] = None):
        """
        Initialize the API server.
        
        Args:
            jarvis_instance: The instance of Jarvis this API serves
            host: Host to bind to
            port: Port to bind to
            enable_cors: Whether to enable CORS
            api_key: API key for authentication (if None, generates a random one)
            enable_jwt: Whether to enable JWT authentication
            jwt_secret: Secret key for JWT authentication (if None, generates a random one)
            jwt_expiration: JWT token expiration time in hours
            ssl_cert: Path to SSL certificate file
            ssl_key: Path to SSL key file
        """
        self.jarvis = jarvis_instance
        self.host = host
        self.port = port
        self.enable_cors = enable_cors
        self.enable_jwt = enable_jwt
        self.jwt_expiration = jwt_expiration
        self.ssl_cert = ssl_cert
        self.ssl_key = ssl_key
        
        # Generate API key if not provided
        if api_key is None:
            self.api_key = secrets.token_urlsafe(32)
        else:
            self.api_key = api_key
            
        # Generate JWT secret if not provided and JWT is enabled
        if enable_jwt:
            if jwt_secret is None:
                self.jwt_secret = secrets.token_hex(32)
            else:
                self.jwt_secret = jwt_secret
        else:
            self.jwt_secret = None
            
        # Create Flask app
        self.app = Flask("jarvis_api")
        
        # Enable CORS if requested
        if enable_cors:
            CORS(self.app)
            
        # Fix for reverse proxies
        self.app.wsgi_app = ProxyFix(self.app.wsgi_app)
        
        # Active user sessions
        self.active_tokens = {}
        
        # Register API endpoints
        self._register_endpoints()
        
        # Server thread
        self.server_thread = None
        self.is_running = False
    
    def _register_endpoints(self):
        """Register all API endpoints."""
        
        # Helper functions for authentication
        def require_api_key(f):
            """Decorator to require API key authentication."""
            def decorated(*args, **kwargs):
                # Check if API key is provided
                api_key = request.headers.get('X-API-Key')
                if api_key is None or api_key != self.api_key:
                    return jsonify({"error": "Invalid or missing API key"}), 401
                return f(*args, **kwargs)
            decorated.__name__ = f.__name__
            return decorated
        
        def require_jwt(f):
            """Decorator to require JWT authentication."""
            def decorated(*args, **kwargs):
                # Check if JWT is provided
                token = None
                auth_header = request.headers.get('Authorization')
                if auth_header:
                    if auth_header.startswith('Bearer '):
                        token = auth_header[7:]
                
                if token is None:
                    return jsonify({"error": "Missing authentication token"}), 401
                
                try:
                    # Decode the token
                    decoded = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
                    
                    # Check if token is in active tokens
                    if token not in self.active_tokens:
                        return jsonify({"error": "Token is not active"}), 401
                    
                    # Add user_id to request
                    request.user_id = decoded['user_id']
                    
                except jwt.ExpiredSignatureError:
                    return jsonify({"error": "Token has expired"}), 401
                except jwt.InvalidTokenError:
                    return jsonify({"error": "Invalid token"}), 401
                
                return f(*args, **kwargs)
            decorated.__name__ = f.__name__
            return decorated
        
        # Choose the appropriate authentication method
        require_auth = require_jwt if self.enable_jwt else require_api_key
        
        # Root endpoint
        @self.app.route('/api', methods=['GET'])
        def api_root():
            """Root API endpoint."""
            return jsonify({
                "name": "Jarvis API",
                "version": "1.0.0",
                "status": "running",
                "auth_method": "jwt" if self.enable_jwt else "api_key",
                "endpoints": [
                    "/api/auth/login",
                    "/api/auth/logout",
                    "/api/auth/refresh",
                    "/api/chat",
                    "/api/query",
                    "/api/tools",
                    "/api/tools/<tool_name>",
                    "/api/memory",
                    "/api/plugins",
                    "/api/plugins/<plugin_name>",
                    "/api/status",
                    "/api/system"
                ]
            })
        
        # Authentication endpoints
        @self.app.route('/api/auth/login', methods=['POST'])
        def login():
            """Login endpoint."""
            data = request.json
            username = data.get('username')
            password = data.get('password')
            
            # For now, just check if API key is provided
            # TODO: Implement actual user authentication
            if not username or not password:
                return jsonify({"error": "Username and password are required"}), 400
            
            # Check credentials (for now, accept any non-empty password)
            if password == "":
                return jsonify({"error": "Invalid credentials"}), 401
            
            # Generate a token
            if self.enable_jwt:
                user_id = username  # Use username as user_id for now
                token_payload = {
                    'user_id': user_id,
                    'exp': datetime.utcnow() + timedelta(hours=self.jwt_expiration)
                }
                token = jwt.encode(token_payload, self.jwt_secret, algorithm="HS256")
                
                # Add token to active tokens
                self.active_tokens[token] = {
                    'user_id': user_id,
                    'created_at': datetime.utcnow(),
                    'expires_at': datetime.utcnow() + timedelta(hours=self.jwt_expiration)
                }
                
                return jsonify({
                    "token": token,
                    "expires_in": self.jwt_expiration * 3600,  # seconds
                    "user_id": user_id
                })
            else:
                # If JWT is disabled, just return the API key
                return jsonify({
                    "api_key": self.api_key
                })
        
        @self.app.route('/api/auth/logout', methods=['POST'])
        @require_auth
        def logout():
            """Logout endpoint."""
            if self.enable_jwt:
                # Get the token
                token = request.headers.get('Authorization')[7:]
                
                # Remove token from active tokens
                if token in self.active_tokens:
                    del self.active_tokens[token]
            
            return jsonify({"success": True})
        
        @self.app.route('/api/auth/refresh', methods=['POST'])
        @require_auth
        def refresh_token():
            """Refresh JWT token."""
            if not self.enable_jwt:
                return jsonify({"error": "JWT authentication is disabled"}), 400
            
            # Get the current token
            old_token = request.headers.get('Authorization')[7:]
            
            # Get user_id from token
            old_token_data = self.active_tokens.get(old_token)
            if not old_token_data:
                return jsonify({"error": "Invalid token"}), 401
            
            user_id = old_token_data['user_id']
            
            # Generate a new token
            token_payload = {
                'user_id': user_id,
                'exp': datetime.utcnow() + timedelta(hours=self.jwt_expiration)
            }
            new_token = jwt.encode(token_payload, self.jwt_secret, algorithm="HS256")
            
            # Add new token to active tokens
            self.active_tokens[new_token] = {
                'user_id': user_id,
                'created_at': datetime.utcnow(),
                'expires_at': datetime.utcnow() + timedelta(hours=self.jwt_expiration)
            }
            
            # Remove old token
            del self.active_tokens[old_token]
            
            return jsonify({
                "token": new_token,
                "expires_in": self.jwt_expiration * 3600  # seconds
            })
        
        # Chat endpoint
        @self.app.route('/api/chat', methods=['POST'])
        @require_auth
        def chat():
            """Chat with Jarvis."""
            data = request.json
            message = data.get('message')
            
            if not message:
                return jsonify({"error": "Message is required"}), 400
            
            try:
                # Process the message
                response = self.jarvis.process_query(message)
                
                return jsonify({
                    "success": True,
                    "response": response
                })
            except Exception as e:
                logger.error(f"Error processing chat message: {str(e)}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500
        
        # Query endpoint
        @self.app.route('/api/query', methods=['POST'])
        @require_auth
        def query():
            """Make a one-time query to Jarvis."""
            data = request.json
            query_text = data.get('query')
            
            if not query_text:
                return jsonify({"error": "Query is required"}), 400
            
            try:
                # Process the query
                response = self.jarvis.process_query(query_text)
                
                return jsonify({
                    "success": True,
                    "response": response
                })
            except Exception as e:
                logger.error(f"Error processing query: {str(e)}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500
        
        # Tools endpoints
        @self.app.route('/api/tools', methods=['GET'])
        @require_auth
        def list_tools():
            """List available tools."""
            try:
                tool_manager = self.jarvis.tool_manager
                tools = tool_manager.get_available_tools()
                descriptions = tool_manager.get_tool_descriptions()
                
                tool_info = [{"name": tool, "description": descriptions.get(tool, "")} 
                            for tool in tools]
                
                return jsonify({
                    "success": True,
                    "tools": tool_info
                })
            except Exception as e:
                logger.error(f"Error listing tools: {str(e)}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500
        
        @self.app.route('/api/tools/<tool_name>', methods=['POST'])
        @require_auth
        def execute_tool(tool_name):
            """Execute a specific tool."""
            data = request.json
            params = data.get('params', {})
            
            try:
                # Execute the tool
                tool_manager = self.jarvis.tool_manager
                if tool_name not in tool_manager.get_available_tools():
                    return jsonify({
                        "success": False,
                        "error": f"Tool '{tool_name}' not found"
                    }), 404
                
                result = tool_manager.execute_tool(tool_name, params)
                
                return jsonify({
                    "success": True,
                    "result": result
                })
            except Exception as e:
                logger.error(f"Error executing tool '{tool_name}': {str(e)}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500
        
        # Goal and quest management endpoints
        @self.app.route('/api/suggest_tasks', methods=['GET'])
        @require_auth
        def suggest_tasks(self) -> Dict[str, Any]:
            """Generate new quests based on user's goals and preferences."""
            try:
                # Initialize goal manager
                manager = GoalManager()
                
                # Generate new quests
                quests = manager.generate_daily_quests()
                
                return {
                    "success": True,
                    "quests": quests,
                    "message": "New daily quests have been generated"
                }
                
            except Exception as e:
                logger.error(f"Error generating quests: {str(e)}")
                return {
                    "success": False,
                    "error": str(e)
                }
                
        @self.app.route('/api/generate_quests', methods=['POST'])
        @require_auth
        def generate_quests(self) -> Dict[str, Any]:
            """Generate new quests from goals."""
            try:
                # Initialize goal manager
                manager = GoalManager()
                
                # Generate new quests
                quests = manager.generate_daily_quests()
                
                return {
                    "success": True,
                    "quests": quests,
                    "message": "New quests have been generated"
                }
                
            except Exception as e:
                logger.error(f"Error generating quests: {str(e)}")
                return {
                    "success": False,
                    "error": str(e)
                }
                
        @self.app.route('/api/goals', methods=['GET'])
        @require_auth
        def get_goals(self) -> Dict[str, Any]:
            """Get all goals for the user."""
            try:
                manager = GoalManager()
                goals = manager.goals.get(manager.username, {}).get("goals", [])
                
                return {
                    "success": True,
                    "goals": goals
                }
                
            except Exception as e:
                logger.error(f"Error getting goals: {str(e)}")
                return {
                    "success": False,
                    "error": str(e)
                }
                
        @self.app.route('/api/quests', methods=['GET'])
        @require_auth
        def get_quests(self) -> Dict[str, Any]:
            """Get all active quests for the user."""
            try:
                if not os.path.exists(GoalManager.QUESTS_FILE):
                    return {"success": True, "quests": []}
                    
                with open(GoalManager.QUESTS_FILE, 'r') as f:
                    quests = json.load(f).get(GoalManager().username, [])
                    
                # Filter out expired quests
                now = datetime.now().isoformat()
                active_quests = [q for q in quests if q.get("expires_at", "") > now and q.get("status") != "completed"]
                
                return {
                    "success": True,
                    "quests": active_quests
                }
                
            except Exception as e:
                logger.error(f"Error getting quests: {str(e)}")
                return {
                    "success": False,
                    "error": str(e)
                }
                
        @self.app.route('/api/complete_task', methods=['POST'])
        @require_auth
        def complete_task(self) -> Dict[str, Any]:
            """Complete a task."""
            try:
                # Get task ID
                task_id = request.json.get('task_id')
                
                # Initialize goal manager
                manager = GoalManager()
                
                # Complete task
                manager.complete_task(task_id)
                
                return {
                    "success": True,
                    "message": "Task has been completed"
                }
                
            except Exception as e:
                logger.error(f"Error completing task: {str(e)}")
                return {
                    "success": False,
                    "error": str(e)
                }
                
        # Memory endpoints
        @self.app.route('/api/memory', methods=['GET'])
        @require_auth
        def get_memory():
            """Get conversation memory."""
            try:
                memory = self.jarvis.memory
                conversation = memory.get_conversation_history()
                
                return jsonify({
                    "success": True,
                    "conversation": conversation
                })
            except Exception as e:
                logger.error(f"Error getting memory: {str(e)}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500
        
        @self.app.route('/api/memory', methods=['DELETE'])
        @require_auth
        def clear_memory():
            """Clear conversation memory."""
            try:
                memory = self.jarvis.memory
                memory.clear()
                
                return jsonify({
                    "success": True
                })
            except Exception as e:
                logger.error(f"Error clearing memory: {str(e)}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500
        
        # Plugin endpoints
        @self.app.route('/api/plugins', methods=['GET'])
        @require_auth
        def list_plugins():
            """List available plugins."""
            try:
                # Check if plugin manager is available
                if not hasattr(self.jarvis, 'plugin_manager'):
                    return jsonify({
                        "success": False,
                        "error": "Plugin system is not enabled"
                    }), 400
                
                plugin_manager = self.jarvis.plugin_manager
                discovered_plugins = plugin_manager.discover_plugins()
                
                return jsonify({
                    "success": True,
                    "plugins": discovered_plugins
                })
            except Exception as e:
                logger.error(f"Error listing plugins: {str(e)}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500
        
        @self.app.route('/api/plugins/<plugin_name>', methods=['POST'])
        @require_auth
        def manage_plugin(plugin_name):
            """Manage a specific plugin."""
            data = request.json
            action = data.get('action')
            
            if not action:
                return jsonify({"error": "Action is required"}), 400
            
            try:
                # Check if plugin manager is available
                if not hasattr(self.jarvis, 'plugin_manager'):
                    return jsonify({
                        "success": False,
                        "error": "Plugin system is not enabled"
                    }), 400
                
                plugin_manager = self.jarvis.plugin_manager
                
                if action == 'load':
                    module_name = data.get('module_name')
                    class_name = data.get('class_name')
                    
                    if not module_name or not class_name:
                        return jsonify({
                            "success": False,
                            "error": "Module name and class name are required for loading a plugin"
                        }), 400
                    
                    plugin = plugin_manager.load_plugin(module_name, class_name)
                    if plugin:
                        return jsonify({
                            "success": True,
                            "plugin": plugin.name
                        })
                    else:
                        return jsonify({
                            "success": False,
                            "error": f"Failed to load plugin from module '{module_name}', class '{class_name}'"
                        }), 500
                        
                elif action == 'unload':
                    success = plugin_manager.unload_plugin(plugin_name)
                    return jsonify({
                        "success": success,
                        "error": None if success else f"Failed to unload plugin '{plugin_name}'"
                    })
                    
                elif action == 'get_settings':
                    settings = plugin_manager.get_plugin_settings(plugin_name)
                    if settings is not None:
                        return jsonify({
                            "success": True,
                            "settings": settings
                        })
                    else:
                        return jsonify({
                            "success": False,
                            "error": f"No settings found for plugin '{plugin_name}'"
                        }), 404
                        
                elif action == 'update_settings':
                    settings = data.get('settings')
                    if not settings:
                        return jsonify({
                            "success": False,
                            "error": "Settings are required for updating plugin settings"
                        }), 400
                        
                    success = plugin_manager.update_plugin_settings(plugin_name, settings)
                    return jsonify({
                        "success": success,
                        "error": None if success else f"Failed to update settings for plugin '{plugin_name}'"
                    })
                    
                elif action == 'reset_settings':
                    success = plugin_manager.reset_plugin_settings(plugin_name)
                    return jsonify({
                        "success": success,
                        "error": None if success else f"Failed to reset settings for plugin '{plugin_name}'"
                    })
                    
                else:
                    return jsonify({
                        "success": False,
                        "error": f"Unknown action '{action}'"
                    }), 400
                    
            except Exception as e:
                logger.error(f"Error managing plugin '{plugin_name}': {str(e)}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500
        
        # Status endpoint
        @self.app.route('/api/status', methods=['GET'])
        @require_auth
        def get_status():
            """Get Jarvis status."""
            try:
                # Gather basic information
                status = {
                    "api_version": "1.0.0",
                    "uptime": time.time() - self.jarvis._start_time if hasattr(self.jarvis, '_start_time') else 0,
                    "tools_available": len(self.jarvis.tool_manager.get_available_tools()),
                    "memory_enabled": True if hasattr(self.jarvis, 'memory') else False,
                    "plugin_system_enabled": True if hasattr(self.jarvis, 'plugin_manager') else False
                }
                
                # Get tool information if available
                if hasattr(self.jarvis, 'tool_manager'):
                    status['tools'] = self.jarvis.tool_manager.get_available_tools()
                
                # Get plugin information if available
                if hasattr(self.jarvis, 'plugin_manager'):
                    plugins = self.jarvis.plugin_manager.get_all_plugins()
                    status['plugins'] = [{"name": name, "version": plugin.version} for name, plugin in plugins.items()]
                
                return jsonify({
                    "success": True,
                    "status": status
                })
            except Exception as e:
                logger.error(f"Error getting status: {str(e)}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500
        
        # System monitor endpoint
        @self.app.route('/api/system', methods=['GET'])
        @require_auth
        def get_system_info():
            """Get system information."""
            try:
                # Check if system monitor is available
                if not hasattr(self.jarvis.tool_manager, 'tools') or "system_info" not in self.jarvis.tool_manager.tools:
                    return jsonify({
                        "success": False,
                        "error": "System info tool is not available"
                    }), 400
                
                system_info = self.jarvis.tool_manager.tools["system_info"]
                info_type = request.args.get('type', 'all')
                
                # Get system information
                result = system_info.get_info(info_type)
                
                return jsonify({
                    "success": True,
                    "system_info": result
                })
            except Exception as e:
                logger.error(f"Error getting system information: {str(e)}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500
    
    def start(self, debug: bool = False, use_reloader: bool = False) -> None:
        """
        Start the API server.
        
        Args:
            debug: Whether to run the server in debug mode
            use_reloader: Whether to use the Flask reloader
        """
        # Check if server is already running
        if self.is_running:
            logger.warning("API server is already running")
            return
        
        # Determine SSL context
        ssl_context = None
        if self.ssl_cert and self.ssl_key:
            ssl_context = (self.ssl_cert, self.ssl_key)
        
        # Print server information
        protocol = "https" if ssl_context else "http"
        logger.info(f"Starting Jarvis API server at {protocol}://{self.host}:{self.port}")
        
        if self.enable_jwt:
            logger.info("JWT authentication is enabled")
        else:
            logger.info(f"API Key authentication is enabled. Your API key is: {self.api_key}")
        
        # Run the server in a separate thread if not in debug mode
        if debug:
            # In debug mode, run directly
            self.is_running = True
            self.app.run(host=self.host, port=self.port, debug=debug, ssl_context=ssl_context, use_reloader=use_reloader)
            self.is_running = False
        else:
            # Create a thread for the server
            self.server_thread = threading.Thread(
                target=self._run_server,
                args=(ssl_context,)
            )
            self.server_thread.daemon = True
            self.server_thread.start()
            self.is_running = True
            
            # Wait a bit to make sure the server starts
            time.sleep(1)
            
            # Check if the server started successfully
            if not self.is_running:
                logger.error("Failed to start API server")
    
    def _run_server(self, ssl_context: Optional[Tuple[str, str]] = None) -> None:
        """
        Run the API server in a separate thread.
        
        Args:
            ssl_context: SSL context for the server
        """
        try:
            self.app.run(
                host=self.host,
                port=self.port,
                debug=False,
                use_reloader=False,
                ssl_context=ssl_context
            )
        except Exception as e:
            logger.error(f"Error running API server: {str(e)}")
            self.is_running = False
    
    def stop(self) -> None:
        """Stop the API server."""
        if not self.is_running:
            logger.warning("API server is not running")
            return
        
        # Stop the server
        self.is_running = False
        logger.info("Stopping Jarvis API server")
        
        if self.server_thread:
            self.server_thread.join(timeout=5)
            
        logger.info("Jarvis API server stopped")
    
    def get_api_key(self) -> str:
        """Get the API key."""
        return self.api_key
    
    def regenerate_api_key(self) -> str:
        """Regenerate the API key."""
        self.api_key = secrets.token_urlsafe(32)
        return self.api_key
    
    def get_jwt_secret(self) -> Optional[str]:
        """Get the JWT secret."""
        return self.jwt_secret
    
    def regenerate_jwt_secret(self) -> Optional[str]:
        """Regenerate the JWT secret."""
        if self.enable_jwt:
            self.jwt_secret = secrets.token_hex(32)
            # Invalidate all active tokens
            self.active_tokens = {}
            return self.jwt_secret
        else:
            return None 