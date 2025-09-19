from flask import Flask, jsonify, request
from jarvis import Jarvis
import os
from datetime import datetime
import json
from dotenv import load_dotenv
import argparse

# Load environment variables
load_dotenv()

# Initialize Flask app (simplified - no templates)
app = Flask(__name__)
app.secret_key = os.urandom(24)

# Memory file path
MEMORY_FILE = os.path.join(os.path.dirname(__file__), 'jarvis_memory.json')

# Initialize Jarvis instance
jarvis = Jarvis()

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
        
        if not user_input:
            return jsonify({"error": "No message provided"}), 400
        
        # Get response from Jarvis
        response = jarvis.chat(user_input)
        
        return jsonify({
            "response": response,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get Jarvis stats."""
    try:
        return jsonify({
            "stats": jarvis.stats,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """Get current tasks."""
    try:
        tasks = [task.to_dict() if hasattr(task, 'to_dict') else task for task in jarvis.tasks]
        return jsonify({
            "tasks": tasks,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/tasks', methods=['POST'])
def add_task():
    """Add a new task."""
    try:
        data = request.get_json()
        
        # Create task using Jarvis
        task_name = data.get('name', '')
        task_description = data.get('description', '')
        task_difficulty = data.get('difficulty', 'E')
        task_reward = data.get('reward', 10)
        
        if not task_name:
            return jsonify({"error": "Task name is required"}), 400
        
        # Add task to Jarvis
        jarvis.add_task(task_name, task_description, task_difficulty, task_reward)
        
        return jsonify({
            "message": "Task added successfully",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/tasks/<int:task_id>/complete', methods=['POST'])
def complete_task(task_id):
    """Complete a task."""
    try:
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
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Jarvis AI Assistant API Server')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    print(f"Starting Jarvis API server on {args.host}:{args.port}")
    print("System functionality has been removed - Jarvis is now a clean AI assistant")
    
    app.run(host=args.host, port=args.port, debug=args.debug)