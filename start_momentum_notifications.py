#!/usr/bin/env python3
"""
Startup script for Momentum Notification Service.

This script provides easy management of the momentum notification service.
"""

import asyncio
import argparse
import logging
import sys
import os
from momentum_notification_service import MomentumNotificationService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def start_service():
    """Start the momentum notification service."""
    logger.info("🚀 Starting Momentum Notification Service...")
    
    try:
        service = MomentumNotificationService()
        await service.start()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        logger.error("Please check your .env file and ensure DISCORD_WEBHOOK_URL is set")
        return False
    except Exception as e:
        logger.error(f"Error starting service: {e}")
        return False
    
    return True


async def test_service():
    """Test the momentum notification service."""
    logger.info("🧪 Testing Momentum Notification Service...")
    
    try:
        service = MomentumNotificationService()
        await service.send_test_notification()
        logger.info("✅ Test completed successfully")
        return True
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        logger.error("Please check your .env file and ensure DISCORD_WEBHOOK_URL is set")
        return False
    except Exception as e:
        logger.error(f"Error testing service: {e}")
        return False


def check_environment():
    """Check if required environment variables are set."""
    logger.info("🔍 Checking environment configuration...")
    
    required_vars = ['DISCORD_WEBHOOK_URL']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please add these to your .env file:")
        for var in missing_vars:
            logger.error(f"  {var}=your_value_here")
        return False
    
    logger.info("✅ Environment configuration looks good")
    return True


def show_status():
    """Show the current status of the service."""
    logger.info("📊 Momentum Notification Service Status:")
    logger.info(f"  📁 Service file: {os.path.abspath('momentum_notification_service.py')}")
    logger.info(f"  📁 Log file: {os.path.abspath('momentum_notifications.log')}")
    logger.info(f"  🔗 Discord webhook: {'SET' if os.getenv('DISCORD_WEBHOOK_URL') else 'NOT SET'}")
    logger.info(f"  📡 Jarvis client URL: {os.getenv('JARVIS_CLIENT_URL', 'http://localhost:3012')}")
    logger.info(f"  ⏰ Notification interval: 3 hours")


async def main():
    """Main entry point with command line argument handling."""
    parser = argparse.ArgumentParser(description='Momentum Notification Service Manager')
    parser.add_argument('action', choices=['start', 'test', 'status', 'check'], 
                       help='Action to perform')
    
    args = parser.parse_args()
    
    if args.action == 'check':
        success = check_environment()
        sys.exit(0 if success else 1)
    
    elif args.action == 'status':
        show_status()
        sys.exit(0)
    
    elif args.action == 'test':
        success = await test_service()
        sys.exit(0 if success else 1)
    
    elif args.action == 'start':
        # Check environment first
        if not check_environment():
            sys.exit(1)
        
        # Start the service
        success = await start_service()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Service stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
