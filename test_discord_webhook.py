#!/usr/bin/env python3
"""
Test Discord Webhook Functionality

This script tests the Discord webhook configuration and sends test notifications
to verify that Jarvis can send alerts to Discord.

Usage:
    python test_discord_webhook.py
"""

import asyncio
import aiohttp
import os
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_discord_webhook():
    """Test Discord webhook functionality."""
    
    # Get webhook URL from environment
    webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
    
    if not webhook_url:
        logger.error("❌ DISCORD_WEBHOOK_URL environment variable not set!")
        logger.info("Please set DISCORD_WEBHOOK_URL in your .env file")
        return False
    
    logger.info(f"🔗 Testing webhook URL: {webhook_url[:50]}...")
    
    # Test message
    test_message = f"""🤖 **Jarvis System Test**

**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**Test Status:** ✅ Webhook connection successful!

**System Information:**
• Jarvis monitoring system is operational
• Discord webhook notifications are working
• System alerts will be sent to this channel

**Next Steps:**
• Start the Discord bot to enable full monitoring
• Access the diagnostics dashboard at http://localhost:8080
• Monitor system health with `/diagnostics` command

---
*This is a test message from Jarvis System Monitor*"""
    
    payload = {"content": test_message}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload) as response:
                if response.status == 204:
                    logger.info("✅ Discord webhook test successful!")
                    logger.info("📱 Check your Discord channel for the test message")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Discord webhook failed with status {response.status}")
                    logger.error(f"Error: {error_text}")
                    return False
                    
    except aiohttp.ClientError as e:
        logger.error(f"❌ Connection error: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return False


async def test_system_monitor():
    """Test the system monitor functionality."""
    try:
        from jarvis.monitoring import SystemMonitor
        
        logger.info("🧪 Testing SystemMonitor class...")
        
        # Create a test monitor instance
        monitor = SystemMonitor(monitoring_interval=5)
        
        # Test metrics collection
        logger.info("📊 Testing metrics collection...")
        metrics = await monitor._collect_metrics()
        
        logger.info("✅ SystemMonitor test successful!")
        logger.info(f"📈 Collected metrics for {len(metrics.servers)} servers")
        logger.info(f"🖥️ System CPU: {metrics.cpu_percent:.1f}%")
        logger.info(f"💾 System Memory: {metrics.memory_percent:.1f}%")
        logger.info(f"💿 System Disk: {metrics.disk_percent:.1f}%")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Could not import SystemMonitor: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ SystemMonitor test failed: {e}")
        return False


async def main():
    """Main test function."""
    logger.info("🚀 Starting Jarvis System Monitoring Tests")
    logger.info("=" * 50)
    
    # Test 1: Discord Webhook
    logger.info("\n1️⃣ Testing Discord Webhook...")
    webhook_success = await test_discord_webhook()
    
    # Test 2: System Monitor
    logger.info("\n2️⃣ Testing System Monitor...")
    monitor_success = await test_system_monitor()
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("📋 Test Results Summary:")
    logger.info(f"Discord Webhook: {'✅ PASS' if webhook_success else '❌ FAIL'}")
    logger.info(f"System Monitor: {'✅ PASS' if monitor_success else '❌ FAIL'}")
    
    if webhook_success and monitor_success:
        logger.info("\n🎉 All tests passed! Jarvis monitoring is ready.")
        logger.info("\n📝 Next steps:")
        logger.info("1. Start the Discord bot: python discord_jarvis_bot_full.py")
        logger.info("2. Start the diagnostics dashboard: python -m jarvis.monitoring.diagnostics_dashboard")
        logger.info("3. Monitor system health with Discord commands")
    else:
        logger.info("\n⚠️ Some tests failed. Please check the configuration.")
        
        if not webhook_success:
            logger.info("\n🔧 Discord Webhook Troubleshooting:")
            logger.info("1. Check that DISCORD_WEBHOOK_URL is set in .env file")
            logger.info("2. Verify the webhook URL is correct")
            logger.info("3. Ensure the webhook hasn't been deleted from Discord")
        
        if not monitor_success:
            logger.info("\n🔧 System Monitor Troubleshooting:")
            logger.info("1. Check that all dependencies are installed")
            logger.info("2. Verify the jarvis.monitoring module is accessible")
            logger.info("3. Check system permissions for process monitoring")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n⏹️ Tests interrupted by user")
    except Exception as e:
        logger.error(f"\n💥 Fatal error: {e}")
