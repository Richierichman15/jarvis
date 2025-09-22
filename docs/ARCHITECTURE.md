# Jarvis - Architecture Overview

## Core Components

### 1. Application Structure
```
jarvis/
├── api/                  # API endpoints and server code
├── data/                # Data storage (JSON files)
│   ├── daily_quests.json
│   ├── desires_structure.json
│   └── user_goals.json
├── static/              # Static files (CSS, JS, images)
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── app.js
│       └── quests.js
├── templates/           # HTML templates
│   ├── base.html
│   ├── index.html
│   └── quest.html
├── goal_manager.py      # Goal and quest generation logic
└── jarvis.py           # Main application logic
```

### 2. Data Flow
1. **User Onboarding**
   - User provides initial preferences and goals
   - System processes input through `goal_manager.py`
   - Creates structured data in `data/` directory

2. **Quest Generation**
   - Uses AI to generate quests based on user goals
   - Stores quests in `daily_quests.json`
   - Renders quests in the UI

3. **User Interaction**
   - User completes/fails quests
   - System updates progress and generates new quests
