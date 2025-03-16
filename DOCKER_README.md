# Running Jarvis in Docker

This guide explains how to run Jarvis AI Assistant in Docker using Docker Compose, which will set up both Jarvis and the required Ollama LLM server in containers.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

## Quick Start

1. Clone the Jarvis repository:
   ```bash
   git clone https://github.com/your-username/jarvis.git
   cd jarvis
   ```

2. Create a `.env` file with your API keys (optional):
   ```bash
   echo "OPENAI_API_KEY=your_openai_key_here" > .env
   echo "OPENWEATHER_API_KEY=your_openweather_key_here" >> .env
   ```

3. Start Jarvis using Docker Compose:
   ```bash
   docker-compose up -d
   ```

4. Access the Jarvis web interface:
   - Open your browser and go to `http://localhost:5000`

## Important Notes

- The first startup will take some time as it needs to:
  - Build the Docker image
  - Download the Ollama container
  - Pull the required models (llama3, mistral, phi3)
  
- You can follow the initial setup progress with:
  ```bash
  docker-compose logs -f
  ```

- Model files are stored in a Docker volume named `ollama_data` and persisted between restarts

## Configuration

### Environment Variables

You can configure Jarvis by editing the `.env` file with these variables:

- `OPENAI_API_KEY`: Your OpenAI API key (optional, for hybrid mode)
- `OPENWEATHER_API_KEY`: Your OpenWeatherMap API key (optional, for weather functionality)

### Changing the Default Model

The default model is set to `llama3:8b-instruct-q4_0`. To change it:

1. Stop the containers:
   ```bash
   docker-compose down
   ```

2. Edit the `jarvis/config.py` file:
   ```python
   LOCAL_MODEL_NAME = LOCAL_MODELS["mistral"]  # Change to your preferred model
   ```

3. Restart the containers:
   ```bash
   docker-compose up -d
   ```

## Advanced Usage

### Using CLI Mode Instead of Web Interface

To use CLI mode (requires connecting to the container):

```bash
docker-compose exec jarvis python main.py chat
```

### Running the Dual Model Comparison

```bash
docker-compose exec jarvis python main.py dual_chat
```

### Getting Weather Information

```bash
docker-compose exec jarvis python main.py weather "New York"
```

## Troubleshooting

### Container doesn't start

Check the logs:
```bash
docker-compose logs jarvis
```

### Models are not loading

Check the Ollama container logs:
```bash
docker-compose logs ollama
```

### Reset Everything

To completely reset the installation (including removing all downloaded models):
```bash
docker-compose down -v
docker-compose up -d
```

## Stopping Jarvis

```bash
docker-compose down
```

To also remove the model data volume:
```bash
docker-compose down -v
``` 