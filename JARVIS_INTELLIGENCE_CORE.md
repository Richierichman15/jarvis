# 🧠 Jarvis Intelligence Core

**Advanced AI-Powered Command Routing and Contextual Memory**

The Jarvis Intelligence Core transforms Jarvis from a command-based system into a truly intelligent assistant that understands natural language, maintains contextual memory, and makes intelligent decisions about which tools to use.

---

## 🎯 **Overview**

The Intelligence Core consists of three main components:

1. **IntentRouter** - LLM-powered command interpretation and routing
2. **ContextRetriever** - Contextual memory and conversation history
3. **Reasoning Engine** - Detailed logging and performance analytics

### **Key Features**
- 🧠 **LLM-Based Intent Recognition** - Uses local or API LLMs to understand user intent
- 🔄 **Contextual Memory** - Retrieves and uses conversation history for better responses
- 🎯 **Intelligent Tool Routing** - Automatically selects the correct tool based on intent
- 📊 **Reasoning Logs** - Detailed logs of decision-making process
- 🔄 **Fallback Mechanisms** - Graceful degradation when LLM is unavailable
- 📈 **Performance Analytics** - Statistics and insights into intent recognition

---

## 🏗️ **Architecture**

```
User Input → IntentRouter → LLM Analysis → Tool Selection → Execution
     ↓              ↓              ↓              ↓
ContextRetriever → Memory → Reasoning → Logging
```

### **Components**

#### **IntentRouter**
- Analyzes natural language input
- Determines user intent (trading, music, fitness, etc.)
- Selects appropriate tool and arguments
- Provides confidence scores and reasoning

#### **ContextRetriever**
- Retrieves conversation history
- Maintains user preferences
- Tracks system state
- Provides contextual information for better decisions

#### **Reasoning Engine**
- Logs all intent analysis decisions
- Tracks performance metrics
- Provides insights for improvement
- Monitors confidence levels

---

## 🚀 **Usage**

### **Basic Integration**

```python
from jarvis.intelligence import IntentRouter, analyze_user_intent

# Initialize router
router = IntentRouter()

# Analyze user intent
result = await router.analyze_intent(
    "show me my portfolio balance",
    user_id="user123",
    channel_id="channel456"
)

print(f"Intent: {result.intent_type.value}")
print(f"Tool: {result.tool_name}")
print(f"Confidence: {result.confidence}")
print(f"Reasoning: {result.reasoning}")
```

### **Discord Bot Integration**

The Intelligence Core is automatically integrated with the Discord bot:

```python
# In discord_jarvis_bot_full.py
if intent_router and INTELLIGENCE_AVAILABLE:
    intent_result = await intent_router.analyze_intent(
        message.content, 
        str(message.author.id), 
        str(message.channel.id)
    )
    
    # Execute the determined tool
    response = await execute_intelligent_tool(intent_result, message)
```

---

## 🎯 **Intent Types**

The Intelligence Core recognizes 7 main intent types:

### **1. Trading (IntentType.TRADING)**
- Portfolio management
- Price queries
- Trade history
- Market analysis
- Risk management

**Examples:**
- "show me my portfolio balance"
- "what's the price of Bitcoin?"
- "get my recent trades"
- "show me momentum signals"

### **2. Music (IntentType.MUSIC)**
- Playback control
- Queue management
- Song discovery
- Voice channel control

**Examples:**
- "play some music"
- "pause the music"
- "skip to the next song"
- "add this to my queue"

### **3. Fitness (IntentType.FITNESS)**
- Workout recommendations
- Exercise instructions
- Fitness tracking
- Goal management

**Examples:**
- "show me chest workouts"
- "what leg exercises can I do?"
- "find beginner exercises"
- "track my workout"

### **4. News (IntentType.NEWS)**
- News scanning
- Information updates
- Market news
- Tech developments

**Examples:**
- "get the latest news"
- "scan tech news for me"
- "what's happening in crypto?"
- "show me AI developments"

