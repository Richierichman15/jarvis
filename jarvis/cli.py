"""
Command Line Interface for Jarvis.
This module provides a command-line interface for interacting with Jarvis.
"""
import os
import sys
import time
import json
from typing import Optional, List, Dict, Any, Union

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.style import Style
from rich.syntax import Syntax
from rich.prompt import Prompt, Confirm
from pathlib import Path

from .jarvis import Jarvis
# from .dual_jarvis import DualJarvis  # Commented out - module not available

import argparse
import logging
from tabulate import tabulate

# Create Typer app
app = typer.Typer(help="Jarvis AI Assistant")

# Create console for rich output
console = Console()

# Styles
user_style = Style(color="blue", bold=True)
assistant_style = Style(color="green")
system_style = Style(color="yellow", italic=True)
code_style = Style(color="cyan")

# Export all commands
__all__ = ['chat', 'query', 'code', 'research', 'weather', 'dual_chat', 'dual_query']


def display_startup_message():
    """Display a stylish startup message."""
    console.print("\n")
    console.print(Panel.fit(
        "[bold blue]J[/bold blue][bold red]A[/bold red][bold yellow]R[/bold yellow]"
        "[bold green]V[/bold green][bold purple]I[/bold purple][bold cyan]S[/bold cyan]", 
        title="Welcome to", 
        subtitle="Just A Rather Very Intelligent System"
    ))
    console.print("\n")


@app.command()
def chat(
    name: str = typer.Option("Boss", help="How Jarvis should address you"),
    openai_key: Optional[str] = typer.Option(None, help="OpenAI API key (or set OPENAI_API_KEY env var)")
):
    """Start an interactive chat session with Jarvis."""
    # Set OpenAI API key if provided
    if openai_key:
        os.environ["OPENAI_API_KEY"] = openai_key
        
    # Display startup message
    display_startup_message()
    
    # Initialize Jarvis
    jarvis = Jarvis(user_name=name)
    
    # Display introduction
    jarvis.greet()
    console.print(f"\nJARVIS: ", style=assistant_style, end="")
    console.print("Welcome! I'm ready to assist you. Type 'help' for available commands.")
    
    # Main interaction loop
    try:
        while True:
            # Get user input
            user_input = typer.prompt(f"\n{name}", prompt_suffix="")
            
            if user_input.lower() in ["exit", "quit", "bye", "goodbye"]:
                console.print("\nJARVIS: Goodbye! It was nice talking with you.", style=assistant_style)
                break
                
            # Show thinking animation
            with console.status("[bold green]Thinking...[/bold green]"):
                # Process query
                response = jarvis.chat(user_input)
                
            # Display response
            console.print(f"\nJARVIS: ", style=assistant_style, end="")
            console.print(response)
            
    except KeyboardInterrupt:
        console.print("\n\nJARVIS: Shutting down. Goodbye!", style=assistant_style)
    except Exception as e:
        console.print(f"\n\nError: {str(e)}", style="bold red")
        return 1
        
    return 0


@app.command()
def query(
    question: str = typer.Argument(..., help="Question to ask Jarvis"),
    name: str = typer.Option("Boss", help="How Jarvis should address you"),
    openai_key: Optional[str] = typer.Option(None, help="OpenAI API key (or set OPENAI_API_KEY env var)")
):
    """Ask Jarvis a single question and get a response."""
    # Set OpenAI API key if provided
    if openai_key:
        os.environ["OPENAI_API_KEY"] = openai_key
        
    # Initialize Jarvis
    jarvis = Jarvis(user_name=name)
    
    # Show thinking animation
    with console.status("[bold green]Thinking...[/bold green]"):
        # Process query
        response = jarvis.chat(question)
        
    # Display response
    console.print(f"JARVIS: ", style=assistant_style, end="")
    console.print(response)
    
    return 0


