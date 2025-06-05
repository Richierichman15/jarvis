# Daily Quest System for Jarvis

## Overview

The Daily Quest System is a comprehensive enhancement to the Jarvis life management application that provides:

- **Automated Daily Quest Generation** based on user goals and progress
- **3x Daily Notifications** (Morning, Evening, Night) via Firebase push notifications
- **XP and Skill Tree Integration** with quest completion rewards
- **3-Month Strategic Planning** with weekly milestones and daily focus areas
- **Intelligent Quest Personalization** based on user stats and preferences

## Features

### 🎯 Daily Quest Generation

The system automatically generates 3-4 daily quests based on:
- **User's long-term goals** (from jarvis_memory.json)
- **Current week focus** from the 3-month plan
- **User's weakest stats** (challenge quests)
- **Foundation activities** (health, personal growth)

**Quest Categories:**
- Financial (expense tracking, investment research, side hustles)
- Programming (coding practice, learning new concepts, building features)
- Health (exercise, meditation, meal prep)
- Personal Growth (journaling, learning, skill practice)
- Communication (networking, public speaking)

### 📅 3-Month Strategic Planning

Creates a comprehensive plan with:
- **Monthly Themes:**
  - Month 1: Foundation Building (habits, routines, basic skills)
  - Month 2: Skill Advancement (technical skills, projects, networking)  
  - Month 3: Growth & Optimization (wealth building, advanced skills, leadership)
- **Weekly Goals** aligned with monthly themes
- **Daily Quest Focus Areas** that rotate to support weekly objectives

### 🔔 Smart Notification System

**Three daily notifications:**
- **7:00 AM** - Morning Quest Assignment with potential XP
- **6:00 PM** - Evening Progress Check with completion stats
- **9:00 PM** - Night Reflection with tomorrow's preview

### ⚡ Enhanced XP System

- **Base XP** from quest completion (10-500 XP based on difficulty)
- **Skill XP** that feeds into the skill tree system
- **Difficulty Multipliers:**
  - E-Rank: 1x multiplier (10 base XP, 5 skill XP)
  - D-Rank: 1.5x multiplier (25 base XP, 10 skill XP)
  - C-Rank: 2x multiplier (50 base XP, 15 skill XP)
  - B-Rank: 3x multiplier (100 base XP, 25 skill XP)
  - A-Rank: 4x multiplier (200 base XP, 40 skill XP)
  - S-Rank: 6x multiplier (500 base XP, 75 skill XP)

## Installation

### Prerequisites

1. Python 3.8+
2. Firebase project with Push Notification setup
3. Ollama with Mistral model (for AI quest generation)

### Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Firebase:**
   Create a `.env` file with your Firebase credentials:
   ```env
   FIREBASE_TYPE=service_account
   FIREBASE_PROJECT_ID=your-project-id
   FIREBASE_PRIVATE_KEY_ID=your-private-key-id
   FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
   FIREBASE_CLIENT_EMAIL=your-service-account@your-project.iam.gserviceaccount.com
   FIREBASE_CLIENT_ID=your-client-id
   FIREBASE_AUTH_URI=https://accounts.google.com/o/oauth2/auth
   FIREBASE_TOKEN_URI=https://oauth2.googleapis.com/token
   FIREBASE_AUTH_PROVIDER_X509_CERT_URL=https://www.googleapis.com/oauth2/v1/certs
   FIREBASE_CLIENT_X509_CERT_URL=https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project.iam.gserviceaccount.com
   VAPIDKEY=your-vapid-key
   ```

3. **Start the application:**
   ```bash
   python app.py
   ```

## Usage

### Accessing the Daily Quest System

1. **Main Menu** → "Strategic Planning"
2. **Or direct URL:** `http://localhost:5002/planning`

### Key Actions

#### Generate a 3-Month Plan
```javascript
// Via Web Interface
Click "🎯 Generate New Plan" button

// Via API
POST /api/three-month-plan/generate
```

