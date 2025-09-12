from flask import Flask, render_template, jsonify, request, session, redirect, url_for, flash
from jarvis import Jarvis
import os
from datetime import datetime, timedelta
import json
import firebase_admin
from firebase_admin import credentials, messaging
from dotenv import load_dotenv
import hashlib
import argparse

# Load environment variables
load_dotenv()

# Import the daily quest system
from jarvis.daily_quest_system import DailyQuestGenerator

# Required Firebase environment variables
REQUIRED_FIREBASE_VARS = [
    "FIREBASE_TYPE",
    "FIREBASE_PROJECT_ID",
    "FIREBASE_PRIVATE_KEY_ID",
    "FIREBASE_PRIVATE_KEY",
    "FIREBASE_CLIENT_EMAIL",
    "FIREBASE_CLIENT_ID",
    "FIREBASE_AUTH_URI",
    "FIREBASE_TOKEN_URI",
    "FIREBASE_AUTH_PROVIDER_X509_CERT_URL",
    "FIREBASE_CLIENT_X509_CERT_URL",
    "VAPIDKEY" 
]

app = Flask(__name__, 
           template_folder='jarvis/templates',
           static_folder='jarvis/static')
# Configure session to be permanent and last for 30 days
app.secret_key = os.getenv('FLASK_SECRET_KEY', os.urandom(24))
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV') == 'production'
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Initialize Firebase Admin with credentials from environment variables
firebase_enabled = False  # Flag to track if Firebase is properly initialized

# Admin credentials from .env
ADMIN_USERNAME = os.getenv('ADMIN')
ADMIN_PASSWORD = os.getenv('ADMINPASSWORD')

# Memory file path
MEMORY_FILE = os.path.join(os.path.dirname(__file__), 'jarvis_memory.json')

def validate_firebase_env():
    """Validate that all required Firebase environment variables are present"""
    missing_vars = [var for var in REQUIRED_FIREBASE_VARS if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"Missing required Firebase environment variables: {', '.join(missing_vars)}")

try:
    # Validate environment variables
    validate_firebase_env()
    
    # Create credentials dictionary
    firebase_creds = {
        "type": os.getenv("FIREBASE_TYPE"),
        "project_id": os.getenv("FIREBASE_PROJECT_ID"),
        "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
        "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace("\\n", "\n"),
        "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
        "client_id": os.getenv("FIREBASE_CLIENT_ID"),
        "auth_uri": os.getenv("FIREBASE_AUTH_URI"),
        "token_uri": os.getenv("FIREBASE_TOKEN_URI"),
        "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_X509_CERT_URL"),
        "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_X509_CERT_URL")
    }
    
    cred = credentials.Certificate(firebase_creds)
    firebase_admin.initialize_app(cred)
    firebase_enabled = True
    print("✅ Firebase Admin SDK initialized successfully!")
except ValueError as ve:
    print(f"⚠️  Firebase initialization skipped: {str(ve)}")
except Exception as e:
    print(f"❌ Error initializing Firebase Admin SDK: {str(e)}")

system = Jarvis()  # Initialize our System

# Initialize the daily quest system
daily_quest_system = DailyQuestGenerator(system)

def load_memory():
    """Load memory from JSON file"""
    try:
        # Create memory directory if it doesn't exist
        os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)
        
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, 'r') as f:
                data = json.load(f)
                if not isinstance(data, dict):
                    data = {}
                if 'users' not in data:
                    data['users'] = {}
                if 'tasks' not in data:
                    data['tasks'] = []
                if 'conversation_history' not in data:
                    data['conversation_history'] = []
                return data
    except Exception as e:
        print(f"Error loading memory: {e}")
    return {"users": {}, "tasks": [], "conversation_history": []}

