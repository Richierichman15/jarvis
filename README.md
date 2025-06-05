# Jarvis System 🤖⚔️

**An RPG-inspired life management system that gamifies personal development and daily tasks.**

Transform your life into an epic quest with the Jarvis System - a powerful AI assistant that helps you level up through daily challenges, skill progression, and achievement unlocking, just like your favorite RPG games!

## 🎮 Features

### 🏆 RPG-Style Progression System
- **Character Stats**: Health, Intelligence, Strength, Wealth tracking
- **XP & Leveling**: Earn experience points and level up by completing quests
- **Rank System**: Progress from E-rank to S-rank Hunter
- **Skill Tree**: Unlock new abilities and specializations as you grow
- **Inventory System**: Collect rewards, artifacts, and resources

### 📋 Intelligent Quest System  
- **Daily Quests**: Auto-generated personalized challenges
- **Quest Categories**: Financial, Programming, Health, Personal Growth, Communication
- **Difficulty Scaling**: E, D, C, B, A, S rank quests with increasing rewards
- **3-Month Planning**: Long-term goal tracking with weekly milestones
- **Smart Recommendations**: AI-driven quest suggestions based on your weakest stats

### 🔔 Push Notification System
- **Firebase Integration**: Real-time push notifications across devices
- **Scheduled Reminders**: Morning quest assignments, evening progress checks, nightly reflections
- **Achievement Alerts**: Get notified when you level up or unlock new skills
- **Custom Notifications**: Personalized messages based on your progress

### 🌐 Modern Web Interface
- **Responsive Design**: Works seamlessly on desktop and mobile
- **Real-time Updates**: Live stats and progress tracking
- **Interactive Dashboard**: Comprehensive overview of your journey
- **Progress Visualization**: Beautiful charts and progress bars

## 🚀 Quick Start

### Local Development

1. **Clone the repository**:
```bash
git clone <repository-url>
cd jarvis
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Set up environment**:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Run the application**:
```bash
python app.py
```

5. **Open your browser**: Navigate to `http://localhost:8080`

### 🔥 Firebase Deployment

For detailed deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).

Quick deployment:
```bash
# Install Firebase CLI
npm install -g firebase-tools

# Login and initialize
firebase login
firebase init

# Deploy
firebase deploy
```

## 🏗️ Architecture

### 📁 Project Structure
```
jarvis/
├── jarvis/                 # Core system modules
│   ├── api/               # API server and endpoints
│   ├── models/            # AI models (OpenAI, Claude, Ollama)
│   ├── tools/             # System tools and utilities
│   ├── memory/            # Conversation and session memory
│   ├── plugins/           # Extensible plugin system
│   ├── templates/         # HTML templates
│   ├── static/           # CSS, JS, and assets
│   ├── utils/            # Utility functions and Firebase
│   ├── config.py         # Centralized configuration
│   ├── jarvis.py         # Main system class
│   └── daily_quest_system.py  # RPG quest management
├── app.py                # Main Flask application
├── main.py              # Firebase Functions entry point
├── firebase.json        # Firebase configuration
└── requirements.txt     # Python dependencies
```

### 🔧 Core Components

1. **Jarvis Core**: Main AI system with conversation memory and tool integration
2. **Quest System**: RPG-style task management with XP rewards
3. **Firebase Manager**: Push notifications and cloud integration  
4. **Configuration System**: Centralized environment management
5. **API Server**: RESTful endpoints for all system operations

## 🎯 RPG System Details

### 📊 Character Progression
- **Starting Level**: 1 (E-rank Hunter)
- **Level Cap**: 50 (configurable)
- **XP Sources**: Quest completion, daily habits, skill practice
- **Stat Growth**: Balanced progression across Health, Intelligence, Strength, Wealth

### ⚔️ Quest Types

| Type | Focus | Example Quests |
|------|-------|----------------|
| 🏃 Health | Physical wellness | 20-min workout, meditation session |
| 🧠 Programming | Technical skills | Code practice, learn new language |
| 💰 Financial | Wealth building | Expense tracking, investment research |
| 📚 Personal Growth | Self-improvement | Journaling, skill practice |
| 🗣️ Communication | Social skills | Networking, public speaking |

### 🏅 Rank Progression
- **E-Rank**: 0 - 1,000 XP (Beginner)
- **D-Rank**: 1,000 - 2,500 XP (Novice)  
- **C-Rank**: 2,500 - 5,000 XP (Intermediate)
- **B-Rank**: 5,000 - 10,000 XP (Advanced)
- **A-Rank**: 10,000 - 20,000 XP (Expert)
- **S-Rank**: 20,000+ XP (Master)

## 🛠️ Configuration

### Environment Variables
```env
# Core Settings
ENVIRONMENT=development
DEBUG=False
SECRET_KEY=your-secret-key

# Firebase Configuration
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY=your-private-key
VAPID_KEY=your-vapid-key

# Quest System
DAILY_QUEST_COUNT=4
XP_MULTIPLIER=1.0
MAX_LEVEL=50

# Notification Schedule  
MORNING_NOTIFICATION=07:00
EVENING_NOTIFICATION=18:00
NIGHT_NOTIFICATION=21:00
```

### Customization Options
- **Quest Generation**: Modify templates in `daily_quest_system.py`
- **Skill Trees**: Edit `jarvis/skills_config.json`
- **UI Themes**: Customize CSS in `jarvis/static/css/`
- **Notification Messages**: Update templates in notification system

## 📱 API Reference

### Core Endpoints
```
GET  /api/stats              # Get character statistics
GET  /api/tasks              # Get all quests (with filters)
POST /api/daily-quests/generate  # Generate new daily quests
POST /api/complete_quest_advanced  # Complete quest with XP
GET  /api/health            # System health check
```

### Quest Management
```
POST /api/toggle_quest_active    # Activate/deactivate quest
GET  /api/daily-quests/stats    # Get daily progress stats
POST /api/three-month-plan/generate  # Create long-term plan
```

### Notifications
```
POST /api/save-notification-token  # Register for push notifications
POST /api/notification/manual     # Send test notification
GET  /api/notifications          # Get recent notifications
```

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit changes**: `git commit -m 'Add amazing feature'`
4. **Push to branch**: `git push origin feature/amazing-feature`
5. **Open a Pull Request**

### Development Guidelines
- Follow Python PEP 8 style guide
- Add type hints for new functions
- Include docstrings for public methods
- Test Firebase integration locally
- Update documentation for new features

## 🐛 Troubleshooting

### Common Issues
- **Firebase not connecting**: Check environment variables and service account permissions
- **Notifications not working**: Verify VAPID key and browser permissions
- **Quest generation failing**: Ensure skills configuration file is valid JSON

### Debug Mode
```bash
# Enable debug logging
export DEBUG=True
python app.py
```

### Health Check
Visit `/api/health` to verify all system components are working correctly.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Solo Leveling** - Inspiration for the rank and progression system
- **RPG Games** - Quest and leveling mechanics
- **Firebase** - Real-time notifications and hosting
- **Flask** - Lightweight web framework
- **OpenAI/Anthropic** - AI model integration

---

**Ready to start your journey from E-rank to S-rank?** 🗡️✨

Transform your daily routine into an epic adventure. Every task completed brings you closer to becoming the ultimate version of yourself!

[Get Started →](DEPLOYMENT.md) | [View API Docs →](/api) | [Join Community →](#) 