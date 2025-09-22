# Jarvis HTTP MCP Server - Local Endpoint Guide

Your Jarvis MCP server is now available as an HTTP API on **localhost:3010**!

## 🚀 Quick Start

### Start the HTTP MCP Server

```bash
# Method 1: Using CLI
python -m jarvis.cli mcp-http-server --name "YourName" --port 3010

# Method 2: Using standalone script
python run_http_mcp_server.py "YourName" localhost 3010

# Method 3: Custom host/port
python run_http_mcp_server.py "YourName" 0.0.0.0 8080
```

### Test the Server

```bash
# Health check
curl http://localhost:3010/health

# List all tools
curl http://localhost:3010/mcp/tools

# Call a tool
curl -X POST http://localhost:3010/mcp/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "jarvis_chat", "arguments": {"message": "Hello Jarvis!"}}'
```

## 📍 Available Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Home page with server info |
| `/docs` | GET | Documentation page |
| `/health` | GET | Health check |
| `/mcp/status` | GET | Server status |
| `/mcp/tools` | GET | List all available tools |
| `/mcp/tools/call` | POST | Call a Jarvis tool |
| `/mcp/ws` | GET | WebSocket endpoint |

## 🛠️ Available Tools

All 12 Jarvis tools are available via HTTP API:

### 1. Chat with Jarvis
```bash
curl -X POST http://localhost:3010/mcp/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "jarvis_chat",
    "arguments": {
      "message": "What can you help me with?"
    }
  }'
```

### 2. Schedule a Task
```bash
curl -X POST http://localhost:3010/mcp/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "jarvis_schedule_task",
    "arguments": {
      "description": "Call the dentist",
      "priority": "medium",
      "category": "personal"
    }
  }'
```

### 3. Get Tasks
```bash
curl -X POST http://localhost:3010/mcp/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "jarvis_get_tasks",
    "arguments": {
      "status": "pending"
    }
  }'
```

### 4. Complete a Task
```bash
curl -X POST http://localhost:3010/mcp/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "jarvis_complete_task",
    "arguments": {
      "task_index": 1
    }
  }'
```

### 5. Web Search
```bash
curl -X POST http://localhost:3010/mcp/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "jarvis_web_search",
    "arguments": {
      "query": "Python best practices 2024"
    }
  }'
```

### 6. Calculator
```bash
curl -X POST http://localhost:3010/mcp/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "jarvis_calculate",
    "arguments": {
      "expression": "2 + 2 * 3"
    }
  }'
```

### 7. Get System Status
```bash
curl -X POST http://localhost:3010/mcp/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "jarvis_get_status",
    "arguments": {}
  }'
```

### 8. Get Settings
```bash
curl -X POST http://localhost:3010/mcp/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "jarvis_get_settings",
    "arguments": {}
  }'
```

### 9. Update Setting
```bash
curl -X POST http://localhost:3010/mcp/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "jarvis_update_setting",
    "arguments": {
      "key": "communication_style",
      "value": "casual"
    }
  }'
```

### 10. Get Memory
```bash
curl -X POST http://localhost:3010/mcp/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "jarvis_get_memory",
    "arguments": {
      "limit": 5
    }
  }'
```

## 🌐 Web Interface

Visit these URLs in your browser:

- **Home:** http://localhost:3010/
- **Documentation:** http://localhost:3010/docs
- **Health Check:** http://localhost:3010/health
- **List Tools:** http://localhost:3010/mcp/tools

## 🔌 WebSocket Support

For real-time communication, connect to the WebSocket endpoint:

```javascript
const ws = new WebSocket('ws://localhost:3010/mcp/ws');

ws.onopen = function() {
    // List tools
    ws.send(JSON.stringify({
        type: 'list_tools'
    }));
    
    // Call a tool
    ws.send(JSON.stringify({
        type: 'call_tool',
        tool: 'jarvis_chat',
        arguments: { message: 'Hello!' }
    }));
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
};
```

## 📱 Integration Examples

### Python Client
```python
import requests

# List tools
response = requests.get('http://localhost:3010/mcp/tools')
tools = response.json()

# Call a tool
response = requests.post('http://localhost:3010/mcp/tools/call', 
    json={
        'name': 'jarvis_chat',
        'arguments': {'message': 'Hello Jarvis!'}
    }
)
result = response.json()
print(result['result']['response'])
```

### JavaScript/Node.js Client
```javascript
const axios = require('axios');

// List tools
const tools = await axios.get('http://localhost:3010/mcp/tools');

// Call a tool
const result = await axios.post('http://localhost:3010/mcp/tools/call', {
    name: 'jarvis_chat',
    arguments: { message: 'Hello Jarvis!' }
});
console.log(result.data.result.response);
```

### cURL Examples
```bash
# Get server status
curl http://localhost:3010/mcp/status

# List all tools
curl http://localhost:3010/mcp/tools | jq '.tools[].name'

# Chat with Jarvis
curl -X POST http://localhost:3010/mcp/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "jarvis_chat", "arguments": {"message": "Help me plan my day"}}' | jq '.result.response'
```

## 🔧 Configuration

### Environment Variables
```bash
export OPENAI_API_KEY="your-openai-key"
export CLAUDE_API_KEY="your-claude-key"
export OPENWEATHER_API_KEY="your-weather-key"
```

### Custom Port/Host
```bash
# Run on different port
python run_http_mcp_server.py "YourName" localhost 8080

# Run on all interfaces
python run_http_mcp_server.py "YourName" 0.0.0.0 3010
```

## 🚨 Troubleshooting

### Server won't start
```bash
# Check if port is in use
lsof -i :3010

# Kill existing process
pkill -f "run_http_mcp_server.py"
```

### Connection refused
```bash
# Check server is running
curl http://localhost:3010/health

# Check firewall
sudo ufw status
```

### Tool errors
```bash
# Check server logs
python run_http_mcp_server.py "YourName" 2>&1 | tee server.log
```

## 📊 Response Format

All API responses follow this format:

```json
{
  "result": {
    "response": "Tool execution result"
  },
  "tool": "jarvis_chat",
  "timestamp": "2024-01-01T12:00:00.000000"
}
```

Error responses:
```json
{
  "error": "Error message",
  "timestamp": "2024-01-01T12:00:00.000000"
}
```

## 🎯 Next Steps

1. **Start the server:** `python run_http_mcp_server.py "YourName"`
2. **Test the endpoints:** Visit http://localhost:3010/
3. **Integrate with your apps:** Use the HTTP API endpoints
4. **Build a frontend:** Create a web interface using the API
5. **Set up monitoring:** Monitor the `/health` endpoint

Your Jarvis MCP server is now running as a full HTTP API on **localhost:3010**! 🚀
