# JARVIS - Just A Rather Very Intelligent System

An AI assistant inspired by Iron Man's JARVIS, built with a hybrid approach using both local models and cloud AI.

## Features

- **Hybrid Intelligence**: Uses local models (via Ollama) for basic tasks and OpenAI for complex reasoning
- **Memory**: Remembers conversation history for context
- **Tools**: Can search the web and use other tools to help answer questions
- **Beautiful CLI**: Stylish command-line interface for interacting with JARVIS

## Requirements

- Python 3.8+
- [Ollama](https://ollama.ai/) for local model inference
- OpenAI API key (optional)

## Installation

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Make sure Ollama is installed and running
4. Pull the DeepSeek Coder model (or another model of your choice):
   ```
   ollama pull deepseek-coder
   ```

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

### Using OpenAI

To use OpenAI for more complex reasoning, set your API key:

```bash
export OPENAI_API_KEY=your_api_key_here
```

Or pass it directly:

```bash
python main.py chat --openai-key your_api_key_here
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