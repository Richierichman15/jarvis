#!/usr/bin/env python3
"""
Momentum Notification Service - Sends Discord notifications every 3 hours with trading momentum updates.

This service runs continuously and sends momentum signals to Discord at regular intervals.
"""

import asyncio
import aiohttp
import logging
import os
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Import formatter for AI-powered formatting
try:
    from formatter import format_response
    from jarvis.models.model_manager import ModelManager
    FORMATTER_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Could not import formatter or model manager: {e}")
    FORMATTER_AVAILABLE = False

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('momentum_notifications.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MomentumNotificationService:
    """Service that sends momentum updates to Discord every 3 hours."""
    
    def __init__(self):
        """Initialize the momentum notification service."""
        self.jarvis_client_url = os.getenv('JARVIS_CLIENT_URL', 'http://localhost:3012')
        self.discord_webhook_url = os.getenv('DISCORD_WEBHOOK_URL', '')
        self.notification_interval = 3 * 60 * 60  # 3 hours in seconds
        self.session: Optional[aiohttp.ClientSession] = None
        self.is_running = False
        self.last_notification = None
        
        # Initialize model manager for AI formatting
        self.model_manager = None
        if FORMATTER_AVAILABLE:
            try:
                self.model_manager = ModelManager()
                logger.info("✅ Model manager initialized for formatting")
            except Exception as e:
                logger.warning(f"⚠️ Could not initialize model manager: {e}")
                logger.warning("Momentum data will be sent without AI formatting")
        else:
            logger.warning("⚠️ Formatter not available - momentum data will be sent without AI formatting")
        
        # Validate configuration
        if not self.discord_webhook_url:
            logger.error("❌ DISCORD_WEBHOOK_URL not set in environment variables")
            logger.error("Please add DISCORD_WEBHOOK_URL to your .env file")
            raise ValueError("DISCORD_WEBHOOK_URL is required")
        
        logger.info(f"✅ Momentum Notification Service initialized")
        logger.info(f"📡 Jarvis Client URL: {self.jarvis_client_url}")
        logger.info(f"⏰ Notification interval: {self.notification_interval // 3600} hours")
        logger.info(f"🔗 Discord webhook: {'SET' if self.discord_webhook_url else 'NOT SET'}")
    
    async def start(self):
        """Start the momentum notification service."""
        if self.is_running:
            logger.warning("Service is already running")
            return
        
        self.is_running = True
        self.session = aiohttp.ClientSession()
        
        logger.info("🚀 Starting Momentum Notification Service...")
        logger.info("📊 Will send momentum updates every 3 hours")
        
        try:
            # Send initial notification
            await self.send_momentum_notification()
            
            # Start the main loop
            await self._main_loop()
            
        except KeyboardInterrupt:
            logger.info("🛑 Service stopped by user")
        except Exception as e:
            logger.error(f"❌ Error in service: {e}")
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop the momentum notification service."""
        self.is_running = False
        
        if self.session:
            await self.session.close()
            self.session = None
        
        logger.info("🛑 Momentum Notification Service stopped")
    
    async def _main_loop(self):
        """Main service loop that runs every 3 hours."""
        while self.is_running:
            try:
                # Calculate next notification time
                next_notification = datetime.now() + timedelta(seconds=self.notification_interval)
                self.last_notification = next_notification
                
                logger.info(f"⏰ Next momentum notification scheduled for: {next_notification.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Wait for the notification interval
                await asyncio.sleep(self.notification_interval)
                
                if self.is_running:
                    # Send momentum notification
                    await self.send_momentum_notification()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                # Wait a bit before retrying
                await asyncio.sleep(300)  # 5 minutes
    
    async def send_momentum_notification(self):
        """Send momentum signals to Discord."""
        try:
            logger.info("📊 Fetching momentum signals...")
            
            # Get momentum signals from Jarvis
            momentum_data = await self._get_momentum_signals()
            
            if not momentum_data:
                logger.warning("⚠️ No momentum data received")
                return
            
            # Create Discord embed (now async)
            embed = await self._create_momentum_embed(momentum_data)
            
            # Send to Discord
            await self._send_discord_webhook(embed)
            
            logger.info("✅ Momentum notification sent successfully")
            
        except Exception as e:
            logger.error(f"❌ Error sending momentum notification: {e}")
    
    async def _get_momentum_signals(self) -> Optional[Dict[str, Any]]:
        """Get momentum signals from the Jarvis trading server."""
        try:
            if not self.session:
                logger.error("HTTP session not initialized")
                return None
            
            # Call the momentum signals tool
            payload = {
                "tool": "trading.trading.get_momentum_signals",
                "args": {},
                "server": "jarvis"
            }
            
            async with self.session.post(
                f"{self.jarvis_client_url}/run-tool",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('ok'):
                        result = data.get('result', {})
                        logger.info("📈 Momentum signals retrieved successfully")
                        return result
                    else:
                        error_msg = data.get('detail', 'Unknown error')
                        logger.error(f"Tool call failed: {error_msg}")
                        return None
                else:
                    error_msg = await response.text()
                    logger.error(f"HTTP {response.status}: {error_msg}")
                    return None
                    
        except asyncio.TimeoutError:
            logger.error("Timeout while fetching momentum signals")
            return None
        except Exception as e:
            logger.error(f"Error fetching momentum signals: {e}")
            return None
    
    async def _create_momentum_embed(self, momentum_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a Discord embed for momentum signals."""
        current_time = datetime.now()
        
        # Format the momentum data using the same logic as Discord bot
        if isinstance(momentum_data, dict) and 'momentum_signals' in momentum_data:
            signals = momentum_data['momentum_signals']
            
            # Format using AI if available
            if self.model_manager and FORMATTER_AVAILABLE:
                try:
                    # Convert to string for formatter
                    raw_json = json.dumps(momentum_data, indent=2)
                    formatted_text = await format_response(
                        raw_response=raw_json,
                        model_manager=self.model_manager,
                        context="Momentum signals update for Discord notification. Format with emojis and percentages."
                    )
                    description = formatted_text
                except Exception as e:
                    logger.warning(f"AI formatting failed, using fallback: {e}")
                    description = self._format_momentum_fallback(signals)
            else:
                description = self._format_momentum_fallback(signals)
        else:
            # Fallback for unexpected format
            description = json.dumps(momentum_data, indent=2)[:2000]
        
        # Create embed with formatted description
        embed = {
            "title": "📊 Momentum Signals Update",
            "description": description,
            "color": 0x3498DB,
            "timestamp": current_time.isoformat(),
            "footer": {
                "text": "Momentum Notification Service • Updated every 3 hours"
            },
            "fields": [
                {
                    "name": "⏰ Next Update",
                    "value": f"<t:{int((current_time + timedelta(seconds=self.notification_interval)).timestamp())}:R>",
                    "inline": True
                },
                {
                    "name": "🔄 Service Status",
                    "value": "🟢 Active",
                    "inline": True
                }
            ]
        }
        
        return embed
    
    def _format_momentum_fallback(self, signals: Dict[str, Any]) -> str:
        """Fallback formatting when AI is unavailable."""
        lines = []
        
        for symbol, data in list(signals.items())[:10]:  # Limit to 10
            price = data.get('current_price', 0)
            momentum_6h = data.get('momentum_6h_pct', 0)
            momentum_24h = data.get('momentum_24h_pct', 0)
            signal = data.get('signal_strength', 'NEUTRAL')
            
            # Choose emoji based on signal
            if 'UP' in signal:
                emoji = "📈"
            elif 'DOWN' in signal:
                emoji = "📉"
            else:
                emoji = "➡️"
            
            # Format symbol (BTC-USD -> BTC/USD)
            display_symbol = symbol.replace('-', '/')
            
            lines.append(
                f"{emoji} **{display_symbol}**: ${price:,.2f} | "
                f"6h: {momentum_6h:+.2f}% | 24h: {momentum_24h:+.2f}% | {signal}"
            )
        
        return "\n".join(lines) if lines else "No momentum signals available"
    
    async def _send_discord_webhook(self, embed: Dict[str, Any]):
        """Send embed to Discord via webhook."""
        try:
            if not self.session:
                logger.error("HTTP session not initialized")
                return
            
            webhook_data = {
                "embeds": [embed],
                "username": "Jarvis Momentum Bot",
                "avatar_url": "https://cdn.discordapp.com/emojis/1234567890123456789.png"  # Optional: add custom avatar
            }
            
            async with self.session.post(
                self.discord_webhook_url,
                json=webhook_data,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                
                if response.status == 204:
                    logger.info("✅ Discord webhook sent successfully")
                else:
                    error_msg = await response.text()
                    logger.error(f"Discord webhook failed: HTTP {response.status} - {error_msg}")
                    
        except Exception as e:
            logger.error(f"Error sending Discord webhook: {e}")
    
    async def send_test_notification(self):
        """Send a test notification to verify the service is working."""
        logger.info("🧪 Sending test momentum notification...")
        
        # Initialize session if not already done
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        try:
            # Create a test embed
            test_embed = {
                "title": "🧪 Test Momentum Notification",
                "description": "This is a test notification to verify the momentum service is working correctly.",
                "color": 0x00FF00,  # Green color
                "timestamp": datetime.now().isoformat(),
                "footer": {
                    "text": "Test Notification • Momentum Service"
                },
                "fields": [
                    {
                        "name": "✅ Service Status",
                        "value": "Test successful - service is operational",
                        "inline": False
                    }
                ]
            }
            
            await self._send_discord_webhook(test_embed)
            logger.info("✅ Test notification sent")
        finally:
            # Clean up session for test
            if self.session:
                await self.session.close()
                self.session = None


async def main():
    """Main entry point."""
    logger.info("🚀 Starting Momentum Notification Service...")
    
    try:
        service = MomentumNotificationService()
        await service.start()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        logger.error("Please check your .env file and ensure DISCORD_WEBHOOK_URL is set")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        logger.info("👋 Momentum Notification Service shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Service stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
