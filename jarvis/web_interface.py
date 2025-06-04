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

from flask import Flask, render_template, request, jsonify, send_from_directory
import pygments
from pygments import lexers, formatters
from pygments.util import ClassNotFound

from .jarvis import Jarvis
from .tools.code_editor import CodeEditorTool
from .firebase_service import get_firebase_service

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), "templates"))

# Initialize Jarvis and Firebase
jarvis_instance = None
code_editor = CodeEditorTool()
firebase_service = get_firebase_service()

# Initialize Firebase on startup
@app.before_first_request
def initialize_firebase():
    """Initialize Firebase service when the app starts."""
    firebase_service.initialize()


def get_jarvis(user_name="User"):
    """Get or create a Jarvis instance."""
    global jarvis_instance
    if jarvis_instance is None:
        jarvis_instance = Jarvis(user_name=user_name)
    return jarvis_instance


# Create templates directory if it doesn't exist
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
os.makedirs(templates_dir, exist_ok=True)


# Create HTML templates
@app.route("/")
def index():
    """Render the index page."""
    return render_template("index.html")


# API endpoints
@app.route("/api/chat", methods=["POST"])
def chat():
    """Handle chat messages."""
    data = request.json
    message = data.get("message", "")
    user_name = data.get("user_name", "User")
    
    if not message:
        return jsonify({"error": "No message provided"}), 400
    
    try:
        # Process the message
        jarvis = get_jarvis(user_name)
        response = jarvis.process_query(message)
        
        # Extract code blocks if any
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
    data = request.json
    original = data.get("original", "")
    modified = data.get("modified", "")
    
    if not original or not modified:
        return jsonify({"error": "Both original and modified code are required"}), 400
    
    # Calculate diff
    diff_result = code_editor.diff(original, modified)
    return jsonify({"diff": diff_result})


# Firebase notification API endpoints
@app.route("/api/firebase-config", methods=["GET"])
def get_firebase_config():
    """Get Firebase configuration for frontend."""
    try:
        config = firebase_service.get_config()
        return jsonify(config)
    except Exception as e:
        logger.error(f"Error getting Firebase config: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/save-notification-token", methods=["POST"])
def save_notification_token():
    """Save FCM token for a user."""
    try:
        data = request.json
        token = data.get("token")
        user_id = data.get("userId", "default_user")
        
        if not token:
            return jsonify({"success": False, "error": "No token provided"}), 400
        
        success = firebase_service.save_user_token(user_id, token)
        
        if success:
            return jsonify({"success": True, "message": "Token saved successfully"})
        else:
            return jsonify({"success": False, "error": "Failed to save token"}), 500
            
    except Exception as e:
        logger.error(f"Error saving notification token: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/send-notification", methods=["POST"])
def send_notification():
    """Send a notification to a user."""
    try:
        data = request.json
        user_id = data.get("userId", "default_user")
        title = data.get("title", "")
        message = data.get("message", "")
        delay = data.get("delay", 0)  # in seconds
        
        if not title or not message:
            return jsonify({"success": False, "error": "Title and message are required"}), 400
        
        success = firebase_service.send_notification(
            user_id, title, message, 
            data={"type": "custom"}, 
            delay_seconds=delay
        )
        
        if success:
            return jsonify({"success": True, "message": "Notification sent successfully"})
        else:
            return jsonify({"success": False, "error": "Failed to send notification"}), 500
            
    except Exception as e:
        logger.error(f"Error sending notification: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/add-xp", methods=["POST"])
def add_xp():
    """Add XP to a user."""
    try:
        data = request.json
        user_id = data.get("userId", "default_user")
        amount = data.get("amount", 0)
        reason = data.get("reason", "")
        
        if amount <= 0:
            return jsonify({"success": False, "error": "Amount must be greater than 0"}), 400
        
        result = firebase_service.add_user_xp(user_id, amount, reason)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error adding XP: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/load-progress", methods=["POST"])
def load_progress():
    """Load user progress."""
    try:
        data = request.json
        user_id = data.get("userId", "default_user")
        
        result = firebase_service.get_user_progress(user_id)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error loading progress: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/save-progress", methods=["POST"])
