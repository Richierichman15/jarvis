"""
Main Flask application for Jarvis System.
Handles web interface, API endpoints, and Firebase integration.
"""
from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from flask_cors import CORS
import os
import json
import logging
from datetime import datetime

# Import centralized configuration and utilities
from jarvis.config import config
from jarvis.utils import firebase_manager, send_notification, broadcast_notification
from jarvis import Jarvis
from jarvis.daily_quest_system import DailyQuestGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app with centralized configuration
app = Flask(__name__, 
           template_folder='jarvis/templates',
           static_folder='jarvis/static')

# Configure app from centralized config
app.secret_key = config.app_config["secret_key"]
app.config['DEBUG'] = config.app_config["debug"]

# Enable CORS with proper origins
CORS(app, origins=config.get_cors_origins())

# Initialize Firebase
firebase_initialized = firebase_manager.initialize()
if firebase_initialized:
    logger.info("🔥 Firebase integration enabled")
else:
    logger.warning("⚠️ Firebase integration disabled - check configuration")

# Initialize System
system = Jarvis()
logger.info("🤖 Jarvis System initialized")

# Initialize Daily Quest System with enhanced configuration
daily_quest_system = DailyQuestGenerator(system)
logger.info("📋 Daily Quest System initialized")

# Enhanced notification callback with Firebase integration
def enhanced_notification_callback(notification_data):
    """Enhanced notification callback with Firebase and logging."""
    try:
        notification_type = notification_data.get('type', 'System Notification')
        title = notification_data.get('title', notification_type)
        message = notification_data.get('message', '')
        
        logger.info(f"📢 Sending notification: {title}")
        
        # Send Firebase notification if available and tokens exist
        if firebase_initialized:
            active_tokens = firebase_manager.get_active_tokens()
            if active_tokens:
                result = broadcast_notification(
                    title=title,
                    body=message,
                    data={
                        'type': notification_data.get('type', ''),
                        'notification_time': notification_data.get('notification_time', ''),
                        'quest_id': notification_data.get('quest_id', ''),
                        'click_action': url_for('show_notification', 
                                               notification_type=notification_type.lower().replace(' ', '_'))
                    }
                )
                
                if result.get('success'):
                    logger.info(f"✅ Notification sent to {len(active_tokens)} devices")
                else:
                    logger.error(f"❌ Failed to send notification: {result.get('error')}")
            else:
                logger.info("📱 No active notification tokens")
        
        # Store notification for web interface
        store_notification(notification_data)
        
    except Exception as e:
        logger.error(f"Error in notification callback: {str(e)}")

# Register enhanced notification callback
daily_quest_system.register_notification_callback(enhanced_notification_callback)

# Start notification scheduler
daily_quest_system.schedule_daily_notifications()
logger.info("⏰ Notification scheduler started")

# Enhanced dashboard categories with better organization
DASHBOARD_CATEGORIES = {
    "🎯 Quest System": [
        "Available Quests",
        "Active Quests", 
        "Completed Quests",
        "Daily Challenges",
        "Quest History"
    ],
    "📊 Stats & Progress": [
        "Character Stats",
        "Skill Tree",
        "Experience Points",
        "Level Progress",
        "Achievements"
    ],
    "🎒 Inventory": [
        "Equipment",
        "Items & Resources",
        "Artifacts",
        "Storage Management"
    ],
    "📚 Knowledge Base": [
        "Quest Log",
        "System Messages",
        "Notifications",
        "Learning Resources",
        "History"
    ],
    "⚙️ System": [
        "User Profile",
        "Preferences",
        "Notifications",
        "System Settings",
        "Help & Support"
    ]
}

# In-memory notification store (replace with database in production)
notifications_store = []

def store_notification(notification_data):
    """Store notification in memory with timestamp."""
    notification_entry = {
        'id': len(notifications_store) + 1,
        'timestamp': datetime.now().isoformat(),
        **notification_data
    }
    notifications_store.append(notification_entry)
    
    # Keep only last 100 notifications
    if len(notifications_store) > 100:
        notifications_store.pop(0)

