# Jarvis Model Configuration

## 🎯 Current Setup

### **Primary Model: GPT-4o-mini**
All Jarvis components now use **GPT-4o-mini** as the primary LLM for faster, more cost-effective responses.

---

## 📊 Model Hierarchy

### 1. **Jarvis Models** (`jarvis/models/`)
Used by: Discord bot formatter, general Jarvis responses

**Priority:**
1. ✅ **OpenAI GPT-4o-mini** (Primary - fast, cost-effective)
2. ✅ **Ollama Local LLM** (Fallback if OpenAI fails - free, private)
3. ❌ **Claude** (Removed per your request)

**Configuration:**
- Model: `gpt-4o-mini`
- API Key: `OPENAI_KEY` or `OPENAI_API_KEY`
- File: `jarvis/models/openai_model.py`

### 2. **Brain Module** (`brain/`)
Used by: Jarvis "brain" API, memory-enhanced conversations

**Priority:**
1. ✅ **OpenAI GPT-4o-mini** (Primary, if `LLM_PROVIDER=openai`)
2. ✅ **Ollama (llama3.1)** (Alternative/Fallback)

**Configuration:**
- Model: `gpt-4o-mini` (configurable via `OPENAI_MODEL`)
- API Key: `OPENAI_KEY` or `OPENAI_API_KEY`
- Provider: Set via `LLM_PROVIDER` environment variable
- File: `brain/config.py` and `brain/llm.py`

---

## ⚙️ Environment Variables

### **Required:**
```env
# Your OpenAI API key (brain checks both)
OPENAI_KEY=sk-...
# OR
OPENAI_API_KEY=sk-...
```

### **Optional (Brain Module):**
```env
# LLM provider selection (default: "ollama")
LLM_PROVIDER=openai

# Model selection (default: "gpt-4o-mini")
OPENAI_MODEL=gpt-4o-mini

# Ollama settings (if using Ollama)
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.1
```

---

## 🔄 Model Fallback Flow

### Discord Bot (Formatter):
```
User Query
    ↓
Try GPT-4o-mini (OpenAI)
    ↓ [If fails]
Try Ollama Local LLM (Mistral 7B)
    ↓ [If fails]
Return error message
```

### Brain Module:
```
User Query
    ↓
Check LLM_PROVIDER setting
    ↓
If "openai" → Use GPT-4o-mini
If "ollama" → Try Ollama first
    ↓ [If Ollama fails]
Fallback to GPT-4o-mini (if key available)
    ↓ [If both fail]
Return safe fallback response
```

---

## 💰 Cost Comparison

| Model | Input | Output | Use Case |
|-------|-------|--------|----------|
| **GPT-4o-mini** | $0.150/1M | $0.600/1M | ✅ Primary (Fast, cheap) |
| **Ollama (Local)** | Free | Free | ✅ Fallback (Free, private) |
| GPT-4 Turbo | $10/1M | $30/1M | ❌ Too expensive |
| Claude 3 Sonnet | $3/1M | $15/1M | ❌ Removed (per request) |

**Savings:** ~98% cost reduction by switching to GPT-4o-mini!

---

## 🧪 Testing Your Configuration

### Test 1: Verify OpenAI Key
```bash
python verify_openai_key.py
```

**Expected Output:**
```
✅ OpenAI model initialized successfully!
   Using model: gpt-4o-mini
✅ Model response: Hello, I am Jarvis!
```

### Test 2: Test Brain Module
```bash
# Start the brain server (if not running)
python -m uvicorn brain.chat:app --port 8000

# Test it
curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d '{"input":"Hello Jarvis"}'
```

### Test 3: Test Discord Bot Formatter
```bash
# Start Discord bot
python discord_jarvis_bot_full.py

# Look for this in logs:
# ✅ AI model initialized for response formatting
# OpenAI model initialized successfully
```

---

## 📝 Files Modified

### ✅ Updated:
1. **`jarvis/models/openai_model.py`**
   - Changed model from `gpt-4-turbo-preview` → `gpt-4o-mini`
   - Added support for `OPENAI_KEY` environment variable

2. **`brain/config.py`**
   - Added support for `OPENAI_KEY` environment variable
   - Already configured to use `gpt-4o-mini` by default

### ℹ️ Already Configured:
- `brain/llm.py` - Brain LLM logic with fallbacks
- `jarvis/models/model_manager.py` - Model manager with OpenAI → Claude fallback

---

## 🎯 Current Behavior

### When You Use Jarvis:

#### Discord Bot Commands:
```
You: /balance
    ↓
Bot calls MCP tool → Returns JSON
    ↓
GPT-4o-mini formats it:
"Your portfolio stands at $15,420.88..."
```

#### Brain Chat API:
```
You: "Remember my goal is to learn Python"
    ↓
Brain uses GPT-4o-mini (via LLM_PROVIDER=openai)
    ↓
If OpenAI unavailable → Fallback to Ollama
    ↓
Jarvis: "Noted! I'll remember that..."
```

---

## 🔧 Switching Models

### To Use GPT-4 (More Expensive):
```python
# In jarvis/models/openai_model.py
self.model = "gpt-4o"  # or "gpt-4-turbo"
```

### To Use Different Brain Model:
```env
# In .env file
OPENAI_MODEL=gpt-4o
# or
OPENAI_MODEL=gpt-3.5-turbo
```

### To Use Ollama for Brain:
```env
# In .env file
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.1
```

---

## 📊 Model Performance

| Metric | GPT-4o-mini | Ollama (Local) | GPT-4 Turbo |
|--------|-------------|----------------|-------------|
| Speed | ⚡ Fast (1-2s) | ⚡⚡ Very Fast (<1s) | 🐢 Slower (2-4s) |
| Cost | 💰 Very Low | 🆓 **FREE** | 💰💰💰 High |
| Quality | ⭐⭐⭐⭐ Excellent | ⭐⭐⭐ Good | ⭐⭐⭐⭐⭐ Best |
| Privacy | ☁️ Cloud API | 🏠 **Local Only** | ☁️ Cloud API |
| Use Case | ✅ Primary | ✅ Fallback/Offline | ❌ Too expensive |

---

## ✅ Benefits of GPT-4o-mini

1. **98% cost reduction** compared to GPT-4 Turbo
2. **Faster responses** (1-2 seconds vs 2-4 seconds)
3. **Good quality** for most Jarvis tasks
4. **Lower latency** for Discord bot responses
5. **Higher rate limits** on OpenAI API

---

## 🚀 Ready to Test!

Your Jarvis is now configured to use GPT-4o-mini everywhere:

✅ **Discord bot formatter** - GPT-4o-mini with Claude fallback  
✅ **Brain module** - GPT-4o-mini with Ollama fallback  
✅ **API key** - Recognizes both `OPENAI_KEY` and `OPENAI_API_KEY`  

**Restart your Discord bot and try it out!**

```bash
python discord_jarvis_bot_full.py
```

Look for:
```
OpenAI model initialized successfully
✅ AI model initialized for response formatting
```

Then test with: `/balance`, `/portfolio`, or any command!

