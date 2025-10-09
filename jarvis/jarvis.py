"""
JARVIS - Just A Rather Very Intelligent System
An advanced AI assistant inspired by the AI from Iron Man.
Designed to help users with productivity, learning, and daily tasks.
"""
import os
import sys
import json
import re
import subprocess
import platform
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
try:
    from langchain_ollama import OllamaLLM
    from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

class Task:
    """Represents a task or reminder for the user."""
    def __init__(self, name, description, priority="medium", category="general", deadline=None, status="pending"):
        self.name = name
        self.description = description
        self.priority = priority  # low, medium, high, urgent
        self.category = category  # work, personal, learning, health, etc.
        self.deadline = deadline
        self.status = status
        self.created_at = datetime.now().isoformat()
        self.completed_at = None
        self.estimated_duration = None  # in minutes

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "priority": self.priority,
            "category": self.category,
            "deadline": self.deadline,
            "status": self.status,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "estimated_duration": self.estimated_duration
        }

    @classmethod
    def from_dict(cls, data):
        """Create a Task instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")
            
        required_fields = ["name", "description"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        task = cls(
            name=data["name"],
            description=data["description"],
            priority=data.get("priority", "medium"),
            category=data.get("category", "general"),
            deadline=data.get("deadline"),
            status=data.get("status", "pending")
        )
        
        # Restore additional fields
        if "created_at" in data:
            task.created_at = data["created_at"]
        if "completed_at" in data:
            task.completed_at = data["completed_at"]
        if "estimated_duration" in data:
            task.estimated_duration = data["estimated_duration"]
            
        return task

class Jarvis:
    """JARVIS - Just A Rather Very Intelligent System"""
    
    def __init__(self, user_name="Sir"):
        self.user_name = user_name
        self.name = "JARVIS"
        self.version = "2.0.0"
        self.personality = "professional, helpful, and slightly witty"
        
        # Set memory file path relative to the jarvis directory
        self.memory_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'jarvis_memory.json')
        self.conversation_history = []
        self.tasks = []
        self.reminders = []
        
        # User preferences and settings
        self.preferences = {
            "communication_style": "professional",
            "notification_level": "medium",
            "auto_suggestions": True,
            "voice_enabled": False,
            "dark_mode": False
        }
        
        # System information
        self.system_info = {
            "os": platform.system(),
            "hostname": platform.node(),
            "python_version": platform.python_version(),
            "uptime": datetime.now().isoformat()
        }
        
        self.load_memory()
        
        # Initialize AI model if available
        self.llm = None
        if LANGCHAIN_AVAILABLE:
            try:
                # Use model from brain.env if available, otherwise fallback to default
                model_name = os.environ.get("OLLAMA_MODEL", "llama3.1:8b-instruct-q8_0")
                self.llm = OllamaLLM(
                    model=model_name,
                    callbacks=[StreamingStdOutCallbackHandler()],
                    temperature=0.7
                )
            except Exception as e:
                print(f"Warning: Could not initialize AI model: {e}")
                self.llm = None
        else:
            print("Info: AI chat capabilities disabled (langchain not available)")
    
    def _task_identity(self, task: "Task"):
        """Return a tuple that uniquely identifies a task to help deduplicate."""
        try:
            return (task.name, task.description, task.category)
        except Exception:
            return None

    def _dedupe_tasks(self):
        """Remove duplicate tasks, preserving the first occurrence."""
        unique = {}
        deduped = []
        for t in self.tasks:
            key = self._task_identity(t) if isinstance(t, Task) else (
                t.get("name"), t.get("description"), t.get("category")
            ) if isinstance(t, dict) else None
            if key and key not in unique:
                unique[key] = True
                deduped.append(t)
        self.tasks = deduped
    
    def load_memory(self):
        """Load memory from JSON file."""
        try:
            # Create memory directory if it doesn't exist
            os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
            
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r') as f:
                    data = json.load(f)
                    
                    # Initialize default structure if needed
                    if not isinstance(data, dict):
                        data = {}
                    if 'users' not in data:
                        data['users'] = {}
                    
                    # Load user-specific data if available
                    if self.user_name in data['users']:
                        user_data = data['users'][self.user_name]
                        if isinstance(user_data, dict):
                            if 'preferences' in user_data:
                                self.preferences.update(user_data['preferences'])
                            if 'tasks' in user_data and isinstance(user_data['tasks'], list):
                                self.tasks = []
                                for t in user_data['tasks']:
                                    try:
                                        if isinstance(t, dict) and 'name' in t:
                                            self.tasks.append(Task.from_dict(t))
                                    except Exception as e:
                                        print(f"Error loading task: {e}")
                            if 'conversation_history' in user_data:
                                self.conversation_history = user_data['conversation_history']
                
                # Ensure we don't keep duplicates
                self._dedupe_tasks()
            else:
                # Create default memory file if it doesn't exist
                self.save_memory()
                    
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading memory: {e}")
            # Create default memory file
            self.save_memory()
    
    def save_memory(self):
        """Save memory to JSON file."""
        try:
            # Create memory directory if it doesn't exist
            os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
            
            # Load existing data or create new
            try:
                with open(self.memory_file, 'r') as f:
                    data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                data = {'users': {}}
            
            # Ensure users dict exists
            if not isinstance(data, dict):
                data = {}
            if 'users' not in data:
                data['users'] = {}
            
            # Deduplicate tasks before persisting
            self._dedupe_tasks()

            # Update user data
            if self.user_name not in data['users']:
                data['users'][self.user_name] = {}
            
            # Convert tasks to dict format
            task_dicts = []
            for task in self.tasks:
                if isinstance(task, Task):
                    task_dicts.append(task.to_dict())
                elif isinstance(task, dict) and 'name' in task:
                    task_dicts.append(task)
            
            # Save user-specific data
            data['users'][self.user_name].update({
                'preferences': self.preferences,
                'tasks': task_dicts,
                'conversation_history': self.conversation_history[-50:],  # Keep last 50 conversations
                'last_updated': datetime.now().isoformat()
            })

            # Save to file
            with open(self.memory_file, 'w') as f:
                json.dump(data, f, indent=4)
                
        except Exception as e:
            print(f"Error saving memory: {e}")
    
    def greet(self):
        """Display welcome message and system status."""
        current_time = datetime.now().strftime("%H:%M")
        greeting = self._get_time_based_greeting()
        
        print(f"\n{'='*60}")
        print(f"🤖 {self.name} v{self.version} - Online")
        print(f"{greeting}, {self.user_name}")
        print(f"Current time: {current_time}")
        print(f"System: {self.system_info['os']} on {self.system_info['hostname']}")
        print(f"{'='*60}")
        print("Available Commands:")
        print("  help        - Display all available commands")
        print("  status      - Show system status and tasks")
        print("  tasks       - View all tasks and reminders")
        print("  schedule    - Schedule a new task or reminder")
        print("  complete    - Mark a task as completed")
        print("  system      - Show system information")
        print("  settings    - Manage preferences")
        print("  exit        - Shutdown JARVIS")
        print(f"{'='*60}")
        
        # Show pending tasks if any
        pending_tasks = [t for t in self.tasks if t.status == "pending"]
        if pending_tasks:
            print(f"\n📋 You have {len(pending_tasks)} pending task(s):")
            for i, task in enumerate(pending_tasks[:3], 1):  # Show first 3
                priority_icon = {"urgent": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(task.priority, "⚪")
                print(f"  {i}. {priority_icon} {task.name}")
            if len(pending_tasks) > 3:
                print(f"  ... and {len(pending_tasks) - 3} more")
    
    def _get_time_based_greeting(self):
        """Get appropriate greeting based on time of day."""
        hour = datetime.now().hour
        if 5 <= hour < 12:
            return "Good morning"
        elif 12 <= hour < 17:
            return "Good afternoon"
        elif 17 <= hour < 21:
            return "Good evening"
        else:
            return "Good evening"  # Late night
    
    def get_help(self):
        """Display comprehensive help information."""
        print(f"\n{'='*60}")
        print(f"🤖 {self.name} - Command Reference")
        print(f"{'='*60}")
        print("📋 TASK MANAGEMENT:")
        print("  tasks                    - View all tasks")
        print("  schedule <description>   - Create a new task")
        print("  complete <number>        - Mark task as completed")
        print("  priority <number> <level> - Change task priority")
        print("  delete <number>          - Remove a task")
        print()
        print("📊 SYSTEM COMMANDS:")
        print("  status                   - Show system overview")
        print("  system                   - Display system information")
        print("  settings                 - Manage preferences")
        print("  clear                    - Clear conversation history")
        print("  memory                   - Show recent conversations")
        print()
        print("💬 CONVERSATION:")
        print("  Just type naturally to chat with JARVIS")
        print("  Ask questions, request help, or have a conversation")
        print()
        print("🔧 UTILITY COMMANDS:")
        print("  time                     - Show current time")
        print("  weather                  - Get weather information")
        print("  news                     - Get latest news headlines")
        print("  help                     - Show this help message")
        print("  exit                     - Shutdown JARVIS")
        print(f"{'='*60}")
    
    def show_status(self):
        """Display current system status and overview."""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        pending_tasks = [t for t in self.tasks if t.status == "pending"]
        completed_tasks = [t for t in self.tasks if t.status == "completed"]
        urgent_tasks = [t for t in pending_tasks if t.priority == "urgent"]
        
        print(f"\n{'='*60}")
        print(f"📊 {self.name} System Status")
        print(f"{'='*60}")
        print(f"⏰ Current Time: {current_time}")
        print(f"👤 User: {self.user_name}")
        print(f"🖥️  System: {self.system_info['os']} {self.system_info['python_version']}")
        print(f"💾 Memory: {len(self.conversation_history)} conversations stored")
        print()
        print("📋 TASK OVERVIEW:")
        print(f"  📝 Total Tasks: {len(self.tasks)}")
        print(f"  ⏳ Pending: {len(pending_tasks)}")
        print(f"  ✅ Completed: {len(completed_tasks)}")
        print(f"  🔴 Urgent: {len(urgent_tasks)}")
        print()
        
        if urgent_tasks:
            print("🚨 URGENT TASKS:")
            for task in urgent_tasks:
                print(f"  • {task.name}")
            print()
        
        if pending_tasks:
            print("📋 RECENT PENDING TASKS:")
            for task in pending_tasks[:5]:  # Show first 5
                priority_icon = {"urgent": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(task.priority, "⚪")
                print(f"  {priority_icon} {task.name}")
        print(f"{'='*60}")
    
    def show_tasks(self):
        """Display all tasks with detailed information."""
        if not self.tasks:
            print(f"\n📋 No tasks found, {self.user_name}. You're all caught up!")
            return

        pending_tasks = [t for t in self.tasks if t.status == "pending"]
        completed_tasks = [t for t in self.tasks if t.status == "completed"]
        
        print(f"\n{'='*60}")
        print(f"📋 Task Overview - {self.user_name}")
        print(f"{'='*60}")
        
        if pending_tasks:
            print("⏳ PENDING TASKS:")
            for i, task in enumerate(pending_tasks, 1):
                priority_icon = {"urgent": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(task.priority, "⚪")
                category_icon = {"work": "💼", "personal": "👤", "learning": "📚", "health": "🏃", "general": "📝"}.get(task.category, "📝")
                
                print(f"\n{i}. {priority_icon} {category_icon} {task.name}")
                print(f"   📝 {task.description}")
                print(f"   🏷️  Category: {task.category.title()}")
                print(f"   ⚡ Priority: {task.priority.title()}")
                if task.deadline:
                    print(f"   ⏰ Deadline: {task.deadline}")
                if task.estimated_duration:
                    print(f"   ⏱️  Estimated: {task.estimated_duration} minutes")
                print(f"   📅 Created: {datetime.fromisoformat(task.created_at).strftime('%Y-%m-%d %H:%M')}")
        
        if completed_tasks:
            print(f"\n✅ COMPLETED TASKS ({len(completed_tasks)}):")
            for task in completed_tasks[-5:]:  # Show last 5 completed
                completed_date = datetime.fromisoformat(task.completed_at).strftime('%Y-%m-%d %H:%M') if task.completed_at else "Unknown"
                print(f"  ✓ {task.name} - Completed: {completed_date}")
        
        print(f"\n{'='*60}")
    
    def schedule_task(self, description, priority="medium", category="general", deadline=None, duration=None):
        """Create a new task or reminder."""
        # Check for duplicates
        for existing in self.tasks:
            if (isinstance(existing, Task) and 
                existing.name.lower() == description.lower() and 
                existing.status != "completed"):
                print(f"\n⚠️  Task '{description}' already exists, {self.user_name}.")
                return
        
        task = Task(
            name=description,
            description=description,
            priority=priority,
            category=category,
            deadline=deadline
        )
        
        if duration:
            task.estimated_duration = duration
        
        self.tasks.append(task)
        self._dedupe_tasks()
        self.save_memory()
        
        priority_icon = {"urgent": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(priority, "⚪")
        print(f"\n✅ Task scheduled successfully, {self.user_name}.")
        print(f"📝 {priority_icon} {description}")
        print(f"🏷️  Category: {category.title()}")
        if deadline:
            print(f"⏰ Deadline: {deadline}")
        if duration:
            print(f"⏱️  Estimated duration: {duration} minutes")
    
    def complete_task(self, task_index):
        """Mark a task as completed."""
        try:
            task = self.tasks[task_index - 1]
            if task.status == "completed":
                print(f"\n✅ Task '{task.name}' is already completed, {self.user_name}.")
                return

            task.status = "completed"
            task.completed_at = datetime.now().isoformat()
            
            self.save_memory()
            
            print(f"\n🎉 Excellent work, {self.user_name}!")
            print(f"✅ Completed: {task.name}")
            print(f"⏰ Finished at: {datetime.now().strftime('%H:%M')}")
            
            # Check if there are more pending tasks
            pending_count = len([t for t in self.tasks if t.status == "pending"])
            if pending_count > 0:
                print(f"📋 {pending_count} task(s) remaining.")
            else:
                print("🎯 All tasks completed! You're doing great!")
            
        except IndexError:
            print(f"\n❌ Invalid task number, {self.user_name}. Please check the task list.")
        except Exception as e:
            print(f"\n❌ Error completing task: {e}")
    
    def delete_task(self, task_index):
        """Remove a task from the list."""
        try:
            task = self.tasks[task_index - 1]
            task_name = task.name
            del self.tasks[task_index - 1]
            self.save_memory()
            print(f"\n🗑️  Task '{task_name}' has been removed, {self.user_name}.")
        except IndexError:
            print(f"\n❌ Invalid task number, {self.user_name}.")
        except Exception as e:
            print(f"\n❌ Error deleting task: {e}")
    
    def update_task_priority(self, task_index, new_priority):
        """Update the priority of a task."""
        try:
            if new_priority not in ["low", "medium", "high", "urgent"]:
                print(f"\n❌ Invalid priority level, {self.user_name}. Use: low, medium, high, or urgent.")
                return
                
            task = self.tasks[task_index - 1]
            old_priority = task.priority
            task.priority = new_priority
            self.save_memory()
            
            priority_icon = {"urgent": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(new_priority, "⚪")
            print(f"\n✅ Priority updated for '{task.name}', {self.user_name}.")
            print(f"📊 Changed from {old_priority} to {priority_icon} {new_priority}")
            
        except IndexError:
            print(f"\n❌ Invalid task number, {self.user_name}.")
        except Exception as e:
            print(f"\n❌ Error updating priority: {e}")
    
    def show_system_info(self):
        """Display detailed system information."""
        print(f"\n{'='*60}")
        print(f"🖥️  System Information - {self.name}")
        print(f"{'='*60}")
        print(f"🤖 AI Assistant: {self.name} v{self.version}")
        print(f"👤 User: {self.user_name}")
        print(f"⏰ Uptime: {self.system_info['uptime']}")
        print()
        print("💻 SYSTEM DETAILS:")
        print(f"  🖥️  Operating System: {self.system_info['os']}")
        print(f"  🏠 Hostname: {self.system_info['hostname']}")
        print(f"  🐍 Python Version: {self.system_info['python_version']}")
        print()
        print("📊 MEMORY USAGE:")
        print(f"  💾 Tasks Stored: {len(self.tasks)}")
        print(f"  💬 Conversations: {len(self.conversation_history)}")
        print(f"  📁 Memory File: {self.memory_file}")
        print()
        print("⚙️  PREFERENCES:")
        for key, value in self.preferences.items():
            print(f"  {key.replace('_', ' ').title()}: {value}")
        print(f"{'='*60}")
    
    def show_settings(self):
        """Display and manage user preferences."""
        print(f"\n{'='*60}")
        print(f"⚙️  Settings - {self.name}")
        print(f"{'='*60}")
        print("Current Preferences:")
        for key, value in self.preferences.items():
            print(f"  {key.replace('_', ' ').title()}: {value}")
        print()
        print("Available Settings:")
        print("  communication_style: professional, casual, formal")
        print("  notification_level: low, medium, high")
        print("  auto_suggestions: true, false")
        print("  voice_enabled: true, false")
        print("  dark_mode: true, false")
        print()
        print("To change a setting, use: settings <key> <value>")
        print("Example: settings communication_style casual")
        print(f"{'='*60}")
    
    def update_setting(self, key, value):
        """Update a user preference."""
        if key not in self.preferences:
            print(f"\n❌ Unknown setting: {key}")
            return
        
        # Validate values
        if key == "communication_style" and value not in ["professional", "casual", "formal"]:
            print(f"\n❌ Invalid value for {key}. Use: professional, casual, or formal")
            return
        elif key == "notification_level" and value not in ["low", "medium", "high"]:
            print(f"\n❌ Invalid value for {key}. Use: low, medium, or high")
            return
        elif key in ["auto_suggestions", "voice_enabled", "dark_mode"]:
            if value.lower() in ["true", "1", "yes", "on"]:
                value = True
            elif value.lower() in ["false", "0", "no", "off"]:
                value = False
            else:
                print(f"\n❌ Invalid value for {key}. Use: true or false")
                return
        
        old_value = self.preferences[key]
        self.preferences[key] = value
        self.save_memory()
        
        print(f"\n✅ Setting updated, {self.user_name}.")
        print(f"📊 {key.replace('_', ' ').title()}: {old_value} → {value}")
    
    def show_memory(self):
        """Display recent conversation history."""
        if not self.conversation_history:
            print(f"\n💬 No conversation history found, {self.user_name}.")
            return
            
        print(f"\n{'='*60}")
        print(f"💬 Recent Conversations - {self.name}")
        print(f"{'='*60}")
        
        # Show last 10 conversations
        recent_conversations = self.conversation_history[-10:]
        for i, msg in enumerate(recent_conversations, 1):
            role = "🤖 JARVIS" if msg['role'] == "assistant" else f"👤 {self.user_name}"
            content = msg['content'][:100] + "..." if len(msg['content']) > 100 else msg['content']
            print(f"\n{i}. {role}: {content}")
        
        print(f"\n💾 Total conversations stored: {len(self.conversation_history)}")
        print(f"{'='*60}")
    
    def get_current_time(self):
        """Display current time and date."""
        now = datetime.now()
        print(f"\n⏰ Current Time: {now.strftime('%A, %B %d, %Y at %H:%M:%S')}")
        print(f"🌍 Timezone: {now.astimezone().tzinfo}")
    
    def parse_natural_language_task(self, message):
        """Parse natural language to extract task information."""
        # Common task creation patterns
        patterns = [
            r"(?:remind me to|remember to|i need to|i should|i want to|schedule|add task) (.+?)(?: for | in | within )?(\d+)\s*(?:minutes?|hours?|days?)",
            r"(?:create|add|make|set) (?:a |an )?task (?:to |for )?(.+?)(?: for | in | within )?(\d+)\s*(?:minutes?|hours?|days?)",
            r"(?:todo|task|reminder): (.+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message.lower())
            if match:
                activity = match.group(1).strip()
                duration = match.group(2) if len(match.groups()) > 1 else None
                
                # Determine priority based on keywords
                priority = "medium"
                if any(word in activity.lower() for word in ["urgent", "asap", "immediately", "critical"]):
                    priority = "urgent"
                elif any(word in activity.lower() for word in ["important", "priority", "soon"]):
                    priority = "high"
                elif any(word in activity.lower() for word in ["later", "sometime", "when possible"]):
                    priority = "low"
                
                # Determine category based on keywords
                category = "general"
                if any(word in activity.lower() for word in ["work", "meeting", "project", "deadline", "email"]):
                    category = "work"
                elif any(word in activity.lower() for word in ["study", "learn", "read", "course", "book"]):
                    category = "learning"
                elif any(word in activity.lower() for word in ["exercise", "workout", "run", "gym", "health"]):
                    category = "health"
                elif any(word in activity.lower() for word in ["buy", "shop", "grocery", "personal"]):
                    category = "personal"
                
                return {
                    "name": activity.capitalize(),
                    "description": activity,
                    "priority": priority,
                    "category": category,
                    "duration": int(duration) if duration else None
                }
        
        return None
    
    def process_command(self, command):
        """Process user commands and route to appropriate handlers."""
        command = command.strip()
        
        if not command:
            return
        
        # Handle system commands
        if command.lower() == "exit":
            self.save_memory()
            print(f"\n👋 Goodbye, {self.user_name}. JARVIS shutting down.")
            sys.exit(0)
        elif command.lower() == "help":
            self.get_help()
        elif command.lower() == "status":
            self.show_status()
        elif command.lower() == "tasks":
            self.show_tasks()
        elif command.lower() == "system":
            self.show_system_info()
        elif command.lower() == "settings":
            self.show_settings()
        elif command.lower() == "clear":
            self.conversation_history = []
            self.save_memory()
            print(f"\n🧹 Conversation history cleared, {self.user_name}.")
        elif command.lower() == "memory":
            self.show_memory()
        elif command.lower() == "time":
            self.get_current_time()
        elif command.startswith("schedule "):
            task_description = command[9:].strip()
            if task_description:
                self.schedule_task(task_description)
            else:
                print(f"\n❌ Please provide a task description, {self.user_name}.")
        elif command.startswith("complete "):
            try:
                task_num = int(command.split()[1])
                self.complete_task(task_num)
            except (IndexError, ValueError):
                print(f"\n❌ Please provide a valid task number, {self.user_name}.")
        elif command.startswith("delete "):
            try:
                task_num = int(command.split()[1])
                self.delete_task(task_num)
            except (IndexError, ValueError):
                print(f"\n❌ Please provide a valid task number, {self.user_name}.")
        elif command.startswith("priority "):
            try:
                parts = command.split()
                task_num = int(parts[1])
                new_priority = parts[2].lower()
                self.update_task_priority(task_num, new_priority)
            except (IndexError, ValueError):
                print(f"\n❌ Please provide a valid task number and priority, {self.user_name}.")
        elif command.startswith("settings "):
            try:
                parts = command.split(" ", 2)
                if len(parts) >= 3:
                    key = parts[1]
                    value = parts[2]
                    self.update_setting(key, value)
                else:
                    print(f"\n❌ Please provide both setting name and value, {self.user_name}.")
            except Exception as e:
                print(f"\n❌ Error updating setting: {e}")
        else:
            # Handle natural language input
            self.chat(command)
    
    def chat(self, message):
        """Handle natural language conversation with the user."""
        try:
            # Check if this is a task creation request
            task_data = self.parse_natural_language_task(message)
            if task_data:
                self.schedule_task(
                    task_data["name"],
                    task_data["priority"],
                    task_data["category"],
                    duration=task_data.get("duration")
                )
                return
            
            # Add user message to history
            self.conversation_history.append({"role": "user", "content": message})
            
            if not self.llm:
                print(f"\n🤖 {self.name}: I apologize, but my AI capabilities are currently unavailable.")
                print("I can still help you with task management and system commands.")
                return
            
            # Create context for the AI
            context = f"""You are JARVIS, the AI assistant from Iron Man. You are sophisticated, helpful, and slightly witty. You assist {self.user_name} with various tasks and provide intelligent responses.

