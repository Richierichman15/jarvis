"""
Notification helper for Jarvis.
Provides easy integration between Jarvis AI and the notification system.
"""
import logging
import random
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from .firebase_service import get_firebase_service

logger = logging.getLogger(__name__)

class JarvisNotificationHelper:
    """Helper class to integrate notifications with Jarvis AI."""
    
    def __init__(self, user_id: str = "default_user"):
        self.user_id = user_id
        self.firebase_service = get_firebase_service()
        
    def setup_for_user(self, user_id: str):
        """Set up notifications for a specific user."""
        self.user_id = user_id
        
    def notify_task_completion(self, task_name: str, xp_reward: int = 25):
        """Notify when a task is completed and award XP."""
        # Add XP
        result = self.firebase_service.add_user_xp(
            self.user_id, 
            xp_reward, 
            f"Completed task: {task_name}"
        )
        
        # Send completion notification
        if result.get("success"):
            self.firebase_service.send_notification(
                self.user_id,
                "✅ Task Completed!",
                f"Great job! You completed '{task_name}' and earned {xp_reward} XP!",
                {
                    "type": "task_completion",
                    "task": task_name,
                    "xp_reward": str(xp_reward)
                }
            )
            return True
        return False
    
    def send_ai_insight(self, insight: str, priority: str = "normal"):
        """Send an AI-generated insight as a notification."""
        icons = {
            "low": "💡",
            "normal": "🧠", 
            "high": "⚡",
            "critical": "🚨"
        }
        
        icon = icons.get(priority, "💡")
        
        self.firebase_service.send_notification(
            self.user_id,
            f"{icon} AI Insight",
            insight,
            {
                "type": "ai_insight",
                "priority": priority
            }
        )
    
    def suggest_side_quest(self, context: str = ""):
        """Generate and send a side quest based on context."""
        quests = [
            {
                "title": "Code Optimizer",
                "description": "Review and optimize an old piece of code",
                "xp_reward": 75,
                "difficulty": "medium"
            },
            {
                "title": "Learning Sprint",
                "description": "Spend 30 minutes learning about a new technology",
                "xp_reward": 50,
                "difficulty": "easy"
            },
            {
                "title": "Documentation Writer",
                "description": "Write documentation for a project you're working on",
                "xp_reward": 60,
                "difficulty": "medium"
            },
            {
                "title": "Bug Hunter",
                "description": "Find and fix a bug in your codebase",
                "xp_reward": 100,
                "difficulty": "hard"
            },
            {
                "title": "Automation Champion",
                "description": "Automate a repetitive task you do regularly",
                "xp_reward": 150,
                "difficulty": "hard"
            },
            {
                "title": "Knowledge Sharer",
                "description": "Write a blog post or share knowledge about something you learned",
                "xp_reward": 80,
                "difficulty": "medium"
            }
        ]
        
        # Customize quest based on context if provided
        if context:
            # Simple context-based quest generation
            if "code" in context.lower():
                quest = random.choice([q for q in quests if "code" in q["title"].lower() or "code" in q["description"].lower()])
            elif "learn" in context.lower():
                quest = random.choice([q for q in quests if "learn" in q["title"].lower() or "learn" in q["description"].lower()])
            else:
                quest = random.choice(quests)
        else:
            quest = random.choice(quests)
        
        return self.firebase_service.create_side_quest(
            self.user_id,
            quest["title"],
            quest["description"],
            quest["xp_reward"],
            quest["difficulty"]
        )
    
    def send_break_reminder(self, minutes_working: int = 60):
        """Send a break reminder after extended work."""
        if minutes_working >= 120:  # 2+ hours
            message = "🧘‍♂️ You've been working hard! Time for a proper break. Take 15-20 minutes to recharge."
        elif minutes_working >= 60:  # 1+ hour
            message = "☕ Time for a quick break! Step away from the screen for 5-10 minutes."
        else:
            message = "🌟 Great work! Consider taking a short break to stay fresh."
        
        self.firebase_service.send_notification(
            self.user_id,
            "Break Time!",
            message,
            {"type": "break_reminder", "work_duration": str(minutes_working)}
        )
    
    def celebrate_milestone(self, milestone: str, achievement_unlocked: bool = False):
        """Celebrate a user milestone."""
        celebrations = [
            "🎉 Congratulations!",
            "🌟 Amazing work!",
            "🚀 You're on fire!",
            "💪 Incredible achievement!",
            "⭐ Outstanding!"
        ]
        
        title = random.choice(celebrations)
        xp_bonus = 100 if achievement_unlocked else 50
        
        # Award bonus XP
        self.firebase_service.add_user_xp(
            self.user_id,
            xp_bonus,
            f"Milestone: {milestone}"
        )
        
        message = f"You've reached a major milestone: {milestone}!"
        if achievement_unlocked:
            message += f" Bonus {xp_bonus} XP awarded! 🏆"
        
        self.firebase_service.send_notification(
            self.user_id,
            title,
            message,
            {
                "type": "milestone",
                "milestone": milestone,
                "achievement": achievement_unlocked,
                "xp_bonus": str(xp_bonus)
            }
        )
    
    def schedule_daily_checkin(self, hour: int = 9, minute: int = 0):
        """Schedule a daily check-in notification."""
        checkin_messages = [
            "🌅 Good morning! Ready to tackle today's challenges?",
            "☀️ A new day, new possibilities! What will you build today?",
            "💫 Today is full of potential! Let's make it count!",
            "🎯 Time to set your goals for the day!",
            "🚀 Ready to launch into another productive day?"
        ]
        
        # Calculate time until next scheduled check-in
        now = datetime.now()
        next_checkin = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # If time has passed today, schedule for tomorrow
        if next_checkin <= now:
            next_checkin += timedelta(days=1)
        
        delay_seconds = int((next_checkin - now).total_seconds())
        
        self.firebase_service.send_notification(
            self.user_id,
            "Daily Check-in",
            random.choice(checkin_messages),
            {"type": "daily_checkin"},
            delay_seconds=delay_seconds
        )
        
        logger.info(f"Daily check-in scheduled for {next_checkin}")
    
    def send_motivation_boost(self, context: str = ""):
        """Send a motivational message."""
        motivations = [
            "💪 You've got this! Every expert was once a beginner.",
            "🌟 Progress, not perfection. You're doing amazing!",
            "🚀 The only way to do great work is to love what you do.",
            "⚡ Challenges are what make life interesting. Overcoming them is what makes life meaningful.",
            "🧠 Your mind is your most powerful tool. Use it wisely!",
            "🎯 Success is the sum of small efforts repeated day in and day out.",
            "💡 Innovation distinguishes between a leader and a follower.",
            "🔥 The future belongs to those who learn more skills and combine them in creative ways."
        ]
        
        message = random.choice(motivations)
        
        # Add context-specific motivation if provided
        if "stuck" in context.lower() or "problem" in context.lower():
            message += "\n\nRemember: Every problem is an opportunity to learn and grow!"
        elif "tired" in context.lower() or "exhausted" in context.lower():
            message += "\n\nTake care of yourself. Rest is productive too!"
        
        self.firebase_service.send_notification(
            self.user_id,
            "💫 Motivation Boost",
            message,
            {"type": "motivation", "context": context}
        )
    
    def handle_ai_response_feedback(self, response_quality: str, topic: str = ""):
        """Handle feedback on AI responses to improve engagement."""
        if response_quality == "helpful":
            self.firebase_service.add_user_xp(
                self.user_id, 
                10, 
                f"Helpful AI interaction: {topic}"
            )
            
            # Occasionally send a side quest related to the topic
            if random.random() < 0.3:  # 30% chance
                self.suggest_side_quest(topic)
        
        elif response_quality == "very_helpful":
            self.firebase_service.add_user_xp(
                self.user_id, 
                25, 
                f"Very helpful AI interaction: {topic}"
            )
            
            # Higher chance of side quest for very helpful responses
            if random.random() < 0.5:  # 50% chance
                self.suggest_side_quest(topic)
    
    def get_user_stats(self) -> Dict[str, Any]:
        """Get user progress statistics."""
        result = self.firebase_service.get_user_progress(self.user_id)
        if result.get("success"):
            progress = result["progress"]
            level = progress.get("level", 1)
            total_xp = progress.get("totalXP", 0)
            current_level_xp = total_xp % 100
            
            return {
                "level": level,
                "total_xp": total_xp,
                "current_level_xp": current_level_xp,
                "progress_to_next_level": f"{current_level_xp}/100",
                "achievements": progress.get("achievements", []),
                "quests_completed": progress.get("quests_completed", 0)
            }
        return {}
    
    def check_engagement_trigger(self, last_activity: datetime) -> bool:
        """Check if user needs an engagement notification."""
        time_since_activity = datetime.now() - last_activity
        
        # Send engagement notification if inactive for more than 2 hours
        if time_since_activity > timedelta(hours=2):
            self.firebase_service.send_engagement_notification(self.user_id)
            return True
        
        # Send motivation boost if inactive for more than 1 hour
        elif time_since_activity > timedelta(hours=1):
            self.send_motivation_boost("You've been quiet for a while")
            return True
        
        return False

# Global helper instance
notification_helper = JarvisNotificationHelper()

def get_notification_helper(user_id: str = "default_user") -> JarvisNotificationHelper:
    """Get notification helper instance for a user."""
    notification_helper.setup_for_user(user_id)
    return notification_helper

# Convenience functions for easy integration
def notify_task_completion(task_name: str, user_id: str = "default_user", xp_reward: int = 25):
    """Quick function to notify task completion."""
    helper = get_notification_helper(user_id)
    return helper.notify_task_completion(task_name, xp_reward)

def send_ai_insight(insight: str, user_id: str = "default_user", priority: str = "normal"):
    """Quick function to send AI insight."""
    helper = get_notification_helper(user_id)
    return helper.send_ai_insight(insight, priority)

def suggest_side_quest(context: str = "", user_id: str = "default_user"):
    """Quick function to suggest a side quest."""
    helper = get_notification_helper(user_id)
    return helper.suggest_side_quest(context)

def send_motivation_boost(context: str = "", user_id: str = "default_user"):
    """Quick function to send motivation boost."""
    helper = get_notification_helper(user_id)
    return helper.send_motivation_boost(context)