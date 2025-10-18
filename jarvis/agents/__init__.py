"""
Jarvis Modular Agent System

This package provides a distributed agent architecture where specialized agents
handle different domains (trading, solo leveling, research) and communicate
via Redis channels for scalable, fault-tolerant operation.

Agents:
- TraderAgent: Trading and portfolio management
- SoloLevelingAgent: Life improvement and goal achievement system
- ResearchAgent: News scanning and web research

Components:
- AgentManager: Orchestrates and monitors all agents
- RedisCommunication: Inter-agent messaging system
- AgentBase: Base class for all agents
"""

from .agent_base import AgentBase, AgentStatus, AgentCapability
from .agent_manager import AgentManager
from .redis_communication import RedisCommunication, TaskMessage, ResponseMessage
try:
    from .trader_agent import TraderAgent
    from .solo_leveling_agent import SoloLevelingAgent
    from .research_agent import ResearchAgent
    AGENTS_AVAILABLE = True
except ImportError as e:
    AGENTS_AVAILABLE = False
    # Create placeholder classes for when agents are not available
    class TraderAgent:
        pass
    class SoloLevelingAgent:
        pass
    class ResearchAgent:
        pass

__all__ = [
    'AgentBase',
    'AgentStatus',
    'AgentCapability',
    'AgentManager',
    'RedisCommunication',
    'TaskMessage',
    'ResponseMessage',
    'TraderAgent',
    'SoloLevelingAgent',
    'ResearchAgent'
]