def save_memory(data):
    """Save memory to JSON file"""
    try:
        # Create memory directory if it doesn't exist
        os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)
        with open(MEMORY_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving memory: {e}")

def is_authenticated():
    """Check if user is authenticated"""
    return 'username' in session

def require_auth(f):
    """Decorator to require authentication"""
    def decorated(*args, **kwargs):
        if not is_authenticated():
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated

# Register notification callback for Firebase notifications
def send_firebase_notification(notification_data):
    """Send Firebase notification"""
    if firebase_enabled and 'fcm_token' in session:
        try:
            result = send_notification(
                token=session['fcm_token'],
                title=notification_data.get('title', 'System Notification'),
                body=notification_data.get('message', ''),
                data={
                    'type': notification_data.get('type', ''),
                    'notification_time': notification_data.get('notification_time', ''),
                    'redirect_url': url_for('show_notification', notification_type=notification_data.get('type', 'quest').lower().replace(' ', '_'))
                }
            )
            print(f"Notification sent: {result}")
        except Exception as e:
            print(f"Error sending Firebase notification: {e}")

daily_quest_system.register_notification_callback(send_firebase_notification)

# Start the notification scheduler
daily_quest_system.schedule_daily_notifications()

# Dashboard categories
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

# Store notifications in memory (you might want to move this to a database in production)
notifications = []

class AttrDict:
    def __init__(self, d):
        self._data = {}
        for k, v in d.items():
            if isinstance(v, dict):
                self._data[k] = AttrDict(v)
            elif isinstance(v, list):
                self._data[k] = [AttrDict(x) if isinstance(x, dict) else x for x in v]
            else:
                self._data[k] = v

    def __getattr__(self, name):
        try:
            return self._data[name]
        except KeyError:
            return None

    def __len__(self):
        return len(self._data)

    def items(self):
        return self._data.items()

    def __getitem__(self, key):
        return self._data[key]

    def get(self, key, default=None):
        return self._data.get(key, default)

@app.before_request
def before_request():
    """Run before each request"""
    # Skip for static files and login/logout routes
    if request.endpoint in ['static', 'login', 'logout']:
        return
        
    # Check if user is logged in
    if 'username' not in session:
        return redirect(url_for('login'))
        
    # Update last activity time
    session['last_activity'] = datetime.now().isoformat()
    
    # For non-permanent sessions, check session timeout (4 hours)
    if not session.permanent:
        last_activity = session.get('last_activity')
        if last_activity:
            last_active = datetime.fromisoformat(last_activity)
            if (datetime.now() - last_active) > timedelta(hours=4):
                return redirect(url_for('logout'))
    
    # Check if user needs to complete welcome flow
    memory = load_memory()
    username = session['username']
    if username not in memory['users'] or 'desires' not in memory['users'][username]:
        return redirect(url_for('welcome'))
        
    return render_template('start_menu.html', 
                         stats=system.stats,
                         rank_requirements=system.rank_requirements,
                         tasks=system.tasks,
                         categories=DASHBOARD_CATEGORIES)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    # If already logged in, redirect to index
    if 'username' in session:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember_me = request.form.get('remember_me') == 'on'
        
        # Initialize memory if needed
        if not hasattr(system, 'memory'):
            system.memory = {}
        if 'users' not in system.memory:
            system.memory['users'] = {}
        
        # Create user if doesn't exist
        if username not in system.memory['users']:
            system.memory['users'][username] = {
                'password': password,
                'created_at': datetime.now().isoformat()
            }
            system.save_memory()
        
        # Verify password
        if system.memory['users'][username]['password'] == password:
            session.permanent = remember_me  # Make session permanent if remember me is checked
            session['username'] = username
            session['last_activity'] = datetime.now().isoformat()
            
            # Set session expiration
            if remember_me:
                # 30 days for persistent sessions
                session.permanent = True
                app.permanent_session_lifetime = timedelta(days=30)
            else:
                # Browser session only
                session.permanent = False
                
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password')
            
    return render_template('login.html')

@app.route('/welcome')
@require_auth
def welcome():
    """Show welcome page with three questions"""
    return render_template('welcome.html')

@app.route('/api/save-desires', methods=['POST'])
@require_auth
def save_desires():
    """Save user's desires and generate initial stats"""
    data = request.json
    desires = data.get('desires')
    
    if not desires:
        return jsonify({'success': False, 'error': 'No desires provided'})
    
    # Save desires to memory
    memory = load_memory()
    username = session['username']
    
    if username not in memory['users']:
        memory['users'][username] = {
            'created_at': datetime.utcnow().isoformat(),
            'role': session.get('role', 'user')
        }
    
    memory['users'][username]['desires'] = desires
    save_memory(memory)
    
    # Initialize system with user's desires
    system.initialize_user_profile(desires)
    
    return jsonify({'success': True})

@app.route('/logout')
def logout():
    """Handle logout"""
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    """Render the dashboard page"""
    # Get daily stats
    daily_stats = daily_quest_system.get_daily_stats()
    
    return render_template('dashboard.html',
                         categories=DASHBOARD_CATEGORIES,
                         stats=system.stats,
                         tasks=system.tasks,
                         daily_stats=daily_stats,
                         session=session)

@app.route('/quests')
def show_quests():
    """Render the quests page"""
    # Get daily stats for quest information
    daily_stats = daily_quest_system.get_daily_stats()
    
    return render_template('quest.html',
                         categories=DASHBOARD_CATEGORIES,
                         stats=system.stats,
                         tasks=system.tasks,
                         daily_stats=daily_stats,
                         session=session)

@app.route('/character-status')
def character_status():
    """Render the character status page"""
    if "username" not in session:
        session["username"] = "Gitonga"  # Set default username
    return render_template('status.html',
                         stats=system.stats,
                         rank_requirements=system.rank_requirements)

@app.route('/character-skills')
def character_skills():
    """Render the character skills page"""
    if "username" not in session:
        session["username"] = "User"
    
    # Load the skills configuration
    with open('jarvis/skills_config.json', 'r') as f:
        skills_config = json.load(f)
    
    # Calculate skill points based on level
    skill_points = skills_config['skill_points']['starting_points'] + (system.stats.get('level', 1) - 1) * skills_config['skill_points']['per_level']
    
    # Get skill progress from stats
    skill_progress = system.stats.get('skill_progress', {})
    
    # Determine which skills are unlocked based on level and prerequisites
    for category in skills_config['categories'].values():
        for skill in category['skills']:
            skill['unlocked'] = (
                system.stats.get('level', 1) >= skill['requirements']['level'] and
                all(parent in system.stats.get('unlocked_skills', []) for parent in skill['requirements']['parent_skills'])
            )
            # Add progress information
            skill['progress'] = skill_progress.get(skill['id'], 0)
            skill['max_progress'] = 100  # Default max progress
    
    return render_template('skills.html',
                         stats=system.stats,
                         rank_requirements=system.rank_requirements,
                         skills_config=skills_config,
                         skill_points=skill_points)

@app.route('/inventory')
def inventory():
    """Render the inventory page"""
    if "username" not in session:
        session["username"] = "User"
    return render_template('inventory.html',
                         stats=system.stats,
                         inventory=system.stats.get('inventory', []))

@app.route('/notification/<notification_type>')
def show_notification(notification_type):
    """Show a notification"""
    notification_messages = {
        'quest': {
            'type': 'The Secret Quest',
            'message': 'Courage of the Weak'
        },
        'daily_quest_assignment': {
            'type': 'Daily Quest Assignment',
            'message': 'New daily quests have been assigned!'
        },
        'progress_update': {
            'type': 'Progress Update',
            'message': 'Your daily progress has been updated!'
        },
        'daily_reflection': {
            'type': 'Daily Reflection',
            'message': 'Time to reflect on your progress!'
        },
        'achievement': {
            'type': 'Achievement Unlocked',
            'message': 'First Steps into Darkness'
        },
        'level_up': {
            'type': 'Level Up',
            'message': 'You have reached level 5!'
        },
        'reward': {
            'type': 'Reward Earned',
            'message': 'Obtained: Mystic Artifact'
        }
    }
    
    notification = notification_messages.get(notification_type, {
        'type': 'System Message',
        'message': 'Unknown notification type'
    })
    
    return render_template('notification.html', notification=notification)

@app.route('/api/notify', methods=['POST'])
def create_notification():
    """Create a new notification"""
    data = request.json
    notification_type = data.get('type')
    message = data.get('message')
    
    if not notification_type or not message:
        return jsonify({'success': False, 'error': 'Missing type or message'}), 400
    
    notifications.append({
        'type': notification_type,
        'message': message
    })
    
    return jsonify({'success': True, 'redirect': url_for('show_notification', notification_type=notification_type)})

@app.route('/api/stats')
def get_stats():
    """Get current stats"""
    return jsonify(system.stats)

@app.route('/api/tasks')
def get_tasks():
    """Get all tasks"""
    return jsonify([task.to_dict() for task in system.tasks])

# NEW DAILY QUEST SYSTEM API ENDPOINTS

@app.route('/api/daily-quests/generate', methods=['POST'])
def generate_daily_quests():
    """Generate new daily quests"""
    try:
        quests = daily_quest_system.generate_daily_quests()
        return jsonify({
            'success': True,
            'quests': quests,
            'count': len(quests),
            'message': f'Generated {len(quests)} daily quests successfully!'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/daily-quests/stats')
def get_daily_stats():
    """Get daily quest statistics"""
    try:
        daily_stats = daily_quest_system.get_daily_stats()
        return jsonify({
            'success': True,
            'stats': daily_stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/three-month-plan/generate', methods=['POST'])
def generate_three_month_plan():
    """Generate a new 3-month plan"""
    try:
        plan = daily_quest_system.generate_three_month_plan()
        return jsonify({
            'success': True,
            'plan': plan,
            'message': '3-month plan generated successfully!'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/three-month-plan')
def get_three_month_plan():
    """Get the current 3-month plan"""
    try:
        if daily_quest_system.three_month_plan:
            return jsonify({
                'success': True,
                'plan': daily_quest_system.three_month_plan
            })
        else:
            # Try to load from file
            try:
                with open('three_month_plan.json', 'r') as f:
                    plan = json.load(f)
                daily_quest_system.three_month_plan = plan
                return jsonify({
                    'success': True,
                    'plan': plan
                })
            except FileNotFoundError:
                return jsonify({
                    'success': False,
                    'error': 'No 3-month plan found. Generate one first.'
                }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/complete_quest_advanced', methods=['POST'])
def complete_quest_advanced():
    """Complete a quest with advanced XP system"""
    task_index = request.json.get('task_index')
    
    if task_index is not None:
        try:
            result = daily_quest_system.complete_quest_with_xp(task_index)
            
            if result['success']:
                # Create notification data
                notification = {
                    'type': 'Quest Completed',
                    'title': f'Quest Completed: {result["quest_name"]}',
                    'message': f'You gained {result["xp_gained"]} XP!',
                    'xp_gained': result['xp_gained'],
                    'skill_xp_gained': result['skill_xp_gained'],
                    'skills_affected': result['skills_affected'],
                    'stat_rewards': result['stat_rewards'],
                    'level_up': result['level_up'],
                    'rank_up': result['rank_up']
                }
                
                # Send push notification if Firebase is enabled and token exists
                if firebase_enabled and 'fcm_token' in session:
                    notification_result = send_notification(
                        token=session['fcm_token'],
                        title=notification['title'],
                        body=notification['message'],
                        data={'quest_name': result["quest_name"]}
                    )
                    if not notification_result['success']:
                        print(f"Failed to send notification: {notification_result.get('error')}")
                
                return jsonify({
                    'success': True,
                    'notification': notification,
                    'result': result
                })
            else:
                return jsonify(result), 400
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    return jsonify({'success': False, 'error': 'No task index provided'}), 400

@app.route('/api/notification/manual', methods=['POST'])
def send_manual_notification():
    """Send a manual notification (for testing)"""
    data = request.json
    notification_type = data.get('type', 'morning')
    
    if notification_type == 'morning':
        daily_quest_system._send_morning_notification()
    elif notification_type == 'evening':
        daily_quest_system._send_evening_notification()
    elif notification_type == 'night':
        daily_quest_system._send_night_notification()
    else:
        return jsonify({'success': False, 'error': 'Invalid notification type'}), 400
    
    return jsonify({'success': True, 'message': f'{notification_type.title()} notification sent!'})

@app.route('/planning')
def planning_dashboard():
    """Render the 3-month planning dashboard"""
    if "username" not in session:
        session["username"] = "User"
    
    try:
        # Load the current 3-month plan
        plan_data = daily_quest_system.three_month_plan
        
        # Ensure plan has required structure
        if not isinstance(plan_data, dict):
            plan_data = {}
        if 'months' not in plan_data:
            # Generate default plan structure
            plan_data = {
                "created_at": datetime.now().isoformat(),
                "total_weeks": 12,
                "current_week": 1,
                "months": {
                    "Month 1": {
                        "theme": "Foundation Building",
                        "focus_areas": ["health", "programming", "financial_literacy"],
                        "weeks": {}
                    },
                    "Month 2": {
                        "theme": "Skill Advancement", 
                        "focus_areas": ["programming", "investing", "physical_performance"],
                        "weeks": {}
                    },
                    "Month 3": {
                        "theme": "Mastery & Integration",
                        "focus_areas": ["wealth_building", "software_mastery", "peak_performance"],
                        "weeks": {}
                    }
                }
            }
            daily_quest_system.three_month_plan = plan_data
            daily_quest_system._save_three_month_plan()
        
        # Convert to AttrDict
        plan = AttrDict(plan_data)
    except FileNotFoundError:
        # Create empty plan with required structure
        plan_data = {
            "created_at": datetime.now().isoformat(),
            "total_weeks": 12,
            "current_week": 1,
            "months": {
                "Month 1": {
                    "theme": "Foundation Building",
                    "focus_areas": ["health", "programming", "financial_literacy"],
                    "weeks": {}
                },
                "Month 2": {
                    "theme": "Skill Advancement",
                    "focus_areas": ["programming", "investing", "physical_performance"],
                    "weeks": {}
                },
                "Month 3": {
                    "theme": "Mastery & Integration",
                    "focus_areas": ["wealth_building", "software_mastery", "peak_performance"],
                    "weeks": {}
                }
            }
        }
        plan = AttrDict(plan_data)
    
    return render_template('planning.html',
                         stats=system.stats,
                         plan=plan,
                         current_date=datetime.now().isoformat())

@app.route('/api/toggle_quest_active', methods=['POST'])
def toggle_quest_active():
    """Toggle a quest's active status"""
    data = request.json
    task_index = data.get('task_index')
    is_active = data.get('is_active', False)
    
    if task_index is not None:
        try:
            # Update the task's active status in the system
            task = system.tasks[task_index - 1]  # Convert to 0-based index
            task.active = is_active
            system.save_memory()
            
            return jsonify({
                'success': True,
                'message': f"Quest {'activated' if is_active else 'deactivated'} successfully"
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400
    
    return jsonify({
        'success': False,
        'error': 'No task index provided'
    }), 400

@app.route('/api/save-notification-token', methods=['POST'])
def save_notification_token():
    """Save the FCM token for the user"""
    if not firebase_enabled:
        return jsonify({'success': False, 'error': 'Firebase is not properly configured'})
        
    data = request.json
    token = data.get('token')
    if token:
        session['fcm_token'] = token
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'No token provided'})

def send_notification(token, title, body, data=None):
    """Send a notification to a specific device"""
    if not firebase_enabled:
        return {'success': False, 'error': 'Firebase is not properly configured'}
        
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data or {},
            token=token,
        )
        response = messaging.send(message)
        return {'success': True, 'response': response}
    except Exception as e:
        print(f"Error sending notification: {str(e)}")
        return {'success': False, 'error': str(e)}

@app.route('/api/complete_task', methods=['POST'])
def complete_task():
    """Complete a task and send notification"""
    task_index = request.json.get('task_index')
    quest_name = request.json.get('quest_name', 'Unknown Quest')
    
    if task_index is not None:
        try:
            system.complete_task(task_index)
            
            # Create notification data
            notification = {
                'type': 'Quest Completed',
                'message': quest_name,
                'xp_gained': system.stats.get('last_xp_gained', 100),
                'rewards': system.stats.get('last_rewards', ['Experience Points +100'])
            }
            
            # Send push notification if Firebase is enabled and token exists
            if firebase_enabled and 'fcm_token' in session:
                notification_result = send_notification(
                    token=session['fcm_token'],
                    title=f'Quest Completed: {quest_name}',
                    body=f'You gained {notification["xp_gained"]} XP!',
                    data={'quest_name': quest_name}
                )
                if not notification_result['success']:
                    print(f"Failed to send notification: {notification_result.get('error')}")
            
            return jsonify({
                'success': True,
                'notification': notification
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    return jsonify({'success': False, 'error': 'No task index provided'})

@app.route('/api/suggest_tasks')
def suggest_tasks():
    """Get task suggestions"""
    system.suggest_tasks()
    return jsonify([task.to_dict() for task in system.tasks])

@app.route('/api/inventory', methods=['POST'])
def add_inventory_item():
    """Add a new item to inventory"""
    data = request.json
    if 'inventory' not in system.stats:
        system.stats['inventory'] = []
    
    item = {
        'id': len(system.stats['inventory']) + 1,
        'name': data.get('name'),
        'type': data.get('type'),
        'quantity': data.get('quantity', 1),
        'description': data.get('description', ''),
        'acquired_at': datetime.now().isoformat()
    }
    
    system.stats['inventory'].append(item)
    system.save_memory()
    return jsonify({'success': True, 'item': item})

@app.route('/api/inventory/<int:item_id>', methods=['PUT'])
def update_inventory_item(item_id):
    """Update an inventory item"""
    data = request.json
    inventory = system.stats.get('inventory', [])
    
    for item in inventory:
        if item['id'] == item_id:
            item.update({
                'name': data.get('name', item['name']),
                'type': data.get('type', item['type']),
                'quantity': data.get('quantity', item['quantity']),
                'description': data.get('description', item['description'])
            })
            system.save_memory()
            return jsonify({'success': True, 'item': item})
    
    return jsonify({'success': False, 'error': 'Item not found'}), 404

@app.route('/api/inventory/<int:item_id>', methods=['DELETE'])
def delete_inventory_item(item_id):
    """Delete an inventory item"""
    if 'inventory' not in system.stats:
        return jsonify({'success': False, 'error': 'Inventory not found'}), 404
    
    inventory = system.stats['inventory']
    for i, item in enumerate(inventory):
        if item['id'] == item_id:
            del inventory[i]
            system.save_memory()
            return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'Item not found'}), 404

@app.route('/world-map')
def world_map():
    """Render the world map page"""
    if "username" not in session:
        session["username"] = "User"
    return render_template('world_map.html',
                         stats=system.stats,
                         current_location=system.stats.get('current_location', {
                             'lat': 35.4676,  # Oklahoma City coordinates
                             'lng': -97.5164,
                             'name': 'Oklahoma City'
                         }))

@app.route('/api/update-location', methods=['POST'])
def update_location():
    """Update the user's current location"""
    data = request.json
    location = {
        'lat': data.get('lat'),
        'lng': data.get('lng'),
        'name': data.get('name', 'Unknown Location'),
        'updated_at': datetime.now().isoformat()
    }
    system.stats['current_location'] = location
    system.save_memory()
    return jsonify({'success': True, 'location': location})

@app.route('/api/firebase-config')
def firebase_config():
    """Return Firebase configuration including VAPID key"""
    if not firebase_enabled:
        return jsonify({'success': False, 'error': 'Firebase is not properly configured'})
    
    return jsonify({
        'success': True,
        'vapidKey': os.getenv('VAPIDKEY')
    })

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Jarvis Web Interface")
    parser.add_argument("--web", action="store_true", help="Start the web interface")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=3000, help="Port to bind to")
    
    args = parser.parse_args()
    
    if args.web:
        app.run(host=args.host, port=args.port, debug=True)
    else:
        app.run(debug=True) 