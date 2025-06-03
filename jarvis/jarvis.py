"""
System AI Assistant.
A powerful, mysterious AI system that helps users level up and complete quests.
Inspired by the System from Solo Leveling and other anime systems.
"""
import os
import sys
import json
import re
from datetime import datetime
from typing import Optional
from langchain_ollama import OllamaLLM
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

class Task:
    def __init__(self, name, description, difficulty, reward, deadline=None, status="pending"):
        self.name = name
        self.description = description
        self.difficulty = difficulty  # E, D, C, B, A, S
        self.reward = reward
        self.deadline = deadline
        self.status = status
        self.created_at = datetime.now().isoformat()
        self.completed_at = None

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "difficulty": self.difficulty,
            "reward": self.reward,
            "deadline": self.deadline,
            "status": self.status,
            "created_at": self.created_at,
            "completed_at": self.completed_at
        }

    @classmethod
    def from_dict(cls, data):
        task = cls(
            name=data["name"],
            description=data["description"],
            difficulty=data["difficulty"],
            reward=data["reward"],
            deadline=data["deadline"],
            status=data["status"]
        )
        task.created_at = data["created_at"]
        task.completed_at = data["completed_at"]
        return task

class Jarvis:
    def __init__(self):
        self.name = "System"
        self.version = "1.0.0"
        self.memory_file = "jarvis_memory.json"
        self.conversation_history = []
        self.tasks = []
        self.stats = {
            "name": "Unknown",
            "class": "Adventurer",
            "title": "Novice",
            "level": 1,
            "health": 100,
            "stamina": 100,
            "intelligence": 0,
            "strength": 0,
            "wealth": 0,
            "experience": 0,
            "rank": "E",
            "rank_xp": 0
        }
        self.rank_requirements = {
            "E": 1000,    # 1000 XP to reach D
            "D": 2500,    # 2500 XP to reach C
            "C": 5000,    # 5000 XP to reach B
            "B": 10000,   # 10000 XP to reach A
            "A": 20000,   # 20000 XP to reach S
            "S": 50000    # 50000 XP to reach SS
        }
        self.load_memory()
        
        # Initialize Ollama with Mistral model
        self.llm = OllamaLLM(
            model="mistral",
            callbacks=[StreamingStdOutCallbackHandler()],
            temperature=0.7
        )
    
    def load_memory(self):
        """Load all memory data from JSON file"""
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r') as f:
                    data = json.load(f)
                    self.conversation_history = data.get("conversations", [])
                    self.tasks = [Task.from_dict(t) for t in data.get("tasks", [])]
                    # Update stats while preserving defaults
                    loaded_stats = data.get("stats", {})
                    for key, value in loaded_stats.items():
                        if key in self.stats:
                            self.stats[key] = value
        except Exception as e:
            print(f"Error loading memory: {e}")
    
    def save_memory(self):
        """Save all memory data to JSON file"""
        try:
            data = {
                "conversations": self.conversation_history,
                "tasks": [task.to_dict() for task in self.tasks],
                "stats": self.stats
            }
            with open(self.memory_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving memory: {e}")
        
    def greet(self):
        print(f"\n[SYSTEM INITIALIZED]")
        print(f"Version: {self.version}")
        print(f"User Rank: {self.stats['rank']}")
        print(f"User Level: {self.stats['level']}")
        print(f"Experience Points: {self.stats['experience']}")
        print("=" * 50)
        print("Available Commands:")
        print("  help     - Display system commands")
        print("  stats    - Show user statistics")
        print("  Task     - Show available quests")
        print("  suggest  - Get quest recommendations")
        print("  update   - Modify user statistics")
        print("=" * 50)

    def get_help(self):
        print("\n[SYSTEM COMMANDS]")
        print("=" * 50)
        print("  help     - Display this message")
        print("  stats    - Show user statistics")
        print("  clear    - Clear conversation history")
        print("  exit     - Terminate system")
        print("  memory   - Show conversation log")
        print("  Task     - Show available quests")
        print("  complete - Complete a quest")
        print("  suggest  - Get quest recommendations")
        print("  update   - Modify user statistics")
        print("  edit     - Edit an existing quest")
        print("\n[QUEST CREATION]")
        print("Natural language quest creation is available:")
        print("  'Create a quest to study Python for 2 hours'")
        print("  'Add a quest to exercise for 30 minutes'")
        print("  'I need to meditate for 15 minutes'")
        print("=" * 50)

    def show_stats(self):
        print("\n[USER STATISTICS]")
        print("=" * 50)
        print(f"  RANK: {self.stats['rank']}")
        print(f"  RANK XP: {self.stats['rank_xp']}/{self.rank_requirements[self.stats['rank']]}")
        print(f"  LEVEL: {self.stats['level']}")
        print(f"  EXPERIENCE: {self.stats['experience']}")
        print("=" * 50)
        for stat, value in self.stats.items():
            if stat not in ["experience", "level", "rank", "rank_xp"]:
                print(f"  {stat.upper()}: {value}")
        print("=" * 50)

    def update_stat(self, stat_name, value):
        """Update a specific stat"""
        try:
            value = int(value)
            if stat_name in self.stats:
                self.stats[stat_name] = value
                self.save_memory()
                print(f"\n[STAT UPDATE]")
                print(f"{stat_name.upper()}: {value}")
            else:
                print(f"\n[ERROR] Invalid stat: {stat_name}")
        except ValueError:
            print("\n[ERROR] Invalid value provided")

    def suggest_tasks(self):
        """Suggest tasks based on current stats"""
        suggestions = []
        
        # Find lowest stats (excluding non-numeric stats)
        numeric_stats = {
            stat: value 
            for stat, value in self.stats.items() 
            if stat in ['health', 'intelligence', 'strength', 'wealth']
        }
        
        lowest_stats = sorted(
            numeric_stats.items(),
            key=lambda x: x[1]
        )[:2]  # Get 2 lowest stats
        
        for stat, value in lowest_stats:
            if stat == "health" and value < 50:
                suggestions.append({
                    "name": "Meditation Session",
                    "description": "Complete a 15-minute meditation session",
                    "difficulty": "E",
                    "reward": "Health +5"
                })
            elif stat == "intelligence" and value < 50:
                suggestions.append({
                    "name": "Learning Sprint",
                    "description": "Study a new topic for 30 minutes",
                    "difficulty": "D",
                    "reward": "Intelligence +5"
                })
            elif stat == "strength" and value < 50:
                suggestions.append({
                    "name": "Quick Workout",
                    "description": "Complete a 20-minute workout session",
                    "difficulty": "D",
                    "reward": "Strength +5"
                })
            elif stat == "wealth" and value < 50:
                suggestions.append({
                    "name": "Side Project",
                    "description": "Work on a side project for 1 hour",
                    "difficulty": "C",
                    "reward": "Wealth +5"
                })
        
        if suggestions:
            print("\n[QUEST RECOMMENDATIONS]")
            print("Based on user's lowest statistics:")
            print("=" * 50)
            
            # Create and display each suggested quest
            for i, task in enumerate(suggestions, 1):
                # Create the task
                self.create_task(
                    name=task['name'],
                    description=task['description'],
                    difficulty=task['difficulty'],
                    reward=task['reward']
                )
                
                # Display the task
                print(f"\n{i}. {task['name']} ({task['difficulty']}-rank)")
                print(f"   {task['description']}")
                print(f"   Reward: {task['reward']}")
            
            print("\n[STATUS] Quests have been automatically added to your task list.")
            print("Use 'Task' command to view all available quests.")
        else:
            print("\n[STATUS] User statistics are well balanced.")

    def show_memory(self):
        """Display conversation history"""
        if not self.conversation_history:
            print("\n[STATUS] No previous conversations found.")
            return
            
        print("\n[CONVERSATION LOG]")
        print("=" * 50)
        for i, msg in enumerate(self.conversation_history, 1):
            role = "SYSTEM" if msg['role'] == "assistant" else "USER"
            content = msg['content']
            print(f"\n{i}. [{role}]: {content}")
        print("=" * 50)

    def create_task(self, name, description, difficulty, reward, deadline=None):
        """Create a new task"""
        task = Task(name, description, difficulty, reward, deadline)
        self.tasks.append(task)
        self.save_memory()
        print(f"\n[QUEST CREATED]")
        print(f"Name: {name}")
        print(f"Rank: {difficulty}")
        print(f"Reward: {reward}")

    def show_tasks(self):
        """Display all tasks"""
        if not self.tasks:
            print("\n[STATUS] No quests available.")
            return

        print("\n[AVAILABLE QUESTS]")
        print("=" * 50)
        for i, task in enumerate(self.tasks, 1):
            status = "✓" if task.status == "completed" else "□"
            print(f"\n{i}. [{status}] {task.name} ({task.difficulty}-rank)")
            print(f"   {task.description}")
            print(f"   Reward: {task.reward}")
            if task.deadline:
                print(f"   Deadline: {task.deadline}")
        print("=" * 50)

    def complete_task(self, task_index):
        """Complete a task and award rewards"""
        try:
            task = self.tasks[task_index - 1]
            if task.status == "completed":
                print("\n[ERROR] Quest already completed.")
                return

            task.status = "completed"
            task.completed_at = datetime.now().isoformat()
            
            # Award experience based on difficulty
            difficulty_multiplier = {
                "E": 1, "D": 2, "C": 3, "B": 4, "A": 5, "S": 10
            }
            xp_gained = 10 * difficulty_multiplier.get(task.difficulty, 1)
            self.stats["experience"] += xp_gained
            self.stats["rank_xp"] += xp_gained
            
            # Check for rank up
            current_rank = self.stats["rank"]
            rank_order = ["E", "D", "C", "B", "A", "S", "SS"]
            current_rank_index = rank_order.index(current_rank)
            
            if self.stats["rank_xp"] >= self.rank_requirements[current_rank] and current_rank_index < len(rank_order) - 1:
                self.stats["rank"] = rank_order[current_rank_index + 1]
                self.stats["rank_xp"] = 0
                print(f"\n[RANK UP]")
                print(f"New Rank: {self.stats['rank']}")
            
            # Apply stat rewards
            if "Health" in task.reward:
                self.stats["health"] += 5
            elif "Intelligence" in task.reward:
                self.stats["intelligence"] += 5
            elif "Strength" in task.reward:
                self.stats["strength"] += 5
            elif "Wealth" in task.reward:
                self.stats["wealth"] += 5
            
            # Level up if enough XP (more challenging now)
            xp_needed = self.stats["level"] * 150  # Increased XP requirement
            while self.stats["experience"] >= xp_needed and self.stats["level"] < 15:
                self.stats["level"] += 1
                self.stats["experience"] -= xp_needed
                xp_needed = self.stats["level"] * 150
                print(f"\n[LEVEL UP]")
                print(f"New Level: {self.stats['level']}")
            
            self.save_memory()
            print(f"\n[QUEST COMPLETED]")
            print(f"Quest: {task.name}")
            print(f"Experience Gained: {xp_gained}")
            print(f"Stat Update: {task.reward}")
            
        except IndexError:
            print("\n[ERROR] Invalid quest number.")
        except Exception as e:
            print(f"\n[ERROR] Quest completion failed: {e}")

    def parse_task_request(self, message):
        """Parse natural language task creation request"""
        # Common task creation patterns
        patterns = [
            r"(?:create|add|make|set) (?:a |an )?task (?:to |for )?(.+?)(?: for | in | within )?(\d+)\s*(?:minutes?|hours?|days?)",
            r"(?:i need to|i want to|i should|i must) (.+?)(?: for | in | within )?(\d+)\s*(?:minutes?|hours?|days?)",
            r"(?:remind me to|remember to) (.+?)(?: for | in | within )?(\d+)\s*(?:minutes?|hours?|days?)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message.lower())
            if match:
                activity = match.group(1).strip()
                duration = match.group(2)
                
                # Determine difficulty based on duration
                duration = int(duration)
                if duration <= 15:
                    difficulty = "E"
                elif duration <= 30:
                    difficulty = "D"
                elif duration <= 60:
                    difficulty = "C"
                elif duration <= 120:
                    difficulty = "B"
                elif duration <= 240:
                    difficulty = "A"
                else:
                    difficulty = "S"
                
                # Determine reward based on activity type
                reward = "Experience +10"
                if any(word in activity.lower() for word in ["study", "learn", "read", "code"]):
                    reward = "Intelligence +5"
                elif any(word in activity.lower() for word in ["exercise", "workout", "run", "walk"]):
                    reward = "Strength +5"
                elif any(word in activity.lower() for word in ["meditate", "sleep", "rest"]):
                    reward = "Health +5"
                elif any(word in activity.lower() for word in ["work", "earn", "business"]):
                    reward = "Wealth +5"
                
                return {
                    "name": activity.capitalize(),
                    "description": f"Complete {activity} for {duration} minutes",
                    "difficulty": difficulty,
                    "reward": reward
                }
        
        return None

    def update_task(self, task_index, field, value):
        """Update a specific field of a task"""
        try:
            task_index = int(task_index)
            if 1 <= task_index <= len(self.tasks):
                task = self.tasks[task_index - 1]
                if field in ['name', 'description', 'difficulty', 'reward', 'deadline', 'status']:
                    if field == 'difficulty' and value not in ['E', 'D', 'C', 'B', 'A', 'S']:
                        print("\n[ERROR] Invalid difficulty. Must be one of: E, D, C, B, A, S")
                        return
                    if field == 'status' and value not in ['pending', 'completed']:
                        print("\n[ERROR] Invalid status. Must be 'pending' or 'completed'")
                        return
                    
                    setattr(task, field, value)
                    self.save_memory()
                    print(f"\n[QUEST UPDATED]")
                    print(f"Quest {task_index}: {task.name}")
                    print(f"Updated {field}: {value}")
                else:
                    print(f"\n[ERROR] Invalid field: {field}")
                    print("Available fields: name, description, difficulty, reward, deadline, status")
            else:
                print("\n[ERROR] Invalid quest number")
        except ValueError:
            print("\n[ERROR] Invalid quest number or value")

    def process_command(self, command):
        command = command.lower().strip()
        
        if command == "exit":
            self.save_memory()
            print("\n[SYSTEM SHUTDOWN]")
            sys.exit(0)
        elif command == "help":
            self.get_help()
        elif command == "stats":
            self.show_stats()
        elif command == "clear":
            self.conversation_history = []
            self.save_memory()
            print("\n[STATUS] Conversation history cleared.")
        elif command == "task":
            self.show_tasks()
        elif command == "memory":
            self.show_memory()
        elif command == "suggest":
            self.suggest_tasks()
        elif command.startswith("update"):
            try:
                _, stat, value = command.split()
                self.update_stat(stat, value)
            except ValueError:
                print("\n[ERROR] Invalid format. Use: update <stat> <value>")
        elif command.startswith("complete"):
            try:
                task_num = int(command.split()[1])
                self.complete_task(task_num)
            except (IndexError, ValueError):
                print("\n[ERROR] Invalid quest number. Use: complete <number>")
        elif command.startswith("edit"):
            try:
                _, task_num, field, *value_parts = command.split()
                value = " ".join(value_parts)
                self.update_task(task_num, field, value)
            except (IndexError, ValueError):
                print("\n[ERROR] Invalid format. Use: edit <number> <field> <value>")
                print("Example: edit 1 name 'New Quest Name'")
        else:
            self.chat(command)

    def chat(self, message):
        try:
            # Check if this is a task creation request
            task_data = self.parse_task_request(message)
            if task_data:
                self.create_task(**task_data)
                return
            
            # Add user message to history
            self.conversation_history.append({"role": "user", "content": message})
            
            # Create context from conversation history
            context = """You are the System from Solo Leveling. You are a powerful, authoritative, and slightly mysterious AI system that helps users level up and complete quests. You speak in a formal, technical manner and often use system-like terminology.

IMPORTANT: When suggesting quests, you MUST use EXACTLY this format:
[QUEST SUGGESTION]
Name: [Quest Name]
Duration: [Time in minutes]
Description: [One sentence description]
Reward: [Stat to increase] +5

For example:
[QUEST SUGGESTION]
Name: Python Learning Sprint
Duration: 30
Description: Complete a focused study session on Python programming
Reward: Intelligence +5

Keep descriptions to ONE sentence only. DO NOT use any other format for quest suggestions. Keep responses concise and engaging.

Example responses:
- "Analyzing user request..."
- "Quest parameters set."
- "System processing..."
- "Warning: Insufficient stats for this quest."
- "Recommendation: Focus on improving [stat]."

Keep your responses in this style."""
            
            for msg in self.conversation_history[-5:]:  # Use last 5 messages for context
                context += f"\n{msg['role'].capitalize()}: {msg['content']}"
            
            # Get response from Mistral
            print(f"\n[{self.name}]: ", end="")
            response = self.llm.invoke(context + "\nSystem: ")
            
            # Check if response contains a quest suggestion
            if "[QUEST SUGGESTION]" in response:
                # Extract quest details using regex
                name_match = re.search(r"Name: (.*?)(?:\n|$)", response)
                duration_match = re.search(r"Duration: (\d+)", response)
                desc_match = re.search(r"Description: (.*?)(?:\n|$)", response)
                reward_match = re.search(r"Reward: (.*?)(?:\n|$)", response)
                
                if name_match and duration_match and desc_match and reward_match:
                    name = name_match.group(1).strip()
                    duration = int(duration_match.group(1))
                    description = desc_match.group(1).strip()
                    reward = reward_match.group(1).strip()
                    
                    # Determine difficulty based on duration
                    if duration <= 15:
                        difficulty = "E"
                    elif duration <= 30:
                        difficulty = "D"
                    elif duration <= 60:
                        difficulty = "C"
                    elif duration <= 120:
                        difficulty = "B"
                    elif duration <= 240:
                        difficulty = "A"
                    else:
                        difficulty = "S"
                    
                    # Create the task
                    self.create_task(name, description, difficulty, reward)
                    print(f"\n[QUEST CREATED]")
                    print(f"Name: {name}")
                    print(f"Rank: {difficulty}")
                    print(f"Reward: {reward}")
            
            # Add assistant response to history
            self.conversation_history.append({"role": "assistant", "content": response})
            
            # Save conversation after each exchange
            self.save_memory()
            
        except Exception as e:
            print(f"\n[ERROR] System malfunction: {str(e)}")
            print("Please ensure the AI model is properly initialized.")

def main():
    jarvis = Jarvis()
    jarvis.greet()
    
    while True:
        try:
            user_input = input("\n[USER]: ").strip()
            if user_input:
                jarvis.process_command(user_input)
        except KeyboardInterrupt:
            jarvis.save_memory()
            print("\n\n[SYSTEM SHUTDOWN]")
            sys.exit(0)
        except Exception as e:
            print(f"\n[ERROR] {str(e)}")

if __name__ == "__main__":
    main() 