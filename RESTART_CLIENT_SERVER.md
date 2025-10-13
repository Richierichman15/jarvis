# How to Restart the Client Server to See Detailed Errors

I've added improved error logging to the client API. Please restart it to see the actual error details:

## Steps:

1. **Stop the current server** (press Ctrl+C in the terminal running uvicorn)

2. **Restart with the updated code:**
   ```bash
   python -m uvicorn client.api:create_app --host 0.0.0.0 --port 3012 --factory --log-level debug
   ```

3. **Watch for the detailed error output** - you should now see full tracebacks instead of just "unhandled errors in a TaskGroup"

## What to Look For:

The logs will now show:
- `Full error for session 'system':` followed by a complete traceback
- `Full error for session 'trading':` followed by a complete traceback

This will tell us exactly what's failing (import errors, missing dependencies, etc.)

## Alternative: Quick Test

If you want to test the servers individually first:

```bash
# Test system server
cd E:\Richie\github\system
python system_server.py

# Test trading server  
cd E:\Richie\github\finance
python trading_mcp_server.py
```

These should output something (or show an error) rather than just exiting silently.

