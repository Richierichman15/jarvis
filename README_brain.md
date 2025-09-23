# Jarvis Brain (Conversational Hub)

A small FastAPI service that provides a conversational hub with short- and long-term memory backed by SQLite, and an LLM adapter (Ollama or OpenAI).

## Features
- Short-term: stores the latest messages (SQLite `messages` table)
- Long-term: stores user-marked notes/goals (SQLite `memories` table)
- Summarization: periodically summarizes the last 50 messages into a `summary` memory
- LLM adapter: 
  - Ollama at `http://localhost:11434` (default)
  - OpenAI (if `OPENAI_API_KEY` is set)

## Configuration
Environment variables (via `.env` or shell):
- `LLM_PROVIDER` = `ollama` | `openai` (default: `ollama`)
- `OLLAMA_MODEL` (default: `llama3.1`)
- `OPENAI_MODEL` (default: `gpt-4o-mini`)
- `OPENAI_API_KEY` (optional, required for OpenAI)
- `MEMORY_DB_PATH` (default: `./data/memory.sqlite`)

## Install
```
# In your venv
pip install -r requirements.brain.txt
```

## Run
```
# Makefile target
make brain

# Or directly
uvicorn brain.chat:app --host 0.0.0.0 --port 8088 --reload
```

## API
POST `/chat`
- Body: `{ "input": string, "project"?: string }`
- Returns: `{ "reply": string, "used_memories": string[] }`

Examples:
```
# Store a goal and get a reply (no header variant supported by lenient parser)
curl -X POST localhost:8088/chat -d '{"input":"hey jarvis, remember my goal is to buy a 335i"}'

# Reference the goal later
curl -X POST localhost:8088/chat -d '{"input":"what did I say about the 335i?"}'
```

Tip: you can also send proper JSON headers:
```
curl -X POST localhost:8088/chat \
  -H 'Content-Type: application/json' \
  -d '{"input":"remember my goal is to buy a 335i"}'
```

## Notes on Existing Project Memory
The main Jarvis app currently stores conversation history in `jarvis_memory.json`. The new `brain/` package is independent and does not modify that behavior. If you want Jarvis to use the SQLite-backed memory instead, we can integrate `brain.memory` in a follow-up change.

