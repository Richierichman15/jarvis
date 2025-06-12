"""
Web interface for Jarvis.
This module provides a simple web-based interface for interacting with Jarvis.
"""
import os
import re
import sys
import json
import logging
import hashlib
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime

from flask import Flask, render_template, request, jsonify, send_from_directory, session, redirect, url_for
import pygments
from pygments import lexers, formatters
from pygments.util import ClassNotFound
from dotenv import load_dotenv

from .jarvis import Jarvis
from .tools.code_editor import CodeEditorTool

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), "templates"))
app.secret_key = os.urandom(24)  # Required for session management

# Initialize Jarvis
jarvis_instance = None
code_editor = CodeEditorTool()

# Get admin credentials from environment variables
ADMIN_USERNAME = os.getenv('ADMIN', 'buck')
ADMIN_PASSWORD = os.getenv('ADMINPASSWORD', 'nasty')

# User data file paths
USERS_FILE = os.path.join(os.path.dirname(__file__), 'data', 'users.json')
SESSIONS_FILE = os.path.join(os.path.dirname(__file__), 'data', 'sessions.json')

def load_users():
    """Load users from JSON file."""
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    """Save users to JSON file."""
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def hash_password(password):
    """Hash password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def is_authenticated():
    """Check if user is authenticated."""
    return 'username' in session

def require_auth(f):
    """Decorator to require authentication."""
    def decorated(*args, **kwargs):
        if not is_authenticated():
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated

@app.route('/')
def index():
    """Render the index page."""
    if is_authenticated():
        return redirect(url_for('start_menu'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Check admin credentials
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['username'] = username
            session['role'] = 'admin'
            
            # Check if user exists in users.json
            users = load_users()
            if username not in users:
                # First time login, redirect to welcome page
                return redirect(url_for('welcome'))
            return redirect(url_for('start_menu'))
            
        # Check regular user credentials
        users = load_users()
        if username in users and users[username]['password_hash'] == hash_password(password):
            session['username'] = username
            session['role'] = users[username].get('role', 'user')
            return redirect(url_for('start_menu'))
            
        return render_template('login.html', error='Invalid credentials')
        
    return render_template('login.html')

@app.route('/welcome')
@require_auth
def welcome():
    """Show welcome page with three questions."""
    return render_template('welcome.html')

@app.route('/api/save-desires', methods=['POST'])
@require_auth
def save_desires():
    """Save user's desires and generate initial stats."""
    data = request.json
    desires = data.get('desires')
    
    if not desires:
        return jsonify({'success': False, 'error': 'No desires provided'})
    
    # Save desires to user data
    users = load_users()
    username = session['username']
    
    if username not in users:
        users[username] = {
            'password_hash': hash_password(ADMIN_PASSWORD) if username == ADMIN_USERNAME else None,
            'role': session.get('role', 'user'),
            'created_at': datetime.utcnow().isoformat(),
            'desires': desires
        }
    else:
        users[username]['desires'] = desires
    
    save_users(users)
    
    # Initialize Jarvis instance with user's desires
    jarvis = get_jarvis(username)
    jarvis.initialize_user_profile(desires)
    
    return jsonify({'success': True})

@app.route('/start-menu')
@require_auth
def start_menu():
    """Show the start menu."""
    return render_template('start_menu.html', 
                         stats=get_jarvis(session['username']).stats,
                         categories=DASHBOARD_CATEGORIES)

@app.route('/logout')
def logout():
    """Handle user logout."""
    session.clear()
    return redirect(url_for('login'))

# ... rest of your existing routes ... 