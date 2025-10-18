#!/bin/bash
set -e

# Create necessary directories if they don't exist
mkdir -p /app/jarvis/memory /app/jarvis/debug_logs

# Set default environment variables if not set
export PORT=${PORT:-5000}
export HOST=${HOST:-0.0.0.0}

# Start Ollama service in the background if not running in development mode
if [ -z "$OLLAMA_HOST" ]; then
    echo "Starting Ollama service..."
    ollama serve > /var/log/ollama.log 2>&1 &
    export OLLAMA_HOST="http://localhost:11434"
    
    # Wait for Ollama to be available
    echo "Waiting for Ollama service to be available..."
    until curl -s -f "$OLLAMA_HOST/api/health" > /dev/null 2>&1; do
        echo "Ollama service is not ready - sleeping for 5 seconds"
        sleep 5
    done
    echo "Ollama service is up and running!"
    
    # Pull the required model if not already available
    REQUIRED_MODEL="llama3.1:8b-instruct-q8_0"
    echo "Checking for model: $REQUIRED_MODEL"
    
    if ! curl -s "$OLLAMA_HOST/api/tags" | grep -q "$REQUIRED_MODEL"; then
        echo "Model $REQUIRED_MODEL not found. Pulling now..."
        ollama pull "$REQUIRED_MODEL"
        echo "Model $REQUIRED_MODEL pulled successfully"
    else
        echo "Model $REQUIRED_MODEL is already available"
    fi
    
    echo "Ollama setup complete. Starting Jarvis..."
fi

# Execute the command passed to the script
exec "$@" 