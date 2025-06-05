"""
Daily Quest System for Jarvis
Generates personalized daily quests based on user goals and long-term planning.
Includes notification scheduling and XP integration with skill tree.
"""

import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import schedule
import time
import threading
from enum import Enum

class QuestDifficulty(Enum):
    E = {"xp": 10, "skill_xp": 5, "multiplier": 1}
    D = {"xp": 25, "skill_xp": 10, "multiplier": 1.5}
    C = {"xp": 50, "skill_xp": 15, "multiplier": 2}
    B = {"xp": 100, "skill_xp": 25, "multiplier": 3}
    A = {"xp": 200, "skill_xp": 40, "multiplier": 4}
    S = {"xp": 500, "skill_xp": 75, "multiplier": 6}

class NotificationTime(Enum):
    MORNING = "07:00"
    EVENING = "18:00"
    NIGHT = "21:00"

class DailyQuestGenerator:
    def __init__(self, jarvis_instance):
        self.jarvis = jarvis_instance
        self.load_quest_templates()
        self.load_user_goals()
        self.load_skill_config()
        self.three_month_plan = {}
        self.current_week = 1
        self.notification_callbacks = []
        
    def load_quest_templates(self):
        """Load quest templates organized by goal categories"""
        self.quest_templates = {
            "financial": [
                {
                    "name": "Daily Expense Tracking",
                    "description": "Log all expenses for today and review spending patterns",
                    "difficulty": "D",
                    "base_xp": 25,
                    "skills": ["budget_master", "financial_awareness"],
                    "stat_rewards": {"wealth": 2, "discipline": 1},
                    "time_estimate": 15
                },
                {
                    "name": "Investment Research",
                    "description": "Research one stock or investment opportunity for 30 minutes",
                    "difficulty": "C",
                    "base_xp": 50,
                    "skills": ["financial_literacy", "critical_thinking"],
                    "stat_rewards": {"wealth": 3, "intelligence": 2},
                    "time_estimate": 30
                },
                {
                    "name": "Side Hustle Development",
                    "description": "Work on your side project or business for 1 hour",
                    "difficulty": "B",
                    "base_xp": 100,
                    "skills": ["entrepreneurship", "side_hustle"],
                    "stat_rewards": {"wealth": 5, "confidence": 3},
                    "time_estimate": 60
                }
            ],
            "programming": [
                {
                    "name": "Code Practice Session",
                    "description": "Complete coding challenges or work on a project for 30 minutes",
                    "difficulty": "C",
                    "base_xp": 50,
                    "skills": ["basic_coding", "problem_solving"],
                    "stat_rewards": {"intelligence": 3, "problem_solving": 2},
                    "time_estimate": 30
                },
                {
                    "name": "Learn New Programming Concept",
                    "description": "Study and practice a new programming concept or library",
                    "difficulty": "D",
                    "base_xp": 25,
                    "skills": ["tech_innovator", "continuous_learning"],
                    "stat_rewards": {"intelligence": 2, "tech_mastery": 1},
                    "time_estimate": 20
                },
                {
                    "name": "Build Feature",
                    "description": "Add a new feature to an existing project",
                    "difficulty": "B",
                    "base_xp": 100,
                    "skills": ["tech_innovator", "project_management"],
                    "stat_rewards": {"intelligence": 4, "creativity": 3},
                    "time_estimate": 90
                }
            ],
            "health": [
                {
                    "name": "Morning Exercise",
                    "description": "Complete a 20-minute workout or exercise session",
                    "difficulty": "D",
                    "base_xp": 25,
                    "skills": ["early_riser", "fitness_discipline"],
                    "stat_rewards": {"strength": 2, "health": 3},
                    "time_estimate": 20
                },
                {
                    "name": "Meditation Session",
                    "description": "Practice mindfulness meditation for 15 minutes",
                    "difficulty": "D",
                    "base_xp": 20,
                    "skills": ["daily_meditation", "mindfulness"],
                    "stat_rewards": {"spirit": 2, "focus": 2},
                    "time_estimate": 15
                },
                {
                    "name": "Healthy Meal Prep",
                    "description": "Prepare a nutritious meal and plan healthy eating for the day",
                    "difficulty": "C",
                    "base_xp": 40,
                    "skills": ["nutrition_master", "self_care"],
                    "stat_rewards": {"health": 3, "discipline": 2},
                    "time_estimate": 30
                }
            ],
            "personal_growth": [
                {
                    "name": "Daily Journaling",
                    "description": "Write in your journal for 10 minutes, reflecting on goals and progress",
                    "difficulty": "E",
                    "base_xp": 15,
                    "skills": ["journaling", "self_awareness"],
                    "stat_rewards": {"wisdom": 2, "self_awareness": 1},
                    "time_estimate": 10
                },
                {
                    "name": "Learning Session",
                    "description": "Read or study educational content for 30 minutes",
                    "difficulty": "D",
                    "base_xp": 30,
                    "skills": ["daily_reader", "knowledge_seeker"],
                    "stat_rewards": {"intelligence": 2, "wisdom": 1},
                    "time_estimate": 30
                },
                {
                    "name": "Skill Practice",
                    "description": "Practice a specific skill you're developing for 45 minutes",
                    "difficulty": "C",
                    "base_xp": 60,
                    "skills": ["skill_mastery", "deliberate_practice"],
                    "stat_rewards": {"focus": 3, "mastery": 2},
                    "time_estimate": 45
                }
            ],
            "communication": [
                {
                    "name": "Network Building",
                    "description": "Reach out to one professional contact or make a new connection",
                    "difficulty": "C",
                    "base_xp": 45,
                    "skills": ["networking", "communication"],
                    "stat_rewards": {"charisma": 3, "social_capital": 2},
                    "time_estimate": 15
                },
                {
                    "name": "Public Speaking Practice",
                    "description": "Practice presenting or speaking for 20 minutes",
                    "difficulty": "B",
                    "base_xp": 80,
                    "skills": ["public_speaking", "confidence"],
                    "stat_rewards": {"charisma": 4, "confidence": 3},
                    "time_estimate": 20
                }
            ]
        }
    
    def load_user_goals(self):
        """Load user goals from memory"""
        try:
            with open('jarvis_memory.json', 'r') as f:
                data = json.load(f)
                # Extract goals from the nested structure
                for task in data.get('tasks', []):
                    if isinstance(task, dict) and 'goals' in task:
                        self.user_goals = task['goals']
                        break
                else:
                    self.user_goals = []
        except Exception as e:
            print(f"Error loading user goals: {e}")
            self.user_goals = []
    
    def load_skill_config(self):
        """Load skill configuration"""
        try:
            with open('jarvis/skills_config.json', 'r') as f:
                self.skills_config = json.load(f)
        except Exception as e:
            print(f"Error loading skills config: {e}")
            self.skills_config = {}
    
    def generate_three_month_plan(self) -> Dict:
        """Generate a comprehensive 3-month plan based on user goals"""
        plan = {
            "created_at": datetime.now().isoformat(),
            "total_weeks": 12,
            "months": {}
        }
        
        # Analyze user goals and create monthly themes
        monthly_themes = self._create_monthly_themes()
        
        for month in range(1, 4):
            month_name = ["Month 1", "Month 2", "Month 3"][month-1]
            theme = monthly_themes[month-1]
            
            plan["months"][month_name] = {
                "theme": theme["name"],
                "focus_areas": theme["focus_areas"],
                "weeks": {}
            }
            
            # Generate weekly goals for each month
            for week in range(1, 5):
                week_number = (month-1) * 4 + week
                weekly_goals = self._generate_weekly_goals(theme, week, week_number)
                
                plan["months"][month_name]["weeks"][f"Week {week}"] = {
                    "week_number": week_number,
                    "goals": weekly_goals,
                    "daily_quest_focus": self._get_daily_quest_focus(theme, week)
                }
        
        self.three_month_plan = plan
        self._save_three_month_plan()
        return plan
    
    def _create_monthly_themes(self) -> List[Dict]:
        """Create monthly themes based on user goals"""
        themes = [
            {
                "name": "Foundation Building",
                "focus_areas": ["habits", "routines", "basic_skills", "health"],
                "primary_goals": ["Physical Peak Performance", "Basic Skills Development"]
            },
            {
                "name": "Skill Advancement",
                "focus_areas": ["technical_skills", "learning", "projects", "networking"],
                "primary_goals": ["Programming Language Proficiency", "Master Public Speaking"]
            },
            {
                "name": "Growth & Optimization",
                "focus_areas": ["wealth_building", "advanced_skills", "leadership", "systems"],
                "primary_goals": ["Financial Independence", "Advanced Skill Mastery"]
            }
        ]
        return themes
    
    def _generate_weekly_goals(self, theme: Dict, week: int, week_number: int) -> List[Dict]:
        """Generate specific weekly goals based on the monthly theme"""
        goals = []
        
        if theme["name"] == "Foundation Building":
            if week == 1:
                goals = [
                    {"name": "Establish morning routine", "category": "habits", "difficulty": "D"},
                    {"name": "Complete daily exercise for 7 days", "category": "health", "difficulty": "C"},
                    {"name": "Set up workspace and tools", "category": "productivity", "difficulty": "E"}
                ]
            elif week == 2:
                goals = [
                    {"name": "Track expenses daily", "category": "financial", "difficulty": "D"},
                    {"name": "Read 2 chapters of educational book", "category": "learning", "difficulty": "D"},
                    {"name": "Complete 3 coding practice sessions", "category": "programming", "difficulty": "C"}
                ]
            # Add more weeks...
            
        elif theme["name"] == "Skill Advancement":
            goals = [
                {"name": "Complete advanced tutorial", "category": "programming", "difficulty": "B"},
                {"name": "Give presentation to 5+ people", "category": "communication", "difficulty": "B"},
                {"name": "Network with 3 new professionals", "category": "networking", "difficulty": "C"}
            ]
            
        elif theme["name"] == "Growth & Optimization":
            goals = [
                {"name": "Launch side project MVP", "category": "entrepreneurship", "difficulty": "A"},
                {"name": "Optimize investment portfolio", "category": "financial", "difficulty": "B"},
                {"name": "Mentor someone in your skill area", "category": "leadership", "difficulty": "B"}
            ]
        
        return goals
    
    def _get_daily_quest_focus(self, theme: Dict, week: int) -> List[str]:
        """Get the daily quest focus areas for a specific week"""
        focus_rotation = {
            "Foundation Building": ["health", "personal_growth", "programming"],
            "Skill Advancement": ["programming", "communication", "financial"],
            "Growth & Optimization": ["financial", "programming", "personal_growth", "communication"]
        }
        return focus_rotation.get(theme["name"], ["personal_growth", "health"])
    
    def generate_daily_quests(self, date: datetime = None) -> List[Dict]:
        """Generate personalized daily quests for a specific date"""
        if date is None:
            date = datetime.now()
            
        # Get current week from 3-month plan
        current_week_info = self._get_current_week_info(date)
        
        # Generate 3-4 quests based on current focus and user stats
        daily_quests = []
        
        # Always include one foundation quest (health/personal growth)
        foundation_quest = self._select_quest_by_category(["health", "personal_growth"])
        if foundation_quest:
            daily_quests.append(self._personalize_quest(foundation_quest, "foundation"))
        
        # Add focus-area quests based on current week
        if current_week_info:
            focus_areas = current_week_info.get("daily_quest_focus", ["programming"])
            for area in focus_areas[:2]:  # Take up to 2 focus areas
                quest = self._select_quest_by_category([area])
                if quest:
                    daily_quests.append(self._personalize_quest(quest, "focus"))
        
        # Add a challenge quest based on user's current stats
        challenge_quest = self._generate_challenge_quest()
        if challenge_quest:
            daily_quests.append(challenge_quest)
        
        # Add quests to Jarvis system
        for quest in daily_quests:
            self._add_quest_to_jarvis(quest)
        
        return daily_quests
    
    def _get_current_week_info(self, date: datetime) -> Dict:
        """Get current week information from 3-month plan"""
        if not self.three_month_plan:
            return {}
            
        # Calculate which week we're in (simplified)
        plan_start = datetime.fromisoformat(self.three_month_plan["created_at"].replace('Z', '+00:00'))
        weeks_passed = (date - plan_start).days // 7 + 1
        
        # Find the appropriate month and week
        for month_name, month_data in self.three_month_plan["months"].items():
            for week_name, week_data in month_data["weeks"].items():
                if week_data["week_number"] == weeks_passed:
                    return week_data
        
        return {}
    
    def _select_quest_by_category(self, categories: List[str]) -> Dict:
        """Select a quest template from specified categories"""
        available_quests = []
        
        for category in categories:
            if category in self.quest_templates:
                available_quests.extend(self.quest_templates[category])
        
        if not available_quests:
            return None
            
        # Weight selection based on user's current stats and recent completions
        return random.choice(available_quests)
    
    def _personalize_quest(self, quest_template: Dict, quest_type: str) -> Dict:
        """Personalize a quest template based on user's current state"""
        personalized = quest_template.copy()
        
        # Adjust difficulty based on user level
        user_level = self.jarvis.stats.get("level", 1)
        if user_level > 3 and quest_type == "focus":
            # Increase difficulty for higher level users
            difficulty_order = ["E", "D", "C", "B", "A", "S"]
            current_idx = difficulty_order.index(personalized["difficulty"])
            if current_idx < len(difficulty_order) - 1:
                personalized["difficulty"] = difficulty_order[current_idx + 1]
                personalized["base_xp"] = int(personalized["base_xp"] * 1.5)
        
        # Add personalized elements
        personalized["generated_at"] = datetime.now().isoformat()
        personalized["quest_type"] = quest_type
        personalized["deadline"] = (datetime.now() + timedelta(days=1)).isoformat()
        
        return personalized
    
    def _generate_challenge_quest(self) -> Dict:
        """Generate a challenge quest based on user's weakest stats"""
        stats = self.jarvis.stats
        
        # Find lowest stats (excluding non-numeric stats)
        numeric_stats = {
            key: value for key, value in stats.items() 
            if isinstance(value, (int, float)) and key not in ['level', 'experience', 'rank_xp']
        }
        
        if not numeric_stats:
            return None
            
        lowest_stat = min(numeric_stats, key=numeric_stats.get)
        
        # Generate challenge based on lowest stat
        challenge_templates = {
            "strength": {
                "name": "Strength Challenge",
                "description": "Complete 50 push-ups or equivalent strength exercise",
                "difficulty": "C",
                "base_xp": 75,
                "skills": ["pushup_master", "strength_training"],
                "stat_rewards": {"strength": 5, "endurance": 2}
            },
            "intelligence": {
                "name": "Brain Boost Challenge",
                "description": "Solve complex problems or complete advanced learning for 1 hour",
                "difficulty": "B",
                "base_xp": 120,
                "skills": ["critical_thinker", "problem_solving"],
                "stat_rewards": {"intelligence": 5, "wisdom": 2}
            },
            "wealth": {
                "name": "Wealth Building Challenge",
                "description": "Research and plan a new income opportunity",
                "difficulty": "B",
                "base_xp": 100,
                "skills": ["side_hustle", "entrepreneurship"],
                "stat_rewards": {"wealth": 5, "confidence": 2}
            },
            "health": {
                "name": "Health Optimization Challenge",
                "description": "Complete full health routine: exercise, nutrition, and rest planning",
                "difficulty": "C",
                "base_xp": 80,
                "skills": ["wellness_master", "self_care"],
                "stat_rewards": {"health": 5, "discipline": 3}
            }
        }
        
        template = challenge_templates.get(lowest_stat)
        if template:
            challenge = template.copy()
            challenge["quest_type"] = "challenge"
            challenge["generated_at"] = datetime.now().isoformat()
            challenge["time_estimate"] = 60
            return challenge
            
        return None
    
    def _add_quest_to_jarvis(self, quest: Dict):
        """Add a generated quest to the Jarvis task system"""
        from jarvis.jarvis import Task
        
        # Calculate final XP based on difficulty
        difficulty_info = QuestDifficulty[quest["difficulty"]].value
        final_xp = quest["base_xp"] * difficulty_info["multiplier"]
        
        # Create reward string
        stat_rewards = quest.get("stat_rewards", {})
        reward_parts = [f"XP +{final_xp}"]
        for stat, amount in stat_rewards.items():
            reward_parts.append(f"{stat.title()} +{amount}")
        
        # Create task
        task = Task(
            name=quest["name"],
            description=quest["description"],
            difficulty=quest["difficulty"],
            reward=", ".join(reward_parts),
            deadline=quest.get("deadline")
        )
        
        # Add metadata for XP and skill tracking
        task.base_xp = quest["base_xp"]
        task.final_xp = final_xp
        task.skill_xp = difficulty_info["skill_xp"]
        task.skills = quest.get("skills", [])
        task.stat_rewards = stat_rewards
        task.quest_type = quest.get("quest_type", "daily")
        task.time_estimate = quest.get("time_estimate", 30)
        
        self.jarvis.tasks.append(task)
        self.jarvis.save_memory()
    
    def _save_three_month_plan(self):
        """Save the 3-month plan to file"""
        try:
            with open('three_month_plan.json', 'w') as f:
                json.dump(self.three_month_plan, f, indent=2)
        except Exception as e:
            print(f"Error saving 3-month plan: {e}")
    
    def schedule_daily_notifications(self):
        """Schedule notifications for morning, evening, and night"""
        schedule.clear()  # Clear existing schedules
        
        # Morning notification - Quest Assignment
        schedule.every().day.at(NotificationTime.MORNING.value).do(
            self._send_morning_notification
        )
        
        # Evening notification - Progress Check
        schedule.every().day.at(NotificationTime.EVENING.value).do(
            self._send_evening_notification
        )
        
        # Night notification - Reflection & Tomorrow Preview
        schedule.every().day.at(NotificationTime.NIGHT.value).do(
            self._send_night_notification
        )
        
        # Start the scheduler in a separate thread
        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
    
    def _send_morning_notification(self):
        """Send morning notification with daily quests"""
        daily_quests = self.generate_daily_quests()
        
        if daily_quests:
            quest_count = len(daily_quests)
            total_xp = sum(quest.get("final_xp", quest.get("base_xp", 0)) for quest in daily_quests)
            
            notification_data = {
                "type": "Daily Quest Assignment",
                "title": "🌅 Good Morning, Hunter!",
                "message": f"{quest_count} new quests await! Potential XP: {total_xp}",
                "quests": [{"name": q["name"], "difficulty": q["difficulty"]} for q in daily_quests],
                "notification_time": "morning"
            }
            
            self._trigger_notification(notification_data)
    
    def _send_evening_notification(self):
        """Send evening notification with progress update"""
        completed_today = [task for task in self.jarvis.tasks 
                          if task.status == "completed" 
                          and task.completed_at 
                          and datetime.fromisoformat(task.completed_at).date() == datetime.now().date()]
        
        pending_today = [task for task in self.jarvis.tasks 
                        if task.status == "pending" 
                        and hasattr(task, 'quest_type')]
        
        completed_xp = sum(getattr(task, 'final_xp', 0) for task in completed_today)
        
        notification_data = {
            "type": "Progress Update",
            "title": "🌆 Evening Check-in",
            "message": f"Completed: {len(completed_today)} quests, {completed_xp} XP earned!",
            "progress": {
                "completed": len(completed_today),
                "pending": len(pending_today),
                "xp_earned": completed_xp
            },
            "notification_time": "evening"
        }
        
        self._trigger_notification(notification_data)
    
    def _send_night_notification(self):
        """Send night notification with reflection prompt and tomorrow preview"""
        # Get tomorrow's planned focus
        tomorrow = datetime.now() + timedelta(days=1)
        tomorrow_week_info = self._get_current_week_info(tomorrow)
        
        notification_data = {
            "type": "Daily Reflection",
            "title": "🌙 Time to Reflect",
            "message": "How did today go? Tomorrow's focus: " + 
                      ", ".join(tomorrow_week_info.get("daily_quest_focus", ["Growth"])),
            "reflection_prompt": "What did you learn today? What will you improve tomorrow?",
            "tomorrow_focus": tomorrow_week_info.get("daily_quest_focus", []),
            "notification_time": "night"
        }
        
        self._trigger_notification(notification_data)
    
    def _trigger_notification(self, notification_data: Dict):
        """Trigger notification through registered callbacks"""
        for callback in self.notification_callbacks:
            try:
                callback(notification_data)
            except Exception as e:
                print(f"Error in notification callback: {e}")
    
    def register_notification_callback(self, callback):
        """Register a callback function for notifications"""
        self.notification_callbacks.append(callback)
    
    def complete_quest_with_xp(self, task_index: int) -> Dict:
        """Complete a quest and apply XP to both general and skill systems"""
        try:
            task = self.jarvis.tasks[task_index - 1]
            if task.status == "completed":
                return {"success": False, "error": "Quest already completed"}
            
            # Mark as completed
            task.status = "completed"
            task.completed_at = datetime.now().isoformat()
            
            # Calculate XP rewards
            base_xp = getattr(task, 'final_xp', getattr(task, 'base_xp', 0))
            skill_xp = getattr(task, 'skill_xp', 0)
            
            # Apply general XP
            self.jarvis.stats["experience"] += base_xp
            self.jarvis.stats["rank_xp"] += base_xp
            
            # Apply skill XP to relevant skills
            skills_affected = getattr(task, 'skills', [])
            skill_updates = {}
            
            for skill_id in skills_affected:
                if skill_id in self.jarvis.stats.get('skill_progress', {}):
                    self.jarvis.stats['skill_progress'][skill_id] += skill_xp
                    skill_updates[skill_id] = skill_xp
                else:
                    # Initialize skill progress if not exists
                    if 'skill_progress' not in self.jarvis.stats:
                        self.jarvis.stats['skill_progress'] = {}
                    self.jarvis.stats['skill_progress'][skill_id] = skill_xp
                    skill_updates[skill_id] = skill_xp
            
            # Apply stat rewards
            stat_rewards = getattr(task, 'stat_rewards', {})
            for stat, amount in stat_rewards.items():
                if stat in self.jarvis.stats:
                    self.jarvis.stats[stat] += amount
            
            # Check for level ups and rank ups
            level_up = self._check_level_up()
            rank_up = self._check_rank_up()
            
            # Save progress
            self.jarvis.save_memory()
            
            return {
                "success": True,
                "xp_gained": base_xp,
                "skill_xp_gained": skill_xp,
                "skills_affected": skill_updates,
                "stat_rewards": stat_rewards,
                "level_up": level_up,
                "rank_up": rank_up,
                "quest_name": task.name
            }
            
        except IndexError:
            return {"success": False, "error": "Invalid quest number"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _check_level_up(self) -> bool:
        """Check and handle level up"""
        xp_needed = self.jarvis.stats["level"] * 150
        if self.jarvis.stats["experience"] >= xp_needed and self.jarvis.stats["level"] < 15:
            self.jarvis.stats["level"] += 1
            self.jarvis.stats["experience"] -= xp_needed
            return True
        return False
    
    def _check_rank_up(self) -> bool:
        """Check and handle rank up"""
        current_rank = self.jarvis.stats["rank"]
        rank_order = ["E", "D", "C", "B", "A", "S", "SS"]
        current_rank_index = rank_order.index(current_rank)
        
        if (self.jarvis.stats["rank_xp"] >= self.jarvis.rank_requirements[current_rank] 
            and current_rank_index < len(rank_order) - 1):
            self.jarvis.stats["rank"] = rank_order[current_rank_index + 1]
            self.jarvis.stats["rank_xp"] = 0
            return True
        return False
    
    def get_daily_stats(self) -> Dict:
        """Get daily statistics and progress"""
        today = datetime.now().date()
        
        # Get today's tasks
        today_tasks = [task for task in self.jarvis.tasks 
                      if hasattr(task, 'quest_type') 
                      and (not hasattr(task, 'created_at') 
                           or datetime.fromisoformat(task.created_at).date() == today)]
        
        completed_tasks = [task for task in today_tasks if task.status == "completed"]
        
        # Calculate stats
        total_xp_today = sum(getattr(task, 'final_xp', 0) for task in completed_tasks)
        total_skill_xp_today = sum(getattr(task, 'skill_xp', 0) for task in completed_tasks)
        
        return {
            "date": today.isoformat(),
            "total_quests": len(today_tasks),
            "completed_quests": len(completed_tasks),
            "pending_quests": len(today_tasks) - len(completed_tasks),
            "xp_earned_today": total_xp_today,
            "skill_xp_earned_today": total_skill_xp_today,
            "completion_rate": len(completed_tasks) / len(today_tasks) if today_tasks else 0,
            "current_level": self.jarvis.stats.get("level", 1),
            "current_rank": self.jarvis.stats.get("rank", "E")
        }