#!/usr/bin/env python3
"""
Test script to check connectivity to Ollama LLM server.
Useful for Docker environments to diagnose connection issues.
"""
import os
import sys
import time
import requests
from rich.console import Console
from rich.panel import Panel
import json

console = Console()

def test_ollama_connection(url=None):
    """Test connection to Ollama API server and list available models."""
    if not url:
        # Get the URL from the environment or use default
        url = os.environ.get("LOCAL_MODEL_BASE_URL", "http://localhost:11434/api")
    
    console.print(Panel.fit(f"Testing connection to Ollama at {url}"))
    
    # Test health endpoint
    try:
        console.print("[bold yellow]Testing Ollama health endpoint...[/bold yellow]")
        health_response = requests.get(f"{url}/health", timeout=5)
        health_response.raise_for_status()
        console.print("[bold green]✓ Ollama server is healthy![/bold green]")
    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]✗ Error connecting to Ollama: {str(e)}[/bold red]")
        return False
    
    # List available models
    try:
        console.print("\n[bold yellow]Fetching available models...[/bold yellow]")
        models_response = requests.get(f"{url.replace('/api', '')}/api/tags", timeout=5)
        models_response.raise_for_status()
        models_data = models_response.json()
        
        if "models" in models_data and models_data["models"]:
            console.print("[bold green]✓ Successfully retrieved models![/bold green]")
            console.print("\n[bold]Available Models:[/bold]")
            
            for model in models_data["models"]:
                model_name = model.get("name", "Unknown")
                model_size = model.get("size", 0) / (1024 * 1024 * 1024)  # Convert to GB
                console.print(f"- {model_name} ({model_size:.2f} GB)")
        else:
            console.print("[bold yellow]No models found. You may need to pull models.[/bold yellow]")
            
    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]✗ Error fetching models: {str(e)}[/bold red]")
        return False
    except json.JSONDecodeError:
        console.print("[bold red]✗ Error parsing response from Ollama API[/bold red]")
        return False
    
    console.print("\n[bold green]✓ Ollama connectivity test completed successfully![/bold green]")
    return True

if __name__ == "__main__":
    # Allow passing URL as an argument
    url = sys.argv[1] if len(sys.argv) > 1 else None
    success = test_ollama_connection(url)
    sys.exit(0 if success else 1) 