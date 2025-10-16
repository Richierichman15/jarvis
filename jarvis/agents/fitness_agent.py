#!/usr/bin/env python3
"""
FitnessAgent - Specialized agent for fitness and workout management

This agent handles all fitness-related tasks including workout recommendations,
exercise tracking, fitness goals, and health monitoring.
"""

import asyncio
import logging
import json
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path

from .agent_base import AgentBase, AgentCapability, TaskRequest, TaskResponse

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FitnessAgent(AgentBase):
    """Specialized agent for fitness operations."""
    
    def __init__(self, **kwargs):
        super().__init__(
            name="FitnessAgent",
            capabilities=[AgentCapability.FITNESS],
            version="1.0.0",
            **kwargs
        )
        
        # Fitness-specific configuration
        self.fitness_config = {
            "default_workout_duration": 45,  # minutes
            "max_workout_duration": 120,
            "supported_muscle_groups": [
                "chest", "back", "shoulders", "arms", "legs", 
                "core", "glutes", "cardio", "full_body"
            ],
            "difficulty_levels": ["beginner", "intermediate", "advanced"]
        }
        
        # Fitness state
        self.workouts = []
        self.exercises = []
        self.user_progress = {}
        self.fitness_goals = []
        self.workout_history = []
        
        self.logger = logging.getLogger("agent.fitness")
    
    def _register_task_handlers(self):
        """Register fitness task handlers."""
        self.register_task_handler("list_workouts", self._handle_list_workouts)
        self.register_task_handler("search_workouts", self._handle_search_workouts)
        self.register_task_handler("get_workout_plan", self._handle_get_workout_plan)
        self.register_task_handler("create_workout", self._handle_create_workout)
        self.register_task_handler("start_workout", self._handle_start_workout)
        self.register_task_handler("complete_workout", self._handle_complete_workout)
        self.register_task_handler("get_exercises", self._handle_get_exercises)
        self.register_task_handler("track_exercise", self._handle_track_exercise)
        self.register_task_handler("get_progress", self._handle_get_progress)
        self.register_task_handler("set_goal", self._handle_set_goal)
        self.register_task_handler("get_goals", self._handle_get_goals)
        self.register_task_handler("get_workout_history", self._handle_get_workout_history)
        self.register_task_handler("get_recommendations", self._handle_get_recommendations)
        self.register_task_handler("calculate_calories", self._handle_calculate_calories)
        self.register_task_handler("get_fitness_stats", self._handle_get_fitness_stats)
    
    async def _initialize(self):
        """Initialize fitness-specific resources."""
        try:
            # Load workout database
            await self._load_workout_database()
            
            # Load exercise database
            await self._load_exercise_database()
            
            # Initialize user progress tracking
            await self._initialize_progress_tracking()
            
            self.logger.info("✅ FitnessAgent initialized successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize FitnessAgent: {e}")
            raise
    
    async def _cleanup(self):
        """Cleanup fitness resources."""
        try:
            # Save user progress
            await self._save_user_progress()
            
            self.logger.info("✅ FitnessAgent cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during FitnessAgent cleanup: {e}")
    
    async def _load_workout_database(self):
        """Load workout database."""
        self.logger.info("💪 Loading workout database...")
        
        # Sample workout database
        self.workouts = [
            {
                "id": "workout_001",
                "name": "Chest Day",
                "description": "Complete chest workout for muscle building",
                "muscle_groups": ["chest", "shoulders", "triceps"],
                "difficulty": "intermediate",
                "duration_minutes": 60,
                "exercises": [
                    {
                        "name": "Bench Press",
                        "sets": 4,
                        "reps": "8-12",
                        "weight": "bodyweight + 50-100%",
                        "rest_seconds": 90
                    },
                    {
                        "name": "Incline Dumbbell Press",
                        "sets": 3,
                        "reps": "10-15",
                        "weight": "moderate",
                        "rest_seconds": 60
                    },
                    {
                        "name": "Push-ups",
                        "sets": 3,
                        "reps": "15-25",
                        "weight": "bodyweight",
                        "rest_seconds": 45
                    }
                ],
                "calories_burned": 400,
                "equipment_needed": ["barbell", "dumbbells", "bench"]
            },
            {
                "id": "workout_002",
                "name": "Leg Day",
                "description": "Intense leg workout for strength and size",
                "muscle_groups": ["legs", "glutes"],
                "difficulty": "advanced",
                "duration_minutes": 75,
                "exercises": [
                    {
                        "name": "Squats",
                        "sets": 5,
                        "reps": "6-10",
                        "weight": "heavy",
                        "rest_seconds": 120
                    },
                    {
                        "name": "Deadlifts",
                        "sets": 4,
                        "reps": "5-8",
                        "weight": "heavy",
                        "rest_seconds": 120
                    },
                    {
                        "name": "Lunges",
                        "sets": 3,
                        "reps": "12-15 each leg",
                        "weight": "moderate",
                        "rest_seconds": 60
                    }
                ],
                "calories_burned": 600,
                "equipment_needed": ["barbell", "dumbbells"]
            },
            {
                "id": "workout_003",
                "name": "Back Day",
                "description": "Comprehensive back workout",
                "muscle_groups": ["back", "biceps"],
                "difficulty": "intermediate",
                "duration_minutes": 55,
                "exercises": [
                    {
                        "name": "Pull-ups",
                        "sets": 4,
                        "reps": "6-12",
                        "weight": "bodyweight",
                        "rest_seconds": 90
                    },
                    {
                        "name": "Bent-over Rows",
                        "sets": 4,
                        "reps": "8-12",
                        "weight": "moderate-heavy",
                        "rest_seconds": 75
                    },
                    {
                        "name": "Lat Pulldowns",
                        "sets": 3,
                        "reps": "10-15",
                        "weight": "moderate",
                        "rest_seconds": 60
                    }
                ],
                "calories_burned": 450,
                "equipment_needed": ["pull-up bar", "barbell", "cable machine"]
            },
            {
                "id": "workout_004",
                "name": "Cardio Blast",
                "description": "High-intensity cardio workout",
                "muscle_groups": ["cardio", "full_body"],
                "difficulty": "beginner",
                "duration_minutes": 30,
                "exercises": [
                    {
                        "name": "Jumping Jacks",
                        "sets": 3,
                        "reps": "30 seconds",
                        "weight": "bodyweight",
                        "rest_seconds": 30
                    },
                    {
                        "name": "Burpees",
                        "sets": 3,
                        "reps": "10-15",
                        "weight": "bodyweight",
                        "rest_seconds": 45
                    },
                    {
                        "name": "Mountain Climbers",
                        "sets": 3,
                        "reps": "30 seconds",
                        "weight": "bodyweight",
                        "rest_seconds": 30
                    }
                ],
                "calories_burned": 300,
                "equipment_needed": []
            }
        ]
        
        await asyncio.sleep(0.1)  # Simulate loading time
        self.logger.info(f"✅ Loaded {len(self.workouts)} workouts")
    
    async def _load_exercise_database(self):
        """Load exercise database."""
        self.logger.info("🏃 Loading exercise database...")
        
        # Sample exercise database
        self.exercises = [
            {
                "id": "exercise_001",
                "name": "Push-ups",
                "muscle_groups": ["chest", "shoulders", "triceps"],
                "difficulty": "beginner",
                "equipment": "none",
                "instructions": [
                    "Start in plank position",
                    "Lower body until chest nearly touches floor",
                    "Push back up to starting position",
                    "Keep core tight throughout"
                ],
                "tips": [
                    "Keep body in straight line",
                    "Don't let hips sag",
                    "Breathe out on the way up"
                ]
            },
            {
                "id": "exercise_002",
                "name": "Squats",
                "muscle_groups": ["legs", "glutes"],
                "difficulty": "beginner",
                "equipment": "none",
                "instructions": [
                    "Stand with feet shoulder-width apart",
                    "Lower body as if sitting back into chair",
                    "Go down until thighs parallel to floor",
                    "Push through heels to return to start"
                ],
                "tips": [
                    "Keep chest up",
                    "Don't let knees cave in",
                    "Weight on heels"
                ]
            },
            {
                "id": "exercise_003",
                "name": "Plank",
                "muscle_groups": ["core", "shoulders"],
                "difficulty": "beginner",
                "equipment": "none",
                "instructions": [
                    "Start in push-up position",
                    "Lower to forearms",
                    "Keep body in straight line",
                    "Hold position"
                ],
                "tips": [
                    "Engage core muscles",
                    "Don't let hips sag",
                    "Breathe normally"
                ]
            }
        ]
        
        await asyncio.sleep(0.1)  # Simulate loading time
        self.logger.info(f"✅ Loaded {len(self.exercises)} exercises")
    
    async def _initialize_progress_tracking(self):
        """Initialize user progress tracking."""
        self.logger.info("📊 Initializing progress tracking...")
        
        # Sample user progress
        self.user_progress = {
            "total_workouts": 0,
            "total_calories_burned": 0,
            "workout_streak": 0,
            "favorite_muscle_groups": [],
            "personal_records": {},
            "last_workout": None
        }
        
        # Sample fitness goals
        self.fitness_goals = [
            {
                "id": "goal_001",
                "title": "Workout 3 times per week",
                "description": "Maintain consistent workout schedule",
                "target": 3,
                "current": 0,
                "unit": "workouts per week",
                "deadline": None,
                "status": "active"
            },
            {
                "id": "goal_002",
                "title": "Burn 2000 calories this week",
                "description": "Increase calorie burn through exercise",
                "target": 2000,
                "current": 0,
                "unit": "calories",
                "deadline": None,
                "status": "active"
            }
        ]
        
        await asyncio.sleep(0.1)  # Simulate initialization time
        self.logger.info("✅ Progress tracking initialized")
    
    async def _save_user_progress(self):
        """Save user progress to persistent storage."""
        self.logger.info("💾 Saving user progress...")
        await asyncio.sleep(0.1)  # Simulate saving time
        self.logger.info("✅ User progress saved")
    
    async def _handle_task(self, task: TaskRequest) -> TaskResponse:
        """Handle fitness tasks."""
        try:
            handler = self.task_handlers.get(task.task_type)
            if handler:
                return await handler(task)
            else:
                raise ValueError(f"Unknown fitness task type: {task.task_type}")
                
        except Exception as e:
            self.logger.error(f"Error handling fitness task {task.task_type}: {e}")
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )
    
    async def _handle_list_workouts(self, task: TaskRequest) -> TaskResponse:
        """Handle list workouts request."""
        try:
            muscle_group = task.parameters.get("muscle_group")
            difficulty = task.parameters.get("difficulty")
            duration = task.parameters.get("duration")
            
            filtered_workouts = self.workouts
            
            # Filter by muscle group
            if muscle_group:
                filtered_workouts = [
                    w for w in filtered_workouts 
                    if muscle_group.lower() in [mg.lower() for mg in w["muscle_groups"]]
                ]
            
            # Filter by difficulty
            if difficulty:
                filtered_workouts = [
                    w for w in filtered_workouts 
                    if w["difficulty"].lower() == difficulty.lower()
                ]
            
            # Filter by duration
            if duration:
                max_duration = int(duration)
                filtered_workouts = [
                    w for w in filtered_workouts 
                    if w["duration_minutes"] <= max_duration
                ]
            
            result = {
                "workouts": filtered_workouts,
                "total_workouts": len(self.workouts),
                "filtered_workouts": len(filtered_workouts),
                "filters": {
                    "muscle_group": muscle_group,
                    "difficulty": difficulty,
                    "duration": duration
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
    
    async def _handle_search_workouts(self, task: TaskRequest) -> TaskResponse:
        """Handle search workouts request."""
        try:
            query = task.parameters.get("query", "").lower()
            
            if not query:
                return TaskResponse(
                    task_id=task.task_id,
                    agent_id=self.agent_id,
                    success=False,
                    error="Search query is required"
                )
            
            # Search in workout names, descriptions, and muscle groups
            matching_workouts = []
            for workout in self.workouts:
                if (query in workout["name"].lower() or 
                    query in workout["description"].lower() or
                    any(query in mg.lower() for mg in workout["muscle_groups"])):
                    matching_workouts.append(workout)
            
            result = {
                "query": query,
                "workouts": matching_workouts,
                "total_found": len(matching_workouts)
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
    
    async def _handle_get_workout_plan(self, task: TaskRequest) -> TaskResponse:
        """Handle get workout plan request."""
        try:
            days_per_week = task.parameters.get("days_per_week", 3)
            focus_areas = task.parameters.get("focus_areas", ["full_body"])
            difficulty = task.parameters.get("difficulty", "intermediate")
            
            # Generate workout plan
            workout_plan = []
            
            if days_per_week == 3:
                # 3-day split
                workout_plan = [
                    {"day": 1, "workout": "Chest Day", "muscle_groups": ["chest", "shoulders", "triceps"]},
                    {"day": 2, "workout": "Leg Day", "muscle_groups": ["legs", "glutes"]},
                    {"day": 3, "workout": "Back Day", "muscle_groups": ["back", "biceps"]}
                ]
            elif days_per_week == 4:
                # 4-day split
                workout_plan = [
                    {"day": 1, "workout": "Chest Day", "muscle_groups": ["chest", "shoulders", "triceps"]},
                    {"day": 2, "workout": "Leg Day", "muscle_groups": ["legs", "glutes"]},
                    {"day": 3, "workout": "Back Day", "muscle_groups": ["back", "biceps"]},
                    {"day": 4, "workout": "Cardio Blast", "muscle_groups": ["cardio", "full_body"]}
                ]
            else:
                # Default to full body workouts
                for day in range(1, days_per_week + 1):
                    workout_plan.append({
                        "day": day,
                        "workout": "Full Body Workout",
                        "muscle_groups": ["full_body"]
                    })
            
            result = {
                "workout_plan": workout_plan,
                "days_per_week": days_per_week,
                "focus_areas": focus_areas,
                "difficulty": difficulty,
                "total_workouts": len(workout_plan)
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
    
    async def _handle_create_workout(self, task: TaskRequest) -> TaskResponse:
        """Handle create workout request."""
        try:
            name = task.parameters.get("name")
            description = task.parameters.get("description", "")
            muscle_groups = task.parameters.get("muscle_groups", [])
            exercises = task.parameters.get("exercises", [])
            
            if not name:
                return TaskResponse(
                    task_id=task.task_id,
                    agent_id=self.agent_id,
                    success=False,
                    error="Workout name is required"
                )
            
            new_workout = {
                "id": f"workout_{len(self.workouts) + 1:03d}",
                "name": name,
                "description": description,
                "muscle_groups": muscle_groups,
                "difficulty": task.parameters.get("difficulty", "intermediate"),
                "duration_minutes": task.parameters.get("duration_minutes", 45),
                "exercises": exercises,
                "calories_burned": task.parameters.get("calories_burned", 300),
                "equipment_needed": task.parameters.get("equipment_needed", []),
                "created_at": datetime.now().isoformat()
            }
            
            self.workouts.append(new_workout)
            
            result = {
                "message": f"Workout '{name}' created successfully",
                "workout": new_workout
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
    
    async def _handle_start_workout(self, task: TaskRequest) -> TaskResponse:
        """Handle start workout request."""
        try:
            workout_id = task.parameters.get("workout_id")
            
            workout = next((w for w in self.workouts if w["id"] == workout_id), None)
            
            if not workout:
                return TaskResponse(
                    task_id=task.task_id,
                    agent_id=self.agent_id,
                    success=False,
                    error=f"Workout {workout_id} not found"
                )
            
            # Create workout session
            workout_session = {
                "id": f"session_{len(self.workout_history) + 1:03d}",
                "workout_id": workout_id,
                "workout_name": workout["name"],
                "started_at": datetime.now().isoformat(),
                "status": "in_progress",
                "exercises_completed": 0,
                "total_exercises": len(workout["exercises"])
            }
            
            self.workout_history.append(workout_session)
            
            result = {
                "message": f"Started workout: {workout['name']}",
                "workout_session": workout_session,
                "workout": workout
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
    
    async def _handle_complete_workout(self, task: TaskRequest) -> TaskResponse:
        """Handle complete workout request."""
        try:
            session_id = task.parameters.get("session_id")
            
            session = next((s for s in self.workout_history if s["id"] == session_id), None)
            
            if not session:
                return TaskResponse(
                    task_id=task.task_id,
                    agent_id=self.agent_id,
                    success=False,
                    error=f"Workout session {session_id} not found"
                )
            
            # Update session
            session["status"] = "completed"
            session["completed_at"] = datetime.now().isoformat()
            session["exercises_completed"] = session["total_exercises"]
            
            # Update user progress
            self.user_progress["total_workouts"] += 1
            self.user_progress["workout_streak"] += 1
            self.user_progress["last_workout"] = session["completed_at"]
            
            # Add calories burned
            workout = next((w for w in self.workouts if w["id"] == session["workout_id"]), None)
            if workout:
                self.user_progress["total_calories_burned"] += workout.get("calories_burned", 0)
            
            result = {
                "message": f"Workout '{session['workout_name']}' completed!",
                "workout_session": session,
                "progress_update": {
                    "total_workouts": self.user_progress["total_workouts"],
                    "workout_streak": self.user_progress["workout_streak"],
                    "calories_burned": self.user_progress["total_calories_burned"]
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
    
    async def _handle_get_exercises(self, task: TaskRequest) -> TaskResponse:
        """Handle get exercises request."""
        try:
            muscle_group = task.parameters.get("muscle_group")
            difficulty = task.parameters.get("difficulty")
            equipment = task.parameters.get("equipment")
            
            filtered_exercises = self.exercises
            
            # Filter by muscle group
            if muscle_group:
                filtered_exercises = [
                    e for e in filtered_exercises 
                    if muscle_group.lower() in [mg.lower() for mg in e["muscle_groups"]]
                ]
            
            # Filter by difficulty
            if difficulty:
                filtered_exercises = [
                    e for e in filtered_exercises 
                    if e["difficulty"].lower() == difficulty.lower()
                ]
            
            # Filter by equipment
            if equipment:
                filtered_exercises = [
                    e for e in filtered_exercises 
                    if e["equipment"].lower() == equipment.lower()
                ]
            
            result = {
                "exercises": filtered_exercises,
                "total_exercises": len(self.exercises),
                "filtered_exercises": len(filtered_exercises),
                "filters": {
                    "muscle_group": muscle_group,
                    "difficulty": difficulty,
                    "equipment": equipment
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
    
    async def _handle_track_exercise(self, task: TaskRequest) -> TaskResponse:
        """Handle track exercise request."""
        try:
            exercise_name = task.parameters.get("exercise_name")
            sets = task.parameters.get("sets", 1)
            reps = task.parameters.get("reps", 10)
            weight = task.parameters.get("weight", 0)
            duration = task.parameters.get("duration", 0)  # seconds
            
            exercise_record = {
                "exercise_name": exercise_name,
                "sets": sets,
                "reps": reps,
                "weight": weight,
                "duration": duration,
                "timestamp": datetime.now().isoformat()
            }
            
            # Add to workout history if there's an active session
            active_session = next((s for s in self.workout_history if s["status"] == "in_progress"), None)
            if active_session:
                if "exercise_records" not in active_session:
                    active_session["exercise_records"] = []
                active_session["exercise_records"].append(exercise_record)
                active_session["exercises_completed"] += 1
            
            result = {
                "message": f"Tracked exercise: {exercise_name}",
                "exercise_record": exercise_record,
                "active_session": active_session is not None
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
            time_period = task.parameters.get("time_period", "all")  # week, month, all
            
            # Calculate progress based on time period
            if time_period == "week":
                # Get workouts from last 7 days
                week_ago = datetime.now() - timedelta(days=7)
                recent_workouts = [
                    w for w in self.workout_history 
                    if datetime.fromisoformat(w.get("completed_at", "1970-01-01")) > week_ago
                ]
            elif time_period == "month":
                # Get workouts from last 30 days
                month_ago = datetime.now() - timedelta(days=30)
                recent_workouts = [
                    w for w in self.workout_history 
                    if datetime.fromisoformat(w.get("completed_at", "1970-01-01")) > month_ago
                ]
            else:
                recent_workouts = self.workout_history
            
            progress_data = {
                "time_period": time_period,
                "total_workouts": len(recent_workouts),
                "total_calories_burned": sum(
                    next((w.get("calories_burned", 0) for w in self.workouts if w["id"] == session["workout_id"]), 0)
                    for session in recent_workouts
                ),
                "workout_streak": self.user_progress["workout_streak"],
                "favorite_muscle_groups": self.user_progress["favorite_muscle_groups"],
                "personal_records": self.user_progress["personal_records"],
                "last_workout": self.user_progress["last_workout"],
                "recent_workouts": recent_workouts[-10:]  # Last 10 workouts
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
    
    async def _handle_set_goal(self, task: TaskRequest) -> TaskResponse:
        """Handle set goal request."""
        try:
            title = task.parameters.get("title")
            description = task.parameters.get("description", "")
            target = task.parameters.get("target")
            unit = task.parameters.get("unit", "")
            deadline = task.parameters.get("deadline")
            
            if not title or not target:
                return TaskResponse(
                    task_id=task.task_id,
                    agent_id=self.agent_id,
                    success=False,
                    error="Title and target are required"
                )
            
            new_goal = {
                "id": f"goal_{len(self.fitness_goals) + 1:03d}",
                "title": title,
                "description": description,
                "target": target,
                "current": 0,
                "unit": unit,
                "deadline": deadline,
                "status": "active",
                "created_at": datetime.now().isoformat()
            }
            
            self.fitness_goals.append(new_goal)
            
            result = {
                "message": f"Goal '{title}' set successfully",
                "goal": new_goal
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
    
    async def _handle_get_goals(self, task: TaskRequest) -> TaskResponse:
        """Handle get goals request."""
        try:
            status_filter = task.parameters.get("status")
            
            if status_filter:
                filtered_goals = [g for g in self.fitness_goals if g["status"] == status_filter]
            else:
                filtered_goals = self.fitness_goals
            
            result = {
                "goals": filtered_goals,
                "total_goals": len(self.fitness_goals),
                "filtered_goals": len(filtered_goals),
                "status_counts": {
                    "active": len([g for g in self.fitness_goals if g["status"] == "active"]),
                    "completed": len([g for g in self.fitness_goals if g["status"] == "completed"]),
                    "paused": len([g for g in self.fitness_goals if g["status"] == "paused"])
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
    
    async def _handle_get_workout_history(self, task: TaskRequest) -> TaskResponse:
        """Handle get workout history request."""
        try:
            limit = task.parameters.get("limit", 20)
            
            # Sort by completion date (newest first)
            sorted_history = sorted(
                [w for w in self.workout_history if w["status"] == "completed"],
                key=lambda x: x.get("completed_at", ""),
                reverse=True
            )
            
            result = {
                "workout_history": sorted_history[:limit],
                "total_workouts": len(self.workout_history),
                "showing": min(limit, len(sorted_history))
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
    
    async def _handle_get_recommendations(self, task: TaskRequest) -> TaskResponse:
        """Handle get recommendations request."""
        try:
            user_level = task.parameters.get("user_level", "intermediate")
            available_equipment = task.parameters.get("available_equipment", [])
            time_available = task.parameters.get("time_available", 45)  # minutes
            
            # Generate recommendations based on user preferences
            recommendations = []
            
            # Filter workouts by user criteria
            suitable_workouts = [
                w for w in self.workouts 
                if (w["difficulty"] == user_level or 
                    (user_level == "beginner" and w["difficulty"] in ["beginner", "intermediate"]) or
                    (user_level == "advanced" and w["difficulty"] in ["intermediate", "advanced"]))
                and w["duration_minutes"] <= time_available
                and all(eq in available_equipment or eq == "none" for eq in w["equipment_needed"])
            ]
            
            # Recommend top 3 workouts
            recommendations = suitable_workouts[:3]
            
            result = {
                "recommendations": recommendations,
                "criteria": {
                    "user_level": user_level,
                    "available_equipment": available_equipment,
                    "time_available": time_available
                },
                "total_suitable": len(suitable_workouts)
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
    
    async def _handle_calculate_calories(self, task: TaskRequest) -> TaskResponse:
        """Handle calculate calories request."""
        try:
            exercise_name = task.parameters.get("exercise_name")
            duration = task.parameters.get("duration", 0)  # minutes
            weight = task.parameters.get("weight", 70)  # kg
            intensity = task.parameters.get("intensity", "moderate")  # low, moderate, high
            
            # Simple calorie calculation (this would be more sophisticated in reality)
            base_calories_per_minute = {
                "push-ups": 0.5,
                "squats": 0.6,
                "plank": 0.3,
                "jumping jacks": 0.8,
                "burpees": 1.2,
                "running": 1.0,
                "cycling": 0.7
            }
            
            intensity_multiplier = {
                "low": 0.7,
                "moderate": 1.0,
                "high": 1.3
            }
            
            base_calories = base_calories_per_minute.get(exercise_name.lower(), 0.5)
            calories_per_minute = base_calories * intensity_multiplier.get(intensity, 1.0)
            total_calories = calories_per_minute * duration * (weight / 70)  # Normalize to 70kg
            
            result = {
                "exercise_name": exercise_name,
                "duration_minutes": duration,
                "weight_kg": weight,
                "intensity": intensity,
                "calories_burned": round(total_calories, 1),
                "calories_per_minute": round(calories_per_minute, 2)
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
    
    async def _handle_get_fitness_stats(self, task: TaskRequest) -> TaskResponse:
        """Handle get fitness stats request."""
        try:
            # Calculate comprehensive fitness statistics
            total_workouts = len([w for w in self.workout_history if w["status"] == "completed"])
            total_calories = sum(
                next((w.get("calories_burned", 0) for w in self.workouts if w["id"] == session["workout_id"]), 0)
                for session in self.workout_history
                if session["status"] == "completed"
            )
            
            # Calculate average workout duration
            completed_workouts = [w for w in self.workout_history if w["status"] == "completed"]
            if completed_workouts:
                avg_duration = sum(
                    next((w.get("duration_minutes", 0) for w in self.workouts if w["id"] == session["workout_id"]), 0)
                    for session in completed_workouts
                ) / len(completed_workouts)
            else:
                avg_duration = 0
            
            # Most popular muscle groups
            muscle_group_count = {}
            for session in completed_workouts:
                workout = next((w for w in self.workouts if w["id"] == session["workout_id"]), None)
                if workout:
                    for mg in workout["muscle_groups"]:
                        muscle_group_count[mg] = muscle_group_count.get(mg, 0) + 1
            
            favorite_muscle_groups = sorted(muscle_group_count.items(), key=lambda x: x[1], reverse=True)[:3]
            
            stats = {
                "total_workouts": total_workouts,
                "total_calories_burned": total_calories,
                "workout_streak": self.user_progress["workout_streak"],
                "average_workout_duration": round(avg_duration, 1),
                "favorite_muscle_groups": [mg[0] for mg in favorite_muscle_groups],
                "active_goals": len([g for g in self.fitness_goals if g["status"] == "active"]),
                "completed_goals": len([g for g in self.fitness_goals if g["status"] == "completed"]),
                "last_workout": self.user_progress["last_workout"],
                "workout_frequency": "3x per week" if total_workouts > 0 else "No workouts yet"
            }
            
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=stats
            )
            
        except Exception as e:
            return TaskResponse(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(e)
            )


if __name__ == "__main__":
    # Test the FitnessAgent
    async def test_fitness_agent():
        agent = FitnessAgent()
        
        try:
            await agent.start()
            print(f"✅ FitnessAgent started: {agent.get_info()}")
            
            # Test a task
            task = TaskRequest(
                task_id="test_001",
                agent_id=agent.agent_id,
                capability=AgentCapability.FITNESS,
                task_type="list_workouts",
                parameters={"muscle_group": "chest"}
            )
            
            response = await agent._handle_task(task)
            print(f"💪 Workouts response: {response.result}")
            
            # Simulate running for a bit
            await asyncio.sleep(5)
            
        finally:
            await agent.stop()
            print("✅ FitnessAgent stopped")
    
    asyncio.run(test_fitness_agent())
