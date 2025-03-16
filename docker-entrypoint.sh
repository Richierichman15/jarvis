#!/bin/bash
set -e

# Wait for Ollama to be available
echo "Waiting for Ollama service to be available..."
until curl -s -f "http://ollama:11434/api/health" > /dev/null 2>&1; do
  echo "Ollama service is not ready - sleeping for 5 seconds"
  sleep 5
done
echo "Ollama service is up and running!"

# Check if the required models are available, if not pull them
echo "Checking required models..."
MODELS=("llama3:8b-instruct-q4_0" "mistral:7b-instruct-v0.2-q4_0" "phi3:mini")

for MODEL in "${MODELS[@]}"; do
  echo "Checking for model: $MODEL"
  
  if ! curl -s "http://ollama:11434/api/tags" | grep -q "$MODEL"; then
    echo "Model $MODEL not found. Pulling now..."
    curl -X POST "http://ollama:11434/api/pull" -d "{\"name\":\"$MODEL\"}"
    echo "Model $MODEL pulled successfully"
  else
    echo "Model $MODEL is already available"
  fi
done

echo "All required models are available. Starting Jarvis..."

# Execute the command passed to the script
exec "$@" 