### **5. System (IntentType.SYSTEM)**
- Status monitoring
- Task management
- System diagnostics
- Quest tracking

**Examples:**
- "what's my system status?"
- "show me my tasks"
- "check system health"
- "list my quests"

### **6. Search (IntentType.SEARCH)**
- Web search
- Information retrieval
- Research assistance
- Data gathering

**Examples:**
- "search for AI developments"
- "find information about Tesla stock"
- "look up the latest trends"
- "research cryptocurrency"

### **7. Chat (IntentType.CHAT)**
- Casual conversation
- General questions
- Help requests
- Social interaction

**Examples:**
- "how are you doing?"
- "hello there"
- "what can you help me with?"
- "thank you"

---

## 🔧 **Configuration**

### **Environment Variables**

```bash
# LLM Configuration (for brain package)
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Model Configuration
DEFAULT_MODEL=claude-3-sonnet
LOCAL_MODEL=llama3

# Memory Configuration
MEMORY_ENABLED=true
CONVERSATION_HISTORY_LIMIT=10
```

### **Model Selection**

The Intelligence Core supports multiple LLM backends:

1. **Brain Package** - Local LLM integration
2. **Model Manager** - Jarvis's model management system
3. **OpenAI API** - Cloud-based LLM
4. **Anthropic API** - Claude models

### **Fallback Behavior**

When LLM is unavailable, the system falls back to:
1. Pattern matching with regex
2. Keyword-based routing
3. Default chat response

---

## 📊 **Performance Monitoring**

### **Intent Statistics**

```python
# Get performance statistics
stats = router.get_intent_statistics()

print(f"Total requests: {stats['total_requests']}")
print(f"Average processing time: {stats['average_processing_time']:.3f}s")
print(f"Intent distribution: {stats['intent_types']}")
print(f"Confidence distribution: {stats['confidence_distribution']}")
```

### **Logging**

All intent analysis is logged to `/logs/intents.log`:

```json
{
  "timestamp": "2025-01-22T10:30:00",
  "user_id": "user123",
  "channel_id": "channel456",
  "input_text": "show me my portfolio balance",
  "intent_result": {
    "intent_type": "trading",
    "confidence": 0.95,
    "tool_name": "trading.portfolio.get_overview",
    "arguments": {},
    "reasoning": "User is asking for portfolio balance, which maps to trading tool",
    "context_used": ["recent_trading_queries"],
    "fallback_suggestions": ["Try /portfolio command"]
  },
  "context_summary": {
    "conversation_length": 5,
    "previous_intents": 2,
    "system_status": "operational"
  }
}
```

---

## 🧪 **Testing**

### **Run Tests**

```bash
# Test the intelligence core
python test_intelligence_core.py
```

### **Test Cases**

The test suite includes:

1. **Intent Recognition Tests** - Verify correct intent classification
2. **Tool Routing Tests** - Ensure proper tool selection
3. **Edge Case Tests** - Handle unusual inputs gracefully
4. **Performance Tests** - Measure response times
5. **Fallback Tests** - Verify fallback mechanisms

### **Expected Results**

- **Intent Recognition**: >90% accuracy
- **Tool Routing**: >95% accuracy
- **Processing Time**: <2 seconds average
- **Confidence Scores**: >0.8 for clear intents

---

## 🔄 **Integration Examples**

### **Discord Bot**

```python
# Natural language input
user_message = "show me my portfolio balance"

# Intelligence core analysis
intent_result = await intent_router.analyze_intent(
    user_message, 
    str(message.author.id), 
    str(message.channel.id)
)

# Execute determined tool
if intent_result.intent_type == IntentType.TRADING:
    response = await jarvis_client.call_tool(
        intent_result.tool_name,
        intent_result.arguments,
        "jarvis"
    )
```

### **CLI Interface**

```python
# Command line usage
from jarvis.intelligence import analyze_user_intent

result = await analyze_user_intent(
    "play some music",
    "cli_user",
    "terminal"
)

print(f"Executing: {result.tool_name}")
```

### **Web API**

