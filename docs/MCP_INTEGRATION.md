# Jarvis MCP (Model Context Protocol) Integration

This document describes how to use Jarvis as an MCP server, exposing its AI assistant capabilities as tools that can be called by MCP clients.

## Overview

The Jarvis MCP server exposes the following core functionalities as MCP tools:

- **AI Chat/Query** - Direct conversation with Jarvis AI
- **Task Management** - Create, complete, delete, and list tasks
- **System Status** - Get system information and status
- **Settings Management** - Update user preferences
- **Web Search** - Search the web using Jarvis's search tools
- **Calculator** - Perform mathematical calculations
- **Memory Access** - Retrieve conversation history

## Installation

1. Install the MCP library:
```bash
pip install mcp
```

2. Install Jarvis dependencies:
```bash
pip install -r requirements.txt
```

## Running the MCP Server

### Method 1: Using the CLI
```bash
python -m jarvis.cli mcp-server --name "YourName"
```

### Method 2: Using the standalone script
```bash
python run_mcp_server.py "YourName"
```

### Method 3: Direct Python execution
```python
import asyncio
from jarvis.mcp_server import create_mcp_server

async def main():
    server = create_mcp_server("YourName")
    await server.run()

asyncio.run(main())
```

## Available MCP Tools

### 1. jarvis_chat
Chat with Jarvis AI assistant.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "message": {
      "type": "string",
      "description": "The message to send to Jarvis"
    }
  },
  "required": ["message"]
}
```

**Example:**
```json
{
  "message": "What's the weather like today?"
}
```

### 2. jarvis_schedule_task
Schedule a new task or reminder.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "description": {
      "type": "string",
      "description": "Description of the task"
    },
    "priority": {
      "type": "string",
      "enum": ["low", "medium", "high", "urgent"],
      "description": "Priority level of the task",
      "default": "medium"
    },
    "category": {
      "type": "string",
      "description": "Category of the task (work, personal, learning, health, general)",
      "default": "general"
    },
    "deadline": {
      "type": "string",
      "description": "Deadline for the task (ISO format)",
      "default": null
    },
    "duration": {
      "type": "integer",
      "description": "Estimated duration in minutes",
      "default": null
    }
  },
  "required": ["description"]
}
```

**Example:**
```json
{
  "description": "Review quarterly reports",
  "priority": "high",
  "category": "work",
  "deadline": "2024-03-31T17:00:00",
  "duration": 120
}
```

### 3. jarvis_get_tasks
Get all tasks from Jarvis.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "status": {
      "type": "string",
      "enum": ["all", "pending", "completed"],
      "description": "Filter tasks by status",
      "default": "all"
    }
  }
}
```

**Example:**
```json
{
  "status": "pending"
}
```

### 4. jarvis_complete_task
Mark a task as completed.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "task_index": {
      "type": "integer",
      "description": "Index number of the task to complete (1-based)"
    }
  },
  "required": ["task_index"]
}
```

**Example:**
```json
{
  "task_index": 1
}
```

### 5. jarvis_delete_task
Delete a task.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "task_index": {
      "type": "integer",
      "description": "Index number of the task to delete (1-based)"
    }
  },
  "required": ["task_index"]
}
```

### 6. jarvis_get_status
Get current system status and overview.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {}
}
```

### 7. jarvis_get_system_info
Get detailed system information.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {}
}
```

### 8. jarvis_update_setting
Update a user preference setting.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "key": {
      "type": "string",
      "description": "Setting key to update"
    },
    "value": {
      "type": "string",
      "description": "New value for the setting"
    }
  },
  "required": ["key", "value"]
}
```

**Example:**
```json
{
  "key": "communication_style",
  "value": "casual"
}
```

### 9. jarvis_get_settings
Get current user settings and preferences.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {}
}
```

### 10. jarvis_web_search
Perform a web search.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "query": {
      "type": "string",
      "description": "Search query"
    }
  },
  "required": ["query"]
}
```

**Example:**
```json
{
  "query": "latest AI developments 2024"
}
```

### 11. jarvis_calculate
Perform mathematical calculations.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "expression": {
      "type": "string",
      "description": "Mathematical expression to calculate"
    }
  },
  "required": ["expression"]
}
```

**Example:**
```json
{
  "expression": "2 + 2 * 3"
}
```

### 12. jarvis_get_memory
Get recent conversation history.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "limit": {
      "type": "integer",
      "description": "Maximum number of conversations to return",
      "default": 10
    }
  }
}
```

**Example:**
```json
{
  "limit": 5
}
```

## MCP Client Configuration

To use Jarvis as an MCP server, configure your MCP client with the following settings:

### Claude Desktop Configuration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "jarvis": {
      "command": "python",
      "args": ["/path/to/your/jarvis/run_mcp_server.py", "YourName"],
      "env": {
        "OPENAI_API_KEY": "your-openai-key",
        "CLAUDE_API_KEY": "your-claude-key"
      }
    }
  }
}
```

### Other MCP Clients

For other MCP clients, use the stdio transport with:
- **Command:** `python`
- **Args:** `["/path/to/your/jarvis/run_mcp_server.py", "YourName"]`
- **Transport:** stdio

## Example Usage

### 1. Chat with Jarvis
```json
{
  "tool": "jarvis_chat",
  "arguments": {
    "message": "Help me plan my day"
  }
}
```

### 2. Create a Task
```json
{
  "tool": "jarvis_schedule_task",
  "arguments": {
    "description": "Call the dentist",
    "priority": "medium",
    "category": "personal",
    "duration": 30
  }
}
```

### 3. Get Pending Tasks
```json
{
  "tool": "jarvis_get_tasks",
  "arguments": {
    "status": "pending"
  }
}
```

### 4. Complete a Task
```json
{
  "tool": "jarvis_complete_task",
  "arguments": {
    "task_index": 1
  }
}
```

### 5. Search the Web
```json
{
  "tool": "jarvis_web_search",
  "arguments": {
    "query": "Python best practices 2024"
  }
}
```

## Error Handling

The MCP server includes comprehensive error handling:

- **Invalid parameters** - Returns descriptive error messages
- **Missing dependencies** - Graceful fallback when tools are unavailable
- **Jarvis errors** - Captures and returns error details
- **Network issues** - Handles web search and API failures

## Security Considerations

- The MCP server runs with the same permissions as the user
- API keys should be set via environment variables
- File operations are restricted to safe directories
- No direct system access is exposed through MCP tools

## Troubleshooting

### Common Issues

1. **MCP library not found**
   ```bash
   pip install mcp
   ```

2. **Import errors**
   - Ensure you're running from the project root
   - Check that all dependencies are installed

3. **Tool not available**
   - Some tools require additional setup (web search, calculator)
   - Check the Jarvis configuration

4. **Permission errors**
   - Ensure the script is executable: `chmod +x run_mcp_server.py`

### Debug Mode

To run with debug logging:
```bash
PYTHONPATH=/path/to/jarvis python -u run_mcp_server.py "YourName" 2>&1
```

## Architecture

The MCP integration follows a modular design:

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

This design ensures:
- **Loose coupling** - MCP layer is separate from Jarvis core
- **Extensibility** - Easy to add new tools
- **Maintainability** - Clear separation of concerns
- **Reusability** - Jarvis can be used independently of MCP

## Contributing

To add new MCP tools:

1. Add the tool definition to `list_tools()`
2. Implement the tool handler in `call_tool()`
3. Update this documentation
4. Add tests if applicable

## License

This MCP integration follows the same license as the main Jarvis project.