def save_progress():
    """Save user progress."""
    try:
        data = request.json
        user_id = data.get("userId", "default_user")
        progress = data.get("progress", {})
        
        success = firebase_service.save_user_progress(user_id, progress)
        
        if success:
            return jsonify({"success": True, "message": "Progress saved successfully"})
        else:
            return jsonify({"success": False, "error": "Failed to save progress"}), 500
            
    except Exception as e:
        logger.error(f"Error saving progress: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/create-side-quest", methods=["POST"])
def create_side_quest():
    """Create a side quest for a user."""
    try:
        data = request.json
        user_id = data.get("userId", "default_user")
        title = data.get("title", "")
        description = data.get("description", "")
        xp_reward = data.get("xpReward", 50)
        difficulty = data.get("difficulty", "medium")
        
        if not title or not description:
            return jsonify({"success": False, "error": "Title and description are required"}), 400
        
        success = firebase_service.create_side_quest(
            user_id, title, description, xp_reward, difficulty
        )
        
        if success:
            return jsonify({"success": True, "message": "Side quest created successfully"})
        else:
            return jsonify({"success": False, "error": "Failed to create side quest"}), 500
            
    except Exception as e:
        logger.error(f"Error creating side quest: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/send-reminder", methods=["POST"])
def send_reminder():
    """Send a reminder notification."""
    try:
        data = request.json
        user_id = data.get("userId", "default_user")
        message = data.get("message", "")
        delay_minutes = data.get("delayMinutes", 60)
        
        if not message:
            return jsonify({"success": False, "error": "Message is required"}), 400
        
        success = firebase_service.send_reminder(user_id, message, delay_minutes)
        
        if success:
            return jsonify({"success": True, "message": "Reminder scheduled successfully"})
        else:
            return jsonify({"success": False, "error": "Failed to schedule reminder"}), 500
            
    except Exception as e:
        logger.error(f"Error sending reminder: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/send-engagement", methods=["POST"])
def send_engagement():
    """Send an engagement notification."""
    try:
        data = request.json
        user_id = data.get("userId", "default_user")
        
        success = firebase_service.send_engagement_notification(user_id)
        
        if success:
            return jsonify({"success": True, "message": "Engagement notification sent successfully"})
        else:
            return jsonify({"success": False, "error": "Failed to send engagement notification"}), 500
            
    except Exception as e:
        logger.error(f"Error sending engagement notification: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/sync-progress", methods=["POST"])
def sync_progress():
    """Sync progress in background (for service worker)."""
    try:
        # This endpoint is called by the service worker for background sync
        # For now, just return success
        return jsonify({"success": True, "message": "Progress synced"})
        
    except Exception as e:
        logger.error(f"Error syncing progress: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/notification")
def notification_page():
    """Serve the notification page."""
    return render_template("notification.html")


# Create a simple HTML template for the index page
index_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Jarvis AI Assistant</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
            color: #333;
        }
        .container {
            display: flex;
            height: 100vh;
        }
        .chat-panel {
            flex: 1;
            display: flex;
            flex-direction: column;
            border-right: 1px solid #ccc;
        }
        .code-panel {
            flex: 1;
            display: flex;
            flex-direction: column;
        }
        .chat-messages {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
            background-color: #fff;
        }
        .chat-input {
            padding: 10px;
            background-color: #f0f0f0;
            border-top: 1px solid #ccc;
        }
        .message {
            margin-bottom: 15px;
            padding: 10px;
            border-radius: 5px;
        }
        .user-message {
            background-color: #dcf8c6;
            align-self: flex-end;
        }
        .jarvis-message {
            background-color: #f0f0f0;
        }
        .code-editor {
            flex: 1;
            display: flex;
            flex-direction: column;
        }
        .code-toolbar {
            padding: 10px;
            background-color: #f0f0f0;
            border-bottom: 1px solid #ccc;
        }
        .code-area {
            flex: 1;
            padding: 0;
        }
        #code-textarea {
            width: 100%;
            height: 100%;
            border: none;
            padding: 10px;
            font-family: monospace;
            font-size: 14px;
            resize: none;
        }
        .code-output {
            height: 150px;
            overflow-y: auto;
            padding: 10px;
            background-color: #2d2d2d;
            color: #f0f0f0;
            font-family: monospace;
            font-size: 14px;
            white-space: pre-wrap;
        }
        input, button, select {
            padding: 8px;
            margin: 5px;
        }
        input[type="text"] {
            flex: 1;
        }
        button {
            background-color: #4CAF50;
            color: white;
            border: none;
            cursor: pointer;
        }
        button:hover {
            background-color: #45a049;
        }
        pre {
            background-color: #f0f0f0;
            padding: 10px;
            border-radius: 5px;
            overflow-x: auto;
        }
        code {
            font-family: monospace;
        }
        .highlighted-code {
            margin: 10px 0;
        }
    </style>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/10.7.2/styles/atom-one-dark.min.css">
