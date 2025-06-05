"""
Firebase utilities for Jarvis System.
Handles Firebase initialization, push notifications, and deployment operations.
"""
import json
import logging
from typing import Dict, Any, Optional, List
from jarvis.config import config

# Firebase imports with error handling
try:
    import firebase_admin
    from firebase_admin import credentials, messaging
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    logging.warning("Firebase Admin SDK not available. Install with: pip install firebase-admin")

logger = logging.getLogger(__name__)

class FirebaseManager:
    """Manages Firebase operations for the Jarvis system."""
    
    def __init__(self):
        self.app = None
        self.is_initialized = False
        self.notification_tokens = set()
        
    def initialize(self) -> bool:
        """Initialize Firebase Admin SDK."""
        if not FIREBASE_AVAILABLE:
            logger.error("Firebase Admin SDK not available")
            return False
            
        if self.is_initialized:
            logger.info("Firebase already initialized")
            return True
            
        try:
            # Get Firebase credentials from config
            creds = config.get_firebase_credentials()
            if not creds:
                logger.warning("Firebase credentials not configured")
                return False
                
            # Initialize Firebase Admin SDK
            cred = credentials.Certificate(creds)
            self.app = firebase_admin.initialize_app(cred)
            self.is_initialized = True
            
            logger.info("✅ Firebase Admin SDK initialized successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error initializing Firebase Admin SDK: {str(e)}")
            return False
    
    def send_notification(self, token: str, title: str, body: str, 
                         data: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Send a push notification to a specific device."""
        if not self.is_initialized:
            return {"success": False, "error": "Firebase not initialized"}
            
        try:
            # Create the message
            message_data = {
                "notification": messaging.Notification(
                    title=title,
                    body=body
                ),
                "token": token
            }
            
            # Add data payload if provided
            if data:
                message_data["data"] = data
                
            message = messaging.Message(**message_data)
            
            # Send the message
            response = messaging.send(message)
            
            logger.info(f"Notification sent successfully: {response}")
            return {"success": True, "message_id": response}
            
        except messaging.UnregisteredError:
            logger.warning(f"Token is unregistered: {token}")
            self.remove_token(token)
            return {"success": False, "error": "Token unregistered"}
            
        except messaging.InvalidArgumentError as e:
            logger.error(f"Invalid argument for notification: {str(e)}")
            return {"success": False, "error": f"Invalid argument: {str(e)}"}
            
        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def send_multicast_notification(self, tokens: List[str], title: str, body: str,
                                  data: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Send notifications to multiple devices."""
        if not self.is_initialized:
            return {"success": False, "error": "Firebase not initialized"}
            
        if not tokens:
            return {"success": False, "error": "No tokens provided"}
            
        try:
            # Create the multicast message
            message_data = {
                "notification": messaging.Notification(
                    title=title,
                    body=body
                ),
                "tokens": tokens
            }
            
            # Add data payload if provided
            if data:
                message_data["data"] = data
                
            message = messaging.MulticastMessage(**message_data)
            
            # Send the message
            response = messaging.send_multicast(message)
            
            # Handle failed tokens
            if response.failure_count > 0:
                failed_tokens = []
                for idx, resp in enumerate(response.responses):
                    if not resp.success:
                        failed_token = tokens[idx]
                        failed_tokens.append(failed_token)
                        
                        # Remove unregistered tokens
                        if isinstance(resp.exception, messaging.UnregisteredError):
                            self.remove_token(failed_token)
                
                logger.warning(f"Failed to send to {len(failed_tokens)} tokens")
            
            logger.info(f"Multicast notification sent. Success: {response.success_count}, Failed: {response.failure_count}")
            
            return {
                "success": True,
                "success_count": response.success_count,
                "failure_count": response.failure_count,
                "responses": [{"success": resp.success, "message_id": resp.message_id if resp.success else None} 
                             for resp in response.responses]
            }
            
        except Exception as e:
            logger.error(f"Error sending multicast notification: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def add_token(self, token: str) -> bool:
        """Add a notification token to the active set."""
        if token:
            self.notification_tokens.add(token)
            logger.info(f"Added notification token: {token[:20]}...")
            return True
        return False
    
    def remove_token(self, token: str) -> bool:
        """Remove a notification token from the active set."""
        if token in self.notification_tokens:
            self.notification_tokens.remove(token)
            logger.info(f"Removed notification token: {token[:20]}...")
            return True
        return False
    
    def get_active_tokens(self) -> List[str]:
        """Get all active notification tokens."""
        return list(self.notification_tokens)
    
    def subscribe_to_topic(self, tokens: List[str], topic: str) -> Dict[str, Any]:
        """Subscribe tokens to a topic for topic-based messaging."""
        if not self.is_initialized:
            return {"success": False, "error": "Firebase not initialized"}
            
        try:
            response = messaging.subscribe_to_topic(tokens, topic)
            
            logger.info(f"Subscribed {response.success_count} tokens to topic '{topic}'")
            
            return {
                "success": True,
                "success_count": response.success_count,
                "failure_count": response.failure_count
            }
            
        except Exception as e:
            logger.error(f"Error subscribing to topic: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def unsubscribe_from_topic(self, tokens: List[str], topic: str) -> Dict[str, Any]:
        """Unsubscribe tokens from a topic."""
        if not self.is_initialized:
            return {"success": False, "error": "Firebase not initialized"}
            
        try:
            response = messaging.unsubscribe_from_topic(tokens, topic)
            
            logger.info(f"Unsubscribed {response.success_count} tokens from topic '{topic}'")
            
            return {
                "success": True,
                "success_count": response.success_count,
                "failure_count": response.failure_count
            }
            
        except Exception as e:
            logger.error(f"Error unsubscribing from topic: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def send_topic_notification(self, topic: str, title: str, body: str,
                              data: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Send notification to all devices subscribed to a topic."""
        if not self.is_initialized:
            return {"success": False, "error": "Firebase not initialized"}
            
        try:
            # Create the message
            message_data = {
                "notification": messaging.Notification(
                    title=title,
                    body=body
                ),
                "topic": topic
            }
            
            # Add data payload if provided
            if data:
                message_data["data"] = data
                
            message = messaging.Message(**message_data)
            
            # Send the message
            response = messaging.send(message)
            
            logger.info(f"Topic notification sent to '{topic}': {response}")
            return {"success": True, "message_id": response}
            
        except Exception as e:
            logger.error(f"Error sending topic notification: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def validate_token(self, token: str) -> bool:
        """Validate if a token is still active."""
        if not self.is_initialized:
            return False
            
        try:
            # Try to send a test message (dry run)
            message = messaging.Message(
                notification=messaging.Notification(
                    title="Test",
                    body="Test"
                ),
                token=token
            )
            
            # Use dry_run to validate without actually sending
            messaging.send(message, dry_run=True)
            return True
            
        except messaging.UnregisteredError:
            self.remove_token(token)
            return False
        except Exception:
            return False
    
    def get_web_config(self) -> Dict[str, Any]:
        """Get Firebase web configuration for frontend."""
        return config.get_firebase_web_config()
    
    def cleanup_invalid_tokens(self) -> int:
        """Remove invalid tokens from the active set."""
        if not self.is_initialized:
            return 0
            
        invalid_tokens = []
        for token in self.notification_tokens.copy():
            if not self.validate_token(token):
                invalid_tokens.append(token)
        
        for token in invalid_tokens:
            self.remove_token(token)
            
        logger.info(f"Cleaned up {len(invalid_tokens)} invalid tokens")
        return len(invalid_tokens)

# Global Firebase manager instance
firebase_manager = FirebaseManager()

def get_firebase_manager() -> FirebaseManager:
    """Get the global Firebase manager instance."""
    return firebase_manager

# Convenience functions
def send_notification(token: str, title: str, body: str, data: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Send a notification (convenience function)."""
    return firebase_manager.send_notification(token, title, body, data)

def send_multicast_notification(tokens: List[str], title: str, body: str, data: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Send multicast notification (convenience function)."""
    return firebase_manager.send_multicast_notification(tokens, title, body, data)

def broadcast_notification(title: str, body: str, data: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Broadcast notification to all active tokens."""
    tokens = firebase_manager.get_active_tokens()
    if not tokens:
        return {"success": False, "error": "No active tokens"}
    return firebase_manager.send_multicast_notification(tokens, title, body, data)