# 🤖 Jarvis Modular Agent System

**Distributed AI Architecture with Specialized Agents**

The Jarvis Modular Agent System transforms Jarvis into a distributed AI platform where specialized agents handle different domains, communicate via Redis channels, and are orchestrated by an intelligent AgentManager for scalable, fault-tolerant operation.

---

## 🎯 **Overview**

The Agent System consists of three specialized agents, each handling a specific domain:

1. **TraderAgent** - Trading and portfolio management
2. **SoloLevelingAgent** - Life improvement and goal achievement system
3. **ResearchAgent** - News scanning and web research

### **Key Features**
- 🏗️ **Modular Architecture** - Each agent runs independently
- 🔄 **Redis Communication** - Inter-agent messaging via Redis channels
- 🎯 **Intelligent Routing** - Intelligence Core routes tasks to appropriate agents
- 📊 **Health Monitoring** - Automatic health checks and restart capabilities
- ⚡ **Scalable Design** - Agents can be scaled horizontally
- 🛡️ **Fault Tolerant** - Automatic recovery from failures
- 📈 **Performance Analytics** - Comprehensive monitoring and statistics

---

## 🏗️ **Architecture**

```
User Input → Intelligence Core → AgentManager → Specialized Agents
     ↓              ↓              ↓              ↓
Natural Language → Intent Analysis → Task Routing → Domain Processing
     ↓              ↓              ↓              ↓
Context Memory → LLM Reasoning → Redis Channels → Tool Execution
```

### **Components**

#### **AgentManager**
- Orchestrates all agents
- Monitors health and performance
- Handles automatic restarts
- Manages task distribution
- Provides system statistics

#### **Specialized Agents**
- **TraderAgent**: Portfolio, trades, market data, risk analysis
- **SoloLevelingAgent**: Life improvement, goal achievement, quest system, progress tracking
- **ResearchAgent**: News, web search, content analysis

#### **Redis Communication**
- Task distribution channels
- Response collection
- Heartbeat monitoring
- Management commands
- Priority-based queuing

#### **Intelligence Core Integration**
- Natural language understanding
- Intent classification
- Task routing to agents
- Context-aware processing

---

## 🚀 **Quick Start**

### **Prerequisites**

```bash
# Install Redis (required for agent communication)
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS
brew install redis

# Windows
# Download from https://redis.io/download

# Install Python dependencies
pip install redis aiohttp psutil
```

### **Basic Usage**

```python
from jarvis.agents import AgentManager, AgentCapability
from jarvis.intelligence import IntentRouter

# Start the agent system
async def start_jarvis():
    # Create and start AgentManager
    manager = AgentManager()
    await manager.start()
    
    # Create IntentRouter with agent manager
    router = IntentRouter(agent_manager=manager)
    
    # Analyze user intent and route to agents
    result = await router.analyze_intent(
        "show me my portfolio balance",
        user_id="user123",
        channel_id="channel456"
    )
    
    # Route to appropriate agent
    task_id = await router.route_to_agent(result, "user123")
    
    return task_id

# Run the system
asyncio.run(start_jarvis())
```

### **Discord Bot Integration**

```python
# In discord_jarvis_bot_full.py
from jarvis.agents import AgentManager
from jarvis.intelligence import IntentRouter

# Initialize agent system
agent_manager = AgentManager()
await agent_manager.start()

# Create intelligent router
intent_router = IntentRouter(agent_manager=agent_manager)

# In message handler
intent_result = await intent_router.analyze_intent(
    message.content,
    str(message.author.id),
    str(message.channel.id)
)

task_id = await intent_router.route_to_agent(intent_result, str(message.author.id))
```

---

## 🤖 **Specialized Agents**

### **1. TraderAgent**

**Capabilities**: Live Trading (Primary), Paper Trading (Secondary), Portfolio Management, Market Analysis

**Live Trading Commands**:
- `portfolio.get_overview` - Live portfolio summary
- `portfolio.get_positions` - Live positions with current prices
- `portfolio.get_trades` - Live trade history
- `portfolio.get_performance` - Live performance metrics
- `trading.get_portfolio_balance` - Live balance and positions
- `trading.get_recent_executions` - Recent live trades
- `trading.get_momentum_signals` - Momentum analysis