@app.route('/')
def index():
    """Enhanced main page with better session management."""
    if "username" not in session:
        session["username"] = config.system_config.get("default_username", "Hunter")
    
    # Get daily stats for homepage
    daily_stats = daily_quest_system.get_daily_stats()
    
    return render_template('start_menu.html', 
                         stats=system.stats,
                         rank_requirements=config.quest_config["rank_requirements"],
                         tasks=system.tasks,
                         categories=DASHBOARD_CATEGORIES,
                         daily_stats=daily_stats,
                         firebase_config=config.get_firebase_web_config() if firebase_initialized else None)

@app.route('/dashboard')
def dashboard():
    """Enhanced dashboard with comprehensive stats."""
    daily_stats = daily_quest_system.get_daily_stats()
    
    # Get recent notifications
    recent_notifications = notifications_store[-10:] if notifications_store else []
    
    return render_template('dashboard.html',
                         categories=DASHBOARD_CATEGORIES,
                         stats=system.stats,
                         tasks=system.tasks,
                         daily_stats=daily_stats,
                         recent_notifications=recent_notifications,
                         firebase_enabled=firebase_initialized,
                         session=session)

@app.route('/quests')
def show_quests():
    """Enhanced quests page with filtering and sorting."""
    daily_stats = daily_quest_system.get_daily_stats()
    
    # Filter tasks by status if requested
    filter_status = request.args.get('status', 'all')
    filtered_tasks = system.tasks
    
    if filter_status != 'all':
        filtered_tasks = [task for task in system.tasks if task.status == filter_status]
    
    return render_template('quest.html',
                         categories=DASHBOARD_CATEGORIES,
                         stats=system.stats,
                         tasks=filtered_tasks,
                         all_tasks=system.tasks,
                         daily_stats=daily_stats,
                         filter_status=filter_status,
                         session=session)

@app.route('/character-status')
def character_status():
    """Enhanced character status with detailed progression."""
    if "username" not in session:
        session["username"] = config.system_config.get("default_username", "Hunter")
    
    # Calculate progression percentages
    current_rank = system.stats.get('rank', 'E')
    rank_requirements = config.quest_config["rank_requirements"]
    rank_xp = system.stats.get('rank_xp', 0)
    required_xp = rank_requirements.get(current_rank, 1000)
    rank_progress = min((rank_xp / required_xp) * 100, 100)
    
    return render_template('status.html',
                         stats=system.stats,
                         rank_requirements=rank_requirements,
                         rank_progress=rank_progress,
                         max_level=config.quest_config["max_level"])

@app.route('/character-skills')
def character_skills():
    """Enhanced skills page with better progression tracking."""
    if "username" not in session:
        session["username"] = "Hunter"
    
    try:
        # Load skills configuration
        with open(config.system_config["skills_config_file"], 'r') as f:
            skills_config = json.load(f)
        
        # Calculate available skill points
        base_points = skills_config.get('skill_points', {}).get('starting_points', 0)
        per_level = skills_config.get('skill_points', {}).get('per_level', 1)
        skill_points = base_points + (system.stats.get('level', 1) - 1) * per_level
        
        # Get current skill progress
        skill_progress = system.stats.get('skill_progress', {})
        unlocked_skills = system.stats.get('unlocked_skills', [])
        
        # Enhanced skill processing with better unlock logic
        for category_name, category in skills_config.get('categories', {}).items():
            for skill in category.get('skills', []):
                skill_id = skill.get('id', '')
                requirements = skill.get('requirements', {})
                
                # Check if skill is unlocked
                level_req = requirements.get('level', 1)
                parent_skills = requirements.get('parent_skills', [])
                
                skill['unlocked'] = (
                    system.stats.get('level', 1) >= level_req and
                    all(parent in unlocked_skills for parent in parent_skills)
                )
                
                # Add progress and mastery information
                skill['progress'] = skill_progress.get(skill_id, 0)
                skill['max_progress'] = skill.get('max_progress', 100)
                skill['mastered'] = skill['progress'] >= skill['max_progress']
        
        return render_template('skills.html',
                             stats=system.stats,
                             rank_requirements=config.quest_config["rank_requirements"],
                             skills_config=skills_config,
                             skill_points=skill_points,
                             unlocked_skills=unlocked_skills)
                             
    except Exception as e:
        logger.error(f"Error loading skills: {str(e)}")
        return jsonify({'error': 'Failed to load skills configuration'}), 500

