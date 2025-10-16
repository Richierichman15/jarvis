#!/usr/bin/env python3
"""
SystemAgent - Specialized agent for system monitoring and management

This agent handles all system-related tasks including status monitoring,
task management, quest tracking, and system diagnostics.
"""

import asyncio
import logging
import psutil
import platform
from typing import Any, Dict, List, Optional
from datetime import datetime

from .agent_base import AgentBase, AgentCapability, TaskRequest, TaskResponse

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SystemAgent(AgentBase):
    """Specialized agent for system operations."""
    
    def __init__(self, **kwargs):
        super().__init__(
            name="SystemAgent",
            capabilities=[AgentCapability.SYSTEM],
            version="1.0.0",
            **kwargs
        )
        
        # System-specific configuration
        self.system_config = {
            "monitoring_interval": 30,
            "max_cpu_usage": 80.0,
            "max_memory_usage": 85.0,
            "max_disk_usage": 90.0,
            "alert_thresholds": {
                "cpu": 80.0,
                "memory": 85.0,
                "disk": 90.0
            }
        }
        
        # System state
        self.system_metrics = {}
        self.active_processes = {}
        self.system_alerts = []
        self.quests = []
        self.tasks = []
        
        self.logger = logging.getLogger("agent.system")
    
    def _register_task_handlers(self):
        """Register system task handlers."""
        self.register_task_handler("get_status", self._handle_get_status)
        self.register_task_handler("get_memory", self._handle_get_memory)
        self.register_task_handler("get_tasks", self._handle_get_tasks)
        self.register_task_handler("list_quests", self._handle_list_quests)
        self.register_task_handler("get_system_info", self._handle_get_system_info)
        self.register_task_handler("get_processes", self._handle_get_processes)
        self.register_task_handler("monitor_system", self._handle_monitor_system)
        self.register_task_handler("get_alerts", self._handle_get_alerts)
        self.register_task_handler("create_quest", self._handle_create_quest)
        self.register_task_handler("update_quest", self._handle_update_quest)
        self.register_task_handler("complete_quest", self._handle_complete_quest)
        self.register_task_handler("add_task", self._handle_add_task)
        self.register_task_handler("update_task", self._handle_update_task)
        self.register_task_handler("complete_task", self._handle_complete_task)
        self.register_task_handler("get_health", self._handle_get_health)
        self.register_task_handler("restart_service", self._handle_restart_service)
        self.register_task_handler("get_logs", self._handle_get_logs)
    
    async def _initialize(self):
        """Initialize system-specific resources."""
        try:
            # Initialize system monitoring
            await self._initialize_system_monitoring()
            
            # Load system configuration
            await self._load_system_config()
            
            # Initialize quests and tasks
            await self._initialize_quests_and_tasks()
            
            # Start system monitoring
            self.monitoring_task = asyncio.create_task(self._system_monitoring_loop())
            
            self.logger.info("✅ SystemAgent initialized successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize SystemAgent: {e}")
            raise
    
    async def _cleanup(self):
        """Cleanup system resources."""
        try:
            # Stop system monitoring
            if hasattr(self, 'monitoring_task'):
                self.monitoring_task.cancel()
                try:
                    await self.monitoring_task
                except asyncio.CancelledError:
                    pass
            
            # Save system state
            await self._save_system_state()
            
            self.logger.info("✅ SystemAgent cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during SystemAgent cleanup: {e}")
    
    async def _initialize_system_monitoring(self):
        """Initialize system monitoring capabilities."""
        self.logger.info("📊 Initializing system monitoring...")
        await asyncio.sleep(0.1)  # Simulate initialization time
        self.logger.info("✅ System monitoring initialized")
    
    async def _load_system_config(self):
        """Load system configuration."""
        self.logger.info("📋 Loading system configuration...")
        await asyncio.sleep(0.1)  # Simulate loading time
        self.logger.info("✅ System configuration loaded")
    
    async def _initialize_quests_and_tasks(self):
        """Initialize quests and tasks."""
        self.logger.info("🎯 Initializing quests and tasks...")
        
        # Sample quests
        self.quests = [
            {
                "id": "quest_001",
                "title": "System Health Check",
                "description": "Monitor system health for 24 hours",
                "status": "active",
                "progress": 0.75,
                "created_at": datetime.now().isoformat(),
                "deadline": None,
                "rewards": ["system_health_badge"]
            },
            {
                "id": "quest_002",
                "title": "Performance Optimization",
                "description": "Optimize system performance",
                "status": "pending",
                "progress": 0.0,
                "created_at": datetime.now().isoformat(),
                "deadline": None,
                "rewards": ["performance_badge"]
            }
        ]
        
        # Sample tasks
        self.tasks = [
            {
                "id": "task_001",
                "title": "Update system packages",
                "description": "Update all system packages to latest versions",
                "status": "pending",
                "priority": "high",
                "created_at": datetime.now().isoformat(),
                "due_date": None
            },
            {
                "id": "task_002",
                "title": "Clean up log files",
                "description": "Remove old log files to free up disk space",
                "status": "in_progress",
                "priority": "medium",
                "created_at": datetime.now().isoformat(),
                "due_date": None
            }
        ]
        
        await asyncio.sleep(0.1)  # Simulate loading time
        self.logger.info(f"✅ Initialized {len(self.quests)} quests and {len(self.tasks)} tasks")
    
    async def _system_monitoring_loop(self):
        """Main system monitoring loop."""
        while self.status.value == "running":
            try:
                # Collect system metrics
                await self._collect_system_metrics()
                
                # Check for alerts
                await self._check_system_alerts()
                
                # Update quest progress
                await self._update_quest_progress()
                
                await asyncio.sleep(self.system_config["monitoring_interval"])
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in system monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _collect_system_metrics(self):
        """Collect current system metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            # Network I/O
            network = psutil.net_io_counters()
            
            # Process count
            process_count = len(psutil.pids())
            
            self.system_metrics = {
                "timestamp": datetime.now().isoformat(),
                "cpu": {
                    "usage_percent": cpu_percent,
                    "count": psutil.cpu_count(),
                    "frequency": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "used": memory.used,
                    "usage_percent": memory.percent,
                    "free": memory.free
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "usage_percent": (disk.used / disk.total) * 100
                },
                "network": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv
                },
                "processes": {
                    "count": process_count,
                    "running": len([p for p in psutil.process_iter(['status']) if p.info['status'] == 'running'])
                },
                "system": {
                    "platform": platform.system(),
                    "platform_release": platform.release(),
                    "platform_version": platform.version(),
                    "architecture": platform.machine(),
                    "hostname": platform.node(),
                    "uptime": psutil.boot_time()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")
    
    async def _check_system_alerts(self):
        """Check for system alerts based on thresholds."""
        try:
            if not self.system_metrics:
                return
            
            alerts = []
            
            # CPU alert
            if self.system_metrics["cpu"]["usage_percent"] > self.system_config["alert_thresholds"]["cpu"]:
                alerts.append({
                    "type": "cpu_high",
                    "message": f"High CPU usage: {self.system_metrics['cpu']['usage_percent']:.1f}%",
                    "severity": "warning",
                    "timestamp": datetime.now().isoformat()
                })
            
            # Memory alert
            if self.system_metrics["memory"]["usage_percent"] > self.system_config["alert_thresholds"]["memory"]:
                alerts.append({
                    "type": "memory_high",
                    "message": f"High memory usage: {self.system_metrics['memory']['usage_percent']:.1f}%",
                    "severity": "warning",
                    "timestamp": datetime.now().isoformat()
                })
            
            # Disk alert
            if self.system_metrics["disk"]["usage_percent"] > self.system_config["alert_thresholds"]["disk"]:
                alerts.append({
                    "type": "disk_high",
                    "message": f"High disk usage: {self.system_metrics['disk']['usage_percent']:.1f}%",
                    "severity": "critical",
                    "timestamp": datetime.now().isoformat()
                })
            
            # Add new alerts
            self.system_alerts.extend(alerts)
            
            # Keep only recent alerts (last 100)
            self.system_alerts = self.system_alerts[-100:]
            
        except Exception as e:
            self.logger.error(f"Error checking system alerts: {e}")
    
    async def _update_quest_progress(self):
        """Update quest progress based on system metrics."""
        try:
            for quest in self.quests:
                if quest["status"] == "active":
                    # Update system health quest
                    if quest["id"] == "quest_001":
                        # Simulate progress based on monitoring time
                        quest["progress"] = min(1.0, quest["progress"] + 0.01)
                        
                        if quest["progress"] >= 1.0:
                            quest["status"] = "completed"
                            self.logger.info(f"🎉 Quest completed: {quest['title']}")
            
        except Exception as e:
            self.logger.error(f"Error updating quest progress: {e}")
    
    async def _save_system_state(self):
        """Save system state to persistent storage."""
        self.logger.info("💾 Saving system state...")
        await asyncio.sleep(0.1)  # Simulate saving time
        self.logger.info("✅ System state saved")
    
    async def _handle_task(self, task: TaskRequest) -> TaskResponse:
        """Handle system tasks."""
        try:
            handler = self.task_handlers.get(task.task_type)
            if handler:
                return await handler(task)
            else:
                raise ValueError(f"Unknown system task type: {task.task_type}")
                
        except Exception as e:
            self.logger.error(f"Error handling system task {task.task_type}: {e}")
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_get_status(self, task: TaskRequest) -> TaskResponse:
        """Handle get system status request."""
        try:
            # Ensure we have current metrics
            if not self.system_metrics:
                await self._collect_system_metrics()
            
            status_data = {
                "system_status": "operational",
                "timestamp": datetime.now().isoformat(),
                "metrics": self.system_metrics,
                "alerts": len(self.system_alerts),
                "active_quests": len([q for q in self.quests if q["status"] == "active"]),
                "pending_tasks": len([t for t in self.tasks if t["status"] == "pending"]),
                "uptime": self.get_info().uptime_seconds
            }
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=status_data
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_get_memory(self, task: TaskRequest) -> TaskResponse:
        """Handle get memory usage request."""
        try:
            if not self.system_metrics:
                await self._collect_system_metrics()
            
            memory_data = self.system_metrics.get("memory", {})
            
            result = {
                "memory_usage": memory_data,
                "memory_health": "good" if memory_data.get("usage_percent", 0) < 80 else "warning",
                "timestamp": datetime.now().isoformat()
            }
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=result
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_get_tasks(self, task: TaskRequest) -> TaskResponse:
        """Handle get tasks request."""
        try:
            status_filter = task.parameters.get("status")
            
            if status_filter:
                filtered_tasks = [t for t in self.tasks if t["status"] == status_filter]
            else:
                filtered_tasks = self.tasks
            
            result = {
                "tasks": filtered_tasks,
                "total_tasks": len(self.tasks),
                "filtered_tasks": len(filtered_tasks),
                "status_counts": {
                    "pending": len([t for t in self.tasks if t["status"] == "pending"]),
                    "in_progress": len([t for t in self.tasks if t["status"] == "in_progress"]),
                    "completed": len([t for t in self.tasks if t["status"] == "completed"])
                }
            }
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=result
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_list_quests(self, task: TaskRequest) -> TaskResponse:
        """Handle list quests request."""
        try:
            status_filter = task.parameters.get("status")
            
            if status_filter:
                filtered_quests = [q for q in self.quests if q["status"] == status_filter]
            else:
                filtered_quests = self.quests
            
            result = {
                "quests": filtered_quests,
                "total_quests": len(self.quests),
                "filtered_quests": len(filtered_quests),
                "status_counts": {
                    "active": len([q for q in self.quests if q["status"] == "active"]),
                    "pending": len([q for q in self.quests if q["status"] == "pending"]),
                    "completed": len([q for q in self.quests if q["status"] == "completed"])
                }
            }
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=result
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_get_system_info(self, task: TaskRequest) -> TaskResponse:
        """Handle get system info request."""
        try:
            if not self.system_metrics:
                await self._collect_system_metrics()
            
            system_info = {
                "platform": self.system_metrics.get("system", {}),
                "hardware": {
                    "cpu": self.system_metrics.get("cpu", {}),
                    "memory": self.system_metrics.get("memory", {}),
                    "disk": self.system_metrics.get("disk", {})
                },
                "network": self.system_metrics.get("network", {}),
                "processes": self.system_metrics.get("processes", {}),
                "timestamp": datetime.now().isoformat()
            }
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=system_info
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_get_processes(self, task: TaskRequest) -> TaskResponse:
        """Handle get processes request."""
        try:
            limit = task.parameters.get("limit", 10)
            
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Sort by CPU usage
            processes.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
            
            result = {
                "processes": processes[:limit],
                "total_processes": len(processes),
                "showing": min(limit, len(processes))
            }
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=result
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_monitor_system(self, task: TaskRequest) -> TaskResponse:
        """Handle system monitoring request."""
        try:
            duration = task.parameters.get("duration", 60)  # seconds
            
            # Start monitoring
            start_time = datetime.now()
            await self._collect_system_metrics()
            
            # Simulate monitoring for specified duration
            await asyncio.sleep(min(duration, 10))  # Cap at 10 seconds for testing
            
            end_time = datetime.now()
            
            result = {
                "monitoring_started": start_time.isoformat(),
                "monitoring_ended": end_time.isoformat(),
                "duration_seconds": (end_time - start_time).total_seconds(),
                "metrics_collected": self.system_metrics is not None,
                "alerts_generated": len(self.system_alerts)
            }
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=result
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_get_alerts(self, task: TaskRequest) -> TaskResponse:
        """Handle get alerts request."""
        try:
            severity_filter = task.parameters.get("severity")
            limit = task.parameters.get("limit", 50)
            
            alerts = self.system_alerts
            
            if severity_filter:
                alerts = [a for a in alerts if a.get("severity") == severity_filter]
            
            # Sort by timestamp (newest first)
            alerts.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            
            result = {
                "alerts": alerts[:limit],
                "total_alerts": len(self.system_alerts),
                "filtered_alerts": len(alerts),
                "showing": min(limit, len(alerts))
            }
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=result
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_create_quest(self, task: TaskRequest) -> TaskResponse:
        """Handle create quest request."""
        try:
            title = task.parameters.get("title")
            description = task.parameters.get("description")
            
            if not title or not description:
                return TaskResponse(
                    task_id=task.task_id,
                    agent_id=self.agent_id,
                    success=False,
                    error="Title and description are required"
                )
            
            quest = {
                "id": f"quest_{len(self.quests) + 1:03d}",
                "title": title,
                "description": description,
                "status": "pending",
                "progress": 0.0,
                "created_at": datetime.now().isoformat(),
                "deadline": task.parameters.get("deadline"),
                "rewards": task.parameters.get("rewards", [])
            }
            
            self.quests.append(quest)
            
            result = {
                "message": f"Quest '{title}' created successfully",
                "quest": quest
            }
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=result
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_update_quest(self, task: TaskRequest) -> TaskResponse:
        """Handle update quest request."""
        try:
            quest_id = task.parameters.get("quest_id")
            updates = task.parameters.get("updates", {})
            
            quest = next((q for q in self.quests if q["id"] == quest_id), None)
            
            if not quest:
                return TaskResponse(
                    task_id=task.task_id,
                    agent_id=self.agent_id,
                    success=False,
                    error=f"Quest {quest_id} not found"
                )
            
            # Update quest fields
            for key, value in updates.items():
                if key in quest:
                    quest[key] = value
            
            result = {
                "message": f"Quest {quest_id} updated successfully",
                "quest": quest
            }
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=result
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_complete_quest(self, task: TaskRequest) -> TaskResponse:
        """Handle complete quest request."""
        try:
            quest_id = task.parameters.get("quest_id")
            
            quest = next((q for q in self.quests if q["id"] == quest_id), None)
            
            if not quest:
                return TaskResponse(
                    task_id=task.task_id,
                    agent_id=self.agent_id,
                    success=False,
                    error=f"Quest {quest_id} not found"
                )
            
            quest["status"] = "completed"
            quest["progress"] = 1.0
            quest["completed_at"] = datetime.now().isoformat()
            
            result = {
                "message": f"Quest '{quest['title']}' completed!",
                "quest": quest,
                "rewards": quest.get("rewards", [])
            }
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=result
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_add_task(self, task: TaskRequest) -> TaskResponse:
        """Handle add task request."""
        try:
            title = task.parameters.get("title")
            description = task.parameters.get("description", "")
            priority = task.parameters.get("priority", "medium")
            
            if not title:
                return TaskResponse(
                    task_id=task.task_id,
                    agent_id=self.agent_id,
                    success=False,
                    error="Title is required"
                )
            
            new_task = {
                "id": f"task_{len(self.tasks) + 1:03d}",
                "title": title,
                "description": description,
                "status": "pending",
                "priority": priority,
                "created_at": datetime.now().isoformat(),
                "due_date": task.parameters.get("due_date")
            }
            
            self.tasks.append(new_task)
            
            result = {
                "message": f"Task '{title}' added successfully",
                "task": new_task
            }
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=result
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_update_task(self, task: TaskRequest) -> TaskResponse:
        """Handle update task request."""
        try:
            task_id = task.parameters.get("task_id")
            updates = task.parameters.get("updates", {})
            
            task_obj = next((t for t in self.tasks if t["id"] == task_id), None)
            
            if not task_obj:
                return TaskResponse(
                    task_id=task.task_id,
                    agent_id=self.agent_id,
                    success=False,
                    error=f"Task {task_id} not found"
                )
            
            # Update task fields
            for key, value in updates.items():
                if key in task_obj:
                    task_obj[key] = value
            
            result = {
                "message": f"Task {task_id} updated successfully",
                "task": task_obj
            }
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=result
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_complete_task(self, task: TaskRequest) -> TaskResponse:
        """Handle complete task request."""
        try:
            task_id = task.parameters.get("task_id")
            
            task_obj = next((t for t in self.tasks if t["id"] == task_id), None)
            
            if not task_obj:
                return TaskResponse(
                    task_id=task.task_id,
                    agent_id=self.agent_id,
                    success=False,
                    error=f"Task {task_id} not found"
                )
            
            task_obj["status"] = "completed"
            task_obj["completed_at"] = datetime.now().isoformat()
            
            result = {
                "message": f"Task '{task_obj['title']}' completed!",
                "task": task_obj
            }
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=result
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_get_health(self, task: TaskRequest) -> TaskResponse:
        """Handle get system health request."""
        try:
            if not self.system_metrics:
                await self._collect_system_metrics()
            
            # Calculate health score
            health_score = 100
            issues = []
            
            cpu_usage = self.system_metrics.get("cpu", {}).get("usage_percent", 0)
            memory_usage = self.system_metrics.get("memory", {}).get("usage_percent", 0)
            disk_usage = self.system_metrics.get("disk", {}).get("usage_percent", 0)
            
            if cpu_usage > 80:
                health_score -= 20
                issues.append(f"High CPU usage: {cpu_usage:.1f}%")
            
            if memory_usage > 85:
                health_score -= 25
                issues.append(f"High memory usage: {memory_usage:.1f}%")
            
            if disk_usage > 90:
                health_score -= 30
                issues.append(f"High disk usage: {disk_usage:.1f}%")
            
            health_status = "excellent" if health_score >= 90 else "good" if health_score >= 70 else "warning" if health_score >= 50 else "critical"
            
            result = {
                "health_score": health_score,
                "health_status": health_status,
                "issues": issues,
                "metrics": {
                    "cpu_usage": cpu_usage,
                    "memory_usage": memory_usage,
                    "disk_usage": disk_usage
                },
                "timestamp": datetime.now().isoformat()
            }
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=result
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_restart_service(self, task: TaskRequest) -> TaskResponse:
        """Handle restart service request."""
        try:
            service_name = task.parameters.get("service_name")
            
            if not service_name:
                return TaskResponse(
                    task_id=task.task_id,
                    agent_id=self.agent_id,
                    success=False,
                    error="Service name is required"
                )
            
            # Simulate service restart
            result = {
                "message": f"Service '{service_name}' restart initiated",
                "service_name": service_name,
                "status": "restarting",
                "timestamp": datetime.now().isoformat()
            }
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=result
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_get_logs(self, task: TaskRequest) -> TaskResponse:
        """Handle get logs request."""
        try:
            log_type = task.parameters.get("type", "system")
            limit = task.parameters.get("limit", 50)
            
            # Simulate log entries
            logs = [
                {
                    "timestamp": datetime.now().isoformat(),
                    "level": "INFO",
                    "message": "System monitoring active",
                    "source": "system_agent"
                },
                {
                    "timestamp": datetime.now().isoformat(),
                    "level": "WARNING",
                    "message": "High CPU usage detected",
                    "source": "monitor"
                }
            ]
            
            result = {
                "logs": logs[:limit],
                "log_type": log_type,
                "total_logs": len(logs),
                "showing": min(limit, len(logs))
            }
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=result
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )


if __name__ == "__main__":
    # Test the SystemAgent
    async def test_system_agent():
        agent = SystemAgent()
        
        try:
            await agent.start()
            print(f"✅ SystemAgent started: {agent.get_info()}")
            
            # Test a task
            task = TaskRequest(
                task_id="test_001",
                agent_id=agent.agent_id,
                capability=AgentCapability.SYSTEM,
                task_type="get_status",
                parameters={}
            )
            
            response = await agent._handle_task(task)
            print(f"📊 Status response: {response.result}")
            
            # Simulate running for a bit
            await asyncio.sleep(5)
            
        finally:
            await agent.stop()
            print("✅ SystemAgent stopped")
    
    asyncio.run(test_system_agent())
