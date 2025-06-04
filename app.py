from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from jarvis import Jarvis
import os
from datetime import datetime
import json
import firebase_admin
from firebase_admin import credentials, messaging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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
app.secret_key = os.urandom(24)

# Initialize Firebase Admin with credentials from environment variables
firebase_enabled = False  # Flag to track if Firebase is properly initialized

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

@app.route('/')
def index():
    """Render the main page"""
    if "username" not in session:
        session["username"] = "Gitonga"  # Set default username
    return render_template('start_menu.html', 
                         stats=system.stats,
                         rank_requirements=system.rank_requirements,
                         tasks=system.tasks,
                         categories=DASHBOARD_CATEGORIES)

@app.route('/dashboard')
def dashboard():
    """Render the dashboard page"""
    return render_template('dashboard.html',
                         categories=DASHBOARD_CATEGORIES,
                         stats=system.stats,
                         tasks=system.tasks,
                         session=session)

@app.route('/quests')
def show_quests():
    """Render the quests page"""
    return render_template('quest.html',
                         categories=DASHBOARD_CATEGORIES,
                         stats=system.stats,
                         tasks=system.tasks,
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
    
    # Determine which skills are unlocked based on level and prerequisites
    for category in skills_config['categories'].values():
        for skill in category['skills']:
            skill['unlocked'] = (
                system.stats.get('level', 1) >= skill['requirements']['level'] and
                all(parent in system.stats.get('unlocked_skills', []) for parent in skill['requirements']['parent_skills'])
            )
    
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

@app.route('/logout')
def logout():
    """Handle user logout"""
    session.clear()
    return redirect(url_for('index'))

@app.route('/api/stats')
def get_stats():
    """Get current stats"""
    return jsonify(system.stats)

@app.route('/api/tasks')
def get_tasks():
    """Get all tasks"""
    return jsonify([task.to_dict() for task in system.tasks])

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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002) 