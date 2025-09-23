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
from pathlib import Path
from typing import Optional, Dict, Any, List

from colorama import init, Fore, Style
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Allow running as a script by making local imports work
THIS_DIR = Path(__file__).parent
if str(THIS_DIR) not in sys.path:
    sys.path.append(str(THIS_DIR))
from storage import load_projects as load_local_projects, save_projects as save_local_projects
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
            
        self.session: Optional[ClientSession] = None
        self.tools: Dict[str, Any] = {}
        self.tool_completer: Optional[WordCompleter] = None
        self.local_projects: Dict[str, Dict[str, Any]] = {}
        self.active_project: Optional[str] = None
        
    async def start(self):
        """Start the MCP server and establish connection with retries."""
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

        # Create server parameters for stdio transport
        server_params = StdioServerParameters(
            command=sys.executable,  # Python executable
            args=["-u", str(self.server_path), "Boss"]  # unbuffered stdio, default user
        )

        max_attempts = 3
        attempt = 0
        while attempt < max_attempts:
            attempt += 1
            try:
                # Start the server and create a session
                async with stdio_client(server_params) as (read, write):
                    async with ClientSession(read, write) as session:
                        self.session = session

                        # Initialize the connection
                        await self._initialize()

                        # Start the interactive CLI
                        await self._run_cli()
                        # Normal exit from CLI -> stop trying
                        return
            except ReconnectNeeded:
                if attempt < max_attempts:
                    print(f"{Fore.BLUE}Server down, retrying (attempt {attempt}/{max_attempts})...{Style.RESET_ALL}")
                    await asyncio.sleep(1.0)
                    continue
                else:
                    print(f"{Fore.RED}Server unavailable after {max_attempts} attempts.{Style.RESET_ALL}")
                    break
            except Exception as e:
                if attempt < max_attempts:
                    print(f"{Fore.BLUE}Server down, retrying (attempt {attempt}/{max_attempts})...{Style.RESET_ALL}")
                    await asyncio.sleep(1.0)
                    continue
                else:
                    print(f"{Fore.RED}Failed to start client: {e}{Style.RESET_ALL}")
                    break
    
    async def _initialize(self):
        """Initialize the connection and discover available tools."""
        print(f"{Fore.GREEN}Connected to server!{Style.RESET_ALL}")

        # Perform protocol initialization/handshake
        # This ensures versions/capabilities are negotiated before using tools
        await self.session.initialize()

        # Load any locally saved projects (client-side persistence)
        self.local_projects = load_local_projects()
        if self.local_projects:
            print(f"{Fore.BLUE}Loaded {len(self.local_projects)} locally saved project(s).{Style.RESET_ALL}")
        else:
            print(f"{Fore.BLUE}No locally saved projects found (starting fresh).{Style.RESET_ALL}")

        # Get available tools
        tools_response = await self.session.list_tools()
        self.tools = {tool.name: tool for tool in tools_response.tools}
        
        # Create tool name completer for CLI
        tool_names = list(self.tools.keys())
        self.tool_completer = WordCompleter(tool_names + ['help', 'list', 'exit', 'quit', 'projects', 'use', 'start-api'])
        
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
        label = "jarvis"
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
        print(f"  {Fore.CYAN}start-api{Style.RESET_ALL}         - Start FastAPI on http://127.0.0.1:8000")
        print(f"  {Fore.CYAN}exit/quit{Style.RESET_ALL}         - Exit the client")
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
            # Call the tool
            result = await self.session.call_tool(tool_name, args)

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
        """Launch the FastAPI server in a separate process on port 8000."""
        env = os.environ.copy()
        env["MCP_SERVER_PATH"] = str(self.server_path)
        cmd = [
            sys.executable,
            "-m",
            "uvicorn",
            "client.api:create_app",
            "--factory",
            "--port",
            "8000",
        ]
        try:
            subprocess.Popen(cmd, env=env)
            print(f"{Fore.BLUE}API server starting at http://127.0.0.1:8000 (Ctrl+C to stop in its terminal).{Style.RESET_ALL}")
        except FileNotFoundError:
            print(f"{Fore.RED}uvicorn not found. Install deps: pip install -r client/requirements.txt{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Failed to start API server: {e}{Style.RESET_ALL}")
    
    def _display_result(self, result: Any):
        """Display tool result in a formatted way."""
        print(f"\n{Fore.GREEN}Result:{Style.RESET_ALL}")
        
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
    
