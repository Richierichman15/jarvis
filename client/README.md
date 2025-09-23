Jarvis MCP Client
=================

Minimal, modular MCP client for interacting with the Jarvis MCP server over stdio.

Features
- Launches the Jarvis MCP server as a subprocess.
- Performs MCP handshake and lists available tools.
- Interactive CLI to call tools by name with JSON args.
- Clear output formatting for server responses.
- Structured for easy extension (LLM routing, web/desktop UI).

Requirements
- Python 3.9+
- The Jarvis MCP stdio server script at repo root: `run_mcp_server.py` (default).

Install
1) Create and activate a virtualenv (recommended):
   - `python3 -m venv .venv && source .venv/bin/activate`
2) Install server + client dependencies (choose one):
   - Combined file: `pip install -r client/requirements-all.txt`
   - Or separately:
     - `pip install -r requirements.txt`
     - `pip install -r client/requirements.txt`

Quickstart
- Start Jarvis MCP server (stdio):
  - `python -u run_mcp_server.py "Boss"`
- Start the client (from repo root):
  - `python client/cli.py`
- Optional: point to a custom server path:
  - `python client/cli.py ./run_mcp_server.py`

CLI Usage
- Type `list` to re-list tools.
- Type `help` to see usage and examples.
- Call tools using the tool name and optional JSON args.

Examples
- List tools:
  - `list`
- Chat with Jarvis:
  - `jarvis_chat {"message": "Hello Jarvis!"}`
- Get status:
  - `jarvis_get_status`
- Schedule a task:
  - `jarvis_schedule_task {"description":"Call the dentist","priority":"medium"}`
- Get pending tasks:
  - `jarvis_get_tasks {"status":"pending"}`

Design Notes
- The client uses the official Python MCP SDK (`mcp`).
- Transport is stdio via a Python subprocess of your server file.
- The CLI is built with `prompt_toolkit` for history and completion.
- Output is formatted for readability; tool results are printed as text.

Extend
- LLM routing: see the `_natural_language_to_tool_call` docstring in `cli.py` for where to integrate Ollama/OpenAI.
- Web/Desktop UI: see `create_web_app` in `cli.py` for a FastAPI sketch you can expand later.

Troubleshooting
- “ModuleNotFoundError: aiofiles/httpx” when starting: install deps using `client/requirements-all.txt`.
- “Server not found”: ensure `run_mcp_server.py` exists at repo root and is runnable.
- Handshake errors: confirm both client and server `mcp` versions are compatible and up to date.
- For stdio mode, unbuffered Python helps: `python -u run_mcp_server.py`.
