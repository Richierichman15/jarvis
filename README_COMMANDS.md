# Jarvis Commands & Usage Guide

This guide explains all the commands and endpoints available in your Jarvis system.

## 🚀 Quick Start Commands

### Start the HTTP MCP Server (Recommended for n8n integration)
```bash
python -m jarvis.mcp_http_server --host :: --port 3010
```
- **Purpose**: Provides HTTP endpoints for n8n and other external tools
- **Accessible on**: `http://localhost:3010`
- **IPv6 Support**: Uses `--host ::` to support both IPv4 and IPv6 connections

### Start the Standard MCP Server
```bash
python -m jarvis.mcp_server
```
- **Purpose**: Standard MCP protocol server for MCP clients
- **Usage**: For MCP-compatible clients and tools

### Start the Search Server
```bash
python search/mcp_server.py
```
- **Purpose**: Provides web search functionality via Google News RSS
- **Accessible on**: MCP protocol (used by Jarvis internally)

## 🌐 HTTP Endpoints (Port 3010)

### Health & Status
- **GET** `/health` - Health check endpoint
- **GET** `/status` - Alternative health check
- **GET** `/mcp/status` - MCP server status

### Tool Management
- **GET** `/mcp/tools` - List all available tools
- **POST** `/mcp/tools/call` - Call any Jarvis tool
- **GET** `/mcp/tools/call` - Call tools via GET (for compatibility)

### n8n Integration Endpoints
- **POST** `/tool/jarvis_scan_news` - Dedicated news scanning endpoint
- **POST** `/tool/jarvis_trigger_n8n` - Dedicated n8n trigger endpoint

### Documentation
- **GET** `/` - Home page with server info
- **GET** `/help` - List all available endpoints
- **GET** `/docs` - Full documentation page

## 🔧 Available Jarvis Tools

### Core AI Tools
- `jarvis_chat` - Chat with Jarvis AI assistant
- `jarvis_scan_news` - Scan news across tech topics with AI summaries
- `jarvis_trigger_n8n` - Trigger n8n workflows

### System Tools
- `jarvis_get_status` - Get current system status
- `jarvis_get_system_info` - Get detailed system information
- `jarvis_get_memory` - Get recent conversation history

### Settings & Configuration
- `jarvis_update_setting` - Update user preferences
- `jarvis_get_settings` - Get current settings

### Utility Tools
- `jarvis_web_search` - Perform web searches
- `jarvis_calculate` - Mathematical calculations

### Task Management (Deprecated)
- `jarvis_schedule_task` - Schedule tasks (use system server instead)
- `jarvis_get_tasks` - Get tasks (use system server instead)
- `jarvis_complete_task` - Complete tasks (use system server instead)
- `jarvis_delete_task` - Delete tasks (use system server instead)

### Fitness Tools
- `fitness.list_workouts` - List available workouts
- `fitness.search_workouts` - Search workouts by keyword

### Orchestration
- `orchestrator.run_plan` - Execute multi-step plans

## 📡 n8n Integration Examples

### Using the Dedicated Endpoints (Recommended)

**News Scanning:**
```http
POST http://localhost:3010/tool/jarvis_scan_news
Content-Type: application/json

{}
```

**Trigger n8n Workflow:**
```http
POST http://localhost:3010/tool/jarvis_trigger_n8n
Content-Type: application/json

{}
```

### Using the General MCP Endpoint

**News Scanning:**
```http
POST http://localhost:3010/mcp/tools/call
Content-Type: application/json

{
  "name": "jarvis_scan_news",
  "arguments": {}
}
```

**Chat with Jarvis:**
```http
POST http://localhost:3010/mcp/tools/call
Content-Type: application/json

{
  "name": "jarvis_chat",
  "arguments": {
    "message": "Hello Jarvis!"
  }
}
```

## 🔗 n8n Webhook Configuration

### Your n8n Webhook URL
```
http://localhost:5678/webhook/d3a372f9-f7c5-41aa-b217-8e1f961f4e7d
```

### Triggering Jarvis from n8n
1. **From n8n**: Send POST request to `http://localhost:3010/tool/jarvis_scan_news`
2. **Jarvis processes**: Scans news and generates AI summaries
3. **Response**: Returns structured JSON with results
4. **Back to n8n**: Process the response data

## 🛠️ Development & Testing

### Test HTTP Endpoints
```bash
# Health check
curl http://localhost:3010/health

# List tools
curl http://localhost:3010/mcp/tools

# Test news scanning
curl -X POST http://localhost:3010/tool/jarvis_scan_news \
  -H "Content-Type: application/json" \
  -d '{}'
```

### PowerShell Testing
```powershell
# Health check
Invoke-WebRequest -Uri "http://localhost:3010/health" -Method GET

# Test news scanning
Invoke-WebRequest -Uri "http://localhost:3010/tool/jarvis_scan_news" -Method POST -ContentType "application/json" -Body '{}'
```

## 🔧 Environment Variables

### Required for Full Functionality
- `OPENAI_API_KEY` - OpenAI API access
- `CLAUDE_API_KEY` - Claude API access
- `DISCORD_WEBHOOK_URL` - Discord webhook for notifications

### Optional
- `OPENWEATHER_API_KEY` - Weather API (falls back to web search)
- `MCP_EXTERNAL_SERVERS` - External MCP server configuration

## 📊 Response Formats

### Success Response
```json
{
  "success": true,
  "data": "Tool result or response",
  "timestamp": "2024-01-01T12:00:00",
  "tool": "tool_name"
}
```

### Error Response
```json
{
  "success": false,
  "error": "Error message",
  "timestamp": "2024-01-01T12:00:00",
  "tool": "tool_name"
}
```

## 🚨 Troubleshooting

### Connection Issues
- **ECONNREFUSED**: Make sure the server is running on the correct port
- **IPv6 Issues**: Use `--host ::` to support both IPv4 and IPv6
- **Port Conflicts**: Change port with `--port 3011` if 3010 is busy

### Common Commands
```bash
# Check if server is running
curl http://localhost:3010/health

# Restart server with different port
python -m jarvis.mcp_http_server --host :: --port 3011

# Check available tools
curl http://localhost:3010/mcp/tools
```

## 📝 Notes

- The HTTP MCP server is the recommended way to integrate with n8n
- Use dedicated endpoints (`/tool/`) for simpler n8n integration
- The standard MCP server is for MCP-compatible clients
- All endpoints support CORS for web applications
- Server logs show detailed request/response information

## 🔄 Workflow Example

1. **Start Jarvis HTTP Server**: `python -m jarvis.mcp_http_server --host :: --port 3010`
2. **Configure n8n**: Set webhook URL to `http://localhost:3010/tool/jarvis_scan_news`
3. **Trigger from n8n**: Send POST request to trigger news scanning
4. **Process Results**: n8n receives AI-generated news summaries
5. **Send to Discord**: Use the `send_to_discord` helper method to notify users

This setup provides a complete automation pipeline from n8n → Jarvis → AI Processing → Results → Discord notifications.