**Paper Trading Commands**:
- `paper.get_portfolio` - Paper portfolio summary
- `paper.get_balance` - Paper balance
- `paper.get_performance` - Paper performance
- `paper.get_trades` - Paper trade history

**Example**:
```python
# Natural language input
"show me my live portfolio balance"

# Routes to TraderAgent
task_id = await manager.send_task_to_agent(
    capability=AgentCapability.TRADING,
    task_type="portfolio.get_overview",
    parameters={}
)

# Paper trading example
task_id = await manager.send_task_to_agent(
    capability=AgentCapability.TRADING,
    task_type="paper.get_portfolio",
    parameters={}
)
```

### **2. SoloLevelingAgent**

**Capabilities**: Life Improvement, Goal Achievement, Quest System, Progress Tracking

**Tasks**:
- `get_status` - Get user status and progress
- `get_level` - Get current level and experience
- `get_quests` - Get available quests
- `list_goals` - List user goals
- `get_progress` - Get overall progress
- `create_quest` - Create new quest
- `update_quest` - Update quest
- `complete_quest` - Complete quest
- `create_goal` - Create new goal
- `update_goal` - Update goal
- `get_achievements` - Get achievements
- `get_motivation` - Get motivational message
- `get_daily_summary` - Get daily progress summary
- `level_up` - Level up user

**Example**:
```python
# Natural language input
"what's my current level?"

# Routes to SoloLevelingAgent
task_id = await manager.send_task_to_agent(
    capability=AgentCapability.SYSTEM,
    task_type="get_level",
    parameters={}
)
```

### **3. ResearchAgent**

**Capabilities**: News Scanning, Web Search, Content Analysis

**Tasks**:
- `scan_news` - Scan news sources
- `web_search` - Perform web search
- `search_topic` - Comprehensive topic search
- `get_news_article` - Get full article
- `analyze_content` - Analyze content
- `summarize_article` - Summarize article
- `get_trending_topics` - Get trending topics
- `research_company` - Research company
- `get_market_news` - Get market news
- `get_tech_news` - Get tech news
- `get_crypto_news` - Get crypto news
- `fact_check` - Fact check claims
- `get_research_history` - Get research history
- `save_research` - Save research
- `get_saved_research` - Get saved research

**Example**:
```python
# Natural language input
"get the latest tech news"

# Routes to ResearchAgent
task_id = await manager.send_task_to_agent(
    capability=AgentCapability.RESEARCH,
    task_type="scan_news",
    parameters={"category": "technology", "limit": 10}
)
```

---

## 🔄 **Communication System**

### **Redis Channels**

The agent system uses Redis channels for communication:

- **Task Distribution**: `jarvis_agents:tasks`
- **Response Collection**: `jarvis_agents:responses`
- **Heartbeat Monitoring**: `jarvis_agents:heartbeats`
- **Management Commands**: `jarvis_agents:management`
- **Capability Queues**: `jarvis_agents:queue:{capability}`

### **Message Types**

#### **TaskMessage**
```json
{
  "task_id": "task_123",
  "agent_id": "trader_abc123",
  "capability": "trading",
  "task_type": "portfolio.get_overview",
  "parameters": {},
  "priority": 1,
  "timeout": 30,
  "requester_id": "user123",
  "created_at": "2025-01-22T10:30:00Z"
}
```

#### **ResponseMessage**
```json
{
  "task_id": "task_123",
  "agent_id": "trader_abc123",
  "success": true,
  "result": {
    "total_value": 125000.50,
    "total_pnl": 2500.75
  },
  "error": null,
  "processing_time": 0.245,
  "completed_at": "2025-01-22T10:30:01Z"
}
```

### **Priority System**

Tasks are queued by priority:
- **Priority 1**: High priority (immediate processing)
- **Priority 2**: Normal priority (standard processing)
- **Priority 3**: Low priority (background processing)

---

## 📊 **Monitoring & Health**

### **Health Monitoring**

The AgentManager continuously monitors agent health:

```python
# Get system health
health = await manager.get_system_health()
print(f"Health: {health['overall_health']}")
print(f"Score: {health['health_score']}%")
print(f"Active agents: {health['active_agents']}")
```

### **Agent Status**

```python
# Get specific agent status
status = await manager.get_agent_status("trader_abc123")
print(f"Status: {status['agent']['status']}")
print(f"Uptime: {status['agent']['uptime_seconds']}s")
print(f"Tasks processed: {status['agent']['tasks_processed']}")
```

