# Discord Jarvis Bot

An async Discord bot that integrates with your Jarvis MCP client, allowing you to interact with Jarvis through Discord commands.

## Features

- **Async Architecture**: Fully asynchronous using `discord.py` and `aiohttp`
- **Command Routing**: Smart command parsing for `/news`, `/portfolio`, and more
- **Jarvis Integration**: Direct integration with your local Jarvis MCP server
- **Error Handling**: Graceful handling of network errors and timeouts
- **Logging**: Comprehensive logging of all Discord messages and Jarvis responses
- **Typing Indicators**: Shows typing indicator while waiting for Jarvis response
- **Webhook Notifications**: Optional error notifications via Discord webhook

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements-discord-bot.txt
```

### 2. Discord Bot Setup

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to "Bot" section and create a bot
4. Copy the bot token
5. Go to "OAuth2" > "URL Generator"
6. Select "bot" scope and required permissions
7. Use the generated URL to invite the bot to your server

### 3. Environment Configuration

Create a `.env` file in the project root:

```env
# Discord Bot Configuration
DISCORD_BOT_TOKEN=your_actual_bot_token_here
DISCORD_CLIENT_ID=your_discord_client_id_here
DISCORD_CLIENT_SERVER=your_discord_server_id_here
DISCORD_WEBHOOK_URL=your_discord_webhook_url_here

# Jarvis Configuration
JARVIS_URL=http://localhost:3010/nl
```

### 4. Start Jarvis MCP Server

Make sure your Jarvis MCP server is running:

```bash
python run_http_mcp_server.py
```

The server should be accessible at `http://localhost:3010`

### 5. Run the Discord Bot

```bash
python discord_jarvis_bot.py
```

## Commands

The bot supports the following commands:

- `/news` or `scan news` → Calls `news.fetch` tool
- `/portfolio` or `get portfolio` → Calls `trading.portfolio` tool
- `/status` or `get status` → Gets system status
- `/memory` or `get memory` → Gets recent conversation memory
- `/help` or `help` → Shows available commands
- Any other message → Sent directly to Jarvis for LLM processing

## Architecture

### Components

1. **JarvisMCPClient**: Handles communication with Jarvis MCP server
2. **DiscordCommandRouter**: Routes Discord commands to appropriate Jarvis queries
3. **Async Session Management**: Reuses aiohttp sessions for efficiency
4. **Error Handling**: Comprehensive error handling with fallbacks

### Key Features

- **Connection Reuse**: Single aiohttp session for all requests
- **Timeout Handling**: 30-second timeout for Jarvis requests
- **Response Parsing**: Handles different response formats from Jarvis
- **Message Limits**: Truncates responses that exceed Discord's 2000 character limit
- **Logging**: Logs all interactions to `discord_jarvis_bot.log`

## Error Handling

The bot gracefully handles:

- Network timeouts and connection errors
- Invalid responses from Jarvis
- Discord API errors
- Missing environment variables

## Logging

All interactions are logged to both console and `discord_jarvis_bot.log`:

- Incoming Discord messages
- Outgoing queries to Jarvis
- Jarvis responses
- Errors and exceptions

## Troubleshooting

### Common Issues

1. **Bot not responding**: Check if Jarvis MCP server is running on port 3010
2. **Invalid token**: Verify DISCORD_BOT_TOKEN in .env file
3. **Permission errors**: Ensure bot has proper permissions in Discord server
4. **Connection timeouts**: Check network connectivity to localhost:3010

### Debug Mode

Enable debug logging by modifying the logging level in the script:

```python
logging.basicConfig(level=logging.DEBUG, ...)
```

## Security Notes

- Keep your Discord bot token secure
- The bot only responds in the configured Discord server
- All communication with Jarvis happens locally (localhost:3010)
- Webhook URLs are optional and only used for error notifications

## Stretch Goals Implemented

✅ **Reusable query_jarvis() helper**: Implemented as `JarvisMCPClient.query_jarvis()`
✅ **Shared aiohttp session**: Global session with proper cleanup
✅ **Comprehensive logging**: All messages and responses logged
✅ **Error webhook notifications**: Optional Discord webhook for errors
