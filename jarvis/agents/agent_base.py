#!/usr/bin/env python3
"""
Base Agent Class for Jarvis Modular Agent System

This module provides the base class and interfaces that all specialized agents
inherit from, including communication protocols, health monitoring, and task handling.
"""

import asyncio
import json
import logging
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Callable
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Agent status enumeration."""
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class AgentCapability(Enum):
    """Agent capability enumeration."""
    TRADING = "trading"
    MUSIC = "music"
    SYSTEM = "system"
    FITNESS = "fitness"
    RESEARCH = "research"
    CHAT = "chat"
    UTILITY = "utility"


@dataclass
class AgentInfo:
    """Information about an agent."""
    agent_id: str
    name: str
    version: str
    capabilities: List[AgentCapability]
    status: AgentStatus
    started_at: datetime
    last_heartbeat: datetime
    uptime_seconds: int
    tasks_processed: int
    errors_count: int
    metadata: Dict[str, Any]


@dataclass
class TaskRequest:
    """Task request structure."""
    task_id: str
    agent_id: str
    capability: AgentCapability
    task_type: str
    parameters: Dict[str, Any]
    priority: int = 1
    timeout: int = 30
    created_at: datetime = None
    requester_id: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class TaskResponse:
    """Task response structure."""
    task_id: str
    agent_id: str
    success: bool
    result: Any = None
    error: str = None
    processing_time: float = 0.0
    completed_at: datetime = None
    
    def __post_init__(self):
        if self.completed_at is None:
            self.completed_at = datetime.now()


class AgentBase(ABC):
    """Base class for all Jarvis agents."""
    
    def __init__(
        self,
        name: str,
        capabilities: List[AgentCapability],
        version: str = "1.0.0",
        heartbeat_interval: int = 30,
        max_concurrent_tasks: int = 10
    ):
        self.agent_id = f"{name}_{uuid.uuid4().hex[:8]}"
        self.name = name
        self.version = version
        self.capabilities = capabilities
        self.status = AgentStatus.STARTING
        self.heartbeat_interval = heartbeat_interval
        self.max_concurrent_tasks = max_concurrent_tasks
        
        # Timing and metrics
        self.started_at = datetime.now()
        self.last_heartbeat = datetime.now()
        self.tasks_processed = 0
        self.errors_count = 0
        
        # Task management
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.task_handlers: Dict[str, Callable] = {}
        
        # Communication
        self.redis_comm = None
        self.agent_manager = None
        
        # Configuration
        self.config = {}
        self.metadata = {}
        
        # Logging
        self.logger = logging.getLogger(f"agent.{name}")
        
        # Initialize task handlers
        self._register_task_handlers()
        
        self.logger.info(f"🤖 Agent {self.name} ({self.agent_id}) initialized")
    
    @abstractmethod
    def _register_task_handlers(self):
        """Register task handlers for this agent's capabilities."""
        pass
    
    @abstractmethod
    async def _handle_task(self, task: TaskRequest) -> TaskResponse:
        """Handle a specific task. Must be implemented by subclasses."""
        pass
    
    async def start(self, redis_comm=None, agent_manager=None):
        """Start the agent."""
        try:
            self.status = AgentStatus.STARTING
            self.logger.info(f"🚀 Starting agent {self.name}")
            
            # Set up communication
            self.redis_comm = redis_comm
            self.agent_manager = agent_manager
            
            # Initialize agent-specific resources
            await self._initialize()
            
            # Start heartbeat task
            self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            
            # Start task processing loop
            self.task_loop = asyncio.create_task(self._task_processing_loop())
            
            self.status = AgentStatus.RUNNING
            self.started_at = datetime.now()
            self.last_heartbeat = datetime.now()
            
            self.logger.info(f"✅ Agent {self.name} started successfully")
            
        except Exception as e:
            self.status = AgentStatus.ERROR
            self.errors_count += 1
            self.logger.error(f"❌ Failed to start agent {self.name}: {e}")
            raise
    
    async def stop(self):
        """Stop the agent gracefully."""
        try:
            self.status = AgentStatus.STOPPING
            self.logger.info(f"🛑 Stopping agent {self.name}")
            
            # Cancel heartbeat task
            if hasattr(self, 'heartbeat_task'):
                self.heartbeat_task.cancel()
                try:
                    await self.heartbeat_task
                except asyncio.CancelledError:
                    pass
            
            # Cancel task processing loop
            if hasattr(self, 'task_loop'):
                self.task_loop.cancel()
                try:
                    await self.task_loop
                except asyncio.CancelledError:
                    pass
            
            # Cancel all active tasks
            for task_id, task in self.active_tasks.items():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            # Cleanup agent-specific resources
            await self._cleanup()
            
            self.status = AgentStatus.STOPPED
            self.logger.info(f"✅ Agent {self.name} stopped successfully")
            
        except Exception as e:
            self.status = AgentStatus.ERROR
            self.errors_count += 1
            self.logger.error(f"❌ Error stopping agent {self.name}: {e}")
            raise
    
    async def _initialize(self):
        """Initialize agent-specific resources. Override in subclasses."""
        pass
    
    async def _cleanup(self):
        """Cleanup agent-specific resources. Override in subclasses."""
        pass
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeats to the agent manager."""
        while self.status == AgentStatus.RUNNING:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                
                if self.status == AgentStatus.RUNNING:
                    await self._send_heartbeat()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in heartbeat loop: {e}")
                self.errors_count += 1
    
    async def _send_heartbeat(self):
        """Send heartbeat to agent manager."""
        try:
            if self.agent_manager:
                await self.agent_manager.receive_heartbeat(self.get_info())
            
            self.last_heartbeat = datetime.now()
            
        except Exception as e:
            self.logger.error(f"Error sending heartbeat: {e}")
            self.errors_count += 1
    
    async def _task_processing_loop(self):
        """Main task processing loop."""
        while self.status == AgentStatus.RUNNING:
            try:
                # Check for new tasks from Redis
                if self.redis_comm:
                    task = await self.redis_comm.get_task_for_agent(self.agent_id)
                    if task:
                        await self._process_task(task)
                
                # Clean up completed tasks
                await self._cleanup_completed_tasks()
                
                # Small delay to prevent busy waiting
                await asyncio.sleep(0.1)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in task processing loop: {e}")
                self.errors_count += 1
                await asyncio.sleep(1)  # Wait before retrying
    
    async def _process_task(self, task: TaskRequest):
        """Process a single task."""
        if len(self.active_tasks) >= self.max_concurrent_tasks:
            self.logger.warning(f"Max concurrent tasks reached, rejecting task {task.task_id}")
            return
        
        try:
            # Create task handler
            task_handler = asyncio.create_task(self._execute_task(task))
            self.active_tasks[task.task_id] = task_handler
            
            self.logger.info(f"📋 Processing task {task.task_id} ({task.task_type})")
            
        except Exception as e:
            self.logger.error(f"Error creating task handler for {task.task_id}: {e}")
            self.errors_count += 1
    
    async def _execute_task(self, task: TaskRequest):
        """Execute a task and send response."""
        start_time = time.time()
        
        try:
            # Handle the task
            response = await self._handle_task(task)
            response.processing_time = time.time() - start_time
            
            # Send response back
            if self.redis_comm:
                await self.redis_comm.send_response(response)
            
            self.tasks_processed += 1
            self.logger.info(f"✅ Completed task {task.task_id} in {response.processing_time:.2f}s")
            
        except Exception as e:
            self.logger.error(f"❌ Error executing task {task.task_id}: {e}")
            self.errors_count += 1
            
            # Send error response
            error_response = TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e),
                processing_time=time.time() - start_time
            )
            
            if self.redis_comm:
                await self.redis_comm.send_response(error_response)
    
    async def _cleanup_completed_tasks(self):
        """Remove completed tasks from active tasks."""
        completed_tasks = []
        
        for task_id, task in self.active_tasks.items():
            if task.done():
                completed_tasks.append(task_id)
        
        for task_id in completed_tasks:
            del self.active_tasks[task_id]
    
    def register_task_handler(self, task_type: str, handler: Callable):
        """Register a task handler for a specific task type."""
        self.task_handlers[task_type] = handler
        self.logger.info(f"📝 Registered task handler for {task_type}")
    
    def get_info(self) -> AgentInfo:
        """Get current agent information."""
        uptime = (datetime.now() - self.started_at).total_seconds()
        
        return AgentInfo(
            agent_id=self.agent_id,
            name=self.name,
            version=self.version,
            capabilities=self.capabilities,
            status=self.status,
            started_at=self.started_at,
            last_heartbeat=self.last_heartbeat,
            uptime_seconds=int(uptime),
            tasks_processed=self.tasks_processed,
            errors_count=self.errors_count,
            metadata=self.metadata
        )
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get detailed health status."""
        uptime = (datetime.now() - self.started_at).total_seconds()
        time_since_heartbeat = (datetime.now() - self.last_heartbeat).total_seconds()
        
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "status": self.status.value,
            "uptime_seconds": int(uptime),
            "time_since_heartbeat": int(time_since_heartbeat),
            "active_tasks": len(self.active_tasks),
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "tasks_processed": self.tasks_processed,
            "errors_count": self.errors_count,
            "error_rate": self.errors_count / max(1, self.tasks_processed),
            "capabilities": [cap.value for cap in self.capabilities],
            "is_healthy": (
                self.status == AgentStatus.RUNNING and
                time_since_heartbeat < self.heartbeat_interval * 2 and
                self.errors_count < 10
            )
        }
    
    async def handle_management_command(self, command: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle management commands from the agent manager."""
        try:
            if command == "status":
                return self.get_health_status()
            
            elif command == "restart":
                await self.stop()
                await asyncio.sleep(1)
                await self.start(self.redis_comm, self.agent_manager)
                return {"success": True, "message": "Agent restarted"}
            
            elif command == "config":
                if "config" in parameters:
                    self.config.update(parameters["config"])
                    return {"success": True, "message": "Configuration updated"}
                else:
                    return {"success": True, "config": self.config}
            
            elif command == "metrics":
                return {
                    "tasks_processed": self.tasks_processed,
                    "errors_count": self.errors_count,
                    "uptime_seconds": int((datetime.now() - self.started_at).total_seconds()),
                    "active_tasks": len(self.active_tasks)
                }
            
            else:
                return {"success": False, "error": f"Unknown command: {command}"}
                
        except Exception as e:
            self.logger.error(f"Error handling management command {command}: {e}")
            return {"success": False, "error": str(e)}


class AgentFactory:
    """Factory for creating agent instances."""
    
    @staticmethod
    def create_agent(agent_type: str, **kwargs) -> AgentBase:
        """Create an agent instance based on type."""
        agent_classes = {
            "trader": "TraderAgent",
            "music": "MusicAgent", 
            "system": "SystemAgent",
            "fitness": "FitnessAgent",
            "research": "ResearchAgent"
        }
        
        if agent_type not in agent_classes:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        # Import the specific agent class
        module_name = f"jarvis.agents.{agent_type}_agent"
        class_name = agent_classes[agent_type]
        
        try:
            module = __import__(module_name, fromlist=[class_name])
            agent_class = getattr(module, class_name)
            return agent_class(**kwargs)
        except ImportError as e:
            raise ImportError(f"Could not import {class_name}: {e}")


if __name__ == "__main__":
    # Test the base agent
    async def test_agent():
        class TestAgent(AgentBase):
            def _register_task_handlers(self):
                self.register_task_handler("test", self._handle_test_task)
            
            async def _handle_task(self, task: TaskRequest) -> TaskResponse:
                if task.task_type == "test":
                    return await self._handle_test_task(task)
                else:
                    raise ValueError(f"Unknown task type: {task.task_type}")
            
            async def _handle_test_task(self, task: TaskRequest) -> TaskResponse:
                await asyncio.sleep(1)  # Simulate work
                return TaskResponse(
                    task_id=task.task_id,
                    agent_id=self.agent_id,
                    success=True,
                    result=f"Test completed for {task.parameters.get('message', 'no message')}"
                )
        
        # Create and test agent
        agent = TestAgent("test", [AgentCapability.UTILITY])
        
        try:
            await agent.start()
            print(f"Agent started: {agent.get_info()}")
            
            # Simulate running for a bit
            await asyncio.sleep(5)
            
            print(f"Agent health: {agent.get_health_status()}")
            
        finally:
            await agent.stop()
            print("Agent stopped")
    
    asyncio.run(test_agent())