@app.command()
def code(
    file_path: Optional[str] = typer.Argument(None, help="File to open for editing"),
    name: str = typer.Option("Boss", help="How Jarvis should address you"),
    openai_key: Optional[str] = typer.Option(None, help="OpenAI API key (or set OPENAI_API_KEY env var)"),
    execute: bool = typer.Option(False, "--execute", "-e", help="Execute the code after editing"),
    language: str = typer.Option("python", "--language", "-l", help="Programming language for code execution")
):
    """Start an interactive code editing session with Jarvis."""
    # Set OpenAI API key if provided
    if openai_key:
        os.environ["OPENAI_API_KEY"] = openai_key
        
    # Display startup message
    display_startup_message()
    console.print(Panel.fit("Code Editor Mode", title="JARVIS"))
    
    # Initialize Jarvis
    jarvis = Jarvis(user_name=name)
    
    # Welcome message
    console.print(f"JARVIS: ", style=assistant_style, end="")
    console.print("Welcome to the code editor mode! You can:")
    console.print("  - Edit a file: 'edit filename.py'")
    console.print("  - Execute code: 'run' or 'run filename.py'")
    console.print("  - Get code suggestions: Just ask a coding question")
    console.print("  - Exit: 'exit' or 'quit'")
    
    # Open file if provided
    current_file = None
    current_code = None
    
    if file_path:
        with console.status(f"[bold green]Opening {file_path}...[/bold green]"):
            query = f"edit the file {file_path}"
            response = jarvis.process_query(query)
            
        console.print(f"\nJARVIS: ", style=assistant_style, end="")
        console.print(Markdown(response))
        
        current_file = file_path
        
        # Extract code from the response
        import re
        code_blocks = re.findall(r"```(?:\w+)?\n(.*?)\n```", response, re.DOTALL)
        if code_blocks:
            current_code = code_blocks[0]
    
    # Main interaction loop
    try:
        while True:
            # Get user input
            user_input = typer.prompt(f"\n{name} (code)", prompt_suffix="")
            
            if user_input.lower() in ["exit", "quit", "bye", "goodbye"]:
                console.print("\nJARVIS: Exiting code editor mode.", style=assistant_style)
                break
            
            # Handle special commands
            if user_input.lower().startswith("edit "):
                # Edit a file
                file_path = user_input[5:].strip()
                if not file_path:
                    console.print("Please specify a file to edit.", style=system_style)
                    continue
                    
                with console.status(f"[bold green]Opening {file_path}...[/bold green]"):
                    query = f"edit the file {file_path}"
                    response = jarvis.process_query(query)
                    
                console.print(f"\nJARVIS: ", style=assistant_style, end="")
                console.print(Markdown(response))
                
                current_file = file_path
                
                # Extract code from the response
                import re
                code_blocks = re.findall(r"```(?:\w+)?\n(.*?)\n```", response, re.DOTALL)
                if code_blocks:
                    current_code = code_blocks[0]
                    
            elif user_input.lower() in ["run", "execute"]:
                # Execute current code
                if not current_code:
                    console.print("No code to execute. Please edit a file first.", style=system_style)
                    continue
                    
                with console.status("[bold green]Executing code...[/bold green]"):
                    if current_file:
                        # Detect language from file extension
                        ext = os.path.splitext(current_file)[1].lower()
                        if ext in ['.py', '.pyw']:
                            detected_language = "python"
                        elif ext in ['.js']:
                            detected_language = "javascript"
                        elif ext in ['.sh', '.bash']:
                            detected_language = "bash"
                        else:
                            detected_language = language
                            
                        query = f"execute the file {current_file}"
                    else:
                        detected_language = language
                        query = f"execute this {detected_language} code: {current_code}"
                        
                    response = jarvis.process_query(query)
                    
                console.print(f"\nJARVIS: ", style=assistant_style, end="")
                console.print(Markdown(response))
                
            elif user_input.lower().startswith("run "):
                # Run a specific file
                file_path = user_input[4:].strip()
                if not file_path:
                    console.print("Please specify a file to run.", style=system_style)
                    continue
                    
                with console.status(f"[bold green]Running {file_path}...[/bold green]"):
                    query = f"execute the file {file_path}"
                    response = jarvis.process_query(query)
                    
                console.print(f"\nJARVIS: ", style=assistant_style, end="")
                console.print(Markdown(response))
                
            elif user_input.lower() == "save":
                # Save current code to file
                if not current_file or not current_code:
                    console.print("No file or code to save.", style=system_style)
                    continue
                    
                with console.status(f"[bold green]Saving {current_file}...[/bold green]"):
                    try:
                        # Create directory if it doesn't exist
                        os.makedirs(os.path.dirname(os.path.abspath(current_file)), exist_ok=True)
                        
                        # Write the file
                        with open(current_file, 'w', encoding='utf-8') as f:
                            f.write(current_code)
                            
                        console.print(f"✅ File {current_file} saved successfully.", style=assistant_style)
                    except Exception as e:
                        console.print(f"❌ Error saving file: {str(e)}", style="bold red")
                
            else:
                # Treat as a regular query
                with console.status("[bold green]Thinking...[/bold green]"):
                    response = jarvis.process_query(user_input)
                    
                console.print(f"\nJARVIS: ", style=assistant_style, end="")
                console.print(Markdown(response))
                
                # Check if code was returned
                import re
                code_blocks = re.findall(r"```(?:\w+)?\n(.*?)\n```", response, re.DOTALL)
                if code_blocks and Confirm.ask("Apply this code?", default=False):
                    if current_file:
                        # Apply to current file
                        current_code = code_blocks[0]
                        console.print(f"Code applied to {current_file}. Use 'save' to save changes.", style=system_style)
                    else:
                        # Ask for a file path to save
                        save_path = Prompt.ask("Save to file", default="")
                        if save_path:
                            current_file = save_path
                            current_code = code_blocks[0]
                            
                            # Create directory if it doesn't exist
                            os.makedirs(os.path.dirname(os.path.abspath(current_file)), exist_ok=True)
                            
                            # Write the file
                            with open(current_file, 'w', encoding='utf-8') as f:
                                f.write(current_code)
                                
                            console.print(f"✅ File {current_file} saved successfully.", style=assistant_style)
                            
    except KeyboardInterrupt:
        console.print("\n\nJARVIS: Exiting code editor mode.", style=assistant_style)
    except Exception as e:
        console.print(f"\n\nError: {str(e)}", style="bold red")
        return 1
        
    return 0