@app.route('/inventory')
def inventory():
    """Enhanced inventory with better categorization."""
    if "username" not in session:
        session["username"] = "Hunter"
    
    inventory_items = system.stats.get('inventory', [])
    
    # Categorize inventory items
    categorized_inventory = {
        'weapons': [],
        'armor': [],
        'consumables': [],
        'materials': [],
        'misc': []
    }
    
    for item in inventory_items:
        category = item.get('category', 'misc')
        categorized_inventory.setdefault(category, []).append(item)
    
    return render_template('inventory.html',
                         stats=system.stats,
                         inventory=inventory_items,
                         categorized_inventory=categorized_inventory)

@app.route('/notification/<notification_type>')
def show_notification(notification_type):
    """Enhanced notification display with better templates."""
    
    # Enhanced notification templates
    notification_templates = {
        'quest': {
            'type': 'Quest Available',
            'title': 'New Quest Unlocked', 
            'message': 'A mysterious quest has appeared. Do you have the courage to accept it?',
            'icon': '⚔️',
            'action_text': 'View Quests',
            'action_url': url_for('show_quests')
        },
        'daily_quest_assignment': {
            'type': 'Daily Quest Assignment',
            'title': 'Daily Quests Ready',
            'message': 'Your daily quests have been prepared. Time to level up!',
            'icon': '📋',
            'action_text': 'Start Quests',
            'action_url': url_for('show_quests')
        },
        'progress_update': {
            'type': 'Progress Update',
            'title': 'Progress Tracked',
            'message': 'Your daily progress has been recorded. Keep pushing forward!',
            'icon': '📈',
            'action_text': 'View Progress',
            'action_url': url_for('character_status')
        },
        'daily_reflection': {
            'type': 'Daily Reflection',
            'title': 'Time to Reflect',
            'message': 'How did today go? Reflect on your journey and plan for tomorrow.',
            'icon': '🤔',
            'action_text': 'Open Journal',
            'action_url': url_for('dashboard')
        },
        'achievement': {
            'type': 'Achievement Unlocked',
            'title': 'New Achievement!',
            'message': 'You have unlocked a new achievement! Your dedication is paying off.',
            'icon': '🏆',
            'action_text': 'View Achievements',
            'action_url': url_for('character_skills')
        },
        'level_up': {
            'type': 'Level Up',
            'title': 'Level Up!',
            'message': f'Congratulations! You have reached level {system.stats.get("level", 1)}!',
            'icon': '⬆️',
            'action_text': 'View Stats',
            'action_url': url_for('character_status')
        },
        'reward': {
            'type': 'Reward Earned',
            'title': 'Reward Obtained',
            'message': 'You have earned a valuable reward for your efforts!',
            'icon': '🎁',
            'action_text': 'Check Inventory',
            'action_url': url_for('inventory')
        }
    }
    
    notification = notification_templates.get(notification_type, {
        'type': 'System Message',
        'title': 'System Notification',
        'message': 'You have received a system notification.',
        'icon': '📢',
        'action_text': 'Return to Dashboard',
        'action_url': url_for('dashboard')
    })
    
    return render_template('notification.html', 
                         notification=notification,
                         notification_type=notification_type)

# Enhanced API endpoints with better error handling and responses

@app.route('/api/config')
def get_config():
    """Get system configuration for frontend."""
    return jsonify({
        'success': True,
        'config': config.to_dict(),
        'firebase_enabled': firebase_initialized
    })

@app.route('/api/stats')
def get_stats():
    """Get current stats with enhanced information."""
    return jsonify({
        'success': True,
        'stats': system.stats,
        'rank_requirements': config.quest_config["rank_requirements"],
        'max_level': config.quest_config["max_level"]
    })

