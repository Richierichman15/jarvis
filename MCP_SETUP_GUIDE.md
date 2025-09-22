# Jarvis MCP Setup Guide

This guide will help you set up Jarvis as an MCP (Model Context Protocol) server to expose its AI assistant capabilities as tools.

## Quick Start

### 1. Install Dependencies
```bash
# Install MCP library
pip install mcp

# Install Jarvis dependencies
pip install -r requirements.txt
```

### 2. Start the MCP Server
```bash
# Method 1: Using CLI
python -m jarvis.cli mcp-server --name "YourName"

# Method 2: Using standalone script
python run_mcp_server.py "YourName"
```

### 3. Test the Server
```bash
# Run the simple test script (recommended)
python3 test_mcp_simple.py

# Or run the full MCP test (requires MCP library)
python3 test_mcp_server.py
```

## Available Tools

The MCP server exposes 12 tools:

| Tool | Description |
|------|-------------|
| `jarvis_chat` | Chat with Jarvis AI assistant |
| `jarvis_schedule_task` | Create new tasks and reminders |
| `jarvis_get_tasks` | List all tasks (pending/completed) |
| `jarvis_complete_task` | Mark tasks as completed |
| `jarvis_delete_task` | Delete tasks |
| `jarvis_get_status` | Get system status overview |
| `jarvis_get_system_info` | Get detailed system information |
| `jarvis_update_setting` | Update user preferences |
| `jarvis_get_settings` | Get current settings |
| `jarvis_web_search` | Search the web |
| `jarvis_calculate` | Perform calculations |
| `jarvis_get_memory` | Get conversation history |

## MCP Client Configuration

### For Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "jarvis": {
      "command": "python",
      "args": ["/absolute/path/to/jarvis/run_mcp_server.py", "YourName"],
      "env": {
        "OPENAI_API_KEY": "your-openai-key",
        "CLAUDE_API_KEY": "your-claude-key"
      }
    }
  }
}
```

### For Other MCP Clients

Use stdio transport with:
- **Command:** `python`
- **Args:** `["/absolute/path/to/jarvis/run_mcp_server.py", "YourName"]`

## Example Usage

### Chat with Jarvis
```json
{
  "tool": "jarvis_chat",
  "arguments": {
    "message": "Help me plan my day"
  }
}
```

### Create a Task
```json
{
  "tool": "jarvis_schedule_task",
  "arguments": {
    "description": "Call the dentist",
    "priority": "medium",
    "category": "personal"
  }
}
```

### Search the Web
```json
{
  "tool": "jarvis_web_search",
  "arguments": {
    "query": "Python best practices 2024"
  }
}
```

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   MCP Client    │◄──►│  Jarvis MCP      │◄──►│   Jarvis Core   │
│                 │    │  Server          │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │  Tool Manager    │
                       │  (Web Search,    │
                       │   Calculator,    │
                       │   File Ops)      │
                       └──────────────────┘
```

## Files Created

- `jarvis/mcp_server.py` - Main MCP server implementation
- `run_mcp_server.py` - Standalone server runner
- `test_mcp_server.py` - Test script
- `examples/mcp_client_example.py` - Example client
- `mcp_config.json` - Configuration template
- `docs/MCP_INTEGRATION.md` - Detailed documentation

## Troubleshooting

### Common Issues

1. **MCP library not found**
   ```bash
   pip install mcp
   ```

2. **Import errors**
   - Run from project root directory
   - Check all dependencies are installed

3. **Permission errors**
   ```bash
   chmod +x run_mcp_server.py
   chmod +x test_mcp_server.py
   ```

### Debug Mode

Run with verbose output:
```bash
PYTHONPATH=/path/to/jarvis python -u run_mcp_server.py "YourName" 2>&1
```

## Next Steps

1. **Test the server** - Run `python test_mcp_server.py`
2. **Configure your MCP client** - Use the configuration examples above
3. **Try the tools** - Start with `jarvis_chat` and `jarvis_schedule_task`
4. **Read the full documentation** - Check `docs/MCP_INTEGRATION.md`

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review the detailed documentation in `docs/MCP_INTEGRATION.md`
3. Test with the provided test script
4. Check the example client code

The MCP integration is designed to be modular and extensible, so you can easily add new tools or modify existing ones as needed.
