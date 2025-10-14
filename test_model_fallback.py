#!/usr/bin/env python3
"""
Test script for model fallback configuration.
Tests GPT-4o-mini primary with Ollama fallback (no Claude).
"""

import logging
from jarvis.models.model_manager import ModelManager

# Set up logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)

print("╔════════════════════════════════════════════════════════════╗")
print("║  Model Fallback Configuration Test                         ║")
print("╚════════════════════════════════════════════════════════════╝\n")

# Initialize model manager
print("🔧 Initializing Model Manager...\n")
manager = ModelManager()

# Check what's available
print("\n📊 Model Status:")
print(f"  GPT-4o-mini (Primary): {'✅ Available' if manager.openai_available else '❌ Not available'}")
print(f"  Ollama (Fallback): {'✅ Available' if manager.ollama_available else '❌ Not available'}")

# Test generation
print("\n" + "="*60)
print("Testing Response Generation")
print("="*60)

test_prompt = "Say 'Hello from' followed by your model name."
system_prompt = "You are a helpful assistant. Be brief."

print(f"\nPrompt: {test_prompt}")
print(f"System: {system_prompt}\n")

try:
    response = manager.generate(
        prompt=test_prompt,
        system_prompt=system_prompt,
        max_tokens=50
    )
    
    print("Response:")
    print(f"  {response}\n")
    
    # Determine which model was used
    if manager.openai_available and not response.startswith("Error:"):
        print("✅ SUCCESS! GPT-4o-mini responded")
    elif manager.ollama_available and not response.startswith("Error:"):
        print("✅ SUCCESS! Ollama fallback worked")
    else:
        print(f"❌ FAILED: {response}")
        
except Exception as e:
    print(f"❌ ERROR: {e}")

# Summary
print("\n" + "="*60)
print("SUMMARY")
print("="*60)

if manager.openai_available:
    print("✅ Primary model (GPT-4o-mini) is working")
elif manager.ollama_available:
    print("⚠️  Primary model unavailable, but Ollama fallback is working")
else:
    print("❌ No models available")
    print("\nTroubleshooting:")
    print("1. For GPT-4o-mini: Add OPENAI_KEY to your .env file")
    print("2. For Ollama: Ensure Ollama is running (ollama serve)")
    print("3. Pull a model: ollama pull mistral")

print("\n✨ Configuration:")
print("  • Primary: GPT-4o-mini (fast, cost-effective)")
print("  • Fallback: Ollama local LLM (free, private)")
print("  • Removed: Claude (per your request)")