### **Statistics**

```python
# Get comprehensive statistics
stats = manager.get_statistics()
print(f"Total agents: {stats['agent_count']}")
print(f"Total restarts: {stats['manager_stats']['total_restarts']}")
print(f"Tasks processed: {stats['manager_stats']['tasks_processed']}")
```

### **Automatic Recovery**

- **Heartbeat Monitoring**: Agents send heartbeats every 30 seconds
- **Timeout Detection**: Agents not responding for 60 seconds are marked unhealthy
- **Automatic Restart**: Unhealthy agents are automatically restarted
- **Max Retry Limit**: Agents exceeding 3 restart attempts are removed

---

## 🎯 **Intelligence Core Integration**

### **Natural Language Processing**

The Intelligence Core analyzes user input and routes to appropriate agents:

```python
# Analyze user intent
result = await router.analyze_intent(
    "show me my portfolio balance",
    user_id="user123",
    channel_id="channel456"
)

# Route to agent
task_id = await router.route_to_agent(result, "user123")
```

### **Intent Mapping**

| Intent Type | Agent Capability | Example Input |
|-------------|------------------|---------------|
| Trading | TRADING | "show me my portfolio" |
| Solo Leveling | SYSTEM | "what's my current level?" |
| Goals | SYSTEM | "create a new quest" |
| News | RESEARCH | "get the latest news" |
| Search | RESEARCH | "search for AI developments" |
| Chat | CHAT | "how are you doing?" |

### **Context Awareness**

The system maintains context across interactions:

- **Conversation History**: Previous user interactions
- **User Preferences**: Individual user settings
- **System State**: Current system status
- **Agent Status**: Health and availability of agents

---

## ⚡ **Performance & Scaling**

### **Horizontal Scaling**

Agents can be scaled horizontally:

```python
# Scale TraderAgent to 3 instances
await manager.scale_agent("trader", 3)

# Scale SoloLevelingAgent to 2 instances  
await manager.scale_agent("solo_leveling", 2)
```

### **Load Balancing**

Tasks are distributed across agent instances using:
- **Round-robin distribution**
- **Priority-based queuing**
- **Capability matching**
- **Health-based routing**

### **Performance Metrics**

- **Task Processing Time**: Average time per task
- **Throughput**: Tasks processed per second
- **Error Rate**: Percentage of failed tasks
- **Agent Utilization**: Resource usage per agent
- **Queue Depth**: Pending tasks per capability

### **Optimization**

- **Connection Pooling**: Efficient Redis connections
- **Task Batching**: Group similar tasks
- **Caching**: Cache frequent responses
- **Async Processing**: Non-blocking operations

---

## 🛠️ **Configuration**

### **Agent Configuration**

```python
agent_configs = {
    "trader": {
        "class": "TraderAgent",
        "capabilities": [AgentCapability.TRADING],
        "auto_start": True,
        "max_concurrent_tasks": 5
    },
    "solo_leveling": {
        "class": "SoloLevelingAgent",
        "capabilities": [AgentCapability.SYSTEM],
        "auto_start": True,
        "max_concurrent_tasks": 10
    }
}
```

### **Redis Configuration**

```python
manager = AgentManager(
    redis_url="redis://localhost:6379",
    heartbeat_timeout=60,
    restart_delay=5,
    max_restart_attempts=3
)
```

### **Environment Variables**

```bash
# Redis configuration
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=your_password

# Agent configuration
AGENT_HEARTBEAT_INTERVAL=30
AGENT_MAX_CONCURRENT_TASKS=10
AGENT_RESTART_DELAY=5

# Monitoring
HEALTH_CHECK_INTERVAL=30
MAX_RESTART_ATTEMPTS=3
```

---

## 🧪 **Testing**

### **Run Tests**

```bash
# Test the agent system
python test_agent_system.py

# Test individual components
python -m jarvis.agents.trader_agent
python -m jarvis.agents.solo_leveling_agent
python -m jarvis.agents.research_agent
```

### **Test Coverage**

The test suite covers:
- **Agent Creation**: Individual agent initialization
- **Task Processing**: Task handling and responses
- **Health Monitoring**: Health checks and recovery
- **Communication**: Inter-agent messaging
- **Error Handling**: Failure scenarios and recovery
- **Performance**: Load testing and optimization
- **Integration**: Intelligence Core integration

