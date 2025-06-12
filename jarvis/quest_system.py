"""
Quest and Goal System for Jarvis.
Generates personalized quests and goals based on user desires.
"""
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

# Try to import model manager, but handle if it's not available
try:
    from .models.model_manager import ModelManager
    MODEL_MANAGER_AVAILABLE = True
except ImportError:
    MODEL_MANAGER_AVAILABLE = False


class QuestSystem:
    def __init__(self):
        self.quests_file = Path("jarvis/data/user_quests.json")
        self.goals_file = Path("jarvis/data/user_goals.json")
        self.daily_quests_file = Path("jarvis/data/daily_quests.json")
        
        # Create data directory if it doesn't exist
        self.quests_file.parent.mkdir(exist_ok=True)
        
        # Initialize files
        self._init_files()
        
        # Initialize model manager for generating content if available
        if MODEL_MANAGER_AVAILABLE:
            try:
                self.model_manager = ModelManager()
            except Exception:
                self.model_manager = None
        else:
            self.model_manager = None
        
    def _init_files(self):
        """Initialize quest and goal files."""
        for file_path in [self.quests_file, self.goals_file, self.daily_quests_file]:
            if not file_path.exists():
                self._save_json(file_path, {})
    
    def _load_json(self, file_path: Path) -> Dict:
        """Load JSON data from file."""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _save_json(self, file_path: Path, data: Dict):
        """Save JSON data to file."""
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def generate_goals_from_desires(self, username: str, desires: str) -> List[Dict[str, Any]]:
        """Generate 3-month goals based on user desires."""
        # If we have AI available, use it
        if self.model_manager:
            prompt = f"""
            Based on the following user desires, create a comprehensive 3-month plan with specific, achievable goals:
            
            User Desires: {desires}
            
            Please generate:
            1. 3 main long-term goals (3-month timeline)
            2. 6-9 medium-term goals (monthly milestones)
            3. 15-20 short-term goals (weekly targets)
            
            Format the response as a structured plan that's motivating and actionable.
            Focus on breaking down the desires into concrete, measurable steps.
            """
            
            try:
                response = self.model_manager.generate_response(prompt)
                goals = self._parse_goals_from_response(response, username)
            except Exception as e:
                # Fallback to template-based goals if AI fails
                goals = self._generate_template_goals(desires, username)
        else:
            # Use template-based goals if no AI available
            goals = self._generate_template_goals(desires, username)
        
        # Save goals
        all_goals = self._load_json(self.goals_file)
        all_goals[username] = {
            "desires": desires,
            "goals": goals,
            "created_at": datetime.now().isoformat(),
            "status": "active"
        }
        self._save_json(self.goals_file, all_goals)
        
        return goals
    
    def _generate_template_goals(self, desires: str, username: str) -> List[Dict[str, Any]]:
        """Generate template-based goals when AI is not available."""
        goals = []
        goal_id = 1
        
        # Extract key words from desires for personalization
        key_words = desires.lower().split()
        desire_snippet = desires[:100] + "..." if len(desires) > 100 else desires
        
        # Long-term goals (3 months)
        long_term_templates = [
            f"Achieve significant progress towards: {desire_snippet}",
            f"Master foundational skills needed for: {desire_snippet}",
            f"Create a sustainable plan for: {desire_snippet}"
        ]
        
        for template in long_term_templates:
            goals.append({
                "id": f"{username}_goal_{goal_id}",
                "title": template,
                "description": f"This is a 3-month goal focused on {desires[:50]}...",
                "type": "long-term",
                "timeline_days": 90,
                "status": "pending",
                "progress": 0,
                "created_at": datetime.now().isoformat(),
                "due_date": (datetime.now() + timedelta(days=90)).isoformat()
            })
            goal_id += 1
        
        # Medium-term goals (1 month)
        medium_term_templates = [
            f"Research and plan for {desire_snippet}",
            f"Build initial foundation for {desire_snippet}",
            f"Connect with others interested in {desire_snippet}",
            f"Gather resources needed for {desire_snippet}",
            f"Practice basic skills for {desire_snippet}",
            f"Set up environment for {desire_snippet}"
        ]
        
        for template in medium_term_templates:
            goals.append({
                "id": f"{username}_goal_{goal_id}",
                "title": template,
                "description": f"Monthly milestone towards {desires[:50]}...",
                "type": "medium-term",
                "timeline_days": 30,
                "status": "pending",
                "progress": 0,
                "created_at": datetime.now().isoformat(),
                "due_date": (datetime.now() + timedelta(days=30)).isoformat()
            })
            goal_id += 1
        
        # Short-term goals (1 week)
        short_term_templates = [
            f"Spend 30 minutes daily learning about {desire_snippet}",
            f"Write down specific steps for {desire_snippet}",
            f"Find one resource related to {desire_snippet}",
            f"Take one small action towards {desire_snippet}",
            f"Reflect on progress towards {desire_snippet}",
            f"Share your goal of {desire_snippet} with someone",
            f"Create a timeline for {desire_snippet}",
            f"Identify potential obstacles for {desire_snippet}"
        ]
        
        for template in short_term_templates:
            goals.append({
                "id": f"{username}_goal_{goal_id}",
                "title": template,
                "description": f"Weekly action step towards {desires[:50]}...",
                "type": "short-term",
                "timeline_days": 7,
                "status": "pending",
                "progress": 0,
                "created_at": datetime.now().isoformat(),
                "due_date": (datetime.now() + timedelta(days=7)).isoformat()
            })
            goal_id += 1
        
        return goals
    
    def _parse_goals_from_response(self, response: str, username: str) -> List[Dict[str, Any]]:
        """Parse goals from AI response."""
        goals = []
        lines = response.split('\n')
        
        current_goal = {}
        goal_id = 1
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                if any(keyword in line.lower() for keyword in ['goal', 'milestone', 'target', 'objective']):
                    if current_goal:
                        goals.append(current_goal)
                    
                    # Determine goal type and timeline
                    if 'long-term' in line.lower() or '3-month' in line.lower():
                        goal_type = 'long-term'
                        timeline = 90
                    elif 'medium-term' in line.lower() or 'monthly' in line.lower():
                        goal_type = 'medium-term'
                        timeline = 30
                    else:
                        goal_type = 'short-term'
                        timeline = 7
                    
                    current_goal = {
                        "id": f"{username}_goal_{goal_id}",
                        "title": line,
                        "description": "",
                        "type": goal_type,
                        "timeline_days": timeline,
                        "status": "pending",
                        "progress": 0,
                        "created_at": datetime.now().isoformat(),
                        "due_date": (datetime.now() + timedelta(days=timeline)).isoformat()
                    }
                    goal_id += 1
                elif current_goal and line:
                    current_goal["description"] += line + " "
        
        if current_goal:
            goals.append(current_goal)
        
        # If AI didn't generate enough goals, fall back to template
        if len(goals) < 5:
            return self._generate_fallback_goals("")
        
        return goals
    
    def _generate_fallback_goals(self, desires: str) -> List[Dict[str, Any]]:
        """Generate fallback goals if AI generation fails."""
        return [
            {
                "id": "fallback_goal_1",
                "title": f"Work towards: {desires[:50]}..." if desires else "Set clear personal goals",
                "description": "Take the first step towards achieving your desires",
                "type": "short-term",
                "timeline_days": 7,
                "status": "pending",
                "progress": 0,
                "created_at": datetime.now().isoformat(),
                "due_date": (datetime.now() + timedelta(days=7)).isoformat()
            }
        ]
    
    def generate_daily_quest(self, username: str) -> Dict[str, Any]:
        """Generate a daily quest based on user's goals and desires."""
        user_goals = self.get_user_goals(username)
        
        if not user_goals:
            return self._generate_generic_daily_quest()
        
        # Get active goals
        active_goals = [g for g in user_goals["goals"] if g["status"] == "pending"]
        
        if not active_goals:
            return self._generate_generic_daily_quest()
        
        # Focus on short-term goals for daily quests
        short_term_goals = [g for g in active_goals if g["type"] == "short-term"]
        if not short_term_goals:
            short_term_goals = active_goals[:3]  # Take first 3 if no short-term
        
        # Generate quest based on a random short-term goal
        import random
        goal = random.choice(short_term_goals)
        
        # If we have AI, try to use it
        if self.model_manager:
            quest_prompt = f"""
            Create a daily quest/task that helps progress towards this goal:
            Goal: {goal['title']}
            Description: {goal['description']}
            
            The daily quest should be:
            - Achievable in 1-2 hours
            - Specific and actionable
            - Motivating and engaging
            - Directly related to the goal
            
            Provide just the quest title and a brief description.
            """
            
            try:
                response = self.model_manager.generate_response(quest_prompt)
                quest_title, quest_description = self._parse_quest_from_response(response)
            except:
                quest_title = f"Progress on: {goal['title']}"
                quest_description = f"Take a step forward on {goal['description'][:100]}..."
        else:
            # Use template-based quest generation
            quest_title = f"Daily Progress: {goal['title'][:50]}..."
            quest_description = f"Take concrete action towards: {goal['description'][:100]}..."
        
        daily_quest = {
            "id": f"{username}_daily_{datetime.now().strftime('%Y%m%d')}",
            "username": username,
            "title": quest_title,
            "description": quest_description,
            "related_goal_id": goal["id"],
            "status": "active",
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(days=1)).isoformat(),
            "completion_reward": "Progress towards your dreams! 🌟"
        }
        
        # Save daily quest
        daily_quests = self._load_json(self.daily_quests_file)
        if username not in daily_quests:
            daily_quests[username] = []
        daily_quests[username].append(daily_quest)
        self._save_json(self.daily_quests_file, daily_quests)
        
        return daily_quest
    
    def _parse_quest_from_response(self, response: str) -> tuple:
        """Parse quest title and description from AI response."""
        lines = [line.strip() for line in response.split('\n') if line.strip()]
        
        if len(lines) >= 2:
            return lines[0], ' '.join(lines[1:])
        elif len(lines) == 1:
            return lines[0], "Complete this task to progress towards your goals."
        else:
            return "Daily Progress Quest", "Make progress on your goals today."
    
    def _generate_generic_daily_quest(self) -> Dict[str, Any]:
        """Generate a generic daily quest when no specific goals are available."""
        generic_quests = [
            {
                "title": "Reflect on Your Goals",
                "description": "Spend 15 minutes thinking about what you want to achieve and write down 3 action steps."
            },
            {
                "title": "Learn Something New",
                "description": "Dedicate 30 minutes to learning a new skill or expanding your knowledge in an area of interest."
            },
            {
                "title": "Connect with Your Future Self",
                "description": "Write a letter to yourself describing where you want to be in 3 months."
            },
            {
                "title": "Take Action on a Dream",
                "description": "Do one small thing today that moves you closer to something you've always wanted to do."
            },
            {
                "title": "Plan Your Success",
                "description": "Create a simple plan for achieving one of your goals, breaking it into small steps."
            }
        ]
        
        import random
        quest = random.choice(generic_quests)
        
        return {
            "id": f"generic_daily_{datetime.now().strftime('%Y%m%d')}",
            "username": "generic",
            "title": quest["title"],
            "description": quest["description"],
            "related_goal_id": None,
            "status": "active",
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(days=1)).isoformat(),
            "completion_reward": "Self-improvement achieved! 🌟"
        }
    
    def get_user_goals(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user's goals."""
        all_goals = self._load_json(self.goals_file)
        return all_goals.get(username)
    
    def get_daily_quest(self, username: str) -> Optional[Dict[str, Any]]:
        """Get today's daily quest for user."""
        daily_quests = self._load_json(self.daily_quests_file)
        user_quests = daily_quests.get(username, [])
        
        today = datetime.now().strftime('%Y%m%d')
        for quest in user_quests:
            if today in quest["id"] and quest["status"] == "active":
                return quest
        
        return None
    
    def complete_quest(self, username: str, quest_id: str) -> Dict[str, Any]:
        """Mark a quest as completed."""
        daily_quests = self._load_json(self.daily_quests_file)
        user_quests = daily_quests.get(username, [])
        
        for quest in user_quests:
            if quest["id"] == quest_id:
                quest["status"] = "completed"
                quest["completed_at"] = datetime.now().isoformat()
                self._save_json(self.daily_quests_file, daily_quests)
                return {"success": True, "message": "Quest completed!", "reward": quest.get("completion_reward", "Great job!")}
        
        return {"success": False, "error": "Quest not found"}
    
    def get_user_progress(self, username: str) -> Dict[str, Any]:
        """Get user's overall progress summary."""
        goals = self.get_user_goals(username)
        daily_quests = self._load_json(self.daily_quests_file)
        user_quests = daily_quests.get(username, [])
        
        completed_quests = len([q for q in user_quests if q["status"] == "completed"])
        total_quests = len(user_quests)
        
        if goals:
            completed_goals = len([g for g in goals["goals"] if g["status"] == "completed"])
            total_goals = len(goals["goals"])
        else:
            completed_goals = 0
            total_goals = 0
        
        return {
            "quests_completed": completed_quests,
            "total_quests": total_quests,
            "goals_completed": completed_goals,
            "total_goals": total_goals,
            "quest_completion_rate": (completed_quests / total_quests * 100) if total_quests > 0 else 0,
            "goal_completion_rate": (completed_goals / total_goals * 100) if total_goals > 0 else 0
        }