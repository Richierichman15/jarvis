"""
Web interface for Jarvis.
This module provides a simple web-based interface for interacting with Jarvis.
"""
import os
import re
import sys
import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime

from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for
import pygments
from pygments import lexers, formatters
from pygments.util import ClassNotFound

# Try to import Jarvis components, handle missing dependencies gracefully
try:
    from .jarvis import Jarvis
    JARVIS_AVAILABLE = True
except ImportError as e:
    JARVIS_AVAILABLE = False
    print(f"Warning: Jarvis core not available: {e}")

try:
    from .tools.code_editor import CodeEditorTool
    CODE_EDITOR_AVAILABLE = True
except ImportError as e:
    CODE_EDITOR_AVAILABLE = False
    print(f"Warning: Code editor not available: {e}")

from .auth import UserAuth
from .quest_system import QuestSystem

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), "templates"))

# Initialize components
jarvis_instance = None
code_editor = CodeEditorTool() if CODE_EDITOR_AVAILABLE else None
user_auth = UserAuth()
quest_system = QuestSystem()


def get_jarvis(user_name="User"):
    """Get or create a Jarvis instance."""
    global jarvis_instance
    if jarvis_instance is None and JARVIS_AVAILABLE:
        jarvis_instance = Jarvis(user_name=user_name)
    return jarvis_instance


def authenticate_request():
    """Authenticate request using session token."""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    
    session_id = auth_header.split(' ')[1]
    return user_auth.validate_session(session_id)


# Create templates directory if it doesn't exist
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
os.makedirs(templates_dir, exist_ok=True)


# Authentication routes
@app.route("/login")
def login_page():
    """Render the login page."""
    return render_template("login.html")


@app.route("/welcome")
def welcome_page():
    """Render the welcome page with Jarvis chatbot."""
    return render_template("welcome.html")


@app.route("/dashboard")
def main_dashboard():
    """Render the main dashboard."""
    return render_template("main_dashboard.html")


@app.route("/api/auth/login", methods=["POST"])
def api_login():
    """Handle user login."""
    try:
        data = request.json
        username = data.get("username", "").strip()
        password = data.get("password", "")
        
        if not username or not password:
            return jsonify({"success": False, "error": "Username and password are required"}), 400
        
        result = user_auth.login(username, password)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@app.route("/api/auth/register", methods=["POST"])
def api_register():
    """Handle user registration."""
    try:
        data = request.json
        username = data.get("username", "").strip()
        password = data.get("password", "")
        
        if not username or not password:
            return jsonify({"success": False, "error": "Username and password are required"}), 400
        
        if len(username) < 3:
            return jsonify({"success": False, "error": "Username must be at least 3 characters long"}), 400
            
        if len(password) < 6:
            return jsonify({"success": False, "error": "Password must be at least 6 characters long"}), 400
        
        result = user_auth.register_user(username, password)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@app.route("/api/auth/logout", methods=["POST"])
def api_logout():
    """Handle user logout."""
    try:
        user = authenticate_request()
        if user:
            auth_header = request.headers.get('Authorization')
            session_id = auth_header.split(' ')[1]
            user_auth.logout(session_id)
        
        return jsonify({"success": True, "message": "Logged out successfully"})
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


