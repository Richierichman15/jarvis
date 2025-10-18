#!/usr/bin/env python3
"""Quick script to verify OpenAI key is properly loaded."""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("Checking OpenAI API Key Configuration...\n")

# Check for both possible key names (OPENAI_KEY is primary)
openai_key = os.environ.get("OPENAI_KEY")
openai_api_key = os.environ.get("OPENAI_API_KEY")

print(f"OPENAI_KEY: {'Found' if openai_key else 'Not found'}")
if openai_key:
    print(f"  Value: {openai_key[:10]}...{openai_key[-4:] if len(openai_key) > 14 else ''}")

print(f"\nOPENAI_API_KEY: {'Found' if openai_api_key else 'Not found'}")
if openai_api_key:
    print(f"  Value: {openai_api_key[:10]}...{openai_api_key[-4:] if len(openai_api_key) > 14 else ''}")

# Test if OpenAIModel can initialize
print("\n" + "="*60)
print("Testing OpenAI Model Initialization...")
print("="*60)

try:
    from jarvis.models.openai_model import OpenAIModel
    model = OpenAIModel()
    print("OpenAI model initialized successfully!")
    print(f"   Using model: {model.model}")
    
    # Try a simple test
    print("\nTesting model with a simple query...")
    try:
        response = model.generate(
            prompt="Say 'Hello, I am Jarvis!' and nothing else.",
            max_tokens=20
        )
        print(f"Model response: {response}")
        print("\nSUCCESS! Your OpenAI key is working perfectly!")
    except Exception as e:
        print(f"Model initialized but test failed: {e}")
        import traceback
        traceback.print_exc()
        
except Exception as e:
    print(f"Failed to initialize OpenAI model: {e}")
    import traceback
    print("\nFull error:")
    traceback.print_exc()
    print("\nTroubleshooting:")
    print("1. Make sure your .env file has: OPENAI_KEY=sk-...")
    print("2. Check that the key is valid at: https://platform.openai.com/api-keys")
    print("3. Try: pip install --upgrade openai")

