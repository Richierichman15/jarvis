"""
Jarvis Event Listener - Subscribes to trading MCP server events and sends Discord notifications.
"""

import asyncio
import aiohttp
import discord
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from collections import deque

logger = logging.getLogger(__name__)


class TradingEventListener:
    """Listens for trading events and sends Discord notifications."""
    
    def __init__(self, jarvis_client_url: str, discord_channel: discord.TextChannel):
        """
        Initialize the event listener.
        
        Args:
            jarvis_client_url: URL of Jarvis Client HTTP Server
            discord_channel: Discord channel to send notifications to
        """
        self.jarvis_client_url = jarvis_client_url
        self.discord_channel = discord_channel
        self.session: Optional[aiohttp.ClientSession] = None
        self.monitoring_task: Optional[asyncio.Task] = None
        self.is_monitoring = False
        self.event_history = deque(maxlen=100)  # Keep last 100 events
        self.event_stats = {
            "market_alert": 0,
            "trade_executed": 0,
            "risk_limit_hit": 0,
            "portfolio_milestone": 0,
            "stop_triggered": 0,
            "daily_summary": 0,
            "system_status": 0
        }
        self.pending_events: List[Dict[str, Any]] = []  # For batching
        self.batch_timer: Optional[asyncio.Task] = None
    
    async def start_monitoring(self):
        """Start monitoring trading events."""
        if self.is_monitoring:
            logger.warning("Event monitoring already running")
            return False
        
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        # Start the monitoring loop
        self.is_monitoring = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        logger.info("✅ Event monitoring started")
        return True
    
    async def stop_monitoring(self):
        """Stop monitoring trading events."""
        if not self.is_monitoring:
            logger.warning("Event monitoring not running")
            return False
        
        self.is_monitoring = False
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        if self.batch_timer:
            self.batch_timer.cancel()
        
        logger.info("🛑 Event monitoring stopped")
        return True
    
    async def _monitoring_loop(self):
        """Main monitoring loop that checks for events."""
        logger.info("Starting event monitoring loop...")
        
        while self.is_monitoring:
            try:
                # Call the trading server to check for events
                # This could be polling or a long-polling endpoint
                async with self.session.get(
                    f"{self.jarvis_client_url}/tools",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        # Check if there are any pending events
                        # In a real implementation, you'd have a specific events endpoint
                        pass
                
                # Poll every 5 seconds
                await asyncio.sleep(5)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(10)  # Wait longer on error
    
    async def handle_event(self, event: Dict[str, Any]):
        """
        Handle an incoming event from the trading server.
        
        Args:
            event: Event data with 'type' and other fields
        """
        # Run in background task so it doesn't block
        asyncio.create_task(self._process_event(event))
    
    async def _process_event(self, event: Dict[str, Any]):
        """Process and send event notification."""
        try:
            event_type = event.get("type", "unknown")
            
            # Update statistics
            if event_type in self.event_stats:
                self.event_stats[event_type] += 1
            
            # Add to history
            event["received_at"] = datetime.now().isoformat()
            self.event_history.append(event)
            
            # Log event
            logger.info(f"📨 Received event: {event_type}")
            
            # Create Discord embed based on event type
            embed = self._create_embed(event)
            
            if embed:
                # Check if we should batch this
                if self._should_batch(event_type):
                    self.pending_events.append(event)
                    
                    # Start batch timer if not already running
                    if not self.batch_timer or self.batch_timer.done():
                        self.batch_timer = asyncio.create_task(self._send_batched_events())
                else:
                    # Send immediately
                    await self.discord_channel.send(embed=embed)
                    logger.info(f"✅ Sent Discord notification for {event_type}")
            
        except Exception as e:
            logger.error(f"Error processing event: {e}", exc_info=True)
    
    def _should_batch(self, event_type: str) -> bool:
        """Determine if this event type should be batched."""
        # Batch frequent events like market_alert
        batch_types = ["market_alert"]
        return event_type in batch_types
    
    async def _send_batched_events(self):
        """Send batched events after a delay."""
        await asyncio.sleep(30)  # Wait 30 seconds to batch
        
        if self.pending_events:
            events = self.pending_events.copy()
            self.pending_events.clear()
            
            # Create combined message
            if len(events) == 1:
                # Just send single event
                embed = self._create_embed(events[0])
                await self.discord_channel.send(embed=embed)
            else:
                # Create batched embed
                embed = discord.Embed(
                    title=f"📊 Market Updates ({len(events)} alerts)",
                    color=0x3498DB,
                    timestamp=datetime.now()
                )
                
                description_parts = []
                for event in events[:10]:  # Limit to 10 to avoid exceeding limits
                    symbol = event.get("symbol", "Unknown")
                    change = event.get("change_percent", 0)
                    price = event.get("price", 0)
                    emoji = "🟢" if change > 0 else "🔴"
                    description_parts.append(
                        f"{emoji} **{symbol}**: {change:+.2f}% → ${price:,.2f}"
                    )
                
                if len(events) > 10:
                    description_parts.append(f"\n*...and {len(events) - 10} more alerts*")
                
                embed.description = "\n".join(description_parts)
                await self.discord_channel.send(embed=embed)
            
            logger.info(f"✅ Sent batched notification for {len(events)} events")
    
    def _create_embed(self, event: Dict[str, Any]) -> Optional[discord.Embed]:
        """Create a Discord embed for an event."""
        event_type = event.get("type", "unknown")
        
        if event_type == "market_alert":
            return self._create_market_alert_embed(event)
        elif event_type == "trade_executed":
            return self._create_trade_executed_embed(event)
        elif event_type == "risk_limit_hit":
            return self._create_risk_limit_embed(event)
        elif event_type == "portfolio_milestone":
            return self._create_portfolio_milestone_embed(event)
        elif event_type == "stop_triggered":
            return self._create_stop_triggered_embed(event)
        elif event_type == "daily_summary":
            return self._create_daily_summary_embed(event)
        elif event_type == "system_status":
            return self._create_system_status_embed(event)
        else:
            logger.warning(f"Unknown event type: {event_type}")
            return None
    
    def _create_market_alert_embed(self, event: Dict[str, Any]) -> discord.Embed:
        """Create embed for market_alert event."""
        symbol = event.get("symbol", "Unknown")
        change = event.get("change_percent", 0)
        price = event.get("price", 0)
        volume = event.get("volume", 0)
        timeframe = event.get("timeframe", "1h")
        
        color = 0x00FF00 if change > 0 else 0xFF0000  # Green up, red down
        emoji = "📈" if change > 0 else "📉"
        
        embed = discord.Embed(
            title=f"🚨 Market Alert: {symbol}",
            description=f"{emoji} **{symbol}** moved **{change:+.2f}%** in the last {timeframe}",
            color=color,
            timestamp=datetime.now()
        )
        
        embed.add_field(name="Current Price", value=f"${price:,.2f}", inline=True)
        embed.add_field(name="Change", value=f"{change:+.2f}%", inline=True)
        if volume:
            embed.add_field(name="Volume", value=f"${volume:,.0f}", inline=True)
        
        embed.set_footer(text=f"Alert triggered at {datetime.now().strftime('%H:%M:%S')}")
        
        return embed
    
    def _create_trade_executed_embed(self, event: Dict[str, Any]) -> discord.Embed:
        """Create embed for trade_executed event."""
        side = event.get("side", "UNKNOWN")
        symbol = event.get("symbol", "Unknown")
        size = event.get("size", 0)
        price = event.get("price", 0)
        pnl_percent = event.get("pnl_percent", 0)
        order_type = event.get("order_type", "MARKET")
        
        color = 0x00FF00 if side == "BUY" else 0xFF6B6B
        emoji = "🟢" if side == "BUY" else "🔴"
        
        embed = discord.Embed(
            title=f"✅ Trade Executed: {side} {symbol}",
            description=f"{emoji} **{side}** {size} {symbol} @ ${price:,.2f}",
            color=color,
            timestamp=datetime.now()
        )
        
        embed.add_field(name="Side", value=side, inline=True)
        embed.add_field(name="Size", value=f"{size:,.4f}", inline=True)
        embed.add_field(name="Price", value=f"${price:,.2f}", inline=True)
        embed.add_field(name="Order Type", value=order_type, inline=True)
        
        if pnl_percent:
            pnl_emoji = "📈" if pnl_percent > 0 else "📉"
            embed.add_field(
                name="P&L",
                value=f"{pnl_emoji} {pnl_percent:+.2f}%",
                inline=True
            )
        
        embed.set_footer(text=f"Executed at {datetime.now().strftime('%H:%M:%S')}")
        
        return embed
    
    def _create_risk_limit_embed(self, event: Dict[str, Any]) -> discord.Embed:
        """Create embed for risk_limit_hit event."""
        reason = event.get("reason", "Unknown risk threshold")
        impact = event.get("impact", "Trading halted")
        current_loss = event.get("current_loss", 0)
        limit = event.get("limit", 0)
        
        embed = discord.Embed(
            title="⚠️ Risk Threshold Triggered",
            description=f"**{reason}**\n\nImpact: {impact}",
            color=0xFF0000,
            timestamp=datetime.now()
        )
        
        if current_loss:
            embed.add_field(
                name="Current Loss",
                value=f"{current_loss:.2f}%",
                inline=True
            )
        if limit:
            embed.add_field(
                name="Limit",
                value=f"{limit:.2f}%",
                inline=True
            )
        
        embed.set_footer(text="⚠️ Review your positions immediately")
        
        return embed
    
    def _create_portfolio_milestone_embed(self, event: Dict[str, Any]) -> discord.Embed:
        """Create embed for portfolio_milestone event."""
        milestone = event.get("milestone", 0)
        total_pnl = event.get("total_pnl", 0)
        total_pnl_percent = event.get("total_pnl_percent", 0)
        
        color = 0x00FF00 if total_pnl_percent > 0 else 0xFF0000
        emoji = "🎉" if total_pnl_percent > 0 else "⚠️"
        
        embed = discord.Embed(
            title=f"{emoji} Portfolio Milestone: {milestone}%",
            description=f"Your portfolio has crossed the **{milestone}%** threshold!",
            color=color,
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="Total P&L",
            value=f"${total_pnl:,.2f} ({total_pnl_percent:+.2f}%)",
            inline=False
        )
        
        embed.set_footer(text="Keep up the great work!" if total_pnl_percent > 0 else "Monitor your positions")
        
        return embed
    
    def _create_stop_triggered_embed(self, event: Dict[str, Any]) -> discord.Embed:
        """Create embed for stop_triggered event."""
        symbol = event.get("symbol", "Unknown")
        current_price = event.get("current_price", 0)
        stop_price = event.get("stop_price", 0)
        distance_percent = event.get("distance_percent", 0)
        
        embed = discord.Embed(
            title=f"🛑 Stop Alert: {symbol}",
            description=f"**{symbol}** is approaching your trailing stop",
            color=0xFFA500,
            timestamp=datetime.now()
        )
        
        embed.add_field(name="Current Price", value=f"${current_price:,.2f}", inline=True)
        embed.add_field(name="Stop Price", value=f"${stop_price:,.2f}", inline=True)
        embed.add_field(name="Distance", value=f"{distance_percent:.2f}%", inline=True)
        
        embed.set_footer(text="⚠️ Price is near your stop loss")
        
        return embed
    
    def _create_daily_summary_embed(self, event: Dict[str, Any]) -> discord.Embed:
        """Create embed for daily_summary event."""
        total_trades = event.get("total_trades", 0)
        win_rate = event.get("win_rate", 0)
        total_pnl = event.get("total_pnl", 0)
        total_pnl_percent = event.get("total_pnl_percent", 0)
        best_trade = event.get("best_trade", {})
        worst_trade = event.get("worst_trade", {})
        
        color = 0x00FF00 if total_pnl_percent > 0 else 0xFF0000
        
        embed = discord.Embed(
            title="📊 Daily Trading Summary",
            description=f"Here's your performance for today",
            color=color,
            timestamp=datetime.now()
        )
        
        embed.add_field(name="Total Trades", value=str(total_trades), inline=True)
        embed.add_field(name="Win Rate", value=f"{win_rate:.1f}%", inline=True)
        embed.add_field(
            name="Total P&L",
            value=f"${total_pnl:,.2f} ({total_pnl_percent:+.2f}%)",
            inline=True
        )
        
        if best_trade:
            embed.add_field(
                name="🏆 Best Trade",
                value=f"{best_trade.get('symbol', 'N/A')}: +{best_trade.get('pnl_percent', 0):.2f}%",
                inline=True
            )
        
        if worst_trade:
            embed.add_field(
                name="📉 Worst Trade",
                value=f"{worst_trade.get('symbol', 'N/A')}: {worst_trade.get('pnl_percent', 0):.2f}%",
                inline=True
            )
        
        embed.set_footer(text="Daily summary • Updated every 24 hours")
        
        return embed
    
    def _create_system_status_embed(self, event: Dict[str, Any]) -> discord.Embed:
        """Create embed for system_status event."""
        status = event.get("status", "unknown")
        message = event.get("message", "System status change")
        severity = event.get("severity", "info")
        
        color_map = {
            "emergency": 0xFF0000,
            "warning": 0xFFA500,
            "info": 0x3498DB,
            "success": 0x00FF00
        }
        
        emoji_map = {
            "emergency": "🚨",
            "warning": "⚠️",
            "info": "ℹ️",
            "success": "✅"
        }
        
        color = color_map.get(severity, 0x3498DB)
        emoji = emoji_map.get(severity, "ℹ️")
        
        embed = discord.Embed(
            title=f"{emoji} System Status: {status.upper()}",
            description=message,
            color=color,
            timestamp=datetime.now()
        )
        
        embed.add_field(name="Status", value=status.upper(), inline=True)
        embed.add_field(name="Severity", value=severity.upper(), inline=True)
        
        embed.set_footer(text="Trading system status update")
        
        return embed
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get event statistics."""
        total_events = sum(self.event_stats.values())
        
        return {
            "total_events": total_events,
            "by_type": self.event_stats.copy(),
            "is_monitoring": self.is_monitoring,
            "history_size": len(self.event_history)
        }
    
    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent event history."""
        history_list = list(self.event_history)
        return history_list[-limit:] if limit else history_list
    
    async def cleanup(self):
        """Cleanup resources."""
        await self.stop_monitoring()
        
        if self.session:
            await self.session.close()
            self.session = None

