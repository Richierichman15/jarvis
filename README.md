# JARVIS - Just A Rather Very Intelligent System

An AI assistant inspired by Iron Man's JARVIS, built with a hybrid approach using both local models and cloud AI.

## Features

- **Hybrid Intelligence**: Uses local models (via Ollama) for basic tasks and OpenAI for complex reasoning
- **Memory**: Remembers conversation history for context
- **Tools**: Can search the web and use other tools to help answer questions
- **Beautiful CLI**: Stylish command-line interface for interacting with JARVIS
- **Dual Model Mode**: Compare responses and performance of local and OpenAI models side by side
- **Docker Support**: Run Jarvis and Ollama in containers for easy deployment

## Requirements

- Python 3.8+
- [Ollama](https://ollama.ai/) for local model inference
- OpenAI API key (optional)

## Installation

### Standard Installation

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Make sure Ollama is installed and running
4. Pull the needed models:
   ```
   ollama pull llama3:8b-instruct-q4_0
   ```

### Docker Installation

For containerized deployment (includes Ollama):

1. Make sure you have Docker and Docker Compose installed
2. Clone this repository
3. Start the containers:
   ```
   docker-compose up -d
   ```
4. Access the web interface at http://localhost:5000

See [DOCKER_README.md](DOCKER_README.md) for detailed Docker instructions.

## Usage

### Interactive Chat

Start an interactive chat session with JARVIS:

```bash
python main.py chat --name "Your Name"
```

### Single Query

Ask JARVIS a single question:

```bash
python main.py query "What is the capital of France?" --name "Your Name"
```

### Dual Model Mode

Compare local and OpenAI models in real-time to see which is faster and how responses differ:

```bash
# Interactive dual model chat
python main.py dual_chat --openai-key your_api_key_here

# Single dual model query
python main.py dual_query "What is quantum computing?" --openai-key your_api_key_here
```

Both commands will show responses from the local model and OpenAI side by side, along with performance metrics.

### Weather Information

Get weather information for any location:

```bash
python main.py weather "New York" 
```

For the best weather data, set up an OpenWeatherMap API key:

```bash
export OPENWEATHER_API_KEY=your_api_key_here
```

See [WEATHER_README.md](WEATHER_README.md) for detailed setup instructions.

### Web Interface

Start the web interface:

```bash
python main.py --web
```

## Project Structure

- `jarvis/` - Main package
  - `models/` - AI model handlers
  - `memory/` - Conversation memory
  - `tools/` - Tools JARVIS can use
  - `utils/` - Utility functions
  - `jarvis.py` - Core JARVIS class
  - `cli.py` - Command-line interface

## Extending JARVIS

JARVIS is designed to be extended with new tools and capabilities. Add your own tools in the `jarvis/tools/` directory!

## License

MIT 