# User and quest management routes
@app.route("/api/user/save-desires", methods=["POST"])
def save_user_desires():
    """Save user desires and generate goals."""
    try:
        user = authenticate_request()
        if not user:
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        data = request.json
        desires = data.get("desires", "").strip()
        
        if not desires:
            return jsonify({"success": False, "error": "Desires are required"}), 400
        
        # Save desires
        user_auth.save_user_desires(user["username"], desires)
        
        # Generate goals based on desires
        quest_system.generate_goals_from_desires(user["username"], desires)
        
        return jsonify({"success": True, "message": "Desires saved and goals generated"})
    except Exception as e:
        logger.error(f"Save desires error: {str(e)}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@app.route("/api/user/goals", methods=["GET"])
def get_user_goals():
    """Get user's goals."""
    try:
        user = authenticate_request()
        if not user:
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        goals = quest_system.get_user_goals(user["username"])
        return jsonify({"success": True, "goals": goals["goals"] if goals else []})
    except Exception as e:
        logger.error(f"Get goals error: {str(e)}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@app.route("/api/user/progress", methods=["GET"])
def get_user_progress():
    """Get user's progress summary."""
    try:
        user = authenticate_request()
        if not user:
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        progress = quest_system.get_user_progress(user["username"])
        return jsonify(progress)
    except Exception as e:
        logger.error(f"Get progress error: {str(e)}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@app.route("/api/quest/daily", methods=["GET"])
def get_daily_quest():
    """Get user's daily quest."""
    try:
        user = authenticate_request()
        if not user:
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        # Check if user has a quest for today
        quest = quest_system.get_daily_quest(user["username"])
        
        if not quest:
            # Generate a new daily quest
            quest = quest_system.generate_daily_quest(user["username"])
        
        return jsonify(quest)
    except Exception as e:
        logger.error(f"Get daily quest error: {str(e)}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@app.route("/api/quest/complete", methods=["POST"])
def complete_quest():
    """Mark a quest as completed."""
    try:
        user = authenticate_request()
        if not user:
            return jsonify({"success": False, "error": "Authentication required"}), 401
        
        data = request.json
        quest_id = data.get("quest_id", "")
        
        if not quest_id:
            return jsonify({"success": False, "error": "Quest ID is required"}), 400
        
        result = quest_system.complete_quest(user["username"], quest_id)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Complete quest error: {str(e)}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


# Main route - redirect to login if not authenticated
@app.route("/")
def index():
    """Render the main page or redirect to login."""
    return redirect("/login")


# API endpoints
@app.route("/api/chat", methods=["POST"])
def chat():
    """Handle chat messages."""
    data = request.json
    message = data.get("message", "")
    user_name = data.get("user_name", "User")
    
    # Check authentication
    user = authenticate_request()
    if user:
        user_name = user["username"]
    
    if not message:
        return jsonify({"error": "No message provided"}), 400
    
    try:
        # If Jarvis is available, process the message
        if JARVIS_AVAILABLE:
            # Process the message
            jarvis = get_jarvis(user_name)
            
            # If user is authenticated, incorporate their goals/desires into responses
            if user:
                desires = user_auth.get_user_desires(user["username"])
                if desires:
                    # Add context about user's desires to help Jarvis provide more personalized responses
                    context_message = f"User desires: {desires}. User message: {message}"
                    response = jarvis.process_query(context_message)
                else:
                    response = jarvis.process_query(message)
            else:
                response = jarvis.process_query(message)
        else:
            # Simple fallback response if Jarvis is not available
            response = "I'm sorry, but the full Jarvis AI system is currently unavailable. However, I can still help you with basic tasks and your goals!"
        
        # Extract code blocks if any (only if response contains them)
        code_blocks = re.findall(r"```(?:(\w+))?\n(.*?)\n```", response, re.DOTALL)
        highlighted_blocks = []
        
        for lang, code in code_blocks:
            try:
                if lang:
                    lexer = lexers.get_lexer_by_name(lang)
                else:
                    lexer = lexers.guess_lexer(code)
            except ClassNotFound:
                lexer = lexers.get_lexer_by_name("text")
                
            formatter = formatters.HtmlFormatter(style="monokai")
            highlighted = pygments.highlight(code, lexer, formatter)
            highlighted_blocks.append({"code": code, "highlighted": highlighted, "language": lang or "text"})
        
        return jsonify({
            "success": True,
            "response": response,
            "code_blocks": highlighted_blocks
        })
    except Exception as e:
        logger.error(f"Error processing chat message: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Error processing your request: {str(e)}",
            "response": "I'm sorry, but I encountered an error while processing your request. Please try again."
        }), 500


@app.route("/api/code/edit", methods=["POST"])
def edit_code():
    """Edit code."""
    if not CODE_EDITOR_AVAILABLE:
        return jsonify({"error": "Code editor is not available"}), 500
        
    data = request.json
    file_path = data.get("file_path", "")
    content = data.get("content")
    
    if not file_path:
        return jsonify({"error": "No file path provided"}), 400
    
    if content is not None:
        # Write to file
        result = code_editor.write_file(file_path, content)
    else:
        # Read from file
        result = code_editor.read_file(file_path)
        
    return jsonify(result)


@app.route("/api/code/execute", methods=["POST"])
def execute_code():
    """Execute code."""
    if not CODE_EDITOR_AVAILABLE:
        return jsonify({"error": "Code editor is not available"}), 500
        
    data = request.json
    code = data.get("code", "")
    language = data.get("language", "python")
    
    if not code:
        return jsonify({"error": "No code provided"}), 400
    
    # Execute the code
    result = code_editor.execute_code(code, language)
    return jsonify(result)


@app.route("/api/code/diff", methods=["POST"])
def diff_code():
    """Compare two code snippets."""
    if not CODE_EDITOR_AVAILABLE:
        return jsonify({"error": "Code editor is not available"}), 500
        
    data = request.json
    original = data.get("original", "")
    modified = data.get("modified", "")
    
    if not original or not modified:
        return jsonify({"error": "Both original and modified code are required"}), 400
    
    # Calculate diff
    diff_result = code_editor.diff(original, modified)
    return jsonify({"diff": diff_result})


# Legacy dashboard route (system monitoring)
@app.route('/system-dashboard')
def system_dashboard():
    """Render the system monitoring dashboard."""
    return render_template("dashboard.html")


@app.route("/run")
def run():
    """Run a command via the web interface."""
    user_name = request.args.get("name", "User")
    if JARVIS_AVAILABLE:
        jarvis = get_jarvis(user_name)
    return render_template("index.html") if os.path.exists(os.path.join(templates_dir, "index.html")) else "Index page not available"


def run_web_server(host="127.0.0.1", port=5000, user_name="User"):
    """
    Start the web server.
    
    Args:
        host: Host to bind to
        port: Port to bind to 
        user_name: Default user name for Jarvis
    
    Returns:
        Exit code
    """
    try:
        logger.info(f"Starting Jarvis web server on {host}:{port}")
        logger.info(f"Access the application at: http://{host}:{port}")
        logger.info("Press Ctrl+C to stop the server")
        
        app.run(host=host, port=port, debug=False)
        return 0
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        return 0
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        return 1


# Legacy system monitoring endpoint
@app.route('/dashboard')
def legacy_dashboard():
    """Legacy dashboard endpoint for system monitoring."""
    if request.content_type == 'application/json':
        # API request for data
        try:
            from .tools.system_monitor import SystemMonitorTool
            monitor = SystemMonitorTool()
            
            # Get system status
            cpu_status = monitor.get_cpu_usage()
            memory_status = monitor.get_memory_usage()
            disk_status = monitor.get_disk_usage()
            temp_status = monitor.get_temperature()
            
            return jsonify({
                'cpu': cpu_status,
                'memory': memory_status,
                'disk': disk_status,
                'temperature': temp_status,
                'history': {
                    'cpu': [{'timestamp': datetime.now().isoformat(), 'percent': cpu_status.get('cpu_percent', 0)}],
                    'memory': [{'timestamp': datetime.now().isoformat(), 'percent': memory_status.get('percent', 0)}],
                    'disk': [{'timestamp': datetime.now().isoformat(), 'percent': disk_status.get('disks', [{}])[0].get('percent', 0) if disk_status.get('disks') else 0}],
                    'temperature': [{'timestamp': datetime.now().isoformat(), 'value': 0}]
                }
            })
        except Exception as e:
            logger.error(f"System monitoring error: {str(e)}")
            return jsonify({'error': str(e)}), 500
    else:
        # HTML request for dashboard page
        return render_template("dashboard.html") 