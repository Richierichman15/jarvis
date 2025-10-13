# Trading MCP Server - Complete Tool Reference

This document lists all available tools in the **trading MCP server** and their correct names for use in Discord bot commands.

## 🔧 Tool Namespace Overview

The trading MCP server exposes tools with **double namespace prefixes**:
1. **`trading.trading.*`** - Live exchange trading tools (uses CCXT to connect to Kraken)
2. **`trading.portfolio.*`** - Paper trading portfolio tools (reads from local JSON files)

**Why double prefix?** The MCP server registers tools with namespaces (e.g., `trading.get_price`), then when loaded by the client API under the "trading" server alias, they get another prefix added: `trading.trading.get_price`.

---

## 📊 Trading Namespace Tools (trading.trading.*)

### `trading.trading.get_price`
Get current price for a trading symbol.
- **Args:** `symbol` (string, required) - e.g., "BTC/USDT"
- **Discord Command:** `/price BTC`

### `trading.trading.get_ohlcv`
Get OHLCV (Open, High, Low, Close, Volume) candlestick data.
- **Args:** 
  - `symbol` (string, required) - e.g., "ETH/USDT"
  - `timeframe` (string, optional) - default "1h"
  - `limit` (int, optional) - default 100
- **Discord Command:** `/ohlcv ETH`

### `trading.trading.get_momentum_signals`
Get momentum trading signals.
- **Args:** None
- **Discord Command:** `/momentum`

### `trading.trading.doctor`
Run diagnostics on the trading connection.
- **Args:** None
- **Discord Command:** `/doctor`

### `trading.trading.get_balance`
Get account balance overview from the exchange.
- **Args:** None
- **Discord Command:** `/balance`
- **Note:** Requires API credentials

### `trading.trading.get_positions`
Get current open positions from the exchange.
- **Args:** None
- **Note:** Requires API credentials

### `trading.trading.get_trade_history`
Get historical trades from the exchange.
- **Args:** 
  - `symbol` (string, optional) - filter by symbol
  - `limit` (int, optional) - default 50, max 250
- **Discord Command:** `/history`
- **Note:** Requires API credentials

### `trading.trading.get_pnl_summary`
Get profit and loss summary.
- **Args:** `quote` (string, optional) - quote currency, default "USDT"
- **Discord Command:** `/pnl`
- **Note:** Requires API credentials

### `trading.trading.get_recent_executions`
Get recent trade executions from the live trading system.
- **Args:**
  - `limit` (int, optional) - default 20
  - `symbol` (string, optional) - filter by symbol
- **Discord Command:** `/trades`

### `trading.trading.get_portfolio_balance`
Get portfolio balance information.
- **Args:** None

---

## 📈 Portfolio Namespace Tools (trading.portfolio.*)

### `trading.portfolio.get_overview`
Get paper trading portfolio overview including positions, cash, and performance.
- **Args:** None
- **Discord Commands:** `/portfolio` or `/paper`
- **Returns:** Cash, portfolio value, positions summary, trades count

### `trading.portfolio.get_positions`
Get current paper trading positions with P&L.
- **Args:** None
- **Discord Command:** `/positions`
- **Returns:** Detailed position info including cost basis, current value, P&L

### `trading.portfolio.get_trades`
Get recent paper trading trades.
- **Args:**
  - `limit` (int, optional) - default 50
  - `symbol` (string, optional) - filter by symbol
- **Returns:** List of recent trades with timestamps

### `trading.portfolio.get_performance`
Get paper trading performance metrics and statistics.
- **Args:** None
- **Discord Command:** `/performance`
- **Returns:** Total return, daily P&L, drawdown, trade count

### `trading.portfolio.get_exit_engine_status`
Get exit engine status including active trades and trailing stops.
- **Args:** None
- **Discord Command:** `/exit`
- **Returns:** Active trades, trailing stops, trade states

### `trading.portfolio.get_trading_state`
Get current trading system state and configuration.
- **Args:** None
- **Discord Command:** `/state`
- **Returns:** Portfolio value, cash, trading status, symbols

### `trading.portfolio.get_performance_data`
Get detailed performance data including hourly metrics and benchmarks.
- **Args:** None
- **Returns:** Hourly performance, benchmarks, trade reasoning

### `trading.portfolio.get_export_data`
Get recent export data from CSV files (equity curves, etc.).
- **Args:** `days` (int, optional) - default 7, max 30
- **Discord Command:** `/export`
- **Returns:** Recent CSV export data

---

## ✅ Fixed Tool Mappings

### What Was Wrong
- `/balance` was calling `trading.trading.get_balance` ❌ (double "trading")
- `/portfolio` was calling `trading.portfolio.get_overview` ❌ (wrong namespace)
- `/positions` was calling `trading.portfolio.get_positions` ❌ (wrong namespace)
- `/performance` was looking for server "portfolio" ❌ (should be "jarvis")

### What's Correct Now
- `/balance` → `trading.get_balance` ✅
- `/portfolio` → `portfolio.get_overview` ✅
- `/positions` → `portfolio.get_positions` ✅
- `/performance` → `portfolio.get_performance` ✅
- All tools run on the `"jarvis"` server (the client API routes to the correct MCP server)

---

## 📝 Complete Discord Command Mapping

| Discord Command | MCP Tool Name | Description |
|----------------|---------------|-------------|
| `/balance` | `trading.trading.get_balance` | Exchange account balance |
| `/price BTC` | `trading.trading.get_price` | Get current price |
| `/ohlcv ETH` | `trading.trading.get_ohlcv` | Get OHLCV data |
| `/momentum` | `trading.trading.get_momentum_signals` | Get momentum signals |
| `/doctor` | `trading.trading.doctor` | Run diagnostics |
| `/history` | `trading.trading.get_trade_history` | Exchange trade history |
| `/pnl` | `trading.trading.get_pnl_summary` | Profit/loss summary |
| `/trades` | `trading.trading.get_recent_executions` | Recent executions |
| `/portfolio` | `trading.portfolio.get_overview` | Paper portfolio overview |
| `/paper` | `trading.portfolio.get_overview` | Same as /portfolio |
| `/positions` | `trading.portfolio.get_positions` | Paper positions |
| `/performance` | `trading.portfolio.get_performance` | Performance metrics |
| `/exit` | `trading.portfolio.get_exit_engine_status` | Exit engine status |
| `/state` | `trading.portfolio.get_trading_state` | Trading state |
| `/export` | `trading.portfolio.get_export_data` | Export data |

---

## 🔄 Session Reconnection

The client API now includes automatic session reconnection logic:
- If a tool call fails with "Session is closed" or connection error
- The client will automatically:
  1. Remove the closed session
  2. Wait 0.5 seconds
  3. Reconnect to the MCP server
  4. Retry the tool call once

This prevents temporary connection issues from breaking your Discord bot.

---

## 🚀 Testing

After restarting your servers, test each command to ensure they work:

```bash
# In Discord:
/balance          # Should work now
/portfolio        # Should work now  
/performance      # Should work now
/price BTC        # Should work
/positions        # Should work
```

If you see errors, check:
1. Is the client API server running? (`http://localhost:3012`)
2. Are all MCP servers connected? (check startup logs)
3. For exchange tools, are API credentials configured?

