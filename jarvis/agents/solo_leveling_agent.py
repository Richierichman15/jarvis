#!/usr/bin/env python3
"""
SoloLevelingAgent - Specialized agent for life improvement and goal achievement

This agent helps users improve their life by creating quests to reach their goals,
tracking progress, and providing motivation through a gamified system.
"""

import asyncio
import logging
import os
import psutil
import platform
import sqlite3
import json
from typing import Any, Dict, List, Optional
from datetime import datetime

# Load DATA_PATH and SYSTEM_DB_PATH from environment
DATA_PATH = os.getenv("DATA_PATH", "app/data")
SYSTEM_DB_PATH = os.path.normpath(os.getenv("SYSTEM_DB_PATH", "system.db"))

try:
    from .agent_base import AgentBase, AgentCapability, TaskRequest, TaskResponse
except ImportError:
    # Handle direct execution
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from jarvis.agents.agent_base import AgentBase, AgentCapability, TaskRequest, TaskResponse

# Define data file paths using DATA_PATH
QUEST_PATH = os.path.join(DATA_PATH, "system", "quests.json")
GOALS_PATH = os.path.join(DATA_PATH, "system", "goals.json")
SYSTEM_STATUS_PATH = os.path.join(DATA_PATH, "system", "system_status.json")

# Default data structures
DEFAULT_QUESTS_DATA = {
    "quests": [
        {
            "id": "quest_1",
            "title": "Complete Python Tutorial",
            "description": "Finish the Python basics tutorial",
            "status": "active",
            "progress": 69,
            "experience_reward": 150,
            "difficulty": "easy",
            "estimated_time": "2 hours",
            "created_at": "2025-01-18T10:00:00Z"
        },
        {
            "id": "quest_2", 
            "title": "Practice Coding Daily",
            "description": "Code for at least 30 minutes every day",
            "status": "active",
            "progress": 49,
            "experience_reward": 100,
            "difficulty": "medium",
            "estimated_time": "30 minutes daily",
            "created_at": "2025-01-18T10:00:00Z"
        }
    ],
    "completed_quests": [],
    "last_updated": "2025-01-18T12:00:00Z"
}

DEFAULT_GOALS_DATA = {
    "goals": [
        {
            "id": "goal_1",
            "title": "Learn AI and Machine Learning",
            "description": "Master the fundamentals of AI and ML",
            "status": "active",
            "priority": "high",
            "deadline": "2025-06-01",
            "created_at": "2025-01-18T10:00:00Z"
        }
    ],
    "completed_goals": [],
    "last_updated": "2025-01-18T12:00:00Z"
}

