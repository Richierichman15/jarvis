"""
Firebase service for Jarvis.
Handles push notifications and progress tracking using Firebase Admin SDK.
"""
import os
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import threading
import time
import asyncio

try:
    import firebase_admin
    from firebase_admin import credentials, messaging, firestore
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    logging.warning("Firebase Admin SDK not available. Install with: pip install firebase-admin")

from .config import (
    FIREBASE_ADMIN_SDK_PATH, 
    FIREBASE_CONFIG, 
    FIREBASE_VAPID_KEY,
    DEFAULT_XP_PER_LEVEL,
    MAX_XP_GRANT,
    NOTIFICATION_ENABLED
)

logger = logging.getLogger(__name__)

class FirebaseService:
    """Service for handling Firebase operations."""
    
    def __init__(self):
        self.app = None
        self.db = None
        self.messaging_client = None
        self.initialized = False
        self.user_tokens = {}  # Cache for user tokens
        self.scheduled_notifications = []  # For delayed notifications
        self._scheduler_thread = None
        self._stop_scheduler = False
        
    def initialize(self) -> bool:
        """Initialize Firebase Admin SDK."""
        if not FIREBASE_AVAILABLE:
            logger.error("Firebase Admin SDK not available")
            return False
            
        if not NOTIFICATION_ENABLED:
            logger.info("Notifications disabled in configuration")
            return False
            
        try:
            # Check if already initialized
            if firebase_admin._apps:
                self.app = firebase_admin.get_app()
                logger.info("Using existing Firebase app")
            else:
                # Initialize with service account
                if FIREBASE_ADMIN_SDK_PATH and os.path.exists(FIREBASE_ADMIN_SDK_PATH):
                    cred = credentials.Certificate(FIREBASE_ADMIN_SDK_PATH)
                    self.app = firebase_admin.initialize_app(cred)
                    logger.info("Firebase initialized with service account")
                else:
                    # Try default credentials (for Cloud Run, etc.)
                    try:
                        cred = credentials.ApplicationDefault()
                        self.app = firebase_admin.initialize_app(cred)
                        logger.info("Firebase initialized with default credentials")
                    except Exception as e:
                        logger.error(f"Failed to initialize Firebase: {e}")
                        return False
            
            # Initialize services
            self.db = firestore.client()
            self.messaging_client = messaging
            self.initialized = True
            
            # Start notification scheduler
            self._start_scheduler()
            
            logger.info("✅ Firebase service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error initializing Firebase: {e}")
            return False
    
    def _start_scheduler(self):
        """Start the notification scheduler thread."""
        if self._scheduler_thread is None or not self._scheduler_thread.is_alive():
            self._stop_scheduler = False
            self._scheduler_thread = threading.Thread(target=self._notification_scheduler, daemon=True)
            self._scheduler_thread.start()
            logger.info("📅 Notification scheduler started")
    
    def _notification_scheduler(self):
        """Background thread to handle scheduled notifications."""
        while not self._stop_scheduler:
            try:
                current_time = datetime.now()
                notifications_to_send = []
                
                # Check for notifications ready to send
                for notification in self.scheduled_notifications[:]:
                    if notification['send_time'] <= current_time:
                        notifications_to_send.append(notification)
                        self.scheduled_notifications.remove(notification)
                
                # Send ready notifications
                for notification in notifications_to_send:
                    self._send_immediate_notification(
                        notification['user_id'],
                        notification['title'],
                        notification['message'],
                        notification.get('data', {})
                    )
                
                time.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in notification scheduler: {e}")
                time.sleep(30)  # Wait longer on error
    
    def stop_scheduler(self):
        """Stop the notification scheduler."""
        self._stop_scheduler = True
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=5)
    
    def get_config(self) -> Dict[str, Any]:
        """Get Firebase configuration for frontend."""
        if not self.initialized:
            return {"success": False, "error": "Firebase not initialized"}
        
        return {
            "success": True,
            "config": FIREBASE_CONFIG,
            "vapidKey": FIREBASE_VAPID_KEY
        }
    
    def save_user_token(self, user_id: str, token: str) -> bool:
        """Save FCM token for a user."""
        try:
            if not self.initialized:
                return False
            
            # Cache the token
            self.user_tokens[user_id] = token
            
            # Save to Firestore
            user_ref = self.db.collection('users').document(user_id)
            user_ref.set({
                'fcm_token': token,
                'last_updated': firestore.SERVER_TIMESTAMP,
                'notification_enabled': True
            }, merge=True)
            
            logger.info(f"✅ Saved FCM token for user: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving token: {e}")
            return False
    
    def send_notification(self, user_id: str, title: str, message: str, 
                         data: Optional[Dict] = None, delay_seconds: int = 0) -> bool:
        """Send notification to a user."""
        try:
            if not self.initialized:
                logger.error("Firebase not initialized")
                return False
            
            if delay_seconds > 0:
                # Schedule for later
                send_time = datetime.now() + timedelta(seconds=delay_seconds)
                self.scheduled_notifications.append({
                    'user_id': user_id,
                    'title': title,
                    'message': message,
                    'data': data or {},
                    'send_time': send_time
                })
                logger.info(f"📅 Scheduled notification for {user_id} in {delay_seconds} seconds")
                return True
            else:
                # Send immediately
                return self._send_immediate_notification(user_id, title, message, data)
                
        except Exception as e:
            logger.error(f"❌ Error sending notification: {e}")
            return False
    
    def _send_immediate_notification(self, user_id: str, title: str, message: str, 
                                   data: Optional[Dict] = None) -> bool:
        """Send notification immediately."""
        try:
            # Get user token
            token = self.user_tokens.get(user_id)
            if not token:
                # Try to get from Firestore
                user_ref = self.db.collection('users').document(user_id)
                user_doc = user_ref.get()
                if user_doc.exists:
                    user_data = user_doc.to_dict()
                    token = user_data.get('fcm_token')
                    if token:
                        self.user_tokens[user_id] = token
            
            if not token:
                logger.warning(f"No FCM token found for user: {user_id}")
                return False
            
            # Create notification
            notification = messaging.Notification(
                title=title,
                body=message
            )
            
            # Create message
            fcm_message = messaging.Message(
                notification=notification,
                data=data or {},
                token=token,
                android=messaging.AndroidConfig(
                    notification=messaging.AndroidNotification(
                        icon='/static/images/notification-icon.png',
                        color='#667eea',
                        sound='default',
                        click_action='FLUTTER_NOTIFICATION_CLICK'
                    )
                ),
                webpush=messaging.WebpushConfig(
                    notification=messaging.WebpushNotification(
                        icon='/static/images/notification-icon.png',
                        badge='/static/images/badge-icon.png',
                        vibrate=[200, 100, 200],
                        require_interaction=True
                    )
                )
            )
            
            # Send message
            response = self.messaging_client.send(fcm_message)
            logger.info(f"✅ Notification sent to {user_id}: {response}")
            
            # Log notification to Firestore
            self._log_notification(user_id, title, message, data)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error sending immediate notification: {e}")
            return False
    
    def _log_notification(self, user_id: str, title: str, message: str, data: Dict):
        """Log notification to Firestore."""
        try:
            notifications_ref = self.db.collection('notifications')
            notifications_ref.add({
                'user_id': user_id,
                'title': title,
                'message': message,
                'data': data,
                'sent_at': firestore.SERVER_TIMESTAMP,
                'status': 'sent'
            })
        except Exception as e:
            logger.error(f"Error logging notification: {e}")
    
    def add_user_xp(self, user_id: str, amount: int, reason: str = "") -> Dict[str, Any]:
        """Add XP to user and return progress."""
        try:
            if not self.initialized:
                return {"success": False, "error": "Firebase not initialized"}
            
            if amount <= 0 or amount > MAX_XP_GRANT:
                return {"success": False, "error": f"Invalid XP amount: {amount}"}
            
            # Get user progress
            user_ref = self.db.collection('user_progress').document(user_id)
            user_doc = user_ref.get()
            
            if user_doc.exists:
                progress = user_doc.to_dict()
            else:
                progress = {
                    'totalXP': 0,
                    'level': 1,
                    'achievements': [],
                    'quests_completed': 0,
                    'created_at': firestore.SERVER_TIMESTAMP
                }
            
            # Add XP
            old_level = progress.get('level', 1)
            progress['totalXP'] = progress.get('totalXP', 0) + amount
            new_level = (progress['totalXP'] // DEFAULT_XP_PER_LEVEL) + 1
            progress['level'] = new_level
            progress['last_updated'] = firestore.SERVER_TIMESTAMP
            
            # Save progress
            user_ref.set(progress, merge=True)
            
            # Log XP gain
            self.db.collection('xp_logs').add({
                'user_id': user_id,
                'amount': amount,
                'reason': reason,
                'timestamp': firestore.SERVER_TIMESTAMP,
                'old_total': progress['totalXP'] - amount,
                'new_total': progress['totalXP']
            })
            
            # Check for level up
            if new_level > old_level:
                self.send_notification(
                    user_id,
                    "🎉 Level Up!",
                    f"Congratulations! You've reached level {new_level}!",
                    {"type": "level_up", "new_level": str(new_level)}
                )
            
            logger.info(f"✅ Added {amount} XP to user {user_id}: {reason}")
            return {"success": True, "progress": progress}
            
        except Exception as e:
            logger.error(f"❌ Error adding XP: {e}")
            return {"success": False, "error": str(e)}
    
    def get_user_progress(self, user_id: str) -> Dict[str, Any]:
        """Get user progress."""
        try:
            if not self.initialized:
                return {"success": False, "error": "Firebase not initialized"}
            
            user_ref = self.db.collection('user_progress').document(user_id)
            user_doc = user_ref.get()
            
            if user_doc.exists:
                progress = user_doc.to_dict()
                return {"success": True, "progress": progress}
            else:
                # Create default progress
                default_progress = {
                    'totalXP': 0,
                    'level': 1,
                    'achievements': [],
                    'quests_completed': 0,
                    'created_at': firestore.SERVER_TIMESTAMP
                }
                user_ref.set(default_progress)
                return {"success": True, "progress": default_progress}
                
        except Exception as e:
            logger.error(f"❌ Error getting progress: {e}")
            return {"success": False, "error": str(e)}
    
    def save_user_progress(self, user_id: str, progress: Dict[str, Any]) -> bool:
        """Save user progress to Firestore."""
        try:
            if not self.initialized:
                return False
            
            progress['last_updated'] = firestore.SERVER_TIMESTAMP
            user_ref = self.db.collection('user_progress').document(user_id)
            user_ref.set(progress, merge=True)
            
            logger.info(f"✅ Saved progress for user: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving progress: {e}")
            return False
    
    def create_side_quest(self, user_id: str, title: str, description: str, 
                         xp_reward: int = 50, difficulty: str = "medium") -> bool:
        """Create a side quest for the user."""
        try:
            if not self.initialized:
                return False
            
            quest_data = {
                'user_id': user_id,
                'title': title,
                'description': description,
                'xp_reward': xp_reward,
                'difficulty': difficulty,
                'status': 'active',
                'created_at': firestore.SERVER_TIMESTAMP,
                'completed_at': None
            }
            
            # Save quest
            quest_ref = self.db.collection('side_quests').add(quest_data)
            quest_id = quest_ref[1].id
            
            # Send notification
            self.send_notification(
                user_id,
                "⚔️ New Side Quest!",
                f"{title}\n{description}",
                {
                    "type": "side-quest",
                    "questId": quest_id,
                    "xp_reward": str(xp_reward),
                    "difficulty": difficulty
                }
            )
            
            logger.info(f"✅ Created side quest for user {user_id}: {title}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating side quest: {e}")
            return False
    
    def send_reminder(self, user_id: str, message: str, delay_minutes: int = 60) -> bool:
        """Send a reminder notification."""
        return self.send_notification(
            user_id,
            "⏰ Reminder",
            message,
            {"type": "reminder"},
            delay_seconds=delay_minutes * 60
        )
    
    def send_engagement_notification(self, user_id: str) -> bool:
        """Send an engagement notification to bring user back."""
        engagement_messages = [
            "🤖 Jarvis here! Ready for your next adventure?",
            "💡 I have some interesting insights to share with you!",
            "🎯 Time to tackle that next challenge together!",
            "🚀 Let's continue building something amazing!",
            "⭐ Your AI assistant is ready when you are!"
        ]
        
        import random
        message = random.choice(engagement_messages)
        
        return self.send_notification(
            user_id,
            "👋 Jarvis calling!",
            message,
            {"type": "engagement"}
        )

# Global Firebase service instance
firebase_service = FirebaseService()

def get_firebase_service() -> FirebaseService:
    """Get the global Firebase service instance."""
    return firebase_service