@app.route('/api/tasks')
def get_tasks():
    """Get all tasks with filtering options."""
    status_filter = request.args.get('status')
    difficulty_filter = request.args.get('difficulty')
    
    tasks = system.tasks
    
    # Apply filters
    if status_filter:
        tasks = [task for task in tasks if task.status == status_filter]
    if difficulty_filter:
        tasks = [task for task in tasks if task.difficulty == difficulty_filter]
    
    return jsonify({
        'success': True,
        'tasks': [task.to_dict() for task in tasks],
        'total_count': len(system.tasks),
        'filtered_count': len(tasks)
    })

@app.route('/api/firebase-config')
def firebase_config_endpoint():
    """Get Firebase configuration for frontend."""
    if not firebase_initialized:
        return jsonify({
            'success': False,
            'error': 'Firebase not configured'
        }), 400
    
    return jsonify({
        'success': True,
        'config': config.get_firebase_web_config(),
        'vapid_key': config.vapid_key
    })

@app.route('/api/notifications', methods=['GET'])
def get_notifications():
    """Get recent notifications."""
    limit = request.args.get('limit', 10, type=int)
    recent_notifications = notifications_store[-limit:] if notifications_store else []
    
    return jsonify({
        'success': True,
        'notifications': recent_notifications,
        'total_count': len(notifications_store)
    })

@app.route('/api/save-notification-token', methods=['POST'])
def save_notification_token():
    """Save FCM token for push notifications."""
    if not firebase_initialized:
        return jsonify({
            'success': False, 
            'error': 'Firebase not configured'
        }), 400
    
    data = request.json
    token = data.get('token')
    
    if not token:
        return jsonify({
            'success': False,
            'error': 'Token is required'
        }), 400
    
    # Add token to Firebase manager
    success = firebase_manager.add_token(token)
    
    if success:
        session['fcm_token'] = token
        logger.info(f"📱 Notification token saved for session")
        
        return jsonify({
            'success': True,
            'message': 'Notification token saved successfully'
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Failed to save token'
        }), 500

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
                if firebase_initialized and 'fcm_token' in session:
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
    
    # Load the current 3-month plan
    try:
        if daily_quest_system.three_month_plan:
            plan = daily_quest_system.three_month_plan
        else:
            with open('three_month_plan.json', 'r') as f:
                plan = json.load(f)
                daily_quest_system.three_month_plan = plan
    except FileNotFoundError:
        plan = None
    
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

# Additional utility endpoints for better functionality

@app.route('/logout')
def logout():
    """Handle user logout and cleanup."""
    # Remove FCM token if exists
    if 'fcm_token' in session and firebase_initialized:
        firebase_manager.remove_token(session['fcm_token'])
    
    session.clear()
    logger.info("User logged out")
    return redirect(url_for('index'))

@app.route('/api/inventory', methods=['POST'])
def add_inventory_item():
    """Add a new item to inventory"""
    data = request.json
    if 'inventory' not in system.stats:
        system.stats['inventory'] = []
    
    item = {
        'id': len(system.stats['inventory']) + 1,
        'name': data.get('name'),
        'category': data.get('category', 'misc'),
        'type': data.get('type'),
        'quantity': data.get('quantity', 1),
        'description': data.get('description', ''),
        'rarity': data.get('rarity', 'common'),
        'acquired_at': datetime.now().isoformat()
    }
    
    system.stats['inventory'].append(item)
    system.save_memory()
    
    logger.info(f"Added item to inventory: {item['name']}")
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
                'category': data.get('category', item.get('category', 'misc')),
                'quantity': data.get('quantity', item['quantity']),
                'description': data.get('description', item['description']),
                'rarity': data.get('rarity', item.get('rarity', 'common'))
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
            deleted_item = inventory.pop(i)
            system.save_memory()
            logger.info(f"Deleted item from inventory: {deleted_item['name']}")
            return jsonify({'success': True, 'deleted_item': deleted_item})
    
    return jsonify({'success': False, 'error': 'Item not found'}), 404

