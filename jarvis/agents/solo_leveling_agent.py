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
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

# Load JSON database paths from environment
JSON_DATA_PATH = os.path.normpath(os.getenv("JSON_DATA_PATH", "E:/Richie/github/system/json_data"))

try:
    from .agent_base import AgentBase, AgentCapability, TaskRequest, TaskResponse
except ImportError:
    # Handle direct execution
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from jarvis.agents.agent_base import AgentBase, AgentCapability, TaskRequest, TaskResponse

# Define JSON database file paths
QUESTS_JSON_PATH = os.path.join(JSON_DATA_PATH, "quests.json")
GOALS_JSON_PATH = os.path.join(JSON_DATA_PATH, "goals.json")
ACHIEVEMENTS_JSON_PATH = os.path.join(JSON_DATA_PATH, "achievement.json")
USER_JSON_PATH = os.path.join(JSON_DATA_PATH, "user.json")
USERPROFILE_JSON_PATH = os.path.join(JSON_DATA_PATH, "userprofile.json")

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
        
        # Personality
        self.personality = "supportive, gamified, motivational"

        # Persistent XP/streak storage (SQLite)
        try:
            from .memory_utils import SoloLevelingDB
            db_dir = Path("data").absolute()
            db_dir.mkdir(parents=True, exist_ok=True)
            self.level_db = SoloLevelingDB(str(db_dir / "solo_leveling.sqlite"))
        except Exception as e:
            self.level_db = None
            self.logger.warning(f"XP DB unavailable, continuing without persistence: {e}")

        self.logger = logging.getLogger("agent.solo_leveling")
    
    async def start(self, redis_comm=None, agent_manager=None):
        """Start the agent with JSON database verification."""
        # Log startup information
        print(f"[SoloLevelingAgent] CWD: {os.getcwd()}")
        print(f"[SoloLevelingAgent] JSON_DATA_PATH: {JSON_DATA_PATH}")
        print(f"[SoloLevelingAgent] Quests JSON -> {os.path.abspath(QUESTS_JSON_PATH)} (Exists: {os.path.exists(QUESTS_JSON_PATH)})")
        print(f"[SoloLevelingAgent] Goals JSON -> {os.path.abspath(GOALS_JSON_PATH)} (Exists: {os.path.exists(GOALS_JSON_PATH)})")
        print(f"[SoloLevelingAgent] Achievements JSON -> {os.path.abspath(ACHIEVEMENTS_JSON_PATH)} (Exists: {os.path.exists(ACHIEVEMENTS_JSON_PATH)})")
        print(f"[SoloLevelingAgent] User JSON -> {os.path.abspath(USER_JSON_PATH)} (Exists: {os.path.exists(USER_JSON_PATH)})")
        print(f"[SoloLevelingAgent] UserProfile JSON -> {os.path.abspath(USERPROFILE_JSON_PATH)} (Exists: {os.path.exists(USERPROFILE_JSON_PATH)})")
        
        # Verify JSON database files exist
        await self._verify_json_files()
        
        # Load data from JSON files
        await self._load_json_data()
        
        # Call parent start method
        await super().start(redis_comm, agent_manager)
    
    async def _verify_json_files(self):
        """Verify JSON database files exist."""
        required_files = [
            QUESTS_JSON_PATH,
            GOALS_JSON_PATH, 
            ACHIEVEMENTS_JSON_PATH,
            USER_JSON_PATH,
            USERPROFILE_JSON_PATH
        ]
        
        missing_files = []
        for file_path in required_files:
            if not os.path.exists(file_path):
                missing_files.append(file_path)
        
        if missing_files:
            raise FileNotFoundError(f"Missing JSON database files: {missing_files}")
        
        self.logger.info("✅ All JSON database files found")
    
    async def _load_json_data(self):
        """Load data from JSON database files."""
        try:
            # Load quests
            with open(QUESTS_JSON_PATH, 'r', encoding='utf-8') as f:
                self.quests = json.load(f)
            
            # Load goals
            with open(GOALS_JSON_PATH, 'r', encoding='utf-8') as f:
                self.goals = json.load(f)
            
            # Load achievements
            with open(ACHIEVEMENTS_JSON_PATH, 'r', encoding='utf-8') as f:
                self.achievements = json.load(f)
            
            # Load user profile
            with open(USERPROFILE_JSON_PATH, 'r', encoding='utf-8') as f:
                user_profiles = json.load(f)
                if user_profiles:
                    profile = user_profiles[0]  # Get first user profile
                    self.user_level = profile.get("level", 1)
                    self.user_experience = profile.get("xp", 0)
            
            self.logger.info(f"✅ Loaded {len(self.quests)} quests, {len(self.goals)} goals, {len(self.achievements)} achievements")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load JSON data: {e}")
            raise
    
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
            # Load persisted user state if available
            if hasattr(self, 'level_db') and self.level_db:
                state = self.level_db.get_user_state()
                self.user_level = max(1, int(state.get("level", 1)))
                self.user_experience = int(state.get("xp", 0))
                self.user_streak = int(state.get("streak", 0) or 0)
                self.last_active_date = state.get("last_active_date")

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

            # Persist user XP to SQLite
            if hasattr(self, 'level_db') and self.level_db:
                try:
                    today = datetime.now().date().isoformat()
                    streak = getattr(self, "user_streak", 0)
                    self.level_db.save_user_state(self.user_level, self.user_experience, streak, today)
                except Exception as e:
                    self.logger.warning(f"Failed to persist user state: {e}")
            
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
                if quest.get("completed", 0) == 0:  # Quest is not completed
                    # Simulate progress based on time and effort
                    # In a real system, this would be based on actual user activity
                    current_progress = quest.get("progress", 0)
                    if isinstance(current_progress, (int, float)):
                        quest["progress"] = min(100, current_progress + 1)  # Progress as percentage
                        
                        if quest["progress"] >= 100:
                            await self._complete_quest(quest)
            
        except Exception as e:
            self.logger.error(f"Error updating quest progress: {e}")
    
    async def _complete_quest(self, quest: Dict[str, Any]):
        """Complete a quest and award experience."""
        try:
            quest["completed"] = 1
            quest["progress"] = 100
            
            # Award experience
            experience_gained = 100  # Default XP reward
            self.user_experience += experience_gained
            self.total_quests_completed += 1
            self.daily_quests_completed += 1
            
            self.logger.info(f"Quest completed: {quest.get('name', 'Unknown')} (+{experience_gained} XP)")
            
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
                progress_increase = min(10, experience_gained / 10)  # Convert to percentage
                current_progress = goal.get("progress", 0)
                goal["progress"] = min(100, current_progress + progress_increase)
                
                if goal["progress"] >= 100:
                    goal["completed"] = 1
                    goal["completed_at"] = datetime.now().isoformat()
                    self.logger.info(f"Goal completed: {goal.get('title', 'Unknown')}")
            
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
                if achievement.get("unlocked", 0) == 0:  # Achievement is locked
                    condition_type = achievement.get("condition_type", "")
                    condition_value = achievement.get("condition_value", 0)
                    
                    if condition_type == "tasks_completed":
                        if self.total_quests_completed >= condition_value:
                            achievement["unlocked"] = 1
                            achievement["unlocked_at"] = datetime.now().isoformat()
                            self.logger.info(f"Achievement unlocked: {achievement.get('name', 'Unknown')}")
                    
                    elif condition_type == "level_reached":
                        if self.user_level >= condition_value:
                            achievement["unlocked"] = 1
                            achievement["unlocked_at"] = datetime.now().isoformat()
                            self.logger.info(f"Achievement unlocked: {achievement.get('name', 'Unknown')}")
                    
                    elif condition_type == "xp_earned":
                        if self.user_experience >= condition_value:
                            achievement["unlocked"] = 1
                            achievement["unlocked_at"] = datetime.now().isoformat()
                            self.logger.info(f"Achievement unlocked: {achievement.get('name', 'Unknown')}")
            
        except Exception as e:
            self.logger.error(f"Error checking achievements: {e}")
    
    async def _check_level_achievements(self):
        """Check for level-based achievements."""
        try:
            for achievement in self.achievements:
                if (achievement.get("condition_type") == "level_reached" and 
                    achievement.get("unlocked", 0) == 0):
                    if self.user_level >= achievement.get("condition_value", 0):
                        achievement["unlocked"] = 1
                        achievement["unlocked_at"] = datetime.now().isoformat()
                        self.logger.info(f"Achievement unlocked: {achievement.get('name', 'Unknown')}")
            
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
            
            # Maintain simple streak: if any activity today, increment streak
            today = datetime.now().date().isoformat()
            last_date = getattr(self, "last_active_date", None)
            if last_date != today and (self.daily_quests_completed > 0 or self.total_quests_completed > 0):
                try:
                    from datetime import date
                    prev_date = None if not last_date else datetime.fromisoformat(last_date).date()
                    if prev_date is not None and (datetime.now().date() - prev_date).days == 1:
                        self.user_streak = getattr(self, "user_streak", 0) + 1
                    else:
                        self.user_streak = 1
                    self.last_active_date = today
                except Exception:
                    self.user_streak = getattr(self, "user_streak", 0) or 1
            
        except Exception as e:
            self.logger.error(f"Error updating daily progress: {e}")
    
    async def _save_user_progress(self):
        """Save user progress to JSON files."""
        try:
            self.logger.info("💾 Saving user progress to JSON files...")
            
            # Save quests
            with open(QUESTS_JSON_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.quests, f, indent=2, ensure_ascii=False)
            
            # Save goals
            with open(GOALS_JSON_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.goals, f, indent=2, ensure_ascii=False)
            
            # Save achievements
            with open(ACHIEVEMENTS_JSON_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.achievements, f, indent=2, ensure_ascii=False)
            
            # Update and save user profile
            with open(USERPROFILE_JSON_PATH, 'r', encoding='utf-8') as f:
                user_profiles = json.load(f)
            
            if user_profiles:
                user_profiles[0]["level"] = self.user_level
                user_profiles[0]["xp"] = self.user_experience
                user_profiles[0]["updated_at"] = datetime.now().isoformat()
                
                with open(USERPROFILE_JSON_PATH, 'w', encoding='utf-8') as f:
                    json.dump(user_profiles, f, indent=2, ensure_ascii=False)
            
            self.logger.info("✅ User progress saved to JSON files")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to save user progress: {e}")
    
    async def _save_quests(self):
        """Save quests to JSON file."""
        try:
            with open(QUESTS_JSON_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.quests, f, indent=2, ensure_ascii=False)
            self.logger.info("✅ Quests saved to JSON file")
        except Exception as e:
            self.logger.error(f"❌ Failed to save quests: {e}")
    
    async def _save_goals(self):
        """Save goals to JSON file."""
        try:
            with open(GOALS_JSON_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.goals, f, indent=2, ensure_ascii=False)
            self.logger.info("✅ Goals saved to JSON file")
        except Exception as e:
            self.logger.error(f"❌ Failed to save goals: {e}")
    
    async def _save_achievements(self):
        """Save achievements to JSON file."""
        try:
            with open(ACHIEVEMENTS_JSON_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.achievements, f, indent=2, ensure_ascii=False)
            self.logger.info("✅ Achievements saved to JSON file")
        except Exception as e:
            self.logger.error(f"❌ Failed to save achievements: {e}")
    
    def get_quests(self) -> Dict[str, Any]:
        """Load quests from JSON database."""
        try:
            self.logger.info(f"Loading quests from JSON: {QUESTS_JSON_PATH}")
            
            if not self.quests:
                self.logger.info("No quests loaded in memory")
                return {
                    "message": "No quests found",
                    "quests": []
                }
            
            self.logger.info(f"Loaded {len(self.quests)} quests from JSON")
            
            return {
                "message": f"Loaded {len(self.quests)} quests from JSON database",
                "quests": self.quests
            }
                
        except Exception as e:
            error_msg = f"Error loading quests from JSON: {str(e)}"
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
                "active_goals": len([g for g in self.goals if g.get("completed", 0) == 0]),
                "active_quests": len([q for q in self.quests if q.get("completed", 0) == 0]),
                "achievements_unlocked": len([a for a in self.achievements if a.get("unlocked", 0) == 1]),
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
                if status_filter == "completed":
                    filtered_quests = [q for q in quest_data["quests"] if q.get("completed", 0) == 1]
                elif status_filter == "active" or status_filter == "pending":
                    filtered_quests = [q for q in quest_data["quests"] if q.get("completed", 0) == 0]
                else:
                    filtered_quests = quest_data["quests"]
                
                # Calculate status counts based on completed field
                status_counts = {
                    "active": len([q for q in quest_data["quests"] if q.get("completed", 0) == 0]),
                    "pending": len([q for q in quest_data["quests"] if q.get("completed", 0) == 0]),
                    "completed": len([q for q in quest_data["quests"] if q.get("completed", 0) == 1])
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
            
            if status_filter == "completed":
                filtered_goals = [g for g in filtered_goals if g.get("completed", 0) == 1]
            elif status_filter == "active" or status_filter == "pending":
                filtered_goals = [g for g in filtered_goals if g.get("completed", 0) == 0]
            
            if category_filter:
                filtered_goals = [g for g in filtered_goals if g.get("category") == category_filter]
            
            result = {
                "goals": filtered_goals,
                "total_goals": len(self.goals),
                "filtered_goals": len(filtered_goals),
                "status_counts": {
                    "active": len([g for g in self.goals if g.get("completed", 0) == 0]),
                    "pending": len([g for g in self.goals if g.get("completed", 0) == 0]),
                    "completed": len([g for g in self.goals if g.get("completed", 0) == 1])
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
                        "title": goal.get("title", "Unknown"),
                        "progress": goal.get("progress", 0),
                        "status": "completed" if goal.get("completed", 0) == 1 else "active"
                    }
                    for goal in self.goals
                ],
                "quests_progress": [
                    {
                        "quest_id": quest["id"],
                        "title": quest.get("name", "Unknown"),
                        "progress": quest.get("progress", 0),
                        "status": "completed" if quest.get("completed", 0) == 1 else "active"
                    }
                    for quest in self.quests
                ],
                "achievements": [
                    {
                        "id": ach["id"],
                        "title": ach.get("name", "Unknown"),
                        "status": "unlocked" if ach.get("unlocked", 0) == 1 else "locked",
                        "progress": ach.get("progress", 0),
                        "target": ach.get("condition_value", 0)
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
            
            # Generate new quest ID based on existing quests
            max_id = max([q.get("id", 0) for q in self.quests], default=0)
            if isinstance(max_id, str) and max_id.isdigit():
                max_id = int(max_id)
            elif isinstance(max_id, str):
                max_id = 0
            
            quest = {
                "id": max_id + 1,
                "name": title,
                "description": description,
                "progress": 0,
                "completed": 0
            }
            
            self.quests.append(quest)
            
            # Save to JSON file
            await self._save_quests()
            
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
            
            # Convert quest_id to int if it's a string
            if isinstance(quest_id, str) and quest_id.isdigit():
                quest_id = int(quest_id)
            
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
            
            # Save to JSON file
            await self._save_quests()
            
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
            
            # Convert quest_id to int if it's a string
            if isinstance(quest_id, str) and quest_id.isdigit():
                quest_id = int(quest_id)
            
            quest = next((q for q in self.quests if q["id"] == quest_id), None)
            
            if not quest:
                return TaskResponse(
                    task_id=task.task_id,
                    agent_id=self.agent_id,
                    success=False,
                    error=f"Quest {quest_id} not found"
                )
            
            if quest.get("completed", 0) == 1:
                return TaskResponse(
                    task_id=task.task_id,
                    agent_id=self.agent_id,
                    success=False,
                    error=f"Quest {quest_id} is already completed"
                )
            
            # Complete the quest
            quest["completed"] = 1
            quest["progress"] = 100
            
            # Award experience
            experience_gained = 100  # Default XP reward
            self.user_experience += experience_gained
            self.total_quests_completed += 1
            self.daily_quests_completed += 1
            
            # Persist immediately if DB available
            if hasattr(self, 'level_db') and self.level_db:
                try:
                    today = datetime.now().date().isoformat()
                    streak = getattr(self, "user_streak", 0)
                    self.level_db.save_user_state(self.user_level, self.user_experience, streak, today)
                except Exception as e:
                    self.logger.warning(f"Failed to persist XP on quest complete: {e}")
            
            # Save to JSON files
            await self._save_quests()
            await self._save_user_progress()
            
            result = {
                "message": f"Quest '{quest['name']}' completed!",
                "quest": quest,
                "experience_gained": experience_gained,
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
            
            # Generate new goal ID based on existing goals
            max_id = max([g.get("id", 0) for g in self.goals], default=0)
            if isinstance(max_id, str) and max_id.isdigit():
                max_id = int(max_id)
            elif isinstance(max_id, str):
                max_id = 0
            
            goal = {
                "id": max_id + 1,
                "user_id": 1,  # Default user ID
                "title": title,
                "description": description,
                "category": category,
                "priority": task.parameters.get("priority", "medium"),
                "target_date": task.parameters.get("target_date"),
                "progress": 0.0,
                "completed": 0,
                "completed_at": None,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            self.goals.append(goal)
            
            # Save to JSON file
            await self._save_goals()
            
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
            
            # Convert goal_id to int if it's a string
            if isinstance(goal_id, str) and goal_id.isdigit():
                goal_id = int(goal_id)
            
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
            
            # Update the updated_at timestamp
            goal["updated_at"] = datetime.now().isoformat()
            
            # Save to JSON file
            await self._save_goals()
            
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
            
            # Filter achievements based on unlocked status
            if status_filter == "unlocked":
                filtered_achievements = [a for a in self.achievements if a.get("unlocked", 0) == 1]
            elif status_filter == "locked":
                filtered_achievements = [a for a in self.achievements if a.get("unlocked", 0) == 0]
            else:
                filtered_achievements = self.achievements
            
            result = {
                "achievements": filtered_achievements,
                "total_achievements": len(self.achievements),
                "unlocked_achievements": len([a for a in self.achievements if a.get("unlocked", 0) == 1]),
                "locked_achievements": len([a for a in self.achievements if a.get("unlocked", 0) == 0])
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
                        "title": goal.get("title", "Unknown"),
                        "progress": goal.get("progress", 0),
                        "status": "completed" if goal.get("completed", 0) == 1 else "active"
                    }
                    for goal in self.goals if goal.get("completed", 0) == 0
                ],
                "achievements_unlocked_today": len([
                    a for a in self.achievements 
                    if a.get("unlocked", 0) == 1 and a.get("unlocked_at", "").startswith(datetime.now().strftime("%Y-%m-%d"))
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
