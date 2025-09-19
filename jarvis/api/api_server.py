"""
API server for Jarvis.
This module provides a RESTful API for interacting with Jarvis.
System functionality has been removed - this is now a clean AI assistant API.
"""
import os
import json
import logging
import secrets
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime, timedelta

from flask import Flask, request, jsonify, abort
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
import jwt

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
            ssl_key: Path to SSL private key file
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
            logger.info(f"Generated API key: {self.api_key}")
        else:
            self.api_key = api_key
            
        # Generate JWT secret if not provided
        if jwt_secret is None:
            self.jwt_secret = secrets.token_urlsafe(32)
            logger.info(f"Generated JWT secret: {self.jwt_secret}")
        else:
            self.jwt_secret = jwt_secret
        
        # Initialize Flask app
        self.app = Flask(__name__)
        self.app.secret_key = secrets.token_urlsafe(32)
        
        # Enable CORS if requested
        if enable_cors:
            CORS(self.app)
            
        # Add proxy fix middleware
        self.app.wsgi_app = ProxyFix(self.app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
        
        # Register routes
        self._register_routes()
        
    def _register_routes(self):
        """Register API routes."""
        
        @self.app.route('/')
        def index():
            """API index endpoint."""
            return jsonify({
                "name": "Jarvis API Server",
                "version": "1.0.0",
                "status": "running",
                "timestamp": datetime.now().isoformat(),
                "message": "System functionality has been removed - Jarvis is now a clean AI assistant"
            })
        
        @self.app.route('/api/chat', methods=['POST'])
        def chat():
            """Chat with Jarvis."""
            try:
                data = request.get_json()
                if not data:
                    return jsonify({"error": "No JSON data provided"}), 400
                
                message = data.get('message', '')
                if not message:
                    return jsonify({"error": "No message provided"}), 400
                
                # Get response from Jarvis
                response = self.jarvis.chat(message)
                
                return jsonify({
                    "response": response,
                    "timestamp": datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error in chat endpoint: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/stats', methods=['GET'])
        def get_stats():
            """Get Jarvis stats."""
            try:
                return jsonify({
                    "stats": self.jarvis.stats,
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Error getting stats: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/tasks', methods=['GET'])
        def get_tasks():
            """Get current tasks."""
            try:
                tasks = [task.to_dict() if hasattr(task, 'to_dict') else task for task in self.jarvis.tasks]
                return jsonify({
                    "tasks": tasks,
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Error getting tasks: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/tasks', methods=['POST'])
        def add_task():
            """Add a new task."""
            try:
                data = request.get_json()
                if not data:
                    return jsonify({"error": "No JSON data provided"}), 400
                
                task_name = data.get('name', '')
                task_description = data.get('description', '')
                task_difficulty = data.get('difficulty', 'E')
                task_reward = data.get('reward', 10)
                
                if not task_name:
                    return jsonify({"error": "Task name is required"}), 400
                
                # Add task to Jarvis
                self.jarvis.add_task(task_name, task_description, task_difficulty, task_reward)
                
                return jsonify({
                    "message": "Task added successfully",
                    "timestamp": datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error adding task: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/tasks/<int:task_id>/complete', methods=['POST'])
        def complete_task(task_id):
            """Complete a task."""
            try:
                if task_id < 1 or task_id > len(self.jarvis.tasks):
                    return jsonify({"error": "Invalid task ID"}), 400
                
                # Complete the task
                result = self.jarvis.complete_task(task_id)
                
                return jsonify({
                    "message": "Task completed successfully",
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error completing task: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            """Health check endpoint."""
            return jsonify({
                "status": "healthy",
                "timestamp": datetime.now().isoformat()
            })
    
    def run(self, debug: bool = False):
        """Run the API server."""
        logger.info(f"Starting Jarvis API server on {self.host}:{self.port}")
        logger.info("System functionality has been removed - Jarvis is now a clean AI assistant")
        
        if self.ssl_cert and self.ssl_key:
            self.app.run(
                host=self.host,
                port=self.port,
                debug=debug,
                ssl_context=(self.ssl_cert, self.ssl_key)
            )
        else:
            self.app.run(
                host=self.host,
                port=self.port,
                debug=debug
            )


def create_api_server(jarvis_instance: Any, **kwargs) -> JarvisAPIServer:
    """Create and return a new JarvisAPIServer instance."""
    return JarvisAPIServer(jarvis_instance, **kwargs)


if __name__ == '__main__':
    # Example usage
    from jarvis import Jarvis
    
    jarvis = Jarvis()
    server = create_api_server(jarvis)
    server.run(debug=True)