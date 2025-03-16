"""
Test script for the dual model functionality.
This script allows you to run a simple test of both models in parallel.
"""
import os
import time
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from jarvis.models.dual_model_manager import DualModelManager

console = Console()

def test_dual_model():
    """Test the dual model functionality with a simple prompt."""
    console.print(Panel.fit("Dual Model Test", title="JARVIS"))
    
    # Check if OpenAI API key is set
    if not os.environ.get("OPENAI_API_KEY"):
        console.print("Warning: OpenAI API key not set. Please set the OPENAI_API_KEY environment variable.", style="bold red")
        return 1
    
    # Initialize the dual model manager
    console.print("Initializing dual model manager...")
    manager = DualModelManager()
    
    if not manager.local_available:
        console.print("Error: Local model (Ollama) is not available. Make sure it's installed and running.", style="bold red")
        return 1
        
    if not manager.openai_available:
        console.print("Error: OpenAI API is not available. Check your API key and internet connection.", style="bold red")
        return 1
    
    # Test prompts of varying complexity
    test_prompts = [
        "What is the capital of France?",  # Simple factual
        "Explain how quantum computing works in simple terms.",  # Medium complexity
        "Write a short poem about artificial intelligence.",  # Creative
        "What are the main differences between transformer models and RNNs in natural language processing?",  # Technical
    ]
    
    for i, prompt in enumerate(test_prompts, 1):
        console.print(f"\n[bold]Test {i}:[/bold] {prompt}")
        
        with console.status("[bold green]Running both models in parallel...[/bold green]"):
            result = manager.get_dual_response(prompt)
        
        # Display response
        console.print(Markdown(result["response"]))
        
        # Brief pause between tests
        if i < len(test_prompts):
            time.sleep(1)
    
    console.print("\n[bold green]Dual model test completed![/bold green]")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(test_dual_model()) 