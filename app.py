from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from jarvis import Jarvis
import os

app = Flask(__name__, 
           template_folder='jarvis/templates',
           static_folder='jarvis/static')
app.secret_key = os.urandom(24)  # Required for session management

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
        session["username"] = "User"  # Set default username
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

@app.route('/api/complete_task', methods=['POST'])
def complete_task():
    """Complete a task"""
    task_index = request.json.get('task_index')
    quest_name = request.json.get('quest_name', 'Unknown Quest')
    
    if task_index is not None:
        try:
            system.complete_task(task_index)
            
            # Create notification data
            notification = {
                'type': 'Quest Completed',
                'message': quest_name,
                'xp_gained': system.stats.get('last_xp_gained', 100),  # You might want to get this from your system
                'rewards': system.stats.get('last_rewards', ['Experience Points +100'])  # And this too
            }
            
            return jsonify({
                'success': True,
                'notification': {
                    'type': 'Quest Completed',
                    'message': quest_name
                }
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    return jsonify({'success': False, 'error': 'No task index provided'})

@app.route('/api/suggest_tasks')
def suggest_tasks():
    """Get task suggestions"""
    system.suggest_tasks()
    return jsonify([task.to_dict() for task in system.tasks])

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002) 