@app.command()
def research(
    query: str = typer.Argument(..., help="The research query or topic to investigate"),
    research_type: str = typer.Option("general", help="Type of research: general, crypto, news, products, jobs"),
    name: str = typer.Option("Boss", help="How Jarvis should address you"),
    openai_key: Optional[str] = typer.Option(None, help="OpenAI API key (or set OPENAI_API_KEY env var)")
):
    """Use Jarvis to research a topic on the web with advanced capabilities."""
    display_startup_message()
    
    # Initialize Jarvis (only uses user_name parameter)
    jarvis = Jarvis(user_name=name)
    
    # Show thinking message
    console.print("[system]Researching... Please wait.[/system]", style=system_style)
    
    # Use the web researcher tool directly
    web_researcher_tool = jarvis.tool_manager.tools.get("web_researcher")
    if not web_researcher_tool:
        console.print("[system]Web researcher tool is not available.[/system]", style=system_style)
        return
    
    try:
        # Get research results
        results = web_researcher_tool.research(query, research_type)
        
        # Format the results
        formatted_results = web_researcher_tool.format_research_results(results, research_type)
        
        # Display results
        console.print("\n[bold]Research Results:[/bold]\n")
        console.print(Markdown(formatted_results))
        
        # Show footer
        console.print(f"\n[system]Research completed at {time.strftime('%H:%M:%S')}[/system]", style=system_style)
    
    except Exception as e:
        console.print(f"[bold red]Error during research: {str(e)}[/bold red]")


@app.command()
def weather(
    location: str = typer.Argument(..., help="Location to get weather for (e.g., 'New York', 'London,UK')"),
    name: str = typer.Option("Boss", help="How Jarvis should address you"),
    openai_key: Optional[str] = typer.Option(None, help="OpenAI API key (or set OPENAI_API_KEY env var)")
):
    """Get current weather and forecast for a location."""
    display_startup_message()
    
    # Initialize Jarvis (only uses user_name parameter)
    jarvis = Jarvis(user_name=name)
    
    # Show thinking message
    console.print("[system]Fetching weather data... Please wait.[/system]", style=system_style)
    
    # Use the web researcher tool directly
    web_researcher_tool = jarvis.tool_manager.tools.get("web_researcher")
    if not web_researcher_tool:
        console.print("[system]Weather tool is not available.[/system]", style=system_style)
        return
    
    try:
        # Get weather results
        results = web_researcher_tool.get_weather_info(location)
        
        # Format the results
        formatted_results = web_researcher_tool.format_research_results(results, "weather")
        
        # Display results
        console.print("\n[bold]Weather Information:[/bold]\n")
        console.print(Markdown(formatted_results))
        
        # Show footer
        console.print(f"\n[system]Weather data retrieved at {time.strftime('%H:%M:%S')}[/system]", style=system_style)
    
    except Exception as e:
        console.print(f"[bold red]Error retrieving weather data: {str(e)}[/bold red]")


