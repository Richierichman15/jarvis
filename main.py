"""
Main entry point for Jarvis AI Assistant.
"""
import sys
import argparse
import typer
from jarvis.cli import (
    chat,
    query,
    code,
    research,
    weather,
    dual_chat,
    dual_query
)
from jarvis.web_interface import run_web_server

app = typer.Typer(help="Jarvis AI Assistant")

# Register commands
app.command()(chat)
app.command()(query)
app.command()(code)
app.command()(research)
app.command()(weather)
app.command()(dual_chat)
app.command()(dual_query)

if __name__ == "__main__":
    # Check for web interface flag
    parser = argparse.ArgumentParser(description="Jarvis AI Assistant")
    parser.add_argument("--web", action="store_true", help="Start the web interface")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to (web mode only)")
    parser.add_argument("--port", type=int, default=5000, help="Port to bind to (web mode only)")
    parser.add_argument("--name", default="Boss", help="How Jarvis should address you")
    
    # Parse just the web flag to determine mode
    args, remaining = parser.parse_known_args()
    
    if args.web:
        # Web interface mode
        sys.exit(run_web_server(host=args.host, port=args.port, user_name=args.name))
    else:
        # CLI mode
        app()