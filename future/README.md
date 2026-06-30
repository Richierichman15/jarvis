# Jarvis — Current Capabilities

**Last updated:** June 29, 2026

This folder tracks where Jarvis is today and where it is headed. Future roadmaps and plans will live here as we add them.

---

## What Is Running

Jarvis is a personal AI assistant you control through **Discord**. On your machine it runs as two processes:

| Process | Command | Port / role |
|---------|---------|-------------|
| HTTP client server | `.venv/Scripts/python.exe run_client_http_server.py` | `http://localhost:3012` — exposes MCP tools over HTTP |
| Discord bot | `.venv/Scripts/python.exe discord_jarvis_bot_full.py` | Connects to Discord as **jarvis#8593** |

The Discord bot talks to the HTTP server, which spawns the Jarvis MCP server and exposes its tools. Responses are powered by **Ollama** (`llama3.1` on `http://localhost:11434`).

---

## How to Use It (Discord)

1. Start both processes (HTTP server first, then the bot).
2. In your configured Discord server, type in any channel — **no @mention required**.
3. Use natural language or command-style messages.

**Examples:**

```
hello jarvis
what time is it
what's my status
help
scan news
search latest AI news
```

The bot uses intent routing to pick the right tool, then formats the reply with Ollama when available.

---

## MCP Tools Available Now (13)

These are the tools loaded from the core Jarvis MCP server on your current setup:

| Tool | What it does |
|------|----------------|
| `jarvis_chat` | General conversation with Jarvis |
| `jarvis_get_status` | System and task overview |
| `jarvis_get_system_info` | Host OS, Python version, hostname |
| `jarvis_get_settings` | Read user preferences |
| `jarvis_update_setting` | Change a preference |
| `jarvis_get_memory` | Recent conversation history |
| `jarvis_web_search` | Web search for a query |
| `jarvis_scan_news` | Scan tech/news headlines |
| `jarvis_calculate` | Math / calculations |
| `jarvis_trigger_n8n` | Trigger an n8n workflow (if configured) |
| `orchestrator.run_plan` | Run a multi-step orchestrator plan |
| `fitness.list_workouts` | List saved workouts |
| `fitness.search_workouts` | Search workouts by keyword |

Verify tools anytime:

```bash
curl http://localhost:3012/tools
```

---

## Discord Bot Features (Working)

- **Natural language chat** in your server
- **Intent routing** — classifies what you want and picks a tool
- **Ollama (local LLM)** — `llama3.1` for replies and formatting
- **Conversation context** — short-term memory within a session
- **Music player module** — initialized (voice playback needs Discord voice setup)
- **HTTP API** — `/tools`, `/run-tool`, `/nl`, `/servers` on port 3012

---

## Optional / Not Active on This Machine

These exist in the codebase but are **not** connected or installed on your current setup:

| Feature | Status |
|---------|--------|
| Trading MCP server | Not configured (old paths from another machine) |
| Search MCP server | Not configured |
| System MCP server | Not configured |
| Music MCP server | Not configured |
| Redis / Agent system | Not installed (`pip install redis`) |
| System monitoring | Not installed (`pip install psutil`) |
| OpenAI / Claude APIs | No API keys set — Ollama is the active model |
| n8n workflows | Only works if you configure endpoints |

The project docs (`DISCORD_BOT_COMMANDS.md`, `JARVIS_COMPLETE_CAPABILITIES.md`) describe the **full** vision with 49+ tools across multiple servers. Your live setup today is the **core Jarvis stack** (13 tools + Discord + Ollama).

---

## Full Discord Experience (When MCP Servers Are Connected)

When Jarvis was wired up to the **search** and **trading** MCP servers, Discord could do much more than the core 13 tools. This is the experience we are working back toward.

### Live news headlines

**You ask:**
```
latest news
```
or
```
scan news
```

**Jarvis responds** with a ranked list of headlines, sources, and links — pulled from news feeds (e.g. Google News RSS). Example from a past session (March 18, 2026):

