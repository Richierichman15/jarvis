#!/usr/bin/env python3
"""
Minimal MCP Client for Jarvis
A command-line interface to interact with the Jarvis MCP server.
"""

import asyncio
import json
import subprocess
import sys
import re
import os
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
import shlex
from tabulate import tabulate

from colorama import init, Fore, Style
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Allow running as a script by making local imports work
THIS_DIR = Path(__file__).parent
ROOT_DIR = THIS_DIR.parent  # repo root
if str(THIS_DIR) not in sys.path:
    sys.path.append(str(THIS_DIR))
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))
from storage import (
    load_projects as load_local_projects,
    save_projects as save_local_projects,
    load_servers as load_saved_servers,
    save_servers as save_saved_servers,
    load_active_servers,
    save_active_servers,
)
from llm_router import route_natural_language


class ReconnectNeeded(Exception):
    """Signal that the server/session is down and we should reconnect."""
    pass

# Initialize colorama for cross-platform colored output
init(autoreset=True)

class JarvisClient:
    """
    A minimal MCP client for interacting with the Jarvis MCP server.
    
    This client:
    - Launches the MCP server as a subprocess
    - Connects over stdio transport
    - Performs handshake and discovers available tools
    - Provides an interactive CLI for calling tools
    """
    
    def __init__(self, server_path: Optional[Path] = None):
        """
        Initialize the Jarvis client.
        
        Args:
            server_path: Path to the server script. Defaults to ../run_mcp_server.py
        """
        if server_path is None:
            # Default to the Jarvis stdio server in repo root
            self.server_path = Path(__file__).parent.parent / "run_mcp_server.py"
        else:
            self.server_path = Path(server_path)
            
        # Multi-server sessions
        self.sessions: Dict[str, ClientSession] = {}
        self._server_tasks: Dict[str, asyncio.Task] = {}
        self.active_session: str = "jarvis"
        self.tools: Dict[str, Any] = {}
        self.tool_completer: Optional[WordCompleter] = None
        self.local_projects: Dict[str, Dict[str, Any]] = {}
        self.active_project: Optional[str] = None
        self.saved_servers: Dict[str, Dict[str, Any]] = load_saved_servers()
        self._tools_cache: Dict[str, Dict[str, Any]] = {}
        self.active_servers: Dict[str, Dict[str, Any]] = load_active_servers()
        
    async def start(self):
        """Start default 'jarvis' server, then run the interactive CLI."""
        print(f"{Fore.BLUE}Starting Jarvis MCP server...{Style.RESET_ALL}")

        # Check if server exists
        if not self.server_path.exists():
            print(f"{Fore.RED}Error: Server not found at {self.server_path}{Style.RESET_ALL}")
            sys.exit(1)

        # Optional preflight: verify server dependencies are installed
        missing = self._check_server_dependencies()
        if missing:
            print(
                f"{Fore.YELLOW}Missing server dependencies: {', '.join(missing)}{Style.RESET_ALL}\n"
                f"Install with: pip install -r requirements.txt\n"
                f"Or: pip install -r client/requirements-all.txt\n"
            )

        # Default Jarvis server via Python stdio
        server_params = StdioServerParameters(
            command=sys.executable,
            args=["-u", str(self.server_path), "Boss"],
        )

        # Reset active server tracker for this session
        self.active_servers = {}
        save_active_servers(self.active_servers)

        # Spawn and hold the default 'jarvis' session
        try:
            await self._spawn_and_hold("jarvis", server_params)
        except Exception as e:
            print(f"{Fore.RED}Failed to start default server: {e}{Style.RESET_ALL}")
            return

        # Auto-reconnect any saved servers (except the default 'jarvis')
        if self.saved_servers:
            for alias, entry in self.saved_servers.items():
                if alias == "jarvis" or alias in self.sessions:
                    continue
                cmd = entry.get("command")
                args = entry.get("args") or []
                if not cmd:
                    continue
                try:
                    await self._spawn_and_hold(alias, StdioServerParameters(command=cmd, args=args))
                except Exception as e:
                    print(f"{Fore.YELLOW}Warning: failed to auto-connect saved server '{alias}': {e}{Style.RESET_ALL}")

        # Initialize client-side state and show tools from active session
        await self._initialize()

        # Run CLI until exit, then shutdown all sessions
        try:
            await self._run_cli()
        finally:
            await self._shutdown_all_servers()
    
    async def _initialize(self):
        """Initialize the connection and discover available tools."""
        print(f"{Fore.GREEN}Connected to server(s)!{Style.RESET_ALL}")

        # Load any locally saved projects (client-side persistence)
        self.local_projects = load_local_projects()
        if self.local_projects:
            print(f"{Fore.BLUE}Loaded {len(self.local_projects)} locally saved project(s).{Style.RESET_ALL}")
        else:
            print(f"{Fore.BLUE}No locally saved projects found (starting fresh).{Style.RESET_ALL}")

        # Get available tools
        # Use the active session for tool listing/completion
        active = self.sessions.get(self.active_session)
        if not active:
            raise RuntimeError(f"Active session '{self.active_session}' not connected")
        tools_list = await self._get_tools_cached(self.active_session)
        self.tools = {tool.name: tool for tool in tools_list}
        
        # Create tool name completer for CLI
        tool_names = list(self.tools.keys())
        self.tool_completer = WordCompleter(
            tool_names + ['help', 'list', 'exit', 'quit', 'projects', 'use', 'start-api', 'connect', 'servers']
        )
        
        print(f"\n{Fore.YELLOW}Available tools:{Style.RESET_ALL}")
        for name, tool in self.tools.items():
            print(f"  • {Fore.CYAN}{name}{Style.RESET_ALL}: {tool.description}")
        print()
        
    async def _run_cli(self):
        """Run the interactive command-line interface."""
        print(f"{Fore.BLUE}Jarvis Client Ready!{Style.RESET_ALL}")
        print("Type 'help' for commands, 'exit' to quit\n")
        
        # Command history file
        history = FileHistory('.jarvis_history')
        
        while True:
            try:
                # Get user input with autocompletion
                command = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: prompt(
                        self._prompt(),
                        completer=self.tool_completer,
                        history=history
                    )
                )
                
                # Process the command
                await self._process_command(command.strip())
                
            except (EOFError, KeyboardInterrupt):
                print(f"\n{Fore.YELLOW}Exiting...{Style.RESET_ALL}")
                break
            except ReconnectNeeded:
                # Bubble up to restart the server/session
                raise
            except Exception as e:
                print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")

    def _prompt(self) -> str:
        label = self.active_session or "jarvis"
        if self.active_project:
            label += f"[{self.active_project}]"
        return f"{label}> "

    def _check_server_dependencies(self) -> List[str]:
        """Check that server runtime deps are available in current env."""
        missing: List[str] = []
        try:
            import aiofiles  # noqa: F401
        except Exception:
            missing.append("aiofiles")
        try:
            import httpx  # noqa: F401
        except Exception:
            missing.append("httpx")
        # MCP is required by the client already, so we skip checking it
        return missing
    
    async def _process_command(self, command: str):
        """Process a user command."""
        if not command:
            return
            
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        # Built-in commands
        if cmd in ['exit', 'quit']:
            raise EOFError
        elif cmd == 'help':
            self._show_help()
        elif cmd == 'list':
            await self._list_tools()
        elif cmd == 'projects':
            self._list_local_projects()
        elif cmd == 'use':
            await self._use_project(args)
        elif cmd == 'start-api':
            self._start_api_server()
        elif cmd == 'connect':
            await self._connect_server(args)
        elif cmd == 'servers':
            self._list_servers()
        elif cmd == 'use-server':
            await self._use_server(args)
        elif cmd == 'disconnect':
            await self._disconnect_server(args)
        elif cmd in self.tools:
            await self._call_tool(cmd, args)
        else:
            # Try routing natural language to a tool call
            tool_name, routed_args = route_natural_language(command, self.tools)
            if tool_name:
                print(f"{Fore.BLUE}Routing natural language to: {tool_name}{Style.RESET_ALL}")
                # Convert args dict to JSON string for _call_tool parser
                try:
                    args_json = json.dumps(routed_args or {})
                except Exception:
                    args_json = "{}"
                # Show routed args for transparency
                try:
                    if args_json and args_json != "{}":
                        print(f"{Fore.BLUE}With args: {args_json}{Style.RESET_ALL}")
                except Exception:
                    pass
                await self._call_tool(tool_name, args_json)
            else:
                # Fallback: treat input as a chat message
                try:
                    print(f"{Fore.BLUE}Routing natural language to: jarvis_chat{Style.RESET_ALL}")
                    await self._call_tool("jarvis_chat", json.dumps({"message": command}))
                except Exception:
                    print(f"{Fore.RED}Unknown command: {cmd}{Style.RESET_ALL}")
                    print("Type 'help' for available commands")
    
    def _show_help(self):
        """Show help information."""
        print(f"\n{Fore.YELLOW}Available Commands:{Style.RESET_ALL}")
        print(f"  {Fore.CYAN}help{Style.RESET_ALL}              - Show this help message")
        print(f"  {Fore.CYAN}list{Style.RESET_ALL}              - List all available tools")
        print(f"  {Fore.CYAN}projects{Style.RESET_ALL}          - List locally saved projects (if any)")
        print(f"  {Fore.CYAN}use <name>{Style.RESET_ALL}        - Set active project for tool calls (if supported)")
        print(f"  {Fore.CYAN}start-api{Style.RESET_ALL}         - Start FastAPI on http://127.0.0.1:8001")
        print(f"  {Fore.CYAN}exit/quit{Style.RESET_ALL}         - Exit the client")
        print(f"  {Fore.CYAN}connect <alias> <cmd> [args...] {Style.RESET_ALL}- Connect an MCP server as <alias>")
        print(f"  {Fore.CYAN}servers{Style.RESET_ALL}           - List connected and saved MCP servers")
        print(f"  {Fore.CYAN}use-server <alias>{Style.RESET_ALL} - Make <alias> the active session for direct tool calls")
        print(f"  {Fore.CYAN}disconnect <alias>{Style.RESET_ALL} - Disconnect and remove a server alias")
        print(f"  {Fore.CYAN}<tool> [args]{Style.RESET_ALL}     - Call a tool with JSON arguments")
        print(f"  {Fore.CYAN}--project <name>{Style.RESET_ALL}  - Override active project for a call (if supported)")
        print(f"  Natural language routing supported for a few intents.")
        print(f"\n{Fore.YELLOW}Example tool calls:{Style.RESET_ALL}")
        print(f'  {Fore.GREEN}jarvis_get_status{Style.RESET_ALL}')
        print(f'  {Fore.GREEN}jarvis_chat {{"message": "Hello Jarvis!"}}{Style.RESET_ALL}')
        print(f'  {Fore.GREEN}jarvis_schedule_task {{"description": "Call the dentist", "priority": "medium"}}{Style.RESET_ALL}')
        print(f'  {Fore.GREEN}jarvis_get_tasks {{"status": "pending"}}{Style.RESET_ALL}')
        print()
    
    async def _list_tools(self):
        """List all available tools with their descriptions."""
        print(f"\n{Fore.YELLOW}Available Tools:{Style.RESET_ALL}")
        tools_list = await self._get_tools_cached(self.active_session)
        self.tools = {tool.name: tool for tool in tools_list}
        for name, tool in self.tools.items():
            print(f"\n{Fore.CYAN}{name}{Style.RESET_ALL}")
            print(f"  Description: {tool.description}")
            if getattr(tool, 'inputSchema', None):
                schema = tool.inputSchema
                # Handle dict-like schemas and object-like schemas
                props = None
                required = []
                if isinstance(schema, dict):
                    props = schema.get('properties') or {}
                    required = schema.get('required') or []
                else:
                    props = getattr(schema, 'properties', None) or {}
                    required = getattr(schema, 'required', None) or []
                if props:
                    print("  Parameters:")
                    for param, details in props.items():
                        desc = None
                        if isinstance(details, dict):
                            desc = details.get('description')
                        else:
                            desc = getattr(details, 'description', None)
                        req_marker = "*" if param in required else ""
                        print(f"    • {param}{req_marker}: {desc or 'No description'}")
    
    async def _call_tool(self, tool_name: str, args_str: str):
        """
        Call a tool with the given arguments.
        
        This is where you can later plug in LLM integration to convert
        natural language to tool arguments.
        """
        tool = self.tools[tool_name]
        
        # Extract project override flag: --project <name> or --project=<name>
        project_override = None
        try:
            m = re.search(r"--project(?:\s+|=)(\S+)", args_str)
            if m:
                project_override = m.group(1)
                # Remove the flag from the args string
                args_str = (args_str[:m.start()] + args_str[m.end():]).strip()
        except Exception:
            pass

        # Parse arguments
        try:
            if args_str:
                # Try to parse as JSON
                args = json.loads(args_str)
            else:
                # No arguments provided
                args = {}
        except json.JSONDecodeError:
            # If not valid JSON, try to parse as key=value pairs
            args = self._parse_simple_args(args_str)

        # If tool accepts a 'project' parameter, default from active or override
        if isinstance(args, dict):
            if 'project' not in args:
                if project_override:
                    args['project'] = project_override
                elif self.active_project and self._tool_accepts_project(tool):
                    args['project'] = self.active_project
        
        print(f"{Fore.BLUE}Calling {tool_name}...{Style.RESET_ALL}")
        
        try:
            # Special-case: orchestrator.run_plan executed client-side with multi-server routing
            if tool_name == "orchestrator.run_plan":
                from orchestrator import executor

                class _Router:
                    def __init__(self, outer: 'JarvisClient'):
                        self._outer = outer

                    async def call_tool_server(self, server: Optional[str], tool: str, args: Dict[str, Any]):
                        alias = server or "jarvis"
                        if alias not in self._outer.sessions:
                            raise RuntimeError(f"Server '{alias}' not connected")
                        return await self._outer.sessions[alias].call_tool(tool, args)

                steps = args.get("steps") if isinstance(args, dict) else None
                if not isinstance(steps, list):
                    raise ValueError("orchestrator.run_plan requires args.steps as a list")

                router = _Router(self)
                results = await executor.execute_plan(steps, router)
                # Wrap to be pretty-printable by _display_result
                result = json.dumps({"results": results}, ensure_ascii=False)
            else:
                # Default: call tool on the active session
                session = self.sessions.get(self.active_session)
                if not session:
                    raise RuntimeError(f"Active session '{self.active_session}' not connected")
                result = await session.call_tool(tool_name, args)

            # Display the result
            self._display_result(result)

            # Persist on successful project registration
            if tool_name == "register_project":
                self._maybe_persist_registered_project(args, result)

        except Exception as e:
            if self._should_reconnect_error(e):
                print(f"{Fore.RED}Connection lost while calling '{tool_name}'.{Style.RESET_ALL}")
                # Signal the outer loop to reconnect
                raise ReconnectNeeded() from e
            print(f"{Fore.RED}Error calling tool: {e}{Style.RESET_ALL}")

    async def _spawn_and_hold(self, alias: str, params: StdioServerParameters) -> None:
        """Spawn a subprocess MCP server and hold its session open under alias."""
        # If a prior task exists but has finished, clean it up and allow reconnect
        existing = self._server_tasks.get(alias)
        if existing is not None:
            if existing.done():
                self._server_tasks.pop(alias, None)
            else:
                raise RuntimeError(f"Server alias '{alias}' already connected")

        ready_fut: asyncio.Future = asyncio.get_event_loop().create_future()

        async def runner():
            try:
                async with stdio_client(params) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        # Attach
                        self.sessions[alias] = session
                        if not ready_fut.done():
                            ready_fut.set_result(True)
                        self._mark_server_connected(alias)
                        # Hold open until cancelled
                        try:
                            while True:
                                await asyncio.sleep(3600)
                        except asyncio.CancelledError:
                            pass
            except Exception as e:
                if not ready_fut.done():
                    ready_fut.set_exception(e)
                else:
                    # Surface runtime errors
                    print(f"{Fore.RED}Server '{alias}' stopped: {e}{Style.RESET_ALL}")
            finally:
                # Cleanup on exit
                self.sessions.pop(alias, None)
                # Also remove task handle so reconnect is possible
                self._server_tasks.pop(alias, None)
                self._mark_server_disconnected(alias)

        task = asyncio.create_task(runner(), name=f"mcp-server:{alias}")
        self._server_tasks[alias] = task
        # Wait until initialized or failed
        await ready_fut
        print(f"{Fore.GREEN}Connected server '{alias}'.{Style.RESET_ALL}")

    async def _connect_server(self, args: str) -> None:
        """connect <alias> <command> [args...]"""
        try:
            parts = shlex.split(args or "")
        except Exception:
            parts = (args or "").split()
        if len(parts) < 2:
            print(f"{Fore.YELLOW}Usage: connect <alias> <command> [args...]{Style.RESET_ALL}")
            return
        alias, cmd, *cmd_args = parts
        # If the command was quoted as a single string containing spaces,
        # split it into executable and its arguments for stdio spawning.
        if (not cmd_args) and (" " in cmd or "\t" in cmd):
            try:
                reparsed = shlex.split(cmd)
                if reparsed:
                    cmd, *cmd_args = reparsed
            except Exception:
                pass
        params = StdioServerParameters(command=cmd, args=cmd_args)
        try:
            await self._spawn_and_hold(alias, params)
        except Exception as e:
            print(f"{Fore.RED}Failed to connect '{alias}': {e}{Style.RESET_ALL}")
            return
        # Persist saved connection
        try:
            self.saved_servers[alias] = {"command": cmd, "args": cmd_args}
            save_saved_servers(self.saved_servers)
        except Exception:
            pass
        # Optionally refresh tool list if connecting the active alias
        if alias == self.active_session:
            try:
                await self._initialize()
            except Exception:
                pass

    def _list_servers(self) -> None:
        print(f"\n{Fore.YELLOW}Servers:{Style.RESET_ALL}")
        connected = set(self.sessions.keys())
        if connected:
            print(" Connected:")
            for alias in sorted(connected):
                marker = "*" if alias == self.active_session else " "
                print(f"  {marker} {alias}")
        else:
            print(" Connected: (none)")
        saved = set(self.saved_servers.keys()) - connected
        if saved:
            print(" Saved (not connected):")
            for alias in sorted(saved):
                entry = self.saved_servers.get(alias, {})
                cmd = entry.get("command", "?")
                args = " ".join(entry.get("args", []))
                print(f"    {alias} → {cmd} {args}")

    async def _shutdown_all_servers(self) -> None:
        tasks = list(self._server_tasks.values())
        for t in tasks:
            t.cancel()
        if tasks:
            try:
                await asyncio.gather(*tasks, return_exceptions=True)
            finally:
                self._server_tasks.clear()
        self.active_servers = {}
        save_active_servers(self.active_servers)

    async def _use_server(self, args: str) -> None:
        alias = (args or '').strip()
        if not alias:
            print(f"{Fore.YELLOW}Usage: use-server <alias>{Style.RESET_ALL}")
            return
        if alias not in self.sessions:
            print(f"{Fore.RED}Server '{alias}' not connected. Use: connect {alias} <cmd> [args...]{Style.RESET_ALL}")
            return
        self.active_session = alias
        # Refresh available tools/completion from the new active session
        try:
            tools_list = await self._get_tools_cached(alias)
            self.tools = {tool.name: tool for tool in tools_list}
            tool_names = list(self.tools.keys())
            self.tool_completer = WordCompleter(
                tool_names + ['help', 'list', 'exit', 'quit', 'projects', 'use', 'start-api', 'connect', 'servers', 'use-server']
            )
            print(f"{Fore.GREEN}Active server set to '{alias}'.{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.YELLOW}Warning: failed to refresh tools for '{alias}': {e}{Style.RESET_ALL}")

    async def _disconnect_server(self, args: str) -> None:
        alias = (args or '').strip()
        if not alias:
            print(f"{Fore.YELLOW}Usage: disconnect <alias>{Style.RESET_ALL}")
            return
        existed = False
        task = self._server_tasks.pop(alias, None)
        if task is not None:
            existed = True
            task.cancel()
            try:
                await task
            except Exception:
                pass
        if alias in self.sessions:
            existed = True
            self.sessions.pop(alias, None)
        if not existed:
            print(f"{Fore.YELLOW}Server '{alias}' not connected.{Style.RESET_ALL}")
            return
        # If the active session was removed, pick another if available
        if self.active_session == alias:
            new_active = next(iter(self.sessions.keys()), None)
            self.active_session = new_active or "jarvis"
            # Refresh tools if a session exists
            if new_active and new_active in self.sessions:
                try:
                    tools_list = await self._get_tools_cached(new_active)
                    self.tools = {tool.name: tool for tool in tools_list}
                except Exception:
                    self.tools = {}
            else:
                self.tools = {}
        self._mark_server_disconnected(alias)
        print(f"{Fore.GREEN}Disconnected '{alias}'.{Style.RESET_ALL}")

    def _mark_server_connected(self, alias: str) -> None:
        try:
            self.active_servers[alias] = {"connected": True}
            save_active_servers(self.active_servers)
            self._tools_cache.pop(alias, None)
        except Exception:
            pass

    def _mark_server_disconnected(self, alias: str) -> None:
        try:
            if alias in self.active_servers:
                self.active_servers.pop(alias, None)
                save_active_servers(self.active_servers)
            self._tools_cache.pop(alias, None)
        except Exception:
            pass

    async def _get_tools_cached(self, alias: str):
        session = self.sessions.get(alias)
        if not session:
            raise RuntimeError(f"Session '{alias}' not connected")
        cache = self._tools_cache.setdefault(alias, {"data": None, "expires": 0.0})
        now = time.time()
        if cache["data"] is None or now >= cache["expires"]:
            response = await session.list_tools()
            cache["data"] = response.tools
            cache["expires"] = now + 60.0
        return cache["data"]
    
    def _parse_simple_args(self, args_str: str) -> Dict[str, Any]:
        """
        Parse simple key=value arguments.
        Example: "name=myproject base_url=http://localhost:8080"
        """
        args = {}
        parts = args_str.split()
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                args[key] = value
        return args

    def _tool_accepts_project(self, tool: Any) -> bool:
        schema = getattr(tool, 'inputSchema', None)
        if not schema:
            return False
        props = None
        if isinstance(schema, dict):
            props = schema.get('properties') or {}
        else:
            props = getattr(schema, 'properties', None) or {}
        return 'project' in props

    def _list_local_projects(self):
        print(f"\n{Fore.YELLOW}Local Projects:{Style.RESET_ALL}")
        if not self.local_projects:
            print("  (none saved)")
            return
        for name, info in self.local_projects.items():
            marker = "*" if self.active_project == name else " "
            base_url = info.get('base_url', '')
            print(f" {marker} {name}  →  {base_url}")

    async def _use_project(self, args: str):
        name = (args or '').strip()
        if not name:
            print(f"{Fore.YELLOW}Usage: use <project_name>{Style.RESET_ALL}")
            return
        if name not in self.local_projects:
            print(f"{Fore.RED}Unknown project '{name}'. Save one via register_project first.{Style.RESET_ALL}")
            return
        self.active_project = name
        print(f"{Fore.GREEN}Active project set to '{name}'.{Style.RESET_ALL}")

    def _start_api_server(self) -> None:
        """Launch the FastAPI server in a separate process on port 8001."""
        env = os.environ.copy()
        env["MCP_SERVER_PATH"] = str(self.server_path)
        cmd = [
            sys.executable,
            "-m",
            "uvicorn",
            "client.api:create_app",
            "--factory",
            "--port",
            "8001",
        ]
        try:
            subprocess.Popen(cmd, env=env)
            print(f"{Fore.BLUE}API server starting at http://127.0.0.1:8001 (Ctrl+C to stop in its terminal).{Style.RESET_ALL}")
        except FileNotFoundError:
            print(f"{Fore.RED}uvicorn not found. Install deps: pip install -r client/requirements.txt{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Failed to start API server: {e}{Style.RESET_ALL}")
    
    def _display_result(self, result: Any):
        """Display tool result in a formatted way."""
        print(f"\n{Fore.GREEN}Result:{Style.RESET_ALL}")
        text_view = self._extract_text(result)

        if self._try_render_orchestrator_table(text_view):
            print()
            return

        if self._try_render_json_payload(text_view):
            print()
            return

        # String-like response
        if isinstance(result, str):
            print(result)
        # MCP ToolResponse with content list
        elif hasattr(result, 'content'):
            # Handle different content types
            for content in result.content:
                # Content objects (SDK) or dicts from raw JSON
                if hasattr(content, 'text') or (isinstance(content, dict) and 'text' in content):
                    # Text content
                    text = content.text if hasattr(content, 'text') else content.get('text')
                    print(text)
                elif hasattr(content, 'data') or (isinstance(content, dict) and 'data' in content):
                    # Data content (like images, etc.)
                    mime = getattr(content, 'mimeType', None)
                    if mime is None and isinstance(content, dict):
                        mime = content.get('mimeType')
                    print(f"[Data content: {mime or 'application/octet-stream'}]")
                else:
                    # Unknown content type
                    print(content)
        else:
            # Fallback for unexpected result format
            print(result)
        print()

    def _try_render_orchestrator_table(self, text_view: str) -> bool:
        """Render orchestrator results in a compact table if possible."""
        if not text_view:
            return False
        try:
            data = json.loads(text_view)
        except Exception:
            return False

        if not isinstance(data, dict) or not isinstance(data.get("results"), list):
            return False

        results_list = data["results"]
        if not results_list or not isinstance(results_list[0], dict):
            return False

        if not {"tool", "ok"}.issubset(results_list[0].keys()):
            return False

        rows = []
        for entry in results_list:
            tool = entry.get("tool")
            ok = entry.get("ok")
            if ok:
                preview_src = str(entry.get("data", ""))
            else:
                preview_src = "ERR: " + str(entry.get("error", ""))
            preview = preview_src.replace("\n", " ")
            if len(preview) > 96:
                preview = preview[:93] + "..."
            rows.append([tool, "✅" if ok else "❌", preview])

        print(tabulate(rows, headers=["Tool", "OK", "Preview"], tablefmt="github"))
        return True

    def _try_render_json_payload(self, text_view: str, max_table_rows: int = 20) -> bool:
        """Detect JSON payloads and pretty-print or tabulate them."""
        if not text_view:
            return False

        stripped = text_view.strip()
        if not stripped or stripped[0] not in "{[":
            return False

        try:
            data = json.loads(stripped)
        except Exception:
            return False

        # List of dicts → render as table
        if isinstance(data, list) and data and all(isinstance(item, dict) for item in data):
            headers = list(data[0].keys())
            for item in data[1:]:
                for key in item.keys():
                    if key not in headers:
                        headers.append(key)

            def _cell(value: Any) -> str:
                if isinstance(value, (dict, list)):
                    return json.dumps(value, ensure_ascii=False)
                return "" if value is None else str(value)

            rows = [
                [_cell(item.get(header)) for header in headers]
                for item in data[:max_table_rows]
            ]

            if rows:
                print(tabulate(rows, headers=headers, tablefmt="github"))
            else:
                print("(no rows)")

            if len(data) > max_table_rows:
                print("... (more)")
            return True

        # Any other JSON → pretty-print inside a code block
        pretty = json.dumps(data, indent=2, ensure_ascii=False)
        print("```json")
        print(pretty)
        print("```")
        return True

    def _should_reconnect_error(self, e: Exception) -> bool:
        msg = str(e).lower()
        indicators = [
            "broken pipe",
            "connection reset",
            "connection refused",
            "eof",
            "closed",
            "disconnected",
            "no such file or directory",
        ]
        return any(ind in msg for ind in indicators)

    def _extract_text(self, result: Any) -> str:
        """Extract textual content from a tool call result for inspection."""
        if isinstance(result, str):
            return result
        if hasattr(result, 'content') and getattr(result, 'content') is not None:
            texts: List[str] = []
            for content in result.content:
                if hasattr(content, 'text'):
                    texts.append(getattr(content, 'text') or '')
                elif isinstance(content, dict) and 'text' in content:
                    texts.append(str(content.get('text') or ''))
            return "\n".join(t for t in texts if t)
        return str(result)

    def _maybe_persist_registered_project(self, args: Dict[str, Any], result: Any) -> None:
        """If registration succeeded, store the project locally to JSON."""
        # Require name and base_url to be present in the original args
        name = args.get('name') if isinstance(args, dict) else None
        base_url = args.get('base_url') if isinstance(args, dict) else None
        if not name or not base_url:
            return

        # Inspect server response text for success marker
        text = self._extract_text(result)
        success_markers = ["✅", "registered successfully"]
        error_markers = ["❌", "error", "failed"]
        is_success = any(m in text for m in success_markers) and not any(m in text.lower() for m in error_markers)
        if not is_success:
            return

        # Update in-memory and persist to disk
        entry = {
            "base_url": base_url,
            "notes": args.get('notes', ''),
        }
        self.local_projects[name] = entry
        try:
            save_local_projects(self.local_projects)
            print(f"{Fore.GREEN}Saved project '{name}' locally to .jarvis_projects.json{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.YELLOW}Warning: Failed to save local project cache: {e}{Style.RESET_ALL}")

    # EXTENSION POINT: LLM Integration
    # Uncomment and implement this method to add LLM support
    """
    async def _natural_language_to_tool_call(self, query: str) -> Tuple[str, Dict[str, Any]]:
        '''
        Convert natural language query to tool name and arguments.
        This is where you'd integrate with Ollama, OpenAI, etc.
        
        Example implementation:
        - Send query to LLM with tool descriptions
        - Parse LLM response to extract tool name and args
        - Return (tool_name, args_dict)
        '''
        # TODO: Implement LLM integration
        pass
    """

    # EXTENSION POINT: Web/Desktop UI
    # You could add methods here to expose the client via FastAPI
    """
    def create_web_app(self):
        '''Create a FastAPI app that exposes the MCP client via REST API.'''
        from fastapi import FastAPI
        app = FastAPI()
        
        @app.post("/tools/{tool_name}")
        async def call_tool(tool_name: str, args: Dict[str, Any]):
            result = await self.session.call_tool(tool_name, args)
            return {"result": result}
        
        return app
    """


async def main():
    """Main entry point for the CLI client."""
    print(f"{Fore.MAGENTA}╔══════════════════════════════════╗{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}║        Jarvis MCP Client         ║{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}╚══════════════════════════════════╝{Style.RESET_ALL}\n")
    
    # Check for custom server path from command line
    server_path = None
    if len(sys.argv) > 1:
        server_path = Path(sys.argv[1])
    
    # Create and start the client
    client = JarvisClient(server_path)
    
    try:
        await client.start()
    except Exception as e:
        print(f"{Fore.RED}Failed to start client: {e}{Style.RESET_ALL}")
        sys.exit(1)


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
    
