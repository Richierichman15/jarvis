"""
Jarvis Modular Agent System

This package provides a distributed agent architecture where specialized agents
handle different domains (trading, music, system, fitness, research) and communicate
via Redis channels for scalable, fault-tolerant operation.

Agents:
- TraderAgent: Trading and portfolio management
- MusicAgent: Music playback and queue management
- SystemAgent: System monitoring and management
- FitnessAgent: Workout and fitness tracking
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
    from .music_agent import MusicAgent
    from .system_agent import SystemAgent
    from .fitness_agent import FitnessAgent
    from .research_agent import ResearchAgent
    AGENTS_AVAILABLE = True
except ImportError as e:
    AGENTS_AVAILABLE = False
    # Create placeholder classes for when agents are not available
    class TraderAgent:
        pass
    class MusicAgent:
        pass
    class SystemAgent:
        pass
    class FitnessAgent:
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
    'MusicAgent',
    'SystemAgent',
    'FitnessAgent',
    'ResearchAgent'
]