Your personality:
- Professional but friendly
- Helpful and resourceful
- Slightly witty and charming
- Knowledgeable about technology and productivity
- Respectful and supportive

Current context:
- User: {self.user_name}
- Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}
- Pending tasks: {len([t for t in self.tasks if t.status == 'pending'])}
- System: {self.system_info['os']}

Keep responses concise but helpful. You can suggest tasks, provide information, or have a conversation.
If the user asks for help with productivity, suggest specific tasks or improvements.

Recent conversation:"""
            
            for msg in self.conversation_history[-3:]:  # Use last 3 messages for context
                role = "User" if msg['role'] == "user" else "JARVIS"
                context += f"\n{role}: {msg['content']}"
            
            # Get response from AI
            print(f"\n🤖 {self.name}: ", end="")
            response = self.llm.invoke(context + f"\nJARVIS: ")
            
            # Add assistant response to history
            self.conversation_history.append({"role": "assistant", "content": response})
            
            # Save conversation
            self.save_memory()
            
        except Exception as e:
            print(f"\n❌ I apologize, {self.user_name}, but I encountered an error: {str(e)}")
            print("Please try again or use a system command.")

def main():
    """Main entry point for JARVIS."""
    jarvis = Jarvis()
    jarvis.greet()
    
    while True:
        try:
            user_input = input(f"\n👤 {jarvis.user_name}: ").strip()
            if user_input:
                jarvis.process_command(user_input)
        except KeyboardInterrupt:
            jarvis.save_memory()
            print(f"\n\n👋 Goodbye, {jarvis.user_name}. JARVIS shutting down.")
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")

if __name__ == "__main__":
    main()