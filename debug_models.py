"""
Debug script to test model availability and functionality.
"""
import sys
import os
from jarvis.models.local_model import OllamaModel
from jarvis.models.openai_model import OpenAIModel
from jarvis.models.model_manager import ModelManager
from jarvis.config import OPENAI_API_KEY

def debug_models():
    print("=== JARVIS Model Debug ===")
    
    # 1. Check if OpenAI API key is set
    print("\n1. Checking OpenAI API key...")
    if OPENAI_API_KEY:
        print(f"   ✓ OpenAI API key is set: {OPENAI_API_KEY[:5]}...{OPENAI_API_KEY[-5:]}")
    else:
        print("   ✗ OpenAI API key is not set")
    
    # 2. Test local model
    print("\n2. Testing local model (Ollama)...")
    local_model = OllamaModel()
    local_available = local_model.is_available()
    print(f"   Local model available: {local_available}")
    
    if local_available:
        try:
            test_prompt = "Say hello in one word"
            print(f"   Sending test prompt: '{test_prompt}'")
            response = local_model.generate(test_prompt, max_tokens=10)
            print(f"   Response: '{response}'")
        except Exception as e:
            print(f"   Error testing local model: {str(e)}")
    
    # 3. Test OpenAI model
    print("\n3. Testing OpenAI model...")
    try:
        openai_model = OpenAIModel()
        openai_available = openai_model.is_available()
        print(f"   OpenAI model available: {openai_available}")
        
        if openai_available:
            test_prompt = "Say hello in one word"
            print(f"   Sending test prompt: '{test_prompt}'")
            response = openai_model.generate(test_prompt, max_tokens=10)
            print(f"   Response: '{response}'")
    except Exception as e:
        print(f"   Error testing OpenAI model: {str(e)}")
    
    # 4. Test ModelManager
    print("\n4. Testing ModelManager...")
    try:
        model_manager = ModelManager()
        print(f"   Local model available: {model_manager.local_available}")
        print(f"   OpenAI model available: {model_manager.openai_available}")
        
        if model_manager.local_available or model_manager.openai_available:
            test_prompt = "Say hello in one word"
            print(f"   Sending test prompt: '{test_prompt}'")
            response_data = model_manager.get_response(test_prompt)
            print(f"   Response: '{response_data['response']}'")
            print(f"   Model used: {response_data['model_used']}")
            print(f"   Complexity: {response_data['complexity']}")
    except Exception as e:
        print(f"   Error testing ModelManager: {str(e)}")
    
    print("\n=== Debug Complete ===")

if __name__ == "__main__":
    debug_models() 