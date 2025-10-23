#!/usr/bin/env python3
"""
TraderAgent - Specialized agent for trading and portfolio management

This agent handles all trading-related tasks including portfolio management,
market data retrieval, trade execution, and risk analysis using MCP server commands.
"""

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional
from datetime import datetime

# Load DATA_PATH from environment
DATA_PATH = os.getenv("DATA_PATH", "app/data")

try:
    from .agent_base import AgentBase, AgentCapability, TaskRequest, TaskResponse
except ImportError:
    # Handle direct execution
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from jarvis.agents.agent_base import AgentBase, AgentCapability, TaskRequest, TaskResponse

# Define data file paths using DATA_PATH
PORTFOLIO_PATH = os.path.join(DATA_PATH, "live", "live_portfolio_state.json")
LIVE_TRADES_PATH = os.path.join(DATA_PATH, "live", "live_trades.json")
EXIT_ENGINE_PATH = os.path.join(DATA_PATH, "live", "exit_engine_state.json")

# Default data structures
DEFAULT_PORTFOLIO_DATA = {
    "portfolio_value": 5000.0,
    "cash": 5000.0,
    "initial_balance": 5000.0,
    "return_percentage": 0.0,
    "trading_active": True,
    "positions": {},
    "crypto_symbols": ["BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "ADA-USD", "TRX-USD", "XLM-USD", "PAXG-USD"],
    "last_updated": "2025-01-18T12:00:00Z",
    "daily_pnl": 0.0,
    "daily_drawdown": 0.0,
    "daily_trade_count": 0,
    "daily_start_value": 5000.0,
    "daily_start_value_date": "2025-01-18"
}

DEFAULT_LIVE_TRADES_DATA = {
    "trades": []
}

DEFAULT_EXIT_ENGINE_DATA = {
    "active_trades": {},
    "trailing_stops": {},
    "trade_states": {},
    "last_updated": "2025-01-18T12:00:00Z"
}

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TraderAgent(AgentBase):
    """Specialized agent for trading operations using MCP server commands."""
    
    def __init__(self, **kwargs):
        super().__init__(
            name="TraderAgent",
            capabilities=[AgentCapability.TRADING],
            version="1.0.0",
            **kwargs
        )
        
        # Trading-specific configuration
        self.trading_config = {
            "max_position_size": 10000,
            "risk_tolerance": "medium",
            "default_timeframe": "1h",
            "supported_exchanges": ["binance", "coinbase", "kraken"],
            "trading_mode": "live"  # Primary mode
        }
        
        # Trading state
        self.active_positions = {}
        self.pending_orders = {}
        self.market_data_cache = {}
        
        # Personality
        self.personality = "pragmatic, risk-aware, data-driven"

        # Pattern memory DB
        try:
            from .memory_utils import TraderMemoryDB
            from pathlib import Path
            db_dir = Path("data").absolute()
            db_dir.mkdir(parents=True, exist_ok=True)
            self.trader_db = TraderMemoryDB(str(db_dir / "trader_memory.sqlite"))
        except Exception as e:
            self.trader_db = None
            self.logger.warning(f"Trader DB unavailable, continuing without persistence: {e}")
        
        self.logger = logging.getLogger("agent.trader")
    
    async def start(self, redis_comm=None, agent_manager=None):
        """Start the agent with data file verification."""
        # Log startup information
        print(f"[TraderAgent] CWD: {os.getcwd()}")
        print(f"[TraderAgent] DATA_PATH: {DATA_PATH}")
        print(f"[TraderAgent] Portfolio Path -> {os.path.abspath(PORTFOLIO_PATH)}")
        print(f"[TraderAgent] Exists: {os.path.exists(PORTFOLIO_PATH)}")
        print(f"[TraderAgent] Live Trades Path -> {os.path.abspath(LIVE_TRADES_PATH)}")
        print(f"[TraderAgent] Exists: {os.path.exists(LIVE_TRADES_PATH)}")
        print(f"[TraderAgent] Exit Engine Path -> {os.path.abspath(EXIT_ENGINE_PATH)}")
        print(f"[TraderAgent] Exists: {os.path.exists(EXIT_ENGINE_PATH)}")
        
        # Verify data files exist
        await self._verify_data_files()
        
        # Call parent start method
        await super().start(redis_comm, agent_manager)
    
    async def _verify_data_files(self):
        """Verify and create required data files."""
        required_files = [
            {"path": PORTFOLIO_PATH, "default_data": DEFAULT_PORTFOLIO_DATA},
            {"path": LIVE_TRADES_PATH, "default_data": DEFAULT_LIVE_TRADES_DATA},
            {"path": EXIT_ENGINE_PATH, "default_data": DEFAULT_EXIT_ENGINE_DATA}
        ]
        self._verify_data_files_helper(required_files)
    
    def _verify_data_files_helper(self, required_files):
        """Helper to verify and create data files."""
        import json
        for file_info in required_files:
            file_path = file_info['path']
            default_data = file_info.get('default_data', {})
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Create file with default data if it doesn't exist
            if not os.path.exists(file_path):
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(default_data, f, indent=2, ensure_ascii=False)
                    print(f"WARNING: Created placeholder: {file_path}")
                except Exception as e:
                    print(f"ERROR: Failed to create {file_path}: {e}")
    
    def _register_task_handlers(self):
        """Register trading task handlers for MCP server commands."""
        # Live Trading (Primary) Commands
        self.register_task_handler("portfolio.get_overview", self._handle_portfolio_overview)
        self.register_task_handler("portfolio.get_positions", self._handle_portfolio_positions)
        self.register_task_handler("portfolio.get_trades", self._handle_portfolio_trades)
        self.register_task_handler("portfolio.get_performance", self._handle_portfolio_performance)
        self.register_task_handler("trading.get_portfolio_balance", self._handle_trading_balance)
        self.register_task_handler("trading.get_recent_executions", self._handle_recent_executions)
        self.register_task_handler("trading.get_momentum_signals", self._handle_momentum_signals)
        
        # Paper Trading (Secondary) Commands
        self.register_task_handler("paper.get_portfolio", self._handle_paper_portfolio)
        self.register_task_handler("paper.get_balance", self._handle_paper_balance)
        self.register_task_handler("paper.get_performance", self._handle_paper_performance)
        self.register_task_handler("paper.get_trades", self._handle_paper_trades)
    
    async def _initialize(self):
        """Initialize trading-specific resources."""
        try:
            # Initialize trading connections
            await self._initialize_trading_connections()
            
            # Load trading configuration
            await self._load_trading_config()
            
            # Start market data updates
            self.market_data_task = asyncio.create_task(self._update_market_data())
            
            self.logger.info("TraderAgent initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize TraderAgent: {e}")
            raise
    
    async def _cleanup(self):
        """Cleanup trading resources."""
        try:
            # Cancel market data updates
            if hasattr(self, 'market_data_task'):
                self.market_data_task.cancel()
                try:
                    await self.market_data_task
                except asyncio.CancelledError:
                    pass
            
            # Close trading connections
            await self._close_trading_connections()
            
            self.logger.info("TraderAgent cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during TraderAgent cleanup: {e}")
    
    async def _initialize_trading_connections(self):
        """Initialize connections to trading APIs."""
        # This would connect to actual trading APIs
        # For now, we'll simulate the connections
        self.logger.info("Initializing trading connections...")
        await asyncio.sleep(0.1)  # Simulate connection time
        self.logger.info("Trading connections established")
    
    async def _close_trading_connections(self):
        """Close trading API connections."""
        self.logger.info("Closing trading connections...")
        await asyncio.sleep(0.1)  # Simulate cleanup time
        self.logger.info("Trading connections closed")
    
    async def _load_trading_config(self):
        """Load trading configuration."""
        # This would load from config files or database
        self.logger.info("Loading trading configuration...")
        await asyncio.sleep(0.1)  # Simulate loading time
        self.logger.info("Trading configuration loaded")
    
    async def _update_market_data(self):
        """Periodically update market data cache."""
        while self.status.value == "running":
            try:
                # Update market data for active symbols
                for symbol in self.active_positions.keys():
                    await self._fetch_market_data(symbol)
                
                await asyncio.sleep(30)  # Update every 30 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error updating market data: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _fetch_market_data(self, symbol: str):
        """Fetch market data for a symbol."""
        # This would fetch real market data
        # For now, we'll simulate it
        self.market_data_cache[symbol] = {
            "price": 50000.0 + (hash(symbol) % 10000),
            "volume": 1000000,
            "timestamp": datetime.now()
        }
    
    async def _call_mcp_server(self, tool_name: str, args: dict = None, server: str = "trading") -> dict:
        """Helper method to call MCP server tools."""
        import aiohttp
        if args is None:
            args = {}
        
        self.logger.info(f"🌐 Making HTTP request to MCP server: {tool_name} on {server}")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:3012/run-tool",
                json={"tool": tool_name, "args": args, "server": server},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                self.logger.info(f"📡 HTTP response status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    self.logger.info(f"📦 Response data: {data}")
                    if data.get('ok'):
                        result = data.get('result', {})
                        self.logger.info(f"✅ MCP server returned: {result}")
                        return result
                    else:
                        error_msg = f"MCP server error: {data.get('detail', 'Unknown error')}"
                        self.logger.error(f"❌ {error_msg}")
                        raise Exception(error_msg)
                else:
                    error_msg = f"HTTP error: {response.status}"
                    self.logger.error(f"❌ {error_msg}")
                    raise Exception(error_msg)
    
    # Live Trading Handler Methods
    async def _handle_portfolio_overview(self, task: TaskRequest) -> TaskResponse:
        """Handle portfolio overview requests."""
        try:
            self.logger.info(f"📊 Handling portfolio overview request...")
            result = await self._call_mcp_server("portfolio.get_overview", {}, "trading")
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=result
            )
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_portfolio_positions(self, task: TaskRequest) -> TaskResponse:
        """Handle portfolio positions requests."""
        try:
            self.logger.info(f"📈 Handling portfolio positions request...")
            result = await self._call_mcp_server("portfolio.get_positions", {}, "trading")
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=result
            )
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_portfolio_trades(self, task: TaskRequest) -> TaskResponse:
        """Handle portfolio trades requests."""
        try:
            limit = task.parameters.get("limit", 50)
            symbol = task.parameters.get("symbol")
            
            args = {"limit": limit}
            if symbol:
                args["symbol"] = symbol
            
            self.logger.info(f"📋 Handling portfolio trades request...")
            result = await self._call_mcp_server("portfolio.get_trades", args, "trading")
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=result
            )
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_portfolio_performance(self, task: TaskRequest) -> TaskResponse:
        """Handle portfolio performance requests."""
        try:
            self.logger.info(f"📊 Handling portfolio performance request...")
            result = await self._call_mcp_server("portfolio.get_performance", {}, "trading")
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=result
            )
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_trading_balance(self, task: TaskRequest) -> TaskResponse:
        """Handle trading balance requests."""
        try:
            self.logger.info(f"💰 Handling trading balance request...")
            result = await self._call_mcp_server("trading.get_portfolio_balance", {}, "trading")
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=result
            )
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_recent_executions(self, task: TaskRequest) -> TaskResponse:
        """Handle recent executions requests."""
        try:
            limit = task.parameters.get("limit", 20)
            symbol = task.parameters.get("symbol")
            
            args = {"limit": limit}
            if symbol:
                args["symbol"] = symbol
            
            self.logger.info(f"⚡ Handling recent executions request...")
            result = await self._call_mcp_server("trading.get_recent_executions", args, "trading")
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=result
            )
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_momentum_signals(self, task: TaskRequest) -> TaskResponse:
        """Handle momentum signals requests."""
        try:
            symbols = task.parameters.get("symbols")
            
            args = {}
            if symbols:
                args["symbols"] = symbols
            
            self.logger.info(f"📈 Handling momentum signals request...")
            result = await self._call_mcp_server("trading.get_momentum_signals", args, "trading")
            
            # Persist signals for pattern learning (best-effort)
            try:
                signals = result.get("momentum_signals") if isinstance(result, dict) else None
                if signals and hasattr(self, 'trader_db') and self.trader_db:
                    self.trader_db.log_momentum_signals(signals)
            except Exception as e:
                self.logger.warning(f"Failed to persist momentum signals: {e}")
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=result
            )
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    # Paper Trading Handler Methods
    async def _handle_paper_portfolio(self, task: TaskRequest) -> TaskResponse:
        """Handle paper portfolio requests."""
        try:
            self.logger.info(f"📄 Handling paper portfolio request...")
            result = await self._call_mcp_server("paper.get_portfolio", {}, "trading")
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=result
            )
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_paper_balance(self, task: TaskRequest) -> TaskResponse:
        """Handle paper balance requests."""
        try:
            self.logger.info(f"💰 Handling paper balance request...")
            result = await self._call_mcp_server("paper.get_balance", {}, "trading")
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=result
            )
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_paper_performance(self, task: TaskRequest) -> TaskResponse:
        """Handle paper performance requests."""
        try:
            self.logger.info(f"📊 Handling paper performance request...")
            result = await self._call_mcp_server("paper.get_performance", {}, "trading")
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=result
            )
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_paper_trades(self, task: TaskRequest) -> TaskResponse:
        """Handle paper trades requests."""
        try:
            limit = task.parameters.get("limit", 50)
            symbol = task.parameters.get("symbol")
            
            args = {"limit": limit}
            if symbol:
                args["symbol"] = symbol
            
            self.logger.info(f"📋 Handling paper trades request...")
            result = await self._call_mcp_server("paper.get_trades", args, "trading")
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=result
            )
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )

    async def _handle_task(self, task: TaskRequest) -> TaskResponse:
        """Handle trading tasks."""
        try:
            handler = self.task_handlers.get(task.task_type)
            if handler:
                return await handler(task)
            else:
                raise ValueError(f"Unknown trading task type: {task.task_type}")
                
        except Exception as e:
            self.logger.error(f"Error handling trading task {task.task_type}: {e}")
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    # Live Trading (Primary) Command Handlers
    
    async def _handle_portfolio_overview(self, task: TaskRequest) -> TaskResponse:
        """Handle live portfolio overview request."""
        try:
            self.logger.info(f"🔍 Calling MCP server for portfolio.get_overview...")
            # Call the real MCP server for portfolio data
            portfolio_data = await self._call_mcp_server("portfolio.get_overview", {}, "trading")
            self.logger.info(f"📊 Received portfolio data: {portfolio_data}")
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=portfolio_data
            )
            
        except Exception as e:
            self.logger.error(f"❌ Error calling MCP server: {e}")
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_portfolio_positions(self, task: TaskRequest) -> TaskResponse:
        """Handle live portfolio positions request."""
        try:
            # Call the real MCP server for positions data
            positions_data = await self._call_mcp_server("portfolio.get_positions", {}, "trading")
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=positions_data
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_portfolio_trades(self, task: TaskRequest) -> TaskResponse:
        """Handle live portfolio trades request."""
        try:
            self.logger.info(f"🔍 Calling MCP server for portfolio.get_trades...")
            # Call the real MCP server for portfolio trades
            trades_data = await self._call_mcp_server("portfolio.get_trades", {}, "trading")
            self.logger.info(f"📊 Received portfolio trades: {trades_data}")
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=trades_data
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_portfolio_performance(self, task: TaskRequest) -> TaskResponse:
        """Handle live portfolio performance request."""
        try:
            self.logger.info(f"🔍 Calling MCP server for portfolio.get_performance...")
            # Call the real MCP server for portfolio performance
            performance_data = await self._call_mcp_server("portfolio.get_performance", {}, "trading")
            self.logger.info(f"📊 Received portfolio performance: {performance_data}")
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=performance_data
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_trading_balance(self, task: TaskRequest) -> TaskResponse:
        """Handle live trading balance request."""
        try:
            # Call the real MCP server for balance data
            balance_data = await self._call_mcp_server("trading.get_portfolio_balance", {}, "trading")
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=balance_data
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_recent_executions(self, task: TaskRequest) -> TaskResponse:
        """Handle recent live trade executions request."""
        try:
            self.logger.info(f"🔍 Calling MCP server for trading.get_recent_executions...")
            # Call the real MCP server for recent executions
            executions_data = await self._call_mcp_server("trading.get_recent_executions", {}, "trading")
            self.logger.info(f"📊 Received recent executions: {executions_data}")
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=executions_data
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_momentum_signals(self, task: TaskRequest) -> TaskResponse:
        """Handle momentum signals request."""
        try:
            self.logger.info(f"🔍 Calling MCP server for trading.get_momentum_signals...")
            # Call the real MCP server for momentum signals
            signals_data = await self._call_mcp_server("trading.get_momentum_signals", {}, "trading")
            self.logger.info(f"📊 Received momentum signals: {signals_data}")
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=signals_data
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    # Paper Trading (Secondary) Command Handlers
    
    async def _handle_paper_portfolio(self, task: TaskRequest) -> TaskResponse:
        """Handle paper trading portfolio request."""
        try:
            # Call the real MCP server for paper portfolio data
            paper_portfolio_data = await self._call_mcp_server("paper.get_portfolio", {}, "trading")
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=paper_portfolio_data
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_paper_balance(self, task: TaskRequest) -> TaskResponse:
        """Handle paper trading balance request."""
        try:
            # Call the real MCP server for paper balance data
            paper_balance_data = await self._call_mcp_server("paper.get_balance", {}, "trading")
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=paper_balance_data
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_paper_performance(self, task: TaskRequest) -> TaskResponse:
        """Handle paper trading performance request."""
        try:
            paper_performance_data = {
                "daily_pnl": 750.0,
                "weekly_pnl": 2000.0,
                "monthly_pnl": 5000.0,
                "total_pnl": 15000.0,
                "daily_pnl_percent": 0.75,
                "weekly_pnl_percent": 2.0,
                "monthly_pnl_percent": 5.0,
                "total_pnl_percent": 15.0,
                "best_trade": 1500.0,
                "worst_trade": -400.0,
                "win_rate": 0.70,
                "profit_factor": 2.1,
                "trading_mode": "paper"
            }
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=paper_performance_data
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_paper_trades(self, task: TaskRequest) -> TaskResponse:
        """Handle paper trading trades request."""
        try:
            paper_trades_data = {
                "trades": [
                    {
                        "id": "paper_trade_001",
                        "symbol": "BTC/USD",
                        "side": "buy",
                        "size": 0.05,
                        "price": 47000.0,
                        "timestamp": "2025-01-22T11:00:00Z",
                        "pnl": 150.0
                    },
                    {
                        "id": "paper_trade_002",
                        "symbol": "ETH/USD",
                        "side": "sell",
                        "size": 3.0,
                        "price": 3150.0,
                        "timestamp": "2025-01-22T10:45:00Z",
                        "pnl": 150.0
                    }
                ],
                "total_trades": 2,
                "total_pnl": 300.0,
                "trading_mode": "paper"
            }
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=paper_trades_data
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )


if __name__ == "__main__":
    # Test the TraderAgent
    async def test_trader_agent():
        agent = TraderAgent()
        
        try:
            await agent.start()
            print(f"TraderAgent started: {agent.get_info()}")
            
            # Test a live trading task
            task = TaskRequest(
                task_id="test_001",
                agent_id=agent.agent_id,
                capability=AgentCapability.TRADING,
                task_type="portfolio.get_overview",
                parameters={}
            )
            
            response = await agent._handle_task(task)
            print(f"Portfolio response: {response.result}")
            
            # Test a paper trading task
            paper_task = TaskRequest(
                task_id="test_002",
                agent_id=agent.agent_id,
                capability=AgentCapability.TRADING,
                task_type="paper.get_portfolio",
                parameters={}
            )
            
            paper_response = await agent._handle_task(paper_task)
            print(f"Paper portfolio response: {paper_response.result}")
            
            # Simulate running for a bit
            await asyncio.sleep(5)
            
        finally:
            await agent.stop()
            print("TraderAgent stopped")
    
    asyncio.run(test_trader_agent())