### **Expected Results**

- **Agent Creation**: All agents start successfully
- **Task Processing**: >95% success rate
- **Health Monitoring**: Automatic recovery from failures
- **Communication**: Reliable message delivery
- **Performance**: <100ms average task processing time

---

## 🔧 **Troubleshooting**

### **Common Issues**

#### **Redis Connection Failed**
```bash
# Check Redis status
redis-cli ping

# Start Redis server
sudo systemctl start redis-server

# Check Redis logs
sudo journalctl -u redis-server
```

#### **Agent Not Responding**
```python
# Check agent health
health = await manager.get_system_health()
print(f"Unhealthy agents: {health['unhealthy_agents']}")

# Restart specific agent
await manager.restart_agent("agent_id")
```

#### **High Memory Usage**
```python
# Check agent statistics
stats = manager.get_statistics()
print(f"Memory usage: {stats['memory_usage']}")

# Scale down agents
await manager.scale_agent("agent_type", 1)
```

### **Debug Mode**

```python
# Enable debug logging
import logging
logging.getLogger('jarvis.agents').setLevel(logging.DEBUG)

# Check Redis info
redis_info = await manager.redis_comm.get_redis_info()
print(f"Redis info: {redis_info}")
```

### **Performance Issues**

- **Check Redis performance**: Monitor Redis memory and CPU usage
- **Optimize task processing**: Reduce task complexity
- **Scale agents**: Add more agent instances
- **Monitor queue depth**: Check for task backlog

---

## 🚀 **Deployment**

### **Docker Deployment**

```dockerfile
# Dockerfile for agent system
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "-m", "jarvis.agents.agent_manager"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
  
  jarvis-agents:
    build: .
    depends_on:
      - redis
    environment:
      - REDIS_URL=redis://redis:6379
    ports:
      - "8000:8000"
```

### **Production Considerations**

- **Redis Clustering**: Use Redis Cluster for high availability
- **Load Balancing**: Distribute load across multiple instances
- **Monitoring**: Use Prometheus/Grafana for metrics
- **Logging**: Centralized logging with ELK stack
- **Backup**: Regular Redis data backups
- **Security**: Secure Redis connections and authentication

---

## 🎉 **Benefits**

### **For Users**
- **Natural Language**: No need to learn specific commands
- **Specialized Responses**: Domain experts handle each request
- **Faster Processing**: Parallel task execution
- **Better Reliability**: Fault-tolerant architecture
- **Scalable Performance**: Handles increased load

### **For Developers**
- **Modular Design**: Easy to add new agents
- **Independent Development**: Agents can be developed separately
- **Easy Testing**: Individual agent testing
- **Clear Separation**: Domain-specific logic isolation
- **Extensible**: Simple to add new capabilities

### **For System**
- **High Availability**: Automatic recovery from failures
- **Horizontal Scaling**: Add more agents as needed
- **Resource Efficiency**: Optimized resource usage
- **Performance Monitoring**: Comprehensive metrics
- **Fault Isolation**: Failures don't affect other agents

---

## 🔮 **Future Enhancements**

### **Planned Features**
- **Agent Clustering**: Multi-node agent deployment
- **Advanced Load Balancing**: Intelligent task distribution
- **Machine Learning**: Adaptive performance optimization
- **Event Streaming**: Real-time event processing
- **GraphQL API**: Modern API interface
- **WebSocket Support**: Real-time communication
- **Container Orchestration**: Kubernetes deployment
- **Service Mesh**: Advanced networking

### **Integration Opportunities**
- **Microservices**: Full microservices architecture
- **Event Sourcing**: Event-driven architecture
- **CQRS**: Command Query Responsibility Segregation
- **Distributed Tracing**: Request tracing across agents
- **Circuit Breakers**: Fault tolerance patterns
- **Rate Limiting**: API rate limiting
- **Authentication**: OAuth2/JWT integration
- **API Gateway**: Centralized API management

---

**The Jarvis Modular Agent System represents a significant evolution in AI assistant architecture, providing a scalable, fault-tolerant, and intelligent platform that can grow with your needs while maintaining high performance and reliability.**

*Last updated: January 2025*