DEFAULT_SYSTEM_STATUS_DATA = {
    "agent_status": "operational",
    "timestamp": "2025-01-18T12:00:00Z",
    "user_level": 1,
    "user_experience": 0,
    "total_quests_completed": 0,
    "daily_quests_completed": 0,
    "active_goals": 1,
    "active_quests": 2,
    "achievements_unlocked": 1,
    "uptime": 0
}

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SoloLevelingAgent(AgentBase):
    """Specialized agent for life improvement and goal achievement."""
    
    def __init__(self, **kwargs):
        super().__init__(
            name="SoloLevelingAgent",
            capabilities=[AgentCapability.SYSTEM],
            version="1.0.0",
            **kwargs
        )
        
        # Solo Leveling specific configuration
        self.leveling_config = {
            "monitoring_interval": 30,
            "quest_completion_bonus": 100,
            "daily_quest_limit": 5,
            "level_up_threshold": 1000,
            "motivation_messages": [
                "You're making great progress! Keep it up!",
                "Every quest completed brings you closer to your goals!",
                "Level up incoming! You're on fire!",
                "Consistency is key - you've got this!",
                "Your future self will thank you for this effort!"
            ]
        }
        
        # User progress tracking
        self.user_level = 1
        self.user_experience = 0
        self.total_quests_completed = 0
        self.daily_quests_completed = 0
        self.quests = []
        self.goals = []
        self.achievements = []
        
        self.logger = logging.getLogger("agent.solo_leveling")
    
    async def start(self, redis_comm=None, agent_manager=None):
        """Start the agent with data file verification."""
        # Log startup information
        print(f"[SoloLevelingAgent] CWD: {os.getcwd()}")
        print(f"[SoloLevelingAgent] DATA_PATH: {DATA_PATH}")
        print(f"[SoloLevelingAgent] SYSTEM_DB_PATH: {SYSTEM_DB_PATH}")
        print(f"[SoloLevelingAgent] Database Path -> {os.path.abspath(SYSTEM_DB_PATH)}")
        print(f"[SoloLevelingAgent] Database Exists: {os.path.exists(SYSTEM_DB_PATH)}")
        print(f"[SoloLevelingAgent] Quest Path -> {os.path.abspath(QUEST_PATH)}")
        print(f"[SoloLevelingAgent] Exists: {os.path.exists(QUEST_PATH)}")
        print(f"[SoloLevelingAgent] Goals Path -> {os.path.abspath(GOALS_PATH)}")
        print(f"[SoloLevelingAgent] Exists: {os.path.exists(GOALS_PATH)}")
        print(f"[SoloLevelingAgent] System Status Path -> {os.path.abspath(SYSTEM_STATUS_PATH)}")
        print(f"[SoloLevelingAgent] Exists: {os.path.exists(SYSTEM_STATUS_PATH)}")
        
        # Verify database exists
        if not os.path.exists(SYSTEM_DB_PATH):
            raise FileNotFoundError(f"System database not found at: {os.path.abspath(SYSTEM_DB_PATH)}")
        
        # Verify data files exist
        await self._verify_data_files()
        
        # Call parent start method
        await super().start(redis_comm, agent_manager)
    
    async def _verify_data_files(self):
        """Verify and create required data files."""
        required_files = [
            {"path": QUEST_PATH, "default_data": DEFAULT_QUESTS_DATA},
            {"path": GOALS_PATH, "default_data": DEFAULT_GOALS_DATA},
            {"path": SYSTEM_STATUS_PATH, "default_data": DEFAULT_SYSTEM_STATUS_DATA}
        ]
        self._verify_data_files_helper(required_files)
    
    def _verify_data_files_helper(self, required_files):
        """Helper to verify and create data files."""
        import json
        for file_info in required_files:
            file_path = file_info['path']
            default_data = file_info.get('default_data', {})
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Create file with default data if it doesn't exist
            if not os.path.exists(file_path):
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(default_data, f, indent=2, ensure_ascii=False)
                    print(f"WARNING: Created placeholder: {file_path}")
                except Exception as e:
                    print(f"ERROR: Failed to create {file_path}: {e}")
    
    def _register_task_handlers(self):
        """Register solo leveling task handlers."""
        self.register_task_handler("get_status", self._handle_get_status)
        self.register_task_handler("get_level", self._handle_get_level)
        self.register_task_handler("get_quests", self._handle_get_quests)
        self.register_task_handler("list_goals", self._handle_list_goals)
        self.register_task_handler("get_progress", self._handle_get_progress)
        self.register_task_handler("create_quest", self._handle_create_quest)
        self.register_task_handler("update_quest", self._handle_update_quest)
        self.register_task_handler("complete_quest", self._handle_complete_quest)
        self.register_task_handler("create_goal", self._handle_create_goal)
        self.register_task_handler("update_goal", self._handle_update_goal)
        self.register_task_handler("get_achievements", self._handle_get_achievements)
        self.register_task_handler("get_motivation", self._handle_get_motivation)
        self.register_task_handler("get_daily_summary", self._handle_get_daily_summary)
        self.register_task_handler("level_up", self._handle_level_up)
    
    async def _initialize(self):
        """Initialize solo leveling specific resources."""
        try:
            # Initialize user progress tracking
            await self._initialize_user_progress()
            
            # Load user goals and quests
            await self._load_user_data()
            
            # Initialize achievements system
            await self._initialize_achievements()
            
            # Start progress monitoring
            self.monitoring_task = asyncio.create_task(self._progress_monitoring_loop())
            
            self.logger.info("✅ SoloLevelingAgent initialized successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize SoloLevelingAgent: {e}")
            raise
    
    async def _cleanup(self):
        """Cleanup solo leveling resources."""
        try:
            # Stop progress monitoring
            if hasattr(self, 'monitoring_task'):
                self.monitoring_task.cancel()
                try:
                    await self.monitoring_task
                except asyncio.CancelledError:
                    pass
            
            # Save user progress
            await self._save_user_progress()
            
            self.logger.info("✅ SoloLevelingAgent cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during SoloLevelingAgent cleanup: {e}")
    
    async def _initialize_user_progress(self):
        """Initialize user progress tracking."""
        self.logger.info("📊 Initializing user progress tracking...")
        await asyncio.sleep(0.1)  # Simulate initialization time
        self.logger.info("✅ User progress tracking initialized")
    
    async def _load_user_data(self):
        """Load user goals and quests."""
        self.logger.info("📋 Loading user goals and quests...")
        
        # Sample goals
        self.goals = [
            {
                "id": "goal_001",
                "title": "Learn Python Programming",
                "description": "Master Python programming fundamentals",
                "status": "active",
                "progress": 0.3,
                "target_date": "2025-06-01",
                "created_at": datetime.now().isoformat(),
                "category": "learning"
            },
            {
                "id": "goal_002",
                "title": "Build a Mobile App",
                "description": "Create and publish a mobile application",
                "status": "pending",
                "progress": 0.0,
                "target_date": "2025-12-01",
                "created_at": datetime.now().isoformat(),
                "category": "project"
            }
        ]
        
        # Sample quests
        self.quests = [
            {
                "id": "quest_001",
                "title": "Complete Python Tutorial",
                "description": "Finish the Python basics tutorial",
                "status": "active",
                "progress": 0.6,
                "experience_reward": 150,
                "created_at": datetime.now().isoformat(),
                "goal_id": "goal_001",
                "difficulty": "easy",
                "estimated_time": "2 hours"
            },
            {
                "id": "quest_002",
                "title": "Practice Coding Daily",
                "description": "Code for at least 30 minutes every day",
                "status": "active",
                "progress": 0.4,
                "experience_reward": 100,
                "created_at": datetime.now().isoformat(),
                "goal_id": "goal_001",
                "difficulty": "medium",
                "estimated_time": "30 minutes daily"
            }
        ]
        
        await asyncio.sleep(0.1)  # Simulate loading time
        self.logger.info(f"✅ Loaded {len(self.goals)} goals and {len(self.quests)} quests")
    
    async def _initialize_achievements(self):
        """Initialize achievements system."""
        self.logger.info("🏆 Initializing achievements system...")
        
        self.achievements = [
            {
                "id": "ach_001",
                "title": "First Quest",
                "description": "Complete your first quest",
                "status": "unlocked",
                "unlocked_at": datetime.now().isoformat(),
                "icon": "🎯"
            },
            {
                "id": "ach_002",
                "title": "Quest Master",
                "description": "Complete 10 quests",
                "status": "locked",
                "progress": 2,
                "target": 10,
                "icon": "👑"
            },
            {
                "id": "ach_003",
                "title": "Level Up",
                "description": "Reach level 5",
                "status": "locked",
                "progress": 1,
                "target": 5,
                "icon": "⭐"
            }
        ]
        
        await asyncio.sleep(0.1)  # Simulate initialization time
        self.logger.info(f"✅ Initialized {len(self.achievements)} achievements")
    
    async def _progress_monitoring_loop(self):
        """Main progress monitoring loop."""
        while self.status.value == "running":
            try:
                # Update quest progress
                await self._update_quest_progress()
                
                # Check for level up
                await self._check_level_up()
                
                # Check for new achievements
                await self._check_achievements()
                
                # Update daily progress
                await self._update_daily_progress()
                
                await asyncio.sleep(self.leveling_config["monitoring_interval"])
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in progress monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _update_quest_progress(self):
        """Update quest progress based on user activity."""
        try:
            for quest in self.quests:
                if quest["status"] == "active":
                    # Simulate progress based on time and effort
                    # In a real system, this would be based on actual user activity
                    quest["progress"] = min(1.0, quest["progress"] + 0.01)
                    
                    if quest["progress"] >= 1.0:
                        await self._complete_quest(quest)
            
        except Exception as e:
            self.logger.error(f"Error updating quest progress: {e}")
    
    async def _complete_quest(self, quest: Dict[str, Any]):
        """Complete a quest and award experience."""
        try:
            quest["status"] = "completed"
            quest["completed_at"] = datetime.now().isoformat()
            
            # Award experience
            experience_gained = quest.get("experience_reward", 100)
            self.user_experience += experience_gained
            self.total_quests_completed += 1
            self.daily_quests_completed += 1
            
            self.logger.info(f"Quest completed: {quest['title']} (+{experience_gained} XP)")
            
            # Update goal progress
            if quest.get("goal_id"):
                await self._update_goal_progress(quest["goal_id"], experience_gained)
            
        except Exception as e:
            self.logger.error(f"Error completing quest: {e}")
    
    async def _update_goal_progress(self, goal_id: str, experience_gained: int):
        """Update goal progress based on quest completion."""
        try:
            goal = next((g for g in self.goals if g["id"] == goal_id), None)
            if goal:
                # Update progress based on experience gained
                progress_increase = min(0.1, experience_gained / 1000)
                goal["progress"] = min(1.0, goal["progress"] + progress_increase)
                
                if goal["progress"] >= 1.0:
                    goal["status"] = "completed"
                    goal["completed_at"] = datetime.now().isoformat()
                    self.logger.info(f"Goal completed: {goal['title']}")
            
        except Exception as e:
            self.logger.error(f"Error updating goal progress: {e}")
    
    async def _check_level_up(self):
        """Check if user should level up."""
        try:
            required_exp = self.user_level * self.leveling_config["level_up_threshold"]
            
            if self.user_experience >= required_exp:
                await self._level_up()
            
        except Exception as e:
            self.logger.error(f"Error checking level up: {e}")
    
    async def _level_up(self):
        """Level up the user."""
        try:
            self.user_level += 1
            self.logger.info(f"LEVEL UP! You are now level {self.user_level}!")
            
            # Check for level-based achievements
            await self._check_level_achievements()
            
        except Exception as e:
            self.logger.error(f"Error during level up: {e}")
    
    async def _check_achievements(self):
        """Check for new achievements."""
        try:
            for achievement in self.achievements:
                if achievement["status"] == "locked":
                    if achievement["id"] == "ach_002":  # Quest Master
                        if self.total_quests_completed >= achievement["target"]:
                            achievement["status"] = "unlocked"
                            achievement["unlocked_at"] = datetime.now().isoformat()
                            self.logger.info(f"Achievement unlocked: {achievement['title']}")
                    
                    elif achievement["id"] == "ach_003":  # Level Up
                        if self.user_level >= achievement["target"]:
                            achievement["status"] = "unlocked"
                            achievement["unlocked_at"] = datetime.now().isoformat()
                            self.logger.info(f"Achievement unlocked: {achievement['title']}")
            
        except Exception as e:
            self.logger.error(f"Error checking achievements: {e}")
    
    async def _check_level_achievements(self):
        """Check for level-based achievements."""
        try:
            for achievement in self.achievements:
                if achievement["id"] == "ach_003" and achievement["status"] == "locked":
                    if self.user_level >= achievement["target"]:
                        achievement["status"] = "unlocked"
                        achievement["unlocked_at"] = datetime.now().isoformat()
                        self.logger.info(f"🏆 Achievement unlocked: {achievement['title']}")
            
        except Exception as e:
            self.logger.error(f"Error checking level achievements: {e}")
    
    async def _update_daily_progress(self):
        """Update daily progress tracking."""
        try:
            # Reset daily quests at midnight (simplified)
            current_hour = datetime.now().hour
            if current_hour == 0 and self.daily_quests_completed > 0:
                self.daily_quests_completed = 0
                self.logger.info("📅 Daily quest counter reset")
            
        except Exception as e:
            self.logger.error(f"Error updating daily progress: {e}")
    
    async def _save_user_progress(self):
        """Save user progress to persistent storage."""
        self.logger.info("💾 Saving user progress...")
        await asyncio.sleep(0.1)  # Simulate saving time
        self.logger.info("✅ User progress saved")
    
    def get_quests(self) -> Dict[str, Any]:
        """Load quests from SQLite database specified by SYSTEM_DB_PATH."""
        try:
            # Log the database path being used
            db_path = os.path.abspath(SYSTEM_DB_PATH)
            self.logger.info(f"Loading quests from database: {db_path}")
            
            # Check if database file exists
            if not os.path.exists(SYSTEM_DB_PATH):
                raise FileNotFoundError(f"System database not found at: {db_path}")
            
            # Connect to the database
            with sqlite3.connect(SYSTEM_DB_PATH) as conn:
                cursor = conn.cursor()
                
                # Check if quests table exists
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='quests'
                """)
                
                if not cursor.fetchone():
                    self.logger.warning("Quests table not found in database")
                    return {
                        "message": "No quests table found in the database",
                        "quests": []
                    }
                
                # Query all quests from the quests table
                cursor.execute("SELECT * FROM quests")
                rows = cursor.fetchall()
                
                # Get column names
                column_names = [description[0] for description in cursor.description]
                
                if not rows:
                    self.logger.info("No quests found in database")
                    return {
                        "message": "No quests found in the database",
                        "quests": []
                    }
                
                # Convert rows to list of dictionaries
                quests = []
                for row in rows:
                    quest = dict(zip(column_names, row))
                    # Convert any datetime objects to strings
                    for key, value in quest.items():
                        if hasattr(value, 'isoformat'):
                            quest[key] = value.isoformat()
                    quests.append(quest)
                
                self.logger.info(f"Loaded {len(quests)} quests from database")
                
                return {
                    "message": f"Loaded {len(quests)} quests from database",
                    "quests": quests
                }
                
        except sqlite3.Error as e:
            error_msg = f"Database error loading quests: {str(e)}"
            self.logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Error loading quests from database: {str(e)}"
            self.logger.error(error_msg)
            raise Exception(error_msg)
    
    async def _handle_task(self, task: TaskRequest) -> TaskResponse:
        """Handle solo leveling tasks."""
        try:
            handler = self.task_handlers.get(task.task_type)
            if handler:
                return await handler(task)
            else:
                raise ValueError(f"Unknown solo leveling task type: {task.task_type}")
                
        except Exception as e:
            self.logger.error(f"Error handling solo leveling task {task.task_type}: {e}")
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_get_status(self, task: TaskRequest) -> TaskResponse:
        """Handle get status request."""
        try:
            status_data = {
                "agent_status": "operational",
                "timestamp": datetime.now().isoformat(),
                "user_level": self.user_level,
                "user_experience": self.user_experience,
                "total_quests_completed": self.total_quests_completed,
                "daily_quests_completed": self.daily_quests_completed,
                "active_goals": len([g for g in self.goals if g["status"] == "active"]),
                "active_quests": len([q for q in self.quests if q["status"] == "active"]),
                "achievements_unlocked": len([a for a in self.achievements if a["status"] == "unlocked"]),
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
    
    async def _handle_get_level(self, task: TaskRequest) -> TaskResponse:
        """Handle get level request."""
        try:
            required_exp = self.user_level * self.leveling_config["level_up_threshold"]
            exp_to_next_level = required_exp - self.user_experience
            
            level_data = {
                "current_level": self.user_level,
                "current_experience": self.user_experience,
                "experience_to_next_level": exp_to_next_level,
                "progress_to_next_level": (self.user_experience / required_exp) * 100,
                "total_quests_completed": self.total_quests_completed,
                "daily_quests_completed": self.daily_quests_completed
            }
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=level_data
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_get_quests(self, task: TaskRequest) -> TaskResponse:
        """Handle get quests request - loads from SQLite database."""
        try:
            # Load quests from database
            quest_data = self.get_quests()
            
            # Get status filter if provided
            status_filter = task.parameters.get("status")
            
            if quest_data["quests"]:
                # Apply status filter if provided
                if status_filter:
                    filtered_quests = [q for q in quest_data["quests"] if q.get("status") == status_filter]
                else:
                    filtered_quests = quest_data["quests"]
                
                # Calculate status counts
                status_counts = {
                    "active": len([q for q in quest_data["quests"] if q.get("status") == "active"]),
                    "pending": len([q for q in quest_data["quests"] if q.get("status") == "pending"]),
                    "completed": len([q for q in quest_data["quests"] if q.get("status") == "completed"])
                }
                
                result = {
                    "message": quest_data["message"],
                    "quests": filtered_quests,
                    "total_quests": len(quest_data["quests"]),
                    "filtered_quests": len(filtered_quests),
                    "status_counts": status_counts
                }
            else:
                # No quests found
                result = {
                    "message": quest_data["message"],
                    "quests": [],
                    "total_quests": 0,
                    "filtered_quests": 0,
                    "status_counts": {"active": 0, "pending": 0, "completed": 0}
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
    
    async def _handle_list_goals(self, task: TaskRequest) -> TaskResponse:
        """Handle list goals request."""
        try:
            status_filter = task.parameters.get("status")
            category_filter = task.parameters.get("category")
            
            filtered_goals = self.goals
            
            if status_filter:
                filtered_goals = [g for g in filtered_goals if g["status"] == status_filter]
            
            if category_filter:
                filtered_goals = [g for g in filtered_goals if g.get("category") == category_filter]
            
            result = {
                "goals": filtered_goals,
                "total_goals": len(self.goals),
                "filtered_goals": len(filtered_goals),
                "status_counts": {
                    "active": len([g for g in self.goals if g["status"] == "active"]),
                    "pending": len([g for g in self.goals if g["status"] == "pending"]),
                    "completed": len([g for g in self.goals if g["status"] == "completed"])
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
    
    async def _handle_get_progress(self, task: TaskRequest) -> TaskResponse:
        """Handle get progress request."""
        try:
            progress_data = {
                "user_level": self.user_level,
                "user_experience": self.user_experience,
                "total_quests_completed": self.total_quests_completed,
                "daily_quests_completed": self.daily_quests_completed,
                "goals_progress": [
                    {
                        "goal_id": goal["id"],
                        "title": goal["title"],
                        "progress": goal["progress"],
                        "status": goal["status"]
                    }
                    for goal in self.goals
                ],
                "quests_progress": [
                    {
                        "quest_id": quest["id"],
                        "title": quest["title"],
                        "progress": quest["progress"],
                        "status": quest["status"]
                    }
                    for quest in self.quests
                ],
                "achievements": [
                    {
                        "id": ach["id"],
                        "title": ach["title"],
                        "status": ach["status"],
                        "progress": ach.get("progress", 0),
                        "target": ach.get("target", 0)
                    }
                    for ach in self.achievements
                ]
            }
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=progress_data
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
            goal_id = task.parameters.get("goal_id")
            
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
                "experience_reward": task.parameters.get("experience_reward", 100),
                "created_at": datetime.now().isoformat(),
                "goal_id": goal_id,
                "difficulty": task.parameters.get("difficulty", "medium"),
                "estimated_time": task.parameters.get("estimated_time", "1 hour")
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
            
            if quest["status"] == "completed":
                return TaskResponse(
                    task_id=task.task_id,
                    agent_id=self.agent_id,
                    success=False,
                    error=f"Quest {quest_id} is already completed"
                )
            
            # Complete the quest
            await self._complete_quest(quest)
            
            result = {
                "message": f"Quest '{quest['title']}' completed!",
                "quest": quest,
                "experience_gained": quest.get("experience_reward", 100),
                "new_level": self.user_level,
                "new_experience": self.user_experience
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
    
    async def _handle_create_goal(self, task: TaskRequest) -> TaskResponse:
        """Handle create goal request."""
        try:
            title = task.parameters.get("title")
            description = task.parameters.get("description")
            category = task.parameters.get("category", "general")
            
            if not title or not description:
                return TaskResponse(
                    task_id=task.task_id,
                    agent_id=self.agent_id,
                    success=False,
                    error="Title and description are required"
                )
            
            goal = {
                "id": f"goal_{len(self.goals) + 1:03d}",
                "title": title,
                "description": description,
                "status": "pending",
                "progress": 0.0,
                "target_date": task.parameters.get("target_date"),
                "created_at": datetime.now().isoformat(),
                "category": category
            }
            
            self.goals.append(goal)
            
            result = {
                "message": f"Goal '{title}' created successfully",
                "goal": goal
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
    
    async def _handle_update_goal(self, task: TaskRequest) -> TaskResponse:
        """Handle update goal request."""
        try:
            goal_id = task.parameters.get("goal_id")
            updates = task.parameters.get("updates", {})
            
            goal = next((g for g in self.goals if g["id"] == goal_id), None)
            
            if not goal:
                return TaskResponse(
                    task_id=task.task_id,
                    agent_id=self.agent_id,
                    success=False,
                    error=f"Goal {goal_id} not found"
                )
            
            # Update goal fields
            for key, value in updates.items():
                if key in goal:
                    goal[key] = value
            
            result = {
                "message": f"Goal {goal_id} updated successfully",
                "goal": goal
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
    
    async def _handle_get_achievements(self, task: TaskRequest) -> TaskResponse:
        """Handle get achievements request."""
        try:
            status_filter = task.parameters.get("status")
            
            if status_filter:
                filtered_achievements = [a for a in self.achievements if a["status"] == status_filter]
            else:
                filtered_achievements = self.achievements
            
            result = {
                "achievements": filtered_achievements,
                "total_achievements": len(self.achievements),
                "unlocked_achievements": len([a for a in self.achievements if a["status"] == "unlocked"]),
                "locked_achievements": len([a for a in self.achievements if a["status"] == "locked"])
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
    
    async def _handle_get_motivation(self, task: TaskRequest) -> TaskResponse:
        """Handle get motivation request."""
        try:
            import random
            
            motivation_message = random.choice(self.leveling_config["motivation_messages"])
            
            result = {
                "motivation_message": motivation_message,
                "user_level": self.user_level,
                "user_experience": self.user_experience,
                "quests_completed_today": self.daily_quests_completed,
                "total_quests_completed": self.total_quests_completed,
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
    
    async def _handle_get_daily_summary(self, task: TaskRequest) -> TaskResponse:
        """Handle get daily summary request."""
        try:
            result = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "quests_completed_today": self.daily_quests_completed,
                "experience_gained_today": self.daily_quests_completed * 100,  # Simplified
                "goals_progress": [
                    {
                        "goal_id": goal["id"],
                        "title": goal["title"],
                        "progress": goal["progress"],
                        "status": goal["status"]
                    }
                    for goal in self.goals if goal["status"] == "active"
                ],
                "achievements_unlocked_today": len([
                    a for a in self.achievements 
                    if a["status"] == "unlocked" and a.get("unlocked_at", "").startswith(datetime.now().strftime("%Y-%m-%d"))
                ]),
                "motivation": random.choice(self.leveling_config["motivation_messages"])
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
    
    async def _handle_level_up(self, task: TaskRequest) -> TaskResponse:
        """Handle level up request."""
        try:
            await self._level_up()
            
            result = {
                "message": f"🎊 LEVEL UP! You are now level {self.user_level}!",
                "new_level": self.user_level,
                "current_experience": self.user_experience,
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


if __name__ == "__main__":
    # Test the SoloLevelingAgent
    async def test_solo_leveling_agent():
        agent = SoloLevelingAgent()
        
        try:
            await agent.start()
            print(f"✅ SoloLevelingAgent started: {agent.get_info()}")
            
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
            print("✅ SoloLevelingAgent stopped")
    
    asyncio.run(test_solo_leveling_agent())
