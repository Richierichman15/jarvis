#!/usr/bin/env python3
"""
AgentManager - Orchestrates and monitors all Jarvis agents

This module provides centralized management of all specialized agents,
including spawning, monitoring, health checks, and automatic restart
capabilities for a distributed AI system.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from dataclasses import asdict

from .agent_base import AgentBase, AgentInfo, AgentStatus, AgentCapability, AgentFactory
from .redis_communication import RedisCommunication, TaskMessage, ResponseMessage

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentManager:
    """Manages all Jarvis agents with monitoring and orchestration."""
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        heartbeat_timeout: int = 60,
        restart_delay: int = 5,
        max_restart_attempts: int = 3
    ):
        self.redis_url = redis_url
        self.heartbeat_timeout = heartbeat_timeout
        self.restart_delay = restart_delay
        self.max_restart_attempts = max_restart_attempts
        
        # Agent management
        self.agents: Dict[str, AgentBase] = {}
        self.agent_info: Dict[str, AgentInfo] = {}
        self.agent_restart_counts: Dict[str, int] = {}
        self.agent_last_heartbeat: Dict[str, datetime] = {}
        
        # Communication
        self.redis_comm = None
        
        # Monitoring
        self.monitoring_task = None
        self.is_running = False
        
        # Configuration
        self.agent_configs = {
            "trader": {
                "class": "TraderAgent",
                "capabilities": [AgentCapability.TRADING],
                "auto_start": True,
                "max_concurrent_tasks": 5
            },
            "music": {
                "class": "MusicAgent", 
                "capabilities": [AgentCapability.MUSIC],
                "auto_start": True,
                "max_concurrent_tasks": 3
            },
            "system": {
                "class": "SystemAgent",
                "capabilities": [AgentCapability.SYSTEM],
                "auto_start": True,
                "max_concurrent_tasks": 10
            },
            "fitness": {
                "class": "FitnessAgent",
                "capabilities": [AgentCapability.FITNESS],
                "auto_start": True,
                "max_concurrent_tasks": 5
            },
            "research": {
                "class": "ResearchAgent",
                "capabilities": [AgentCapability.RESEARCH],
                "auto_start": True,
                "max_concurrent_tasks": 8
            }
        }
        
        # Statistics
        self.stats = {
            "total_agents": 0,
            "active_agents": 0,
            "failed_agents": 0,
            "total_restarts": 0,
            "uptime_start": None,
            "tasks_processed": 0,
            "errors_count": 0
        }
        
        self.logger = logging.getLogger("agent_manager")
    
    async def start(self):
        """Start the agent manager and all configured agents."""
        try:
            self.logger.info("🚀 Starting AgentManager...")
            
            # Initialize Redis communication
            await self._initialize_redis()
            
            # Start monitoring
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            
            # Start configured agents
            await self._start_configured_agents()
            
            self.is_running = True
            self.stats["uptime_start"] = datetime.now()
            
            self.logger.info("✅ AgentManager started successfully")
            self.logger.info(f"📊 Managing {len(self.agents)} agents")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to start AgentManager: {e}")
            raise
    
    async def stop(self):
        """Stop the agent manager and all agents."""
        try:
            self.logger.info("🛑 Stopping AgentManager...")
            
            self.is_running = False
            
            # Stop monitoring
            if self.monitoring_task:
                self.monitoring_task.cancel()
                try:
                    await self.monitoring_task
                except asyncio.CancelledError:
                    pass
            
            # Stop all agents
            await self._stop_all_agents()
            
            # Close Redis connection
            if self.redis_comm:
                await self.redis_comm.disconnect()
            
            self.logger.info("✅ AgentManager stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Error stopping AgentManager: {e}")
            raise
    
    async def _initialize_redis(self):
        """Initialize Redis communication."""
        try:
            self.redis_comm = RedisCommunication(self.redis_url)
            await self.redis_comm.connect()
            self.logger.info("✅ Redis communication initialized")
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Redis: {e}")
            raise
    
    async def _start_configured_agents(self):
        """Start all configured agents."""
        for agent_type, config in self.agent_configs.items():
            if config.get("auto_start", True):
                try:
                    await self.start_agent(agent_type, config)
                except Exception as e:
                    self.logger.error(f"❌ Failed to start {agent_type} agent: {e}")
                    self.stats["failed_agents"] += 1
    
    async def start_agent(self, agent_type: str, config: Dict[str, Any] = None) -> str:
        """Start a specific agent."""
        try:
            if agent_type in self.agents:
                self.logger.warning(f"Agent {agent_type} is already running")
                return self.agents[agent_type].agent_id
            
            # Get configuration
            agent_config = config or self.agent_configs.get(agent_type, {})
            
            # Create agent instance
            agent = AgentFactory.create_agent(agent_type, **agent_config)
            
            # Start the agent
            await agent.start(self.redis_comm, self)
            
            # Register agent
            self.agents[agent.agent_id] = agent
            self.agent_info[agent.agent_id] = agent.get_info()
            self.agent_last_heartbeat[agent.agent_id] = datetime.now()
            self.agent_restart_counts[agent.agent_id] = 0
            
            # Update statistics
            self.stats["total_agents"] += 1
            self.stats["active_agents"] += 1
            
            self.logger.info(f"✅ Started {agent_type} agent: {agent.agent_id}")
            
            return agent.agent_id
            
        except Exception as e:
            self.logger.error(f"❌ Failed to start {agent_type} agent: {e}")
            self.stats["failed_agents"] += 1
            raise
    
    async def stop_agent(self, agent_id: str):
        """Stop a specific agent."""
        try:
            if agent_id not in self.agents:
                self.logger.warning(f"Agent {agent_id} not found")
                return
            
            agent = self.agents[agent_id]
            
            # Stop the agent
            await agent.stop()
            
            # Remove from registry
            del self.agents[agent_id]
            del self.agent_info[agent_id]
            del self.agent_last_heartbeat[agent_id]
            
            # Update statistics
            self.stats["active_agents"] -= 1
            
            self.logger.info(f"✅ Stopped agent: {agent_id}")
            
        except Exception as e:
            self.logger.error(f"❌ Error stopping agent {agent_id}: {e}")
            raise
    
    async def restart_agent(self, agent_id: str):
        """Restart a specific agent."""
        try:
            if agent_id not in self.agents:
                self.logger.warning(f"Agent {agent_id} not found")
                return
            
            agent = self.agents[agent_id]
            agent_type = agent.name.lower().replace("agent", "")
            
            self.logger.info(f"🔄 Restarting agent: {agent_id}")
            
            # Stop the agent
            await self.stop_agent(agent_id)
            
            # Wait before restarting
            await asyncio.sleep(self.restart_delay)
            
            # Start the agent again
            config = self.agent_configs.get(agent_type, {})
            await self.start_agent(agent_type, config)
            
            # Update restart count
            self.agent_restart_counts[agent_id] = self.agent_restart_counts.get(agent_id, 0) + 1
            self.stats["total_restarts"] += 1
            
            self.logger.info(f"✅ Restarted agent: {agent_id}")
            
        except Exception as e:
            self.logger.error(f"❌ Error restarting agent {agent_id}: {e}")
            raise
    
    async def _monitoring_loop(self):
        """Main monitoring loop for agent health checks."""
        while self.is_running:
            try:
                await self._check_agent_health()
                await self._update_statistics()
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _check_agent_health(self):
        """Check health of all agents and restart if needed."""
        current_time = datetime.now()
        unhealthy_agents = []
        
        for agent_id, last_heartbeat in self.agent_last_heartbeat.items():
            time_since_heartbeat = (current_time - last_heartbeat).total_seconds()
            
            if time_since_heartbeat > self.heartbeat_timeout:
                unhealthy_agents.append(agent_id)
                self.logger.warning(f"⚠️ Agent {agent_id} hasn't sent heartbeat in {time_since_heartbeat:.1f}s")
        
        # Restart unhealthy agents
        for agent_id in unhealthy_agents:
            restart_count = self.agent_restart_counts.get(agent_id, 0)
            
            if restart_count < self.max_restart_attempts:
                self.logger.info(f"🔄 Attempting to restart unhealthy agent: {agent_id}")
                try:
                    await self.restart_agent(agent_id)
                except Exception as e:
                    self.logger.error(f"❌ Failed to restart agent {agent_id}: {e}")
            else:
                self.logger.error(f"❌ Agent {agent_id} exceeded max restart attempts ({self.max_restart_attempts})")
                # Remove from active agents
                if agent_id in self.agents:
                    await self.stop_agent(agent_id)
    
    async def _update_statistics(self):
        """Update agent manager statistics."""
        try:
            # Count active agents
            self.stats["active_agents"] = len(self.agents)
            
            # Count failed agents
            self.stats["failed_agents"] = len([
                agent_id for agent_id, count in self.agent_restart_counts.items()
                if count >= self.max_restart_attempts
            ])
            
            # Aggregate task and error counts
            total_tasks = 0
            total_errors = 0
            
            for agent in self.agents.values():
                info = agent.get_info()
                total_tasks += info.tasks_processed
                total_errors += info.errors_count
            
            self.stats["tasks_processed"] = total_tasks
            self.stats["errors_count"] = total_errors
            
        except Exception as e:
            self.logger.error(f"Error updating statistics: {e}")
    
    async def receive_heartbeat(self, agent_info: AgentInfo):
        """Receive heartbeat from an agent."""
        try:
            agent_id = agent_info.agent_id
            
            # Update heartbeat timestamp
            self.agent_last_heartbeat[agent_id] = datetime.now()
            
            # Update agent info
            self.agent_info[agent_id] = agent_info
            
            # Reset restart count on successful heartbeat
            if agent_id in self.agent_restart_counts:
                self.agent_restart_counts[agent_id] = 0
            
        except Exception as e:
            self.logger.error(f"Error processing heartbeat from {agent_info.agent_id}: {e}")
    
    async def send_task_to_agent(
        self,
        capability: AgentCapability,
        task_type: str,
        parameters: Dict[str, Any] = None,
        priority: int = 1,
        timeout: int = 30
    ) -> str:
        """Send a task to agents with the specified capability."""
        try:
            if not self.redis_comm:
                raise RuntimeError("Redis communication not initialized")
            
            task_id = await self.redis_comm.send_task(
                capability=capability,
                task_type=task_type,
                parameters=parameters or {},
                priority=priority,
                timeout=timeout,
                requester_id="agent_manager"
            )
            
            self.logger.info(f"📤 Sent task {task_id} to {capability.value} agents")
            return task_id
            
        except Exception as e:
            self.logger.error(f"Error sending task: {e}")
            raise
    
    async def get_agent_status(self, agent_id: str = None) -> Dict[str, Any]:
        """Get status of specific agent or all agents."""
        try:
            if agent_id:
                if agent_id not in self.agents:
                    return {"error": f"Agent {agent_id} not found"}
                
                agent = self.agents[agent_id]
                return {
                    "agent": agent.get_health_status(),
                    "info": asdict(agent.get_info()),
                    "restart_count": self.agent_restart_counts.get(agent_id, 0),
                    "last_heartbeat": self.agent_last_heartbeat.get(agent_id).isoformat() if agent_id in self.agent_last_heartbeat else None
                }
            else:
                # Return status of all agents
                agents_status = {}
                for aid in self.agents:
                    agents_status[aid] = await self.get_agent_status(aid)
                
                return {
                    "agents": agents_status,
                    "manager_stats": self.stats,
                    "total_agents": len(self.agents),
                    "active_agents": self.stats["active_agents"],
                    "failed_agents": self.stats["failed_agents"]
                }
                
        except Exception as e:
            self.logger.error(f"Error getting agent status: {e}")
            return {"error": str(e)}
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health."""
        try:
            current_time = datetime.now()
            healthy_agents = 0
            unhealthy_agents = 0
            
            for agent_id, last_heartbeat in self.agent_last_heartbeat.items():
                time_since_heartbeat = (current_time - last_heartbeat).total_seconds()
                if time_since_heartbeat < self.heartbeat_timeout:
                    healthy_agents += 1
                else:
                    unhealthy_agents += 1
            
            # Calculate uptime
            uptime_seconds = 0
            if self.stats["uptime_start"]:
                uptime_seconds = (current_time - self.stats["uptime_start"]).total_seconds()
            
            health_score = (healthy_agents / max(1, len(self.agents))) * 100 if self.agents else 0
            
            return {
                "overall_health": "healthy" if health_score >= 80 else "warning" if health_score >= 60 else "critical",
                "health_score": round(health_score, 1),
                "uptime_seconds": int(uptime_seconds),
                "healthy_agents": healthy_agents,
                "unhealthy_agents": unhealthy_agents,
                "total_agents": len(self.agents),
                "manager_stats": self.stats,
                "redis_connected": self.redis_comm is not None,
                "timestamp": current_time.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting system health: {e}")
            return {"error": str(e)}
    
    async def broadcast_command(self, command: str, parameters: Dict[str, Any] = None):
        """Broadcast a command to all agents."""
        try:
            if not self.redis_comm:
                raise RuntimeError("Redis communication not initialized")
            
            await self.redis_comm.broadcast_management_command(command, parameters)
            self.logger.info(f"📢 Broadcasted command: {command}")
            
        except Exception as e:
            self.logger.error(f"Error broadcasting command: {e}")
            raise
    
    async def get_agent_capabilities(self) -> Dict[str, List[str]]:
        """Get capabilities of all agents."""
        try:
            capabilities = {}
            
            for agent_id, agent in self.agents.items():
                agent_caps = [cap.value for cap in agent.capabilities]
                capabilities[agent_id] = {
                    "name": agent.name,
                    "capabilities": agent_caps,
                    "status": agent.status.value
                }
            
            return capabilities
            
        except Exception as e:
            self.logger.error(f"Error getting agent capabilities: {e}")
            return {"error": str(e)}
    
    async def scale_agent(self, agent_type: str, count: int):
        """Scale an agent type to the specified count."""
        try:
            current_count = len([a for a in self.agents.values() if a.name.lower().replace("agent", "") == agent_type])
            
            if count > current_count:
                # Scale up
                for _ in range(count - current_count):
                    await self.start_agent(agent_type)
            elif count < current_count:
                # Scale down
                agents_to_stop = [
                    agent_id for agent_id, agent in self.agents.items()
                    if agent.name.lower().replace("agent", "") == agent_type
                ][:current_count - count]
                
                for agent_id in agents_to_stop:
                    await self.stop_agent(agent_id)
            
            self.logger.info(f"📈 Scaled {agent_type} agents to {count} instances")
            
        except Exception as e:
            self.logger.error(f"Error scaling {agent_type} agents: {e}")
            raise
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get current statistics."""
        return {
            "manager_stats": self.stats.copy(),
            "agent_count": len(self.agents),
            "agent_types": list(set(agent.name.lower().replace("agent", "") for agent in self.agents.values())),
            "restart_counts": self.agent_restart_counts.copy(),
            "uptime_seconds": int((datetime.now() - self.stats["uptime_start"]).total_seconds()) if self.stats["uptime_start"] else 0
        }


if __name__ == "__main__":
    # Test the AgentManager
    async def test_agent_manager():
        manager = AgentManager()
        
        try:
            await manager.start()
            print(f"✅ AgentManager started")
            print(f"📊 Statistics: {manager.get_statistics()}")
            
            # Get system health
            health = await manager.get_system_health()
            print(f"🏥 System health: {health}")
            
            # Get agent status
            status = await manager.get_agent_status()
            print(f"📋 Agent status: {len(status.get('agents', {}))} agents")
            
            # Simulate running for a bit
            await asyncio.sleep(10)
            
        finally:
            await manager.stop()
            print("✅ AgentManager stopped")
    
    asyncio.run(test_agent_manager())