```python
# HTTP API integration
@app.post("/analyze-intent")
async def analyze_intent_endpoint(request: IntentRequest):
    result = await intent_router.analyze_intent(
        request.text,
        request.user_id,
        request.channel_id
    )
    return IntentResponse(
        intent=result.intent_type.value,
        tool=result.tool_name,
        confidence=result.confidence,
        reasoning=result.reasoning
    )
```

---

## 🛠️ **Customization**

### **Adding New Intent Types**

```python
# In intent_router.py
class IntentType(Enum):
    # ... existing types ...
    CUSTOM = "custom"

# Add patterns
intent_patterns[IntentType.CUSTOM] = [
    r'\b(custom|special|unique)\b'
]

# Add tool mappings
tool_mappings["custom"] = {
    "tool": "custom.tool.name",
    "server": "jarvis"
}
```

### **Custom Context Retrieval**

```python
class CustomContextRetriever(ContextRetriever):
    async def get_user_context(self, user_id: str, limit: int = 5):
        # Custom context retrieval logic
        return await super().get_user_context(user_id, limit)
```

### **Custom LLM Integration**

```python
class CustomLLMProvider:
    async def generate_response(self, prompt: str) -> str:
        # Custom LLM integration
        pass
```

---

## 📈 **Performance Optimization**

### **Caching**

- Intent results are cached for similar inputs
- Context retrieval is optimized with limits
- Tool mappings are pre-computed

### **Async Processing**

- All operations are asynchronous
- Parallel context retrieval
- Non-blocking LLM calls

### **Memory Management**

- Conversation history limits
- Automatic cleanup of old logs
- Efficient data structures

---

## 🔍 **Troubleshooting**

### **Common Issues**

1. **Low Confidence Scores**
   - Check LLM availability
   - Verify input clarity
   - Review intent patterns

2. **Incorrect Tool Selection**
   - Update tool mappings
   - Improve intent patterns
   - Check LLM prompts

3. **Slow Performance**
   - Monitor processing times
   - Check LLM response times
   - Optimize context retrieval

### **Debug Mode**

```python
# Enable debug logging
import logging
logging.getLogger('jarvis.intelligence').setLevel(logging.DEBUG)

# Check intent logs
tail -f logs/intents.log
```

### **Health Checks**

```python
# Check intelligence core health
router = IntentRouter()
stats = router.get_intent_statistics()

if stats['average_processing_time'] > 5.0:
    print("⚠️ Slow performance detected")
    
if stats['confidence_distribution']['low'] > 50:
    print("⚠️ Many low-confidence results")
```

---

## 🎉 **Benefits**

### **For Users**
- **Natural Language** - No need to memorize commands
- **Context Awareness** - Remembers previous conversations
- **Intelligent Routing** - Always uses the right tool
- **Better Responses** - More accurate and relevant results

### **For Developers**
- **Extensible** - Easy to add new intents and tools
- **Maintainable** - Clear separation of concerns
- **Observable** - Comprehensive logging and metrics
- **Robust** - Fallback mechanisms for reliability

### **For System**
- **Efficient** - Optimized routing and caching
- **Scalable** - Handles multiple users and channels
- **Reliable** - Graceful error handling
- **Insightful** - Rich analytics and monitoring

---

## 🚀 **Future Enhancements**

### **Planned Features**
- **Multi-Modal Input** - Support for images and voice
- **Learning System** - Improve from user feedback
- **Personalization** - User-specific intent patterns
- **Advanced Context** - Long-term memory integration
- **Intent Chaining** - Multi-step command sequences

### **Integration Opportunities**
- **Vector Databases** - Semantic similarity search
- **Knowledge Graphs** - Structured knowledge representation
- **Reinforcement Learning** - Optimize tool selection
- **Federated Learning** - Improve across multiple instances

---

**The Jarvis Intelligence Core represents a significant leap forward in AI assistant capabilities, providing intelligent, context-aware command routing that makes Jarvis truly intelligent and user-friendly.**

*Last updated: January 2025*
