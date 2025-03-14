#!/usr/bin/env python3
"""
Model switcher for Jarvis.
This script switches between different local models in Jarvis.
"""
import os
import sys
import argparse
import re
from pathlib import Path

# Available models
MODELS = {
    "llama3": "llama3:8b-instruct-q4_0",
    "mistral": "mistral:7b-instruct-v0.2-q4_0",
    "phi3": "phi3:mini"
}

def list_models():
    """List available models."""
    print("\nAvailable models:")
    print("-" * 50)
    for name, model_id in MODELS.items():
        print(f"- {name}: {model_id}")
    print("-" * 50)

def get_current_model():
    """Get the current model from config.py"""
    config_path = Path(__file__).parent / "jarvis" / "config.py"
    if not config_path.exists():
        print(f"Error: Config file not found at {config_path}")
        return None
        
    with open(config_path, "r") as f:
        content = f.read()
        
    # Look for LOCAL_MODEL_NAME setting
    match = re.search(r'LOCAL_MODEL_NAME\s*=\s*LOCAL_MODELS\["(\w+)"\]', content)
    if match:
        return match.group(1)
    return None

def switch_model(model_name):
    """Switch to the specified model."""
    if model_name not in MODELS:
        print(f"Error: Model '{model_name}' not found.")
        list_models()
        return False
        
    config_path = Path(__file__).parent / "jarvis" / "config.py"
    if not config_path.exists():
        print(f"Error: Config file not found at {config_path}")
        return False
        
    # Read the config file
    with open(config_path, "r") as f:
        content = f.read()
        
    # Replace the model name
    pattern = r'(LOCAL_MODEL_NAME\s*=\s*LOCAL_MODELS\[)"(\w+)"\]'
    replacement = rf'\1"{model_name}"\]'
    new_content = re.sub(pattern, replacement, content)
    
    # Write the new config
    with open(config_path, "w") as f:
        f.write(new_content)
        
    print(f"Switched to model: {model_name} ({MODELS[model_name]})")
    return True

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Switch between local models for Jarvis")
    parser.add_argument("model", nargs="?", help="Model to switch to (llama3, mistral, phi3)")
    parser.add_argument("--list", "-l", action="store_true", help="List available models")
    
    args = parser.parse_args()
    
    current_model = get_current_model()
    
    if args.list or not args.model:
        list_models()
        if current_model:
            print(f"\nCurrent model: {current_model} ({MODELS.get(current_model, 'Unknown')})")
        return 0
        
    if args.model == current_model:
        print(f"Already using model: {args.model}")
        return 0
        
    if switch_model(args.model):
        return 0
    return 1

if __name__ == "__main__":
    sys.exit(main()) 