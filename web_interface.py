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

from flask import Flask, render_template, request, jsonify, send_from_directory, session, redirect, url_for
import pygments
from pygments import lexers, formatters
from pygments.util import ClassNotFound

from .jarvis import Jarvis
from .tools.code_editor import CodeEditorTool

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), "templates"))
app.secret_key = os.urandom(24)  # Required for session management

# Initialize Jarvis
jarvis_instance = None
code_editor = CodeEditorTool()

# Sample categories for dashboard
DASHBOARD_CATEGORIES = {
    "Start Quests": [
        "Available Quests",
        "Active Quests",
        "Completed Quests",
        "Quest History"
    ],
    "Stats & Skills": [
        "Character Stats",
        "Skill Tree",
        "Experience Points",
        "Achievements"
    ],
    "Inventory": [
        "Equipment",
        "Items",
        "Resources",
        "Storage"
    ],
    "Logbook": [
        "Quest Log",
        "System Messages",
        "Notifications",
        "History"
    ],
    "Settings": [
        "User Profile",
        "Preferences",
        "System Settings",
        "Help & Support"
    ]
}

def get_jarvis(user_name="User"):
    """Get or create a Jarvis instance."""
    global jarvis_instance
    if jarvis_instance is None:
        jarvis_instance = Jarvis(user_name=user_name)
    return jarvis_instance

# Create templates directory if it doesn't exist
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
os.makedirs(templates_dir, exist_ok=True)

# ... existing code ...

@app.route("/")
def index():
    """Render the index page."""
    if "username" not in session:
        session["username"] = "User"  # Set default username
    return redirect(url_for("dashboard"))

@app.route("/dashboard")
def dashboard():
    """Render the dashboard page."""
    if request.content_type == 'application/json':
        # API request for data
        from jarvis.tools.system_monitor import system_monitor
        try:
            system_status = system_monitor.get_system_status()
            
            # ... existing system status code ...
            
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
        return render_template('dashboard.html', 
                            categories=DASHBOARD_CATEGORIES,
                            session=session)

@app.route("/logout")
def logout():
    """Handle user logout."""
    session.clear()
    return redirect(url_for("index"))

# ... rest of the existing code ... 