@app.route('/api/skills/unlock', methods=['POST'])
def unlock_skill():
    """Unlock a skill if requirements are met"""
    data = request.json
    skill_id = data.get('skill_id')
    
    if not skill_id:
        return jsonify({'success': False, 'error': 'Skill ID required'}), 400
    
    try:
        # Load skills configuration
        with open(config.system_config["skills_config_file"], 'r') as f:
            skills_config = json.load(f)
        
        # Find the skill
        skill_found = None
        for category in skills_config.get('categories', {}).values():
            for skill in category.get('skills', []):
                if skill.get('id') == skill_id:
                    skill_found = skill
                    break
            if skill_found:
                break
        
        if not skill_found:
            return jsonify({'success': False, 'error': 'Skill not found'}), 404
        
        # Check requirements
        requirements = skill_found.get('requirements', {})
        level_req = requirements.get('level', 1)
        parent_skills = requirements.get('parent_skills', [])
        unlocked_skills = system.stats.get('unlocked_skills', [])
        
        if system.stats.get('level', 1) < level_req:
            return jsonify({'success': False, 'error': f'Requires level {level_req}'}), 400
        
        if not all(parent in unlocked_skills for parent in parent_skills):
            return jsonify({'success': False, 'error': 'Missing prerequisite skills'}), 400
        
        # Unlock the skill
        if skill_id not in unlocked_skills:
            unlocked_skills.append(skill_id)
            system.stats['unlocked_skills'] = unlocked_skills
            system.save_memory()
            
            logger.info(f"Skill unlocked: {skill_found.get('name', skill_id)}")
            return jsonify({'success': True, 'skill': skill_found})
        else:
            return jsonify({'success': False, 'error': 'Skill already unlocked'}), 400
            
    except Exception as e:
        logger.error(f"Error unlocking skill: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint for deployment monitoring"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0.0',
        'firebase_enabled': firebase_initialized,
        'components': {
            'jarvis_system': True,
            'daily_quest_system': True,
            'firebase': firebase_initialized,
            'notification_scheduler': True
        }
    })

@app.route('/api/system/info', methods=['GET'])
def system_info():
    """Get system information and statistics"""
    active_tokens = len(firebase_manager.get_active_tokens()) if firebase_initialized else 0
    
    return jsonify({
        'success': True,
        'system_info': {
            'total_quests': len(system.tasks),
            'completed_quests': len([t for t in system.tasks if t.status == 'completed']),
            'active_notifications': active_tokens,
            'total_notifications_sent': len(notifications_store),
            'firebase_configured': firebase_initialized,
            'environment': config.app_config["environment"],
            'uptime': datetime.now().isoformat()
        }
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    if request.path.startswith('/api/'):
        return jsonify({'success': False, 'error': 'Endpoint not found'}), 404
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(error)}")
    if request.path.startswith('/api/'):
        return jsonify({'success': False, 'error': 'Internal server error'}), 500
    return render_template('500.html'), 500

# Startup logging
@app.before_first_request
def startup_log():
    """Log system startup information"""
    logger.info("🚀 Jarvis System started successfully!")
    logger.info(f"🌍 Environment: {config.app_config['environment']}")
    logger.info(f"🔥 Firebase: {'Enabled' if firebase_initialized else 'Disabled'}")
    logger.info(f"📱 Active tokens: {len(firebase_manager.get_active_tokens()) if firebase_initialized else 0}")

def main():
    """Main function to run the application with proper configuration"""
    # Cleanup invalid tokens on startup
    if firebase_initialized:
        cleaned = firebase_manager.cleanup_invalid_tokens()
        if cleaned > 0:
            logger.info(f"🧹 Cleaned up {cleaned} invalid notification tokens")
    
    # Log startup configuration
    logger.info("🎮 Starting Jarvis System")
    logger.info(f"📡 Host: {config.app_config['host']}")
    logger.info(f"🔌 Port: {config.app_config['port']}")
    logger.info(f"🐛 Debug: {config.app_config['debug']}")
    
    # Run the application
    app.run(
        debug=config.app_config["debug"],
        host=config.app_config["host"],
        port=config.app_config["port"],
        threaded=True  # Enable threading for better performance
    )

if __name__ == '__main__':
    main() 