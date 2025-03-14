"""
Command Line Interface for Jarvis.
This module provides a command-line interface for interacting with Jarvis.
"""
import os
import sys
import time
from typing import Optional, List

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.style import Style
from rich.syntax import Syntax
from rich.prompt import Prompt, Confirm
from pathlib import Path

from .jarvis import Jarvis


app = typer.Typer(help="Jarvis AI Assistant")
console = Console()

# Styles
user_style = Style(color="blue", bold=True)
assistant_style = Style(color="green")
system_style = Style(color="yellow", italic=True)
code_style = Style(color="cyan")


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


if __name__ == "__main__":
    app() 