</head>
<body>
    <div class="container">
        <div class="chat-panel">
            <div class="chat-messages" id="chat-messages"></div>
            <div class="chat-input">
                <form id="chat-form">
                    <div style="display: flex;">
                        <input type="text" id="chat-input" placeholder="Type your message here...">
                        <button type="submit">Send</button>
                    </div>
                </form>
            </div>
        </div>
        <div class="code-panel">
            <div class="code-toolbar">
                <div style="display: flex; justify-content: space-between;">
                    <div>
                        <input type="text" id="file-path" placeholder="File path">
                        <button id="load-btn">Load</button>
                        <button id="save-btn">Save</button>
                    </div>
                    <div>
                        <select id="language-select">
                            <option value="python">Python</option>
                            <option value="javascript">JavaScript</option>
                            <option value="bash">Bash</option>
                            <option value="ruby">Ruby</option>
                            <option value="perl">Perl</option>
                        </select>
                        <button id="run-btn">Run</button>
                    </div>
                </div>
            </div>
            <div class="code-area">
                <textarea id="code-textarea" placeholder="Write or paste your code here..."></textarea>
            </div>
            <div class="code-output" id="code-output"></div>
        </div>
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const chatMessages = document.getElementById('chat-messages');
            const chatForm = document.getElementById('chat-form');
            const chatInput = document.getElementById('chat-input');
            const codeTextarea = document.getElementById('code-textarea');
            const filePathInput = document.getElementById('file-path');
            const loadBtn = document.getElementById('load-btn');
            const saveBtn = document.getElementById('save-btn');
            const runBtn = document.getElementById('run-btn');
            const languageSelect = document.getElementById('language-select');
            const codeOutput = document.getElementById('code-output');
            
            let userName = localStorage.getItem('jarvis_user_name') || 'User';
            // Ask for user name if not set
            if (!localStorage.getItem('jarvis_user_name')) {
                userName = prompt('How should Jarvis address you?', 'User');
                localStorage.setItem('jarvis_user_name', userName);
            }
            
            // Add welcome message
            addMessage('Welcome to Jarvis AI Assistant! How can I help you today?', 'jarvis');
            
            // Handle chat form submission
            chatForm.addEventListener('submit', function(e) {
                e.preventDefault();
                const message = chatInput.value.trim();
                if (message) {
                    addMessage(message, 'user');
                    chatInput.value = '';
                    
                    fetch('/api/chat', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            message: message,
                            user_name: userName
                        })
                    })
                    .then(response => response.json())
                    .then(data => {
                        addMessage(data.response, 'jarvis', data.code_blocks);
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        addMessage('Sorry, there was an error processing your request.', 'jarvis');
                    });
                }
            });
            
            // Handle load button
            loadBtn.addEventListener('click', function() {
                const filePath = filePathInput.value.trim();
                if (filePath) {
                    fetch('/api/code/edit', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            file_path: filePath
                        })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            codeTextarea.value = data.content;
                            // Try to determine language from file extension
                            if (filePath) {
                                const ext = filePath.split('.').pop().toLowerCase();
                                if (ext === 'py') languageSelect.value = 'python';
                                else if (ext === 'js') languageSelect.value = 'javascript';
                                else if (ext === 'rb') languageSelect.value = 'ruby';
                                else if (ext === 'sh' || ext === 'bash') languageSelect.value = 'bash';
                                else if (ext === 'pl') languageSelect.value = 'perl';
                            }
                            codeOutput.textContent = `File ${filePath} loaded successfully.`;
                        } else {
                            codeOutput.textContent = `Error: ${data.error}`;
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        codeOutput.textContent = `Error: ${error.message}`;
                    });
                } else {
                    codeOutput.textContent = 'Please enter a file path.';
                }
            });
            
            // Handle save button
            saveBtn.addEventListener('click', function() {
                const filePath = filePathInput.value.trim();
                const code = codeTextarea.value;
                if (filePath) {
                    fetch('/api/code/edit', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            file_path: filePath,
                            content: code
                        })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            codeOutput.textContent = `File ${filePath} saved successfully.`;
                        } else {
                            codeOutput.textContent = `Error: ${data.error}`;
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        codeOutput.textContent = `Error: ${error.message}`;
                    });
                } else {
                    codeOutput.textContent = 'Please enter a file path.';
                }
            });
            
            // Handle run button
            runBtn.addEventListener('click', function() {
                const code = codeTextarea.value;
                const language = languageSelect.value;
                if (code) {
                    codeOutput.textContent = 'Running code...';
                    fetch('/api/code/execute', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            code: code,
                            language: language
                        })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            codeOutput.textContent = data.output || 'Execution successful (no output).';
                        } else {
                            codeOutput.textContent = `Error: ${data.error}`;
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        codeOutput.textContent = `Error: ${error.message}`;
                    });
                } else {
                    codeOutput.textContent = 'Please enter some code to run.';
                }
            });
            
            // Function to add a message to the chat
            function addMessage(message, sender, codeBlocks = []) {
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${sender}-message`;
                
                // Process markdown-style code blocks in the message
                let processedMessage = message;
                
                // Replace code blocks with placeholders
                const codeBlockPlaceholders = [];
                processedMessage = processedMessage.replace(/```(\w+)?\n([\s\S]*?)\n```/g, function(match, lang, code) {
                    const placeholder = `__CODE_BLOCK_${codeBlockPlaceholders.length}__`;
                    codeBlockPlaceholders.push({ lang, code });
                    return placeholder;
                });
                
                // Convert markdown style formatting
                processedMessage = processedMessage
                    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                    .replace(/\*(.*?)\*/g, '<em>$1</em>')
                    .replace(/`([^`]+)`/g, '<code>$1</code>')
                    .replace(/\\n/g, '<br>')
                    .replace(/\n/g, '<br>');
                
                // Replace the placeholders with actual code blocks
                codeBlockPlaceholders.forEach((block, index) => {
                    const placeholder = `__CODE_BLOCK_${index}__`;
                    const codeHtml = `<div class="highlighted-code"><pre><code class="${block.lang || ''}">${escapeHtml(block.code)}</code></pre></div>`;
                    processedMessage = processedMessage.replace(placeholder, codeHtml);
                });
                
                messageDiv.innerHTML = processedMessage;
                
                // Add pre-processed highlighted code blocks if provided
                if (codeBlocks && codeBlocks.length > 0) {
                    codeBlocks.forEach(block => {
                        if (block.highlighted) {
                            const codeDiv = document.createElement('div');
                            codeDiv.className = 'highlighted-code';
                            codeDiv.innerHTML = block.highlighted;
                            messageDiv.appendChild(codeDiv);
                            
                            // Add a button to copy code to editor
                            const copyBtn = document.createElement('button');
                            copyBtn.innerText = 'Copy to Editor';
                            copyBtn.style.fontSize = '12px';
                            copyBtn.style.padding = '3px 6px';
                            copyBtn.style.marginTop = '5px';
                            copyBtn.addEventListener('click', function() {
                                codeTextarea.value = block.code;
                                if (block.language) {
                                    // Try to set the language selector
                                    const lang = block.language.toLowerCase();
                                    if (lang === 'python' || lang === 'py') languageSelect.value = 'python';
                                    else if (lang === 'javascript' || lang === 'js') languageSelect.value = 'javascript';
                                    else if (lang === 'ruby' || lang === 'rb') languageSelect.value = 'ruby';
                                    else if (lang === 'bash' || lang === 'sh') languageSelect.value = 'bash';
                                    else if (lang === 'perl' || lang === 'pl') languageSelect.value = 'perl';
                                }
                            });
                            codeDiv.appendChild(copyBtn);
                        }
                    });
                }
                
                chatMessages.appendChild(messageDiv);
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
            
            // Helper function to escape HTML
            function escapeHtml(unsafe) {
                return unsafe
                    .replace(/&/g, "&amp;")
                    .replace(/</g, "&lt;")
                    .replace(/>/g, "&gt;")
                    .replace(/"/g, "&quot;")
                    .replace(/'/g, "&#039;");
            }
        });
    </script>
</body>
</html>
"""

# Write the template file
with open(os.path.join(templates_dir, "index.html"), "w") as f:
    f.write(index_html)


@app.route("/run")
def run():
    """Run the web server."""
    user_name = request.args.get("name", "User")
    get_jarvis(user_name)
    return render_template("index.html")


def run_web_server(host="127.0.0.1", port=5000, user_name="User"):
    """Run the web server."""
    # Initialize Jarvis
    get_jarvis(user_name)
    
    print(f"\nStarting Jarvis web interface at http://{host}:{port}")
    print(f"Press Ctrl+C to stop the server")
    
    # Run the Flask app
    app.run(host=host, port=port, debug=True)


# Command to run the web interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Start the Jarvis web interface")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5000, help="Port to bind to")
    parser.add_argument("--name", default="User", help="How Jarvis should address you")
    
    args = parser.parse_args()
    
    # Run the web server
    run_web_server(host=args.host, port=args.port, user_name=args.name)


@app.route('/dashboard')
def dashboard():
    if request.content_type == 'application/json':
        # API request for data
        from jarvis.tools.system_monitor import system_monitor
        try:
            system_status = system_monitor.get_system_status()
            
            # Ensure CPU data is properly structured
            if not system_status.get("cpu", {}).get("success", False):
                system_status["cpu"] = {
                    "success": True,
                    "cpu_percent": 0,
                    "cpu_count": 1,
                    "per_cpu_percent": [0],
                    "top_processes": []
                }
            
            # Ensure memory data is properly structured
            if not system_status.get("memory", {}).get("success", False):
                system_status["memory"] = {
                    "success": True,
                    "percent": 0,
                    "total_gb": 0,
                    "available_gb": 0,
                    "used_gb": 0
                }
            
            # Ensure disk data is properly structured
            if not system_status.get("disk", {}).get("success", False) or not system_status.get("disk", {}).get("disks"):
                system_status["disk"] = {
                    "success": True,
                    "disks": [{"mountpoint": "/", "percent": 0, "total_gb": 0, "used_gb": 0, "free_gb": 0}],
                    "io_stats": {}
                }
                
            # Ensure temperature data is properly structured
            if not system_status.get("temperature", {}).get("success", False) or not system_status.get("temperature", {}).get("temperatures"):
                system_status["temperature"] = {
                    "success": True,
                    "temperatures": {"system": [{"label": "System", "current": 0}]}
                }
                
            # Add history for charts
            if "history" not in system_status:
                system_status["history"] = {
                    "cpu": [{"timestamp": datetime.now().isoformat(), "percent": system_status["cpu"].get("cpu_percent", 0)}],
                    "memory": [{"timestamp": datetime.now().isoformat(), "percent": system_status["memory"].get("percent", 0)}],
                    "disk": [{"timestamp": datetime.now().isoformat(), "percent": system_status["disk"]["disks"][0].get("percent", 0)}],
                    "temperature": [{"timestamp": datetime.now().isoformat(), "value": system_status["temperature"]["temperatures"]["system"][0].get("current", 0)}]
                }
                
            return jsonify(system_status)
        except Exception as e:
            logger.error(f"Error getting system status: {str(e)}")
            # Return basic data structure with error info
            return jsonify({
                "error": str(e),
                "cpu": {"success": True, "cpu_percent": 0},
                "memory": {"success": True, "percent": 0},
                "disk": {"success": True, "disks": [{"percent": 0}]},
                "temperature": {"success": True, "temperatures": {"system": [{"current": 0}]}},
                "history": {
                    "cpu": [{"timestamp": datetime.now().isoformat(), "percent": 0}],
                    "memory": [{"timestamp": datetime.now().isoformat(), "percent": 0}],
                    "disk": [{"timestamp": datetime.now().isoformat(), "percent": 0}],
                    "temperature": [{"timestamp": datetime.now().isoformat(), "value": 0}]
                }
            })
    else:
        # HTML request for dashboard page
        return render_template('dashboard.html') 