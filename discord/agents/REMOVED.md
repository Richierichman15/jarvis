# Agent System - Removed for Performance

This directory contains documentation for the agent system that was removed from the Discord bot to improve performance.

## AgentToolRouter Implementation (Original)

```python
class AgentToolRouter:
    """Routes Discord bot commands to the Agent System."""
    
    def __init__(self, agent_manager: 'AgentManager'):
        self.agent_manager = agent_manager
        
        # Map tool names to agent capabilities and task types
        self.tool_mapping = {
            # Trading commands (new MCP format)
            "portfolio.get_overview": (AgentCapability.TRADING, "portfolio.get_overview"),
            "portfolio.get_positions": (AgentCapability.TRADING, "portfolio.get_positions"),
            "portfolio.get_trades": (AgentCapability.TRADING, "portfolio.get_trades"),
            "portfolio.get_performance": (AgentCapability.TRADING, "portfolio.get_performance"),
            "trading.get_portfolio_balance": (AgentCapability.TRADING, "trading.get_portfolio_balance"),
            "trading.get_recent_executions": (AgentCapability.TRADING, "trading.get_recent_executions"),
            "trading.get_momentum_signals": (AgentCapability.TRADING, "trading.get_momentum_signals"),
            "paper.get_portfolio": (AgentCapability.TRADING, "paper.get_portfolio"),
            "paper.get_balance": (AgentCapability.TRADING, "paper.get_balance"),
            "paper.get_performance": (AgentCapability.TRADING, "paper.get_performance"),
            "paper.get_trades": (AgentCapability.TRADING, "paper.get_trades"),
            
            # Old trading format (for backward compatibility)
            "trading.get_portfolio": (AgentCapability.TRADING, "portfolio.get_overview"),
            
            # Solo Leveling commands
            "system.system.list_quests": (AgentCapability.SYSTEM, "get_quests"),
            "system.system.get_status": (AgentCapability.SYSTEM, "get_status"),
            "system.create_quest": (AgentCapability.SYSTEM, "create_quest"),
            "system.list_goals": (AgentCapability.SYSTEM, "list_goals"),
            "system.get_level": (AgentCapability.SYSTEM, "get_level"),
            
            # Research commands
            "jarvis_scan_news": (AgentCapability.RESEARCH, "scan_news"),
            "jarvis_web_search": (AgentCapability.RESEARCH, "web_search"),
            "search.web.search": (AgentCapability.RESEARCH, "web_search"),
        }
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> str:
        """Route tool call to appropriate agent."""
        if tool_name not in self.tool_mapping:
            return f"Tool '{tool_name}' not found in agent system"
        
        capability, task_type = self.tool_mapping[tool_name]
        
        try:
            # Send task to agent
            task_id = await self.agent_manager.send_task_to_agent(
                capability=capability,
                task_type=task_type,
                parameters=arguments or {}
            )
            
            # Wait for response (with timeout)
            response = await self.agent_manager.wait_for_response(task_id, timeout=30)
            
            if response and response.success:
                return str(response.result)
            else:
                error_msg = response.error if response else "No response from agent"
                return f"Agent error: {error_msg}"
                
        except asyncio.TimeoutError:
            return "Agent request timed out"
        except Exception as e:
            return f"Error calling agent: {str(e)}"
```

## Integration Points

### 1. Initialization (in on_ready handler)
```python
# Initialize Agent System
if AGENT_SYSTEM_AVAILABLE:
    try:
        agent_manager = AgentManager()
        await agent_manager.start()
        logger.info("🤖 Agent System started (3 agents: Trader, SoloLeveling, Research)")
    except Exception as e:
        logger.warning(f"⚠️ Could not start Agent System: {e}")
        agent_manager = None
```

### 2. Tool Execution (in execute_intelligent_tool)
```python
# Try agent system first
if agent_manager is not None:
    try:
        agent_router = AgentToolRouter(agent_manager)
        result = await agent_router.call_tool(tool_name, arguments)
        
        # If agent system returns a valid result, use it
        if not result.startswith("Tool '") and not result.startswith("Agent error:"):
            logger.info(f"✅ Tool executed by agent system: {tool_name}")
            return result
        else:
            logger.warning(f"Agent system couldn't handle tool, falling back to MCP: {result}")
    except Exception as e:
        logger.warning(f"Agent system error, falling back to MCP: {e}")
```

### 3. Cleanup (in on_disconnect handler)
```python
# Stop agent system when bot disconnects
if agent_manager:
    try:
        await agent_manager.stop()
        logger.info("🛑 Agent System stopped")
    except Exception as e:
        logger.error(f"Error stopping agent system: {e}")
```

## Why It Was Removed

1. **Performance Impact:** Added 100-500ms latency per request
2. **Resource Usage:** Required Redis server and separate agent processes
3. **Complexity:** Extra layer of indirection for simple tool calls
4. **Redundancy:** MCP servers already handle tool execution efficiently

## Future Re-integration

To re-enable agents, restore the code blocks above and ensure:
- Redis server is running
- Agent processes are configured
- `AGENT_SYSTEM_AVAILABLE` flag is set
- Import `AgentManager` and `AgentCapability` from `jarvis.agents`

