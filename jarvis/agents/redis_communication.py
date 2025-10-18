#!/usr/bin/env python3
"""
Redis Communication Module for Jarvis Agent System

This module handles inter-agent communication using Redis channels for task
distribution, response collection, and agent coordination.
"""

import asyncio
import json
import logging
import time
from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
import uuid

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logging.warning("Redis not available. Install with: pip install redis")

from .agent_base import TaskRequest, TaskResponse, AgentCapability

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TaskMessage:
    """Message structure for task distribution."""
    
    def __init__(
        self,
        task_id: str = None,
        agent_id: str = None,
        capability: AgentCapability = None,
        task_type: str = None,
        parameters: Dict[str, Any] = None,
        priority: int = 1,
        timeout: int = 30,
        requester_id: str = None
    ):
        self.task_id = task_id or str(uuid.uuid4())
        self.agent_id = agent_id
        self.capability = capability
        self.task_type = task_type
        self.parameters = parameters or {}
        self.priority = priority
        self.timeout = timeout
        self.requester_id = requester_id
        self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Redis storage."""
        return {
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "capability": self.capability.value if self.capability else None,
            "task_type": self.task_type,
            "parameters": self.parameters,
            "priority": self.priority,
            "timeout": self.timeout,
            "requester_id": self.requester_id,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskMessage':
        """Create from dictionary."""
        return cls(
            task_id=data.get("task_id"),
            agent_id=data.get("agent_id"),
            capability=AgentCapability(data["capability"]) if data.get("capability") else None,
            task_type=data.get("task_type"),
            parameters=data.get("parameters", {}),
            priority=data.get("priority", 1),
            timeout=data.get("timeout", 30),
            requester_id=data.get("requester_id")
        )


class ResponseMessage:
    """Message structure for task responses."""
    
    def __init__(
        self,
        task_id: str,
        agent_id: str,
        success: bool,
        result: Any = None,
        error: str = None,
        processing_time: float = 0.0
    ):
        self.task_id = task_id
        self.agent_id = agent_id
        self.success = success
        self.result = result
        self.error = error
        self.processing_time = processing_time
        self.completed_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Redis storage."""
        return {
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "success": self.success,
            "result": self.result,
            "error": self.error,
            "processing_time": self.processing_time,
            "completed_at": self.completed_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ResponseMessage':
        """Create from dictionary."""
        return cls(
            task_id=data["task_id"],
            agent_id=data["agent_id"],
            success=data["success"],
            result=data.get("result"),
            error=data.get("error"),
            processing_time=data.get("processing_time", 0.0)
        )


class RedisCommunication:
    """Redis-based communication system for agents."""
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        namespace: str = "jarvis_agents",
        max_connections: int = 10
    ):
        if not REDIS_AVAILABLE:
            raise ImportError("Redis not available. Install with: pip install redis")
        
        self.redis_url = redis_url
        self.namespace = namespace
        self.max_connections = max_connections
        
        # Redis connection pool
        self.redis_pool = None
        self.redis_client = None
        
        # Channel names
        self.task_channel = f"{namespace}:tasks"
        self.response_channel = f"{namespace}:responses"
        self.heartbeat_channel = f"{namespace}:heartbeats"
        self.management_channel = f"{namespace}:management"
        
        # Task queues by capability
        self.capability_queues = {
            AgentCapability.TRADING: f"{namespace}:queue:trading",
            AgentCapability.MUSIC: f"{namespace}:queue:music",
            AgentCapability.SYSTEM: f"{namespace}:queue:system",
            AgentCapability.FITNESS: f"{namespace}:queue:fitness",
            AgentCapability.RESEARCH: f"{namespace}:queue:research",
            AgentCapability.CHAT: f"{namespace}:queue:chat",
            AgentCapability.UTILITY: f"{namespace}:queue:utility"
        }
        
        # Response tracking
        self.pending_responses: Dict[str, asyncio.Future] = {}
        self.response_timeout = 60  # seconds
        
        # Subscribers
        self.subscribers: Dict[str, asyncio.Task] = {}
        
        self.logger = logging.getLogger("redis_comm")
    
    async def connect(self):
        """Connect to Redis."""
        try:
            self.redis_pool = redis.ConnectionPool.from_url(
                self.redis_url,
                max_connections=self.max_connections,
                decode_responses=True
            )
            self.redis_client = redis.Redis(connection_pool=self.redis_pool)
            
            # Test connection
            await self.redis_client.ping()
            
            self.logger.info("✅ Connected to Redis")
            
            # Start response listener
            await self._start_response_listener()
            
        except Exception as e:
            self.logger.error(f"❌ Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from Redis."""
        try:
            # Stop all subscribers
            for task in self.subscribers.values():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            # Close Redis connection
            if self.redis_client:
                await self.redis_client.close()
            
            if self.redis_pool:
                await self.redis_pool.disconnect()
            
            self.logger.info("✅ Disconnected from Redis")
            
        except Exception as e:
            self.logger.error(f"Error disconnecting from Redis: {e}")
    
    async def _start_response_listener(self):
        """Start listening for task responses."""
        try:
            pubsub = self.redis_client.pubsub()
            await pubsub.subscribe(self.response_channel)
            
            async def response_listener():
                try:
                    async for message in pubsub.listen():
                        if message['type'] == 'message':
                            try:
                                data = json.loads(message['data'])
                                response = ResponseMessage.from_dict(data)
                                
                                # Notify waiting tasks
                                if response.task_id in self.pending_responses:
                                    future = self.pending_responses.pop(response.task_id)
                                    future.set_result(response)
                                
                            except Exception as e:
                                self.logger.error(f"Error processing response: {e}")
                except asyncio.CancelledError:
                    # Graceful shutdown
                    await pubsub.unsubscribe(self.response_channel)
                    await pubsub.close()
                    self.logger.debug("Response listener shut down gracefully")
                    raise
            
            task = asyncio.create_task(response_listener())
            self.subscribers["response_listener"] = task
            
        except Exception as e:
            self.logger.error(f"Error starting response listener: {e}")
    
    async def send_task(
        self,
        capability: AgentCapability,
        task_type: str,
        parameters: Dict[str, Any] = None,
        priority: int = 1,
        timeout: int = 30,
        requester_id: str = None,
        target_agent_id: str = None
    ) -> str:
        """Send a task to agents with the specified capability."""
        try:
            task = TaskMessage(
                agent_id=target_agent_id,
                capability=capability,
                task_type=task_type,
                parameters=parameters or {},
                priority=priority,
                timeout=timeout,
                requester_id=requester_id
            )
            
            # Add to capability queue
            queue_name = self.capability_queues[capability]
            task_data = json.dumps(task.to_dict())
            
            # Use priority scoring for queue ordering
            score = time.time() + (10 - priority)  # Higher priority = lower score
            await self.redis_client.zadd(queue_name, {task_data: score})
            
            # Publish task notification
            await self.redis_client.publish(self.task_channel, task_data)
            
            self.logger.info(f"📤 Sent task {task.task_id} ({task_type}) to {capability.value} queue")
            
            return task.task_id
            
        except Exception as e:
            self.logger.error(f"Error sending task: {e}")
            raise
    
    async def get_task_for_agent(self, agent_id: str) -> Optional[TaskRequest]:
        """Get the next task for a specific agent."""
        try:
            # Check all capability queues for tasks
            for capability, queue_name in self.capability_queues.items():
                # Get highest priority task (lowest score)
                result = await self.redis_client.zpopmin(queue_name, count=1)
                
                if result:
                    task_data = json.loads(result[0][0])
                    task = TaskMessage.from_dict(task_data)
                    
                    # Convert to TaskRequest
                    task_request = TaskRequest(
                        task_id=task.task_id,
                        agent_id=agent_id,
                        capability=task.capability,
                        task_type=task.task_type,
                        parameters=task.parameters,
                        priority=task.priority,
                        timeout=task.timeout,
                        created_at=task.created_at,
                        requester_id=task.requester_id
                    )
                    
                    self.logger.info(f"📥 Agent {agent_id} got task {task.task_id} ({task.task_type})")
                    return task_request
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting task for agent {agent_id}: {e}")
            return None
    
    async def send_response(self, response: TaskResponse):
        """Send a task response."""
        try:
            response_msg = ResponseMessage(
                task_id=response.task_id,
                agent_id=response.agent_id,
                success=response.success,
                result=response.result,
                error=response.error,
                processing_time=response.processing_time
            )
            
            response_data = json.dumps(response_msg.to_dict())
            await self.redis_client.publish(self.response_channel, response_data)
            
            self.logger.info(f"📤 Sent response for task {response.task_id}")
            
        except Exception as e:
            self.logger.error(f"Error sending response: {e}")
            raise
    
    async def wait_for_response(self, task_id: str, timeout: int = None) -> Optional[ResponseMessage]:
        """Wait for a response to a specific task."""
        try:
            timeout = timeout or self.response_timeout
            
            # Create future for this response
            future = asyncio.Future()
            self.pending_responses[task_id] = future
            
            try:
                # Wait for response with timeout
                response = await asyncio.wait_for(future, timeout=timeout)
                return response
                
            except asyncio.TimeoutError:
                # Remove from pending responses
                self.pending_responses.pop(task_id, None)
                self.logger.warning(f"Timeout waiting for response to task {task_id}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error waiting for response: {e}")
            return None
    
    async def send_heartbeat(self, agent_info: Dict[str, Any]):
        """Send agent heartbeat."""
        try:
            heartbeat_data = {
                "agent_id": agent_info["agent_id"],
                "timestamp": datetime.now().isoformat(),
                "status": agent_info["status"],
                "uptime_seconds": agent_info["uptime_seconds"],
                "tasks_processed": agent_info["tasks_processed"],
                "errors_count": agent_info["errors_count"]
            }
            
            await self.redis_client.publish(self.heartbeat_channel, json.dumps(heartbeat_data))
            
        except Exception as e:
            self.logger.error(f"Error sending heartbeat: {e}")
    
    async def broadcast_management_command(self, command: str, parameters: Dict[str, Any] = None):
        """Broadcast a management command to all agents."""
        try:
            command_data = {
                "command": command,
                "parameters": parameters or {},
                "timestamp": datetime.now().isoformat()
            }
            
            await self.redis_client.publish(self.management_channel, json.dumps(command_data))
            
            self.logger.info(f"📢 Broadcasted management command: {command}")
            
        except Exception as e:
            self.logger.error(f"Error broadcasting management command: {e}")
    
    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get statistics about task queues."""
        try:
            stats = {}
            
            for capability, queue_name in self.capability_queues.items():
                queue_size = await self.redis_client.zcard(queue_name)
                stats[capability.value] = {
                    "queue_size": queue_size,
                    "queue_name": queue_name
                }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting queue stats: {e}")
            return {}
    
    async def clear_queues(self):
        """Clear all task queues."""
        try:
            for queue_name in self.capability_queues.values():
                await self.redis_client.delete(queue_name)
            
            self.logger.info("🧹 Cleared all task queues")
            
        except Exception as e:
            self.logger.error(f"Error clearing queues: {e}")
    
    async def get_redis_info(self) -> Dict[str, Any]:
        """Get Redis server information."""
        try:
            info = await self.redis_client.info()
            return {
                "redis_version": info.get("redis_version"),
                "connected_clients": info.get("connected_clients"),
                "used_memory": info.get("used_memory_human"),
                "uptime_in_seconds": info.get("uptime_in_seconds")
            }
            
        except Exception as e:
            self.logger.error(f"Error getting Redis info: {e}")
            return {}


if __name__ == "__main__":
    # Test Redis communication
    async def test_redis_comm():
        comm = RedisCommunication()
        
        try:
            await comm.connect()
            print("✅ Connected to Redis")
            
            # Test sending a task
            task_id = await comm.send_task(
                capability=AgentCapability.UTILITY,
                task_type="test",
                parameters={"message": "Hello from Redis!"}
            )
            print(f"📤 Sent task: {task_id}")
            
            # Test queue stats
            stats = await comm.get_queue_stats()
            print(f"📊 Queue stats: {stats}")
            
            # Test Redis info
            info = await comm.get_redis_info()
            print(f"🔍 Redis info: {info}")
            
        finally:
            await comm.disconnect()
            print("✅ Disconnected from Redis")
    
    if REDIS_AVAILABLE:
        asyncio.run(test_redis_comm())
    else:
        print("❌ Redis not available. Install with: pip install redis")
