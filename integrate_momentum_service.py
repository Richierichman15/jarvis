#!/usr/bin/env python3
"""
Integration script to add momentum notification commands to the existing Discord bot.

This script shows how to integrate the momentum notification service with the existing
discord_jarvis_bot_full.py system.
"""

import asyncio
import logging
from momentum_notification_service import MomentumNotificationService

logger = logging.getLogger(__name__)

# Global momentum service instance
momentum_service = None

async def start_momentum_service():
    """Start the momentum notification service."""
    global momentum_service
    
    try:
        momentum_service = MomentumNotificationService()
        logger.info("✅ Momentum notification service initialized")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to initialize momentum service: {e}")
        return False

async def stop_momentum_service():
    """Stop the momentum notification service."""
    global momentum_service
    
    if momentum_service:
        await momentum_service.stop()
        momentum_service = None
        logger.info("🛑 Momentum notification service stopped")

async def send_momentum_test():
    """Send a test momentum notification."""
    global momentum_service
    
    if not momentum_service:
        return "❌ Momentum service not initialized"
    
    try:
        await momentum_service.send_test_notification()
        return "✅ Test momentum notification sent!"
    except Exception as e:
        return f"❌ Error sending test notification: {e}"

async def get_momentum_status():
    """Get the status of the momentum service."""
    global momentum_service
    
    if not momentum_service:
        return "❌ Momentum service not initialized"
    
    status = {
        "service_running": momentum_service.is_running,
        "last_notification": momentum_service.last_notification,
        "notification_interval": momentum_service.notification_interval,
        "jarvis_client_url": momentum_service.jarvis_client_url,
        "discord_webhook_set": bool(momentum_service.discord_webhook_url)
    }
    
    return f"""📊 **Momentum Service Status**
    
🔄 **Service Status**: {'🟢 Running' if status['service_running'] else '🔴 Stopped'}
⏰ **Interval**: {status['notification_interval'] // 3600} hours
📡 **Jarvis Client**: {status['jarvis_client_url']}
🔗 **Discord Webhook**: {'✅ Set' if status['discord_webhook_set'] else '❌ Not Set'}
📅 **Last Notification**: {status['last_notification'] or 'Never'}"""

# Example integration with Discord bot commands
def add_momentum_commands_to_bot():
    """
    Example of how to add momentum commands to the existing Discord bot.
    
    Add these command handlers to your discord_jarvis_bot_full.py:
    """
    
    example_commands = {
        "/momentum start": "Start momentum notifications every 3 hours",
        "/momentum stop": "Stop momentum notifications", 
        "/momentum test": "Send a test momentum notification",
        "/momentum status": "Show momentum service status",
        "/momentum restart": "Restart the momentum service"
    }
    
    return example_commands

# Example command handler function
async def handle_momentum_command(command: str, message) -> str:
    """Handle momentum-related Discord commands."""
    
    if command == "momentum start":
        if momentum_service and momentum_service.is_running:
            return "⚠️ Momentum service is already running"
        
        success = await start_momentum_service()
        if success:
            # Start the service in background
            asyncio.create_task(momentum_service.start())
            return "✅ Momentum notification service started! You'll receive updates every 3 hours."
        else:
            return "❌ Failed to start momentum service. Check logs for details."
    
    elif command == "momentum stop":
        if not momentum_service or not momentum_service.is_running:
            return "⚠️ Momentum service is not running"
        
        await stop_momentum_service()
        return "🛑 Momentum notification service stopped."
    
    elif command == "momentum test":
        return await send_momentum_test()
    
    elif command == "momentum status":
        return await get_momentum_status()
    
    elif command == "momentum restart":
        await stop_momentum_service()
        await asyncio.sleep(2)  # Brief pause
        success = await start_momentum_service()
        if success:
            asyncio.create_task(momentum_service.start())
            return "🔄 Momentum service restarted successfully!"
        else:
            return "❌ Failed to restart momentum service."
    
    else:
        return """📊 **Momentum Commands Available:**
        
`/momentum start` - Start 3-hour momentum notifications
`/momentum stop` - Stop momentum notifications  
`/momentum test` - Send test notification
`/momentum status` - Show service status
`/momentum restart` - Restart the service"""

if __name__ == "__main__":
    # Example usage
    print("📊 Momentum Service Integration Example")
    print("=" * 50)
    
    commands = add_momentum_commands_to_bot()
    print("Available commands:")
    for cmd, desc in commands.items():
        print(f"  {cmd}: {desc}")
    
    print("\nTo integrate with your Discord bot:")
    print("1. Import this module in discord_jarvis_bot_full.py")
    print("2. Add the command handlers to your command router")
    print("3. Initialize the momentum service in on_ready()")
    print("4. Add cleanup in on_disconnect()")