#### Generate Daily Quests
```javascript
// Via Web Interface  
Click "📋 Generate Daily Quests" button

// Via API
POST /api/daily-quests/generate
```

#### Complete Quests with Enhanced XP
```javascript
// Via API
POST /api/complete_quest_advanced
{
    "task_index": 1
}
```

#### Manual Notification Testing
```javascript
// Via API
POST /api/notification/manual
{
    "type": "morning"  // or "evening" or "night"
}
```

## API Endpoints

### Daily Quest System

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/daily-quests/generate` | POST | Generate new daily quests |
| `/api/daily-quests/stats` | GET | Get daily quest statistics |
| `/api/complete_quest_advanced` | POST | Complete quest with XP rewards |
| `/api/notification/manual` | POST | Send manual notification |

### 3-Month Planning

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/three-month-plan/generate` | POST | Generate new 3-month plan |
| `/api/three-month-plan` | GET | Get current 3-month plan |

## File Structure

```
jarvis/
├── daily_quest_system.py          # Core quest generation system
├── jarvis.py                       # Enhanced with skill XP tracking
├── templates/
│   ├── planning.html               # Strategic planning dashboard
│   ├── notification.html           # Enhanced notification display
│   └── skills.html                 # Updated with progress tracking
├── skills_config.json              # Skill tree configuration
└── static/js/firebase-init.js      # Firebase notification handling

three_month_plan.json               # Generated strategic plan
jarvis_memory.json                  # User data with goals and progress
requirements.txt                    # Updated dependencies
```

## Configuration

### Quest Templates

Modify `quest_templates` in `daily_quest_system.py` to customize:
- Quest categories
- Difficulty levels
- XP rewards
- Skill associations
- Time estimates

### Notification Schedule

Adjust notification times in `daily_quest_system.py`:
```python
class NotificationTime(Enum):
    MORNING = "07:00"  # Change to your preferred time
    EVENING = "18:00"  # Change to your preferred time
    NIGHT = "21:00"    # Change to your preferred time
```

### Skill Tree Integration

Configure skill progression in `jarvis/skills_config.json`:
- Add new skills
- Set unlock requirements
- Define skill categories
- Configure XP thresholds

## User Goals Integration

The system reads user goals from `jarvis_memory.json`. Current supported goals:

1. **Financial Independence**
   - Emergency fund building
   - Investment portfolio development
   
2. **Programming Language Proficiency**
   - Python, JavaScript, and additional languages
   - Advanced course completion
   
3. **Physical Peak Performance**
   - Fitness metrics and health optimization
   
4. **Master Public Speaking**
   - Presentation skills and confidence building

## Troubleshooting

### Firebase Issues
- Verify all environment variables are set correctly
- Check Firebase project permissions
- Ensure VAPID key is properly configured

### Notification Not Working
- Check browser notification permissions
- Verify FCM token is saved in session
- Test with manual notification endpoint

### Quest Generation Issues
- Ensure `jarvis_memory.json` contains user goals
- Check Ollama/Mistral model is running
- Verify skill configuration file exists

### XP Not Updating
- Check task has required metadata (base_xp, skills, etc.)
- Verify `complete_quest_advanced` endpoint is being used
- Ensure user stats are being saved properly

## Future Enhancements

- **Advanced AI Quest Generation** with more sophisticated personalization
- **Achievement System** with milestone rewards
- **Social Features** for sharing progress and competing with friends
- **Integration with Calendar Apps** for better scheduling
- **Mobile App** with native notifications
- **Voice Commands** for quest management
- **Analytics Dashboard** with detailed progress tracking

## Contributing

To add new quest categories or enhance the system:

1. Add quest templates to `quest_templates` in `daily_quest_system.py`
2. Update skill configuration in `skills_config.json`
3. Add corresponding API endpoints if needed
4. Update notification templates as required
5. Test with manual quest generation and completion

## License

This enhanced daily quest system is part of the Jarvis life management application.