```
latest news — 10 result(s):

Live Updates: Iran's Intelligence Chief Killed in Strike; Oil and Gas Prices Jump
  — The New York Times
  — https://news.google.com/rss/articles/...

Iran war live: Iran supreme leader says Israel to pay for killing officials
  — Al Jazeera
  — https://news.google.com/rss/articles/...

Live updates: Iran war news; Oil prices surge as Tehran says energy production
  facilities attacked — CNN
  — https://news.google.com/rss/articles/...
```

**Requires:** Search MCP server and/or `jarvis_scan_news` wired to live feeds.

---

### Crypto momentum & trading data

**You ask:**
```
what is the momentum?
```
or
```
/momentum
```
or natural language like:
```
get my trading data — what is the momentum?
```

**Jarvis responds** with per-asset price and momentum windows (6h and 24h), labeled weak/neutral/strong. Example from a past session (October 31, 2025):

```
Here's a snapshot of the current momentum for various cryptocurrencies:

Bitcoin (BTC-USD):
  Current Price: $108,975.60
  6h Momentum: -0.57% (weak)
  24h Momentum: 2.03% (neutral)

Ethereum (ETH-USD):
  Current Price: $3,821.04
  6h Momentum: -0.40% (weak)
  24h Momentum: 2.69% (neutral)

Solana (SOL-USD):
  Current Price: $185.27
  6h Momentum: -0.63% (weak)
  24h Momentum: 2.18% (neutral)

XRP (XRP-USD):
  Current Price: $2.50
  6h Momentum: -0.13% (weak)
  24h Momentum: 3.23% (weak up)

Cardano (ADA-USD):
  Current Price: $0.60
  6h Momentum: -1.46% (weak)
  24h Momentum: 1.31% (neutral)

... (TRON, Stellar, etc.)
```

**Also available with trading MCP connected:**

| Ask in Discord | What you get |
|----------------|--------------|
| `/portfolio` or "portfolio balance" | Trading portfolio overview |
| `/balance` | Current balance |
| `/positions` | Open positions |
| `/trades` | Recent executions |
| `/paper` | Paper trading balance |
| `/price BTC` | Live price for a symbol |
| `/momentum` | Momentum signals across watchlist |

**Requires:** Trading MCP server (`trading.get_momentum_signals`, portfolio tools, etc.).

---

### Other MCP servers (historical)

When all servers were connected, Discord also had access to:

| Server | Examples |
|--------|----------|
| **Search** | Web search, news scan, research queries |
| **Trading** | Portfolio, momentum, OHLCV, paper trading, PnL |
| **System** | Quests, XP, goals, system status |
| **Music** | Play, queue, skip, search songs in voice channels |

Re-connecting these servers on this machine is a **future goal** (see below).

---

## Environment

Config lives in `.env` (project root) and `jarvis/.env`. Key variables:

| Variable | Purpose |
|----------|---------|
| `DISCORD_BOT_TOKEN` | Discord bot token |
| `DISCORD_CLIENT_SERVER` | Guild ID the bot listens in |
| `JARVIS_CLIENT_URL` | HTTP server URL (`http://localhost:3012`) |
| `OLLAMA_HOST` | Ollama API URL |
| `OLLAMA_MODEL` | Model name (`llama3.1`) |
| `LLM_PROVIDER` | `ollama` |

Always use the venv Python:

```bash
.venv/Scripts/python.exe run_client_http_server.py
.venv/Scripts/python.exe discord_jarvis_bot_full.py
```

---

## Quick Health Check

```bash
# HTTP server up?
curl http://localhost:3012/servers

# Tools loaded?
curl http://localhost:3012/tools

# Ollama up?
curl http://localhost:11434/api/tags
```

---

## Future Plans

Roadmap items for this folder:

1. **Re-connect MCP servers on this machine** — search (news), trading (momentum/portfolio), system (quests), music (voice)
2. **Restore full Discord command set** — `/momentum`, `/portfolio`, `latest news`, etc. as in past sessions
3. **Agent system** — Redis + trader/research agents for background tasks
4. **System monitoring** — psutil-based health alerts in Discord

Additional ideas and specs will be added here as we define them.
