import json
import os
from datetime import datetime, timedelta
import random
from pathlib import Path

# Paths
DATA_DIR = Path(__file__).parent / "data"
DESIRES_FILE = DATA_DIR / "desires_structure.json"
GOALS_FILE = DATA_DIR / "user_goals.json"
QUESTS_FILE = DATA_DIR / "daily_quests.json"

# Ensure data directory exists
DATA_DIR.mkdir(exist_ok=True)

class GoalManager:
    def __init__(self, username="buck"):
        self.username = username
        self.desires = self._load_desires()
        self.goals = self._load_goals()
        
    def _load_desires(self):
        if not DESIRES_FILE.exists():
            return {}
        with open(DESIRES_FILE, 'r') as f:
            return json.load(f).get(self.username, {})
    
    def _load_goals(self):
        if not GOALS_FILE.exists():
            return {self.username: {"goals": [], "created_at": datetime.now().isoformat(), "status": "active"}}
        with open(GOALS_FILE, 'r') as f:
            return json.load(f)
    
    def _save_goals(self):
        with open(GOALS_FILE, 'w') as f:
            json.dump(self.goals, f, indent=2)
    
    def _save_quests(self, quests):
        with open(QUESTS_FILE, 'w') as f:
            json.dump({self.username: quests}, f, indent=2)
    
    def generate_goals_from_desires(self):
        """Generate SMART goals based on the user's desires"""
        if not self.desires:
            return []
        
        goals = []
        goal_id = 1
        now = datetime.now()
        
        # Generate goals for each desire category
        for category, details in self.desires.items():
            if category == "last_updated":
                continue
                
            # Long-term goal (3 months)
            goals.append({
                "id": f"{self.username}_goal_{goal_id}",
                "title": f"{details['description'].capitalize()}",
                "description": f"Achieve significant progress in {category.replace('_', ' ')}",
                "type": "long-term",
                "timeline_days": 90,
                "status": "active",
                "progress": 0,
                "category": category,
                "created_at": now.isoformat(),
                "due_date": (now + timedelta(days=90)).isoformat()
            })
            goal_id += 1
            
            # Medium-term goals (monthly)
            for subcategory in details.get("categories", []):
                goals.append({
                    "id": f"{self.username}_goal_{goal_id}",
                    "title": f"Improve {subcategory.replace('_', ' ')}",
                    "description": f"Monthly milestone for {subcategory.replace('_', ' ')}",
                    "type": "medium-term",
                    "timeline_days": 30,
                    "status": "active",
                    "progress": 0,
                    "category": category,
                    "subcategory": subcategory,
                    "created_at": now.isoformat(),
                    "due_date": (now + timedelta(days=30)).isoformat()
                })
                goal_id += 1
        
        # Update goals in memory and save
        self.goals[self.username] = {
            "goals": goals,
            "created_at": now.isoformat(),
            "status": "active"
        }
        self._save_goals()
        return goals
    
    def generate_daily_quests(self):
        """Generate daily quests from active goals"""
        if self.username not in self.goals:
            return []
            
        active_goals = [g for g in self.goals[self.username].get("goals", []) 
                       if g.get("status") == "active"]
        
        if not active_goals:
            return []
            
        quests = []
        now = datetime.now()
        
        # Create quests for today
        for goal in active_goals:
            # Only create quests for medium-term goals or long-term goals that are due soon
            if goal["type"] == "long-term":
                due_date = datetime.fromisoformat(goal["due_date"])
                days_until_due = (due_date - now).days
                if days_until_due > 14:  # Only create quests for long-term goals due soon
                    continue
            
            quests.append(self._create_quest_from_goal(goal, now))
        
        # Ensure we have at least 3 quests (physical, mental, spiritual)
        while len(quests) < 3:
            goal = random.choice(active_goals)
            quests.append(self._create_quest_from_goal(goal, now))
        
        self._save_quests(quests)
        return quests
    
    def _create_quest_from_goal(self, goal, timestamp):
        """Create a quest from a goal"""
        quest_id = f"{self.username}_quest_{int(timestamp.timestamp())}_{goal['id']}"
        
        # Different quest types based on goal category
        category = goal.get("category", "general")
        quest_types = {
            "fitness": [
                f"Complete a {random.choice(['strength', 'cardio', 'flexibility'])} workout",
                f"Track your meals and hit {random.randint(150, 200)}g of protein",
                f"Get {random.randint(7, 9)} hours of quality sleep"
            ],
            "finance": [
                "Research a new investment opportunity",
                "Read a chapter from a finance book",
                "Review and update your budget"
            ],
            "career": [
                "Work on a coding project for 1 hour",
                "Learn a new programming concept",
                "Network with a professional in your field"
            ],
            "personal_development": [
                "Read for 30 minutes on a new topic",
                "Practice a new skill for 30 minutes",
                "Reflect on your progress and journal"
            ]
        }
        
        # Default quest description
        description = random.choice(quest_types.get(category, ["Work on making progress towards your goal"]))
        
        return {
            "id": quest_id,
            "username": self.username,
            "title": f"Daily: {goal['title']}",
            "description": description,
            "related_goal_id": goal["id"],
            "status": "active",
            "created_at": timestamp.isoformat(),
            "expires_at": (timestamp + timedelta(days=1)).replace(hour=23, minute=59, second=59).isoformat(),
            "completion_reward": "Progress towards your goals! ✨"
        }

# Example usage
if __name__ == "__main__":
    manager = GoalManager()
    print("Generating goals from desires...")
    goals = manager.generate_goals_from_desires()
    print(f"Generated {len(goals)} goals")
    
    print("\nGenerating daily quests...")
    quests = manager.generate_daily_quests()
    print(f"Generated {len(quests)} daily quests")
