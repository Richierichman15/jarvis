"""
Web interface for Jarvis.
This module provides a simple web-based interface for interacting with Jarvis.
System functionality has been removed - this is now a clean AI assistant interface.
"""
import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from flask import Flask, request, jsonify
from dotenv import load_dotenv

from .jarvis import Jarvis

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app (no templates)
app = Flask(__name__)
app.secret_key = os.urandom(24)

# Initialize Jarvis
jarvis_instance = None

def get_jarvis(username: str = "default") -> Jarvis:
    """Get or create Jarvis instance for user."""
    global jarvis_instance
    if jarvis_instance is None:
        jarvis_instance = Jarvis()
    return jarvis_instance

@app.route('/')
def index():
    """Simple API endpoint to check if Jarvis is running."""
    return jsonify({
        "status": "Jarvis is running",
        "message": "Welcome to Jarvis AI Assistant",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    """Chat endpoint for interacting with Jarvis."""
    try:
        data = request.get_json()
        user_input = data.get('message', '')
        username = data.get('username', 'default')
        
        if not user_input:
            return jsonify({"error": "No message provided"}), 400
        
        # Get Jarvis instance
        jarvis = get_jarvis(username)
        
        # Get response from Jarvis
        response = jarvis.chat(user_input)
        
        return jsonify({
            "response": response,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get Jarvis stats."""
    try:
        username = request.args.get('username', 'default')
        jarvis = get_jarvis(username)
        
        return jsonify({
            "stats": jarvis.stats,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """Get current tasks."""
    try:
        username = request.args.get('username', 'default')
        jarvis = get_jarvis(username)
        
        tasks = [task.to_dict() if hasattr(task, 'to_dict') else task for task in jarvis.tasks]
        return jsonify({
            "tasks": tasks,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting tasks: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/tasks', methods=['POST'])
def add_task():
    """Add a new task."""
    try:
        data = request.get_json()
        username = data.get('username', 'default')
        
        # Create task using Jarvis
        task_name = data.get('name', '')
        task_description = data.get('description', '')
        task_difficulty = data.get('difficulty', 'E')
        task_reward = data.get('reward', 10)
        
        if not task_name:
            return jsonify({"error": "Task name is required"}), 400
        
        # Get Jarvis instance and add task
        jarvis = get_jarvis(username)
        jarvis.add_task(task_name, task_description, task_difficulty, task_reward)
        
        return jsonify({
            "message": "Task added successfully",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error adding task: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/tasks/<int:task_id>/complete', methods=['POST'])
def complete_task(task_id):
    """Complete a task."""
    try:
        data = request.get_json() or {}
        username = data.get('username', 'default')
        jarvis = get_jarvis(username)
        
        if task_id < 1 or task_id > len(jarvis.tasks):
            return jsonify({"error": "Invalid task ID"}), 400
        
        # Complete the task
        result = jarvis.complete_task(task_id)
        
        return jsonify({
            "message": "Task completed successfully",
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error completing task: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("Starting Jarvis Web Interface")
    print("System functionality has been removed - Jarvis is now a clean AI assistant")
    app.run(host='127.0.0.1', port=5000, debug=True)