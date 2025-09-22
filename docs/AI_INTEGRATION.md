# AI Integration Guide

## Goal Generation

### 1. User Input Processing
- **Location**: `goal_manager.py`
- **Process**:
  1. Collects user preferences and goals
  2. Structures them using `desires_structure.json`
  3. Converts into structured goals

### 2. Quest Generation
- **Location**: `goal_manager.py`
- **Process**:
  1. Takes structured goals
  2. Generates daily quests using AI
  3. Stores in `daily_quests.json`

### 3. AI Prompt Structure
```python
{
  "user_goals": ["Goal 1", "Goal 2"],
  "timeframe": "daily",
  "difficulty": "beginner",
  "preferences": {
    "time_required": "30 minutes",
    "activity_type": ["physical", "mental", "spiritual"]
  }
}
```

## Key Functions

### `generate_quests(goals, count=3)`
- **Input**: List of goals, number of quests to generate
- **Output**: List of quest objects
- **Process**:
  - Analyzes goals
  - Generates relevant quests
  - Ensures variety in activities

### `evaluate_quest_completion(quest_id, user_input)`
- **Input**: Quest ID, user's completion data
- **Output**: Success status, reward, next steps
- **Process**:
  - Validates completion
  - Awards experience points
  - Suggests follow-up quests
