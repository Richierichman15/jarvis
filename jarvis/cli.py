"""
Command Line Interface for Jarvis.
This module provides a command-line interface for interacting with Jarvis.
"""
import os
import sys
import time
from typing import Optional

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.style import Style

from .jarvis import Jarvis


app = typer.Typer(help="Jarvis AI Assistant")
console = Console()

# Styles
user_style = Style(color="blue", bold=True)
assistant_style = Style(color="green")
system_style = Style(color="yellow", italic=True)


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
    intro = jarvis.get_introduction()
    console.print(f"JARVIS: ", style=assistant_style, end="")
    console.print(Markdown(intro))
    
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
                response = jarvis.process_query(user_input)
                
            # Display response
            console.print(f"\nJARVIS: ", style=assistant_style, end="")
            console.print(Markdown(response))
            
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
        response = jarvis.process_query(question)
        
    # Display response
    console.print(f"JARVIS: ", style=assistant_style, end="")
    console.print(Markdown(response))
    
    return 0


if __name__ == "__main__":
    app() 