# @app.command()
# def dual_chat(
#     name: str = typer.Option("Boss", help="How Jarvis should address you"),
#     openai_key: Optional[str] = typer.Option(None, help="OpenAI API key (or set OPENAI_API_KEY env var)"),
#     claude_key: Optional[str] = typer.Option(None, help="Claude API key (or set CLAUDE_API_KEY env var)")
# ):
#     """Start an interactive chat session with both OpenAI and Claude models."""
#     # Dual model functionality temporarily disabled - DualJarvis module not available
#     console.print("Dual model functionality is currently disabled.", style="bold red")
#     return 1


# @app.command()
# def dual_query(
#     question: str = typer.Argument(..., help="Question to ask both models"),
#     name: str = typer.Option("Boss", help="How Jarvis should address you"),
#     openai_key: Optional[str] = typer.Option(None, help="OpenAI API key (or set OPENAI_API_KEY env var)"),
#     claude_key: Optional[str] = typer.Option(None, help="Claude API key (or set CLAUDE_API_KEY env var)")
# ):
#     """Ask a single question and get responses from both OpenAI and Claude models."""
#     # Dual model functionality temporarily disabled - DualJarvis module not available
#     console.print("Dual model functionality is currently disabled.", style="bold red")
#     return 1


def register_commands(subparsers):
    """Register all available commands with the argument parser."""
    # ... existing commands ...

    # Plugin commands
    plugin_parser = subparsers.add_parser('plugin', help='Manage plugins')
    plugin_subparsers = plugin_parser.add_subparsers(dest='plugin_command', required=True)
    
    # List plugins
    list_parser = plugin_subparsers.add_parser('list', help='List available plugins')
    list_parser.add_argument('--format', choices=['table', 'json'], default='table', help='Output format')
    
    # Load plugin
    load_parser = plugin_subparsers.add_parser('load', help='Load a plugin')
    load_parser.add_argument('module_name', help='Module name of the plugin')
    load_parser.add_argument('class_name', help='Class name of the plugin')
    
    # Unload plugin
    unload_parser = plugin_subparsers.add_parser('unload', help='Unload a plugin')
    unload_parser.add_argument('plugin_name', help='Name of the plugin to unload')
    
    # Get plugin settings
    get_settings_parser = plugin_subparsers.add_parser('get-settings', help='Get plugin settings')
    get_settings_parser.add_argument('plugin_name', help='Name of the plugin')
    get_settings_parser.add_argument('--format', choices=['table', 'json'], default='table', help='Output format')
    
    # Update plugin settings
    update_settings_parser = plugin_subparsers.add_parser('update-settings', help='Update plugin settings')
    update_settings_parser.add_argument('plugin_name', help='Name of the plugin')
    update_settings_parser.add_argument('settings_file', help='JSON file containing settings')
    
    # Reset plugin settings
    reset_settings_parser = plugin_subparsers.add_parser('reset-settings', help='Reset plugin settings to defaults')
    reset_settings_parser.add_argument('plugin_name', help='Name of the plugin')
    
    # API commands
    api_parser = subparsers.add_parser('api', help='Control the API server')
    api_subparsers = api_parser.add_subparsers(dest='api_command', required=True)
    
    # Start API server
    start_parser = api_subparsers.add_parser('start', help='Start the API server')
    start_parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    start_parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    start_parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    
    # Stop API server
    stop_parser = api_subparsers.add_parser('stop', help='Stop the API server')
    
    # Get API key
    get_key_parser = api_subparsers.add_parser('get-key', help='Get the API key')

    # ... other existing commands ...

def handle_plugin_command(args, jarvis):
    """Handle plugin-related commands."""
    if args.plugin_command == 'list':
        plugins = jarvis.discover_plugins()
        if args.format == 'json':
            print(json.dumps(plugins, indent=2))
        else:
            if not plugins:
                print("No plugins available")
                return
            
            table_data = []
            for plugin in plugins:
                table_data.append([
                    plugin['name'],
                    plugin['version'],
                    plugin['type'],
                    "Yes" if plugin['enabled'] else "No",
                    plugin['description']
                ])
            
            headers = ["Name", "Version", "Type", "Enabled", "Description"]
            print(tabulate(table_data, headers=headers, tablefmt="grid"))
    
    elif args.plugin_command == 'load':
        if jarvis.load_plugin(args.module_name, args.class_name):
            print(f"Plugin loaded successfully: {args.module_name}.{args.class_name}")
        else:
            print(f"Failed to load plugin: {args.module_name}.{args.class_name}")
    
    elif args.plugin_command == 'unload':
        if jarvis.unload_plugin(args.plugin_name):
            print(f"Plugin unloaded successfully: {args.plugin_name}")
        else:
            print(f"Failed to unload plugin: {args.plugin_name}")
    
    elif args.plugin_command == 'get-settings':
        settings = jarvis.get_plugin_settings(args.plugin_name)
        if settings is None:
            print(f"No settings found for plugin: {args.plugin_name}")
            return
        
        if args.format == 'json':
            print(json.dumps(settings, indent=2))
        else:
            table_data = []
            for key, value in settings.items():
                table_data.append([key, str(value)])
            
            headers = ["Setting", "Value"]
            print(f"Settings for plugin: {args.plugin_name}")
            print(tabulate(table_data, headers=headers, tablefmt="grid"))
    
    elif args.plugin_command == 'update-settings':
        try:
            with open(args.settings_file, 'r') as f:
                settings = json.load(f)
            
            if jarvis.update_plugin_settings(args.plugin_name, settings):
                print(f"Settings updated successfully for plugin: {args.plugin_name}")
            else:
                print(f"Failed to update settings for plugin: {args.plugin_name}")
        except Exception as e:
            print(f"Error loading settings file: {str(e)}")
    
    elif args.plugin_command == 'reset-settings':
        if jarvis.plugin_manager.reset_plugin_settings(args.plugin_name):
            print(f"Settings reset to defaults for plugin: {args.plugin_name}")
        else:
            print(f"Failed to reset settings for plugin: {args.plugin_name}")

def handle_api_command(args, jarvis):
    """Handle API-related commands."""
    if args.api_command == 'start':
        # Create a new Jarvis instance with API enabled if it's not already
        if jarvis.api_server is None:
            print("Creating a new Jarvis instance with API enabled...")
            jarvis = Jarvis(user_name=getattr(args, 'name', "Boss"), 
                           enable_api=True, 
                           api_host=args.host, 
                           api_port=args.port)
        
        # Start the API server
        if jarvis.start_api_server(debug=args.debug):
            print(f"API server started at http://{args.host}:{args.port}")
            print(f"API Key: {jarvis.get_api_key()}")
            
            # If not in debug mode, keep the main thread alive
            if not args.debug:
                try:
                    print("Press Ctrl+C to stop the server")
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\nStopping API server...")
                    jarvis.stop_api_server()
                    print("API server stopped")
        else:
            print("Failed to start API server")
    
    elif args.api_command == 'stop':
        if jarvis.stop_api_server():
            print("API server stopped")
        else:
            print("Failed to stop API server")
    
    elif args.api_command == 'get-key':
        api_key = jarvis.get_api_key()
        if api_key:
            print(f"API Key: {api_key}")
        else:
            print("API server is not initialized")

def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="Jarvis AI Assistant")
    # ... existing code ...
    
    args = parser.parse_args()
    
    # ... existing code ...
    
    # Create Jarvis instance with plugin system enabled by default
    jarvis = Jarvis(user_name=getattr(args, 'name', "Boss"), enable_plugins=True)
    
    # ... existing code ...
    
    # Handle plugin commands
    if hasattr(args, 'plugin_command'):
        handle_plugin_command(args, jarvis)
        return
    
    # Handle API commands
    if hasattr(args, 'api_command'):
        handle_api_command(args, jarvis)
        return
    
    # ... existing code ...


if __name__ == "__main__":
    app() 