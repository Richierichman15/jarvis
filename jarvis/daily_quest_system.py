"""
Daily Quest System for Jarvis
Uses Jarvis's AI brain to intelligently generate daily quests based on user goals and progress.
Much simpler approach that leverages existing AI capabilities.
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
    """XP rewards for different quest difficulties"""
    E = {"xp": 10, "skill_xp": 5, "multiplier": 1}
    D = {"xp": 25, "skill_xp": 10, "multiplier": 1.5}
    C = {"xp": 50, "skill_xp": 15, "multiplier": 2}
    B = {"xp": 100, "skill_xp": 25, "multiplier": 3}
    A = {"xp": 200, "skill_xp": 40, "multiplier": 4}
    S = {"xp": 500, "skill_xp": 75, "multiplier": 6}

class NotificationTime(Enum):
    """Scheduled notification times"""
    MORNING = "07:00"
    EVENING = "18:00"
    NIGHT = "21:00"

class DailyQuestGenerator:
    def __init__(self, jarvis_instance):
        self.jarvis = jarvis_instance
        self.three_month_plan = {}
        self.notification_callbacks = []
        
    def generate_three_month_plan(self) -> Dict:
        """Use Jarvis's AI to generate a comprehensive 3-month plan"""
        # Create AI prompt for 3-month planning
        planning_prompt = f"""
        You are a strategic life planner. Based on the user's current stats and goals, create a comprehensive 3-month plan.
        
        Current User Stats:
        - Level: {self.jarvis.stats.get('level', 1)}
        - Rank: {self.jarvis.stats.get('rank', 'E')}
        - Health: {self.jarvis.stats.get('health', 0)}
        - Intelligence: {self.jarvis.stats.get('intelligence', 0)}
        - Strength: {self.jarvis.stats.get('strength', 0)}
        - Wealth: {self.jarvis.stats.get('wealth', 0)}
        
        User Goals: {self._get_user_goals_summary()}
        
        Create a strategic 3-month plan with:
        1. Month 1 theme and focus areas
        2. Month 2 theme and focus areas  
        3. Month 3 theme and focus areas
        4. Weekly milestones for each month
        
        Format your response as a clear, actionable plan.
        """
        
        try:
            # Use Jarvis's AI to generate the plan
            plan_response = self.jarvis.llm.invoke(planning_prompt)
            
            # Create structured plan data
            plan = {
                "created_at": datetime.now().isoformat(),
                "ai_generated_plan": plan_response,
                "total_weeks": 12,
                "current_week": 1
            }
            
            self.three_month_plan = plan
            self._save_three_month_plan()
            return plan
            
        except Exception as e:
            print(f"Error generating 3-month plan: {e}")
            return {}
    
    def generate_daily_quests(self, date: datetime = None) -> List[Dict]:
        """Use Jarvis's AI brain to generate intelligent daily quests"""
        if date is None:
            date = datetime.now()
            
        # Create AI prompt for daily quest generation
        quest_prompt = self._create_quest_generation_prompt(date)
        
        try:
            # Use Jarvis's AI to generate quests
            response = self.jarvis.llm.invoke(quest_prompt)
            
            # Parse the AI response and create quests
            daily_quests = self._parse_quest_response(response)
            
            # Add quests to Jarvis system
            for quest in daily_quests:
                self._add_quest_to_jarvis(quest)
            
            print(f"✅ Generated {len(daily_quests)} daily quests using Jarvis AI")
            return daily_quests
            
        except Exception as e:
            print(f"Error generating daily quests: {e}")
            return []
    
    def _create_quest_generation_prompt(self, date: datetime) -> str:
        """Create an intelligent prompt for Jarvis to generate daily quests"""
        
        # Get user context
        current_stats = self.jarvis.stats
        weak_stats = self._find_weakest_stats()
        recent_completions = self._get_recent_completions()
        
        prompt = f"""
        You are Jarvis, the System from Solo Leveling. Generate 3-4 daily quests for today ({date.strftime('%A, %B %d')}).
        
        USER STATUS:
        - Level: {current_stats.get('level', 1)}
        - Rank: {current_stats.get('rank', 'E')}
        - Health: {current_stats.get('health', 0)}
        - Intelligence: {current_stats.get('intelligence', 0)}
        - Strength: {current_stats.get('strength', 0)}
        - Wealth: {current_stats.get('wealth', 0)}
        
        FOCUS AREAS (user's weakest stats): {', '.join(weak_stats)}
        
        USER GOALS: {self._get_user_goals_summary()}
        
        RECENT ACTIVITY: {recent_completions}
        
        QUEST GENERATION RULES:
        1. Create 3-4 specific, actionable quests
        2. Include one quest targeting the weakest stat area
        3. Mix difficulty levels (E, D, C, B, A, S)
        4. Make quests relevant to user's goals
        5. Consider time constraints (realistic for one day)
        
        FORMAT YOUR RESPONSE EXACTLY LIKE THIS:
        [QUEST 1]
        Name: [Quest Name]
        Description: [Detailed description]
        Difficulty: [E/D/C/B/A/S]
        Category: [health/intelligence/strength/wealth/personal_growth]
        Time: [Estimated minutes]
        
        [QUEST 2]
        Name: [Quest Name]
        Description: [Detailed description]
        Difficulty: [E/D/C/B/A/S]
        Category: [health/intelligence/strength/wealth/personal_growth]
        Time: [Estimated minutes]
        
        Continue for all quests. Be creative and motivating!
        """
        
        return prompt
    
    def _parse_quest_response(self, response: str) -> List[Dict]:
        """Parse Jarvis's AI response into structured quest data"""
        quests = []
        
        # Split response into quest blocks
        quest_blocks = response.split('[QUEST')
        
        for block in quest_blocks[1:]:  # Skip first empty block
            try:
                quest = self._extract_quest_from_block(block)
                if quest:
                    quests.append(quest)
            except Exception as e:
                print(f"Error parsing quest block: {e}")
                continue
        
        return quests
    
    def _extract_quest_from_block(self, block: str) -> Optional[Dict]:
        """Extract quest data from a text block"""
        lines = block.strip().split('\n')
        quest = {}
        
        for line in lines:
            line = line.strip()
            if line.startswith('Name:'):
                quest['name'] = line.replace('Name:', '').strip()
            elif line.startswith('Description:'):
                quest['description'] = line.replace('Description:', '').strip()
            elif line.startswith('Difficulty:'):
                quest['difficulty'] = line.replace('Difficulty:', '').strip()
            elif line.startswith('Category:'):
                quest['category'] = line.replace('Category:', '').strip()
            elif line.startswith('Time:'):
                time_str = line.replace('Time:', '').strip()
                quest['time_estimate'] = int(''.join(filter(str.isdigit, time_str))) or 30
        
        # Validate required fields
        if all(key in quest for key in ['name', 'description', 'difficulty']):
            quest['generated_at'] = datetime.now().isoformat()
            quest['quest_type'] = 'daily_ai_generated'
            return quest
        
        return None
    
    def _find_weakest_stats(self) -> List[str]:
        """Find user's weakest stats to target for improvement"""
        numeric_stats = {
            'health': self.jarvis.stats.get('health', 0),
            'intelligence': self.jarvis.stats.get('intelligence', 0),
            'strength': self.jarvis.stats.get('strength', 0),
            'wealth': self.jarvis.stats.get('wealth', 0)
        }
        
        # Sort by value and return 2 weakest
        sorted_stats = sorted(numeric_stats.items(), key=lambda x: x[1])
        return [stat[0] for stat in sorted_stats[:2]]
    
    def _get_recent_completions(self) -> str:
        """Get summary of recently completed quests"""
        recent_tasks = []
        today = datetime.now().date()
        
        for task in self.jarvis.tasks[-5:]:  # Last 5 tasks
            if (task.status == 'completed' and task.completed_at and 
                datetime.fromisoformat(task.completed_at).date() >= today - timedelta(days=3)):
                recent_tasks.append(task.name)
        
        if recent_tasks:
            return f"Recently completed: {', '.join(recent_tasks)}"
        return "No recent completions"
    
    def _get_user_goals_summary(self) -> str:
        """Get a summary of user's goals from memory"""
        try:
            with open('jarvis_memory.json', 'r') as f:
                data = json.load(f)
                for task in data.get('tasks', []):
                    if isinstance(task, dict) and 'goals' in task:
                        goals = task['goals'][:3]  # First 3 goals
                        return '; '.join([goal.get('name', 'Unknown goal') for goal in goals])
        except:
            pass
        return "Financial independence, programming mastery, physical fitness"
    
    def _add_quest_to_jarvis(self, quest: Dict):
        """Add AI-generated quest to Jarvis system"""
        from jarvis.jarvis import Task
        
        # Calculate XP based on difficulty
        difficulty_info = QuestDifficulty[quest["difficulty"]].value
        base_xp = difficulty_info["xp"]
        final_xp = int(base_xp * difficulty_info["multiplier"])
        
        # Create reward string
        reward = f"XP +{final_xp}"
        category = quest.get('category', 'general')
        if category in ['health', 'intelligence', 'strength', 'wealth']:
            stat_bonus = random.randint(1, 3)
            reward += f", {category.title()} +{stat_bonus}"
        
        # Create task
        task = Task(
            name=quest["name"],
            description=quest["description"],
            difficulty=quest["difficulty"],
            reward=reward,
            deadline=(datetime.now() + timedelta(days=1)).isoformat()
        )
        
        # Add metadata for XP tracking
        task.base_xp = base_xp
        task.final_xp = final_xp
        task.skill_xp = difficulty_info["skill_xp"]
        task.quest_type = quest.get("quest_type", "ai_generated")
        task.time_estimate = quest.get("time_estimate", 30)
        task.category = quest.get("category", "general")
        
        self.jarvis.tasks.append(task)
        self.jarvis.save_memory()
    
    def _save_three_month_plan(self):
        """Save the 3-month plan to file"""
        try:
            with open('three_month_plan.json', 'w') as f:
                json.dump(self.three_month_plan, f, indent=2)
        except Exception as e:
            print(f"Error saving 3-month plan: {e}")
    
    # === NOTIFICATION SYSTEM (simplified) ===
    
    def schedule_daily_notifications(self):
        """Schedule daily notifications"""
        schedule.clear()
        
        schedule.every().day.at(NotificationTime.MORNING.value).do(self._send_morning_notification)
        schedule.every().day.at(NotificationTime.EVENING.value).do(self._send_evening_notification)
        schedule.every().day.at(NotificationTime.NIGHT.value).do(self._send_night_notification)
        
        # Start scheduler in background thread
        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(60)
        
        threading.Thread(target=run_scheduler, daemon=True).start()
        print("✅ Daily notification scheduler started")
    
    def _send_morning_notification(self):
        """Morning: Generate and announce daily quests"""
        daily_quests = self.generate_daily_quests()
        total_xp = sum(quest.get("final_xp", 0) for quest in daily_quests)
        
        notification_data = {
            "type": "Daily Quest Assignment",
            "title": "🌅 Good Morning, Hunter!",
            "message": f"{len(daily_quests)} new AI-generated quests await! Potential XP: {total_xp}",
            "notification_time": "morning"
        }
        self._trigger_notification(notification_data)
    
    def _send_evening_notification(self):
        """Evening: Progress check"""
        today_completed = self._get_today_completed_count()
        today_xp = self._get_today_xp_earned()
        
        notification_data = {
            "type": "Progress Update",
            "title": "🌆 Evening Check-in",
            "message": f"Completed: {today_completed} quests, {today_xp} XP earned!",
            "notification_time": "evening"
        }
        self._trigger_notification(notification_data)
    
    def _send_night_notification(self):
        """Night: Reflection prompt"""
        notification_data = {
            "type": "Daily Reflection",
            "title": "🌙 Time to Reflect",
            "message": "How did today's quests go? Tomorrow brings new challenges!",
            "notification_time": "night"
        }
        self._trigger_notification(notification_data)
    
    def _trigger_notification(self, notification_data: Dict):
        """Send notification through registered callbacks"""
        for callback in self.notification_callbacks:
            try:
                callback(notification_data)
            except Exception as e:
                print(f"Error in notification callback: {e}")
    
    def register_notification_callback(self, callback):
        """Register a callback function for notifications"""
        self.notification_callbacks.append(callback)
    
    # === QUEST COMPLETION WITH XP ===
    
    def complete_quest_with_xp(self, task_index: int) -> Dict:
        """Complete a quest and apply XP rewards"""
        try:
            task = self.jarvis.tasks[task_index - 1]
            if task.status == "completed":
                return {"success": False, "error": "Quest already completed"}
            
            # Mark as completed
            task.status = "completed"
            task.completed_at = datetime.now().isoformat()
            
            # Apply XP rewards
            base_xp = getattr(task, 'final_xp', getattr(task, 'base_xp', 10))
            skill_xp = getattr(task, 'skill_xp', 5)
            
            self.jarvis.stats["experience"] += base_xp
            self.jarvis.stats["rank_xp"] += base_xp
            
            # Apply stat bonuses (parse from reward string)
            self._apply_stat_rewards(task.reward)
            
            # Check for level/rank ups
            level_up = self._check_level_up()
            rank_up = self._check_rank_up()
            
            self.jarvis.save_memory()
            
            return {
                "success": True,
                "xp_gained": base_xp,
                "skill_xp_gained": skill_xp,
                "level_up": level_up,
                "rank_up": rank_up,
                "quest_name": task.name
            }
            
        except (IndexError, Exception) as e:
            return {"success": False, "error": str(e)}
    
    def _apply_stat_rewards(self, reward_string: str):
        """Parse and apply stat rewards from reward string"""
        # Simple parsing: "Health +3", "Intelligence +2", etc.
        parts = reward_string.split(', ')
        for part in parts:
            if '+' in part and any(stat in part.lower() for stat in ['health', 'intelligence', 'strength', 'wealth']):
                for stat in ['health', 'intelligence', 'strength', 'wealth']:
                    if stat in part.lower():
                        try:
                            bonus = int(part.split('+')[1])
                            self.jarvis.stats[stat] += bonus
                        except:
                            pass
    
    def _check_level_up(self) -> bool:
        """Check and handle level up"""
        xp_needed = self.jarvis.stats["level"] * 150
        if self.jarvis.stats["experience"] >= xp_needed:
            self.jarvis.stats["level"] += 1
            self.jarvis.stats["experience"] -= xp_needed
            return True
        return False
    
    def _check_rank_up(self) -> bool:
        """Check and handle rank up"""
        current_rank = self.jarvis.stats["rank"]
        rank_order = ["E", "D", "C", "B", "A", "S", "SS"]
        current_idx = rank_order.index(current_rank)
        
        if (self.jarvis.stats["rank_xp"] >= self.jarvis.rank_requirements[current_rank] 
            and current_idx < len(rank_order) - 1):
            self.jarvis.stats["rank"] = rank_order[current_idx + 1]
            self.jarvis.stats["rank_xp"] = 0
            return True
        return False
    
    # === HELPER METHODS ===
    
    def _get_today_completed_count(self) -> int:
        """Count quests completed today"""
        today = datetime.now().date()
        count = 0
        for task in self.jarvis.tasks:
            if (task.status == "completed" and task.completed_at and 
                datetime.fromisoformat(task.completed_at).date() == today):
                count += 1
        return count
    
    def _get_today_xp_earned(self) -> int:
        """Calculate total XP earned today"""
        today = datetime.now().date()
        total_xp = 0
        for task in self.jarvis.tasks:
            if (task.status == "completed" and task.completed_at and 
                datetime.fromisoformat(task.completed_at).date() == today):
                total_xp += getattr(task, 'final_xp', 0)
        return total_xp
    
    def get_daily_stats(self) -> Dict:
        """Get daily statistics"""
        today = datetime.now().date()
        today_tasks = [task for task in self.jarvis.tasks 
                      if hasattr(task, 'quest_type') 
                      and (not hasattr(task, 'created_at') 
                           or datetime.fromisoformat(task.created_at).date() == today)]
        
        completed_tasks = [task for task in today_tasks if task.status == "completed"]
        
        return {
            "date": today.isoformat(),
            "total_quests": len(today_tasks),
            "completed_quests": len(completed_tasks),
            "pending_quests": len(today_tasks) - len(completed_tasks),
            "xp_earned_today": self._get_today_xp_earned(),
            "completion_rate": len(completed_tasks) / len(today_tasks) if today_tasks else 0,
            "current_level": self.jarvis.stats.get("level", 1),
            "current_rank": self.jarvis.stats.get("rank", "E")
        }