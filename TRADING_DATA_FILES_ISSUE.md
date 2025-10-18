# Trading Data Files Issue

## Problem
The trading MCP server is returning errors like "Portfolio data not found" because it's looking for specific data files that don't exist yet.

## Missing Files
The trading MCP server expects these files to exist:

1. **`app/data/live/live_portfolio_state.json`** - Live trading portfolio state
2. **`app/data/live/live_trades.json`** - Live trading trade history  
3. **`app/data/live/exit_engine_state.json`** - Exit engine state for trailing stops

## Root Cause
These files are created by the actual trading system when it runs, but the trading system hasn't been started yet or the files are in a different location.

## Solutions

### Option 1: Start the Trading System
Run the trading system to generate these files:
```bash
python run_crypto_trading.py live
```

### Option 2: Check File Locations
The trading MCP server is looking for files relative to its own directory. Check if the files exist in:
- `E:/Richie/github/trading/app/data/live/` (if trading MCP server is in trading directory)
- Or wherever the trading MCP server is actually located

### Option 3: Create Mock Data Files
Create the missing files with basic structure for testing:

**live_portfolio_state.json:**
```json
{
  "portfolio_value": 5000.0,
  "cash": 5000.0,
  "initial_balance": 5000.0,
  "return_percentage": 0.0,
  "trading_active": true,
  "positions": {},
  "crypto_symbols": ["BTC-USD", "ETH-USD", "SOL-USD"],
  "last_updated": "2025-01-18T12:00:00Z"
}
```

**live_trades.json:**
```json
{
  "trades": []
}
```

**exit_engine_state.json:**
```json
{
  "active_trades": {},
  "trailing_stops": {},
  "trade_states": {},
  "last_updated": "2025-01-18T12:00:00Z"
}
```

## Status
- ✅ **Tool names are correct** - The agents are calling the right MCP server tools
- ❌ **Data files missing** - The trading system needs to be running to create these files
- ✅ **Search tools fixed** - News and search now use `web.search` correctly

## Next Steps
1. Start the trading system to generate the required data files
2. Or create mock data files for testing
3. Test the trading commands again once files exist
