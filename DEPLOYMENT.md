# Jarvis System - Deployment Guide

This guide will help you deploy the Jarvis System to Firebase and set up the RPG-like quest system for better life management.

## 🚀 Quick Firebase Deployment

### Prerequisites

1. **Firebase CLI**: Install the Firebase CLI tools
```bash
npm install -g firebase-tools
```

2. **Python 3.11+**: Ensure you have Python 3.11 or higher
```bash
python --version
```

3. **Firebase Project**: Create a Firebase project at https://console.firebase.google.com/

### Step 1: Firebase Setup

1. **Login to Firebase**:
```bash
firebase login
```

2. **Initialize Firebase in your project**:
```bash
firebase init
```
   - Select "Functions" and "Hosting"
   - Choose your Firebase project
   - Select Python for Functions
   - Use `jarvis/static` as public directory for Hosting

3. **Enable Firebase Services**:
   - Go to Firebase Console → Project Settings
   - Enable Cloud Messaging for push notifications
   - Generate a Web Push certificate (VAPID key)

### Step 2: Environment Configuration

1. **Copy the example environment file**:
```bash
cp .env.example .env
```

2. **Configure Firebase credentials**:
   - Go to Firebase Console → Project Settings → Service Accounts
   - Generate a new private key
   - Download the JSON file
   - Extract the values and add them to your `.env` file

3. **Essential environment variables to configure**:
```env
# Firebase Configuration
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=your-service-account@your-project.iam.gserviceaccount.com

# Firebase Web Configuration  
FIREBASE_API_KEY=your-web-api-key
FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
FIREBASE_MESSAGING_SENDER_ID=your-sender-id
FIREBASE_APP_ID=your-app-id

# Push Notifications
VAPID_KEY=your-vapid-key

# Set to production for deployment
ENVIRONMENT=production
```

### Step 3: Deploy to Firebase

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Deploy Functions and Hosting**:
```bash
firebase deploy
```

3. **Set environment variables in Firebase Functions**:
```bash
# Set all your environment variables
firebase functions:config:set firebase.project_id="your-project-id"
firebase functions:config:set firebase.private_key="your-private-key"
# ... add all other config variables
```

## 🎮 System Features

### RPG-Like Quest System
- **Daily Quests**: Automatically generated based on your goals
- **XP System**: Earn experience points for completing tasks
- **Skill Tree**: Unlock new abilities as you level up
- **Rank System**: Progress from E-rank to S-rank
- **Push Notifications**: Get reminded about quests and achievements

### Core Components
- **Character Stats**: Health, Intelligence, Strength, Wealth
- **Level Progression**: Level up by completing quests and earning XP
- **Inventory System**: Collect rewards and manage resources
- **3-Month Planning**: Long-term goal tracking and planning
- **World Map**: Visual representation of your progress

## 🔧 Local Development

### Running Locally

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Set up environment**:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Run the application**:
```bash
python app.py
```

4. **Access the application**:
   - Open http://localhost:8080 in your browser
   - The system will be available with all RPG features

### Firebase Emulator (for testing)

1. **Start Firebase emulators**:
```bash
firebase emulators:start
```

2. **Test push notifications**:
   - Use the `/api/notification/manual` endpoint
   - Check the Firebase console for message delivery

## 📱 Push Notifications Setup

### Web Push Notifications

1. **Generate VAPID Keys**:
   - Go to Firebase Console → Project Settings → Cloud Messaging
   - Generate Web Push certificates
   - Add the VAPID key to your environment variables

2. **Service Worker**:
   - The `firebase-messaging-sw.js` file is already configured
   - Update with your Firebase config if needed

3. **Testing Notifications**:
```bash
# Send a test morning notification
curl -X POST http://localhost:8080/api/notification/manual \
  -H "Content-Type: application/json" \
  -d '{"type": "morning"}'
```

## ⚙️ Configuration Options

### Quest System Configuration
```env
DAILY_QUEST_COUNT=4          # Number of daily quests to generate
XP_MULTIPLIER=1.0           # XP multiplier for quest completion
LEVEL_UP_BASE_XP=150        # Base XP required to level up
MAX_LEVEL=50                # Maximum character level
```

### Notification Schedule
```env
MORNING_NOTIFICATION=07:00   # Morning quest reminder
EVENING_NOTIFICATION=18:00   # Evening progress check
NIGHT_NOTIFICATION=21:00     # Daily reflection prompt
```

### Rank Requirements
```env
RANK_E_REQUIREMENT=1000     # XP needed for D-rank
RANK_D_REQUIREMENT=2500     # XP needed for C-rank
RANK_C_REQUIREMENT=5000     # XP needed for B-rank
RANK_B_REQUIREMENT=10000    # XP needed for A-rank
RANK_A_REQUIREMENT=20000    # XP needed for S-rank
RANK_S_REQUIREMENT=50000    # XP needed for SS-rank
```

## 🐛 Troubleshooting

### Common Issues

1. **Firebase not initializing**:
   - Check your environment variables
   - Ensure the private key is properly formatted with `\n` for newlines
   - Verify service account permissions

2. **Push notifications not working**:
   - Verify VAPID key is correctly set
   - Check browser permissions for notifications
   - Ensure Firebase Messaging is enabled

3. **Quest system not generating quests**:
   - Check the skills configuration file exists
   - Verify the daily quest system is initialized
   - Check logs for any errors

### Logs and Monitoring

1. **Firebase Functions logs**:
```bash
firebase functions:log
```

2. **Local development logs**:
   - Check console output for detailed logging
   - Use `/api/health` endpoint to check system status

## 🔄 Updates and Maintenance

### Updating the System

1. **Pull latest changes**:
```bash
git pull origin main
```

2. **Update dependencies**:
```bash
pip install -r requirements.txt --upgrade
```

3. **Redeploy**:
```bash
firebase deploy
```

### Database Migration (Future)
- The system is designed to be easily migrated to Firebase Firestore
- Current data is stored in JSON files for simplicity
- Migration scripts will be provided in future updates

## 📚 API Documentation

### Key Endpoints
- `GET /api/config` - Get system configuration
- `GET /api/stats` - Get character statistics
- `GET /api/tasks` - Get all quests with filtering
- `POST /api/daily-quests/generate` - Generate new daily quests
- `POST /api/complete_quest_advanced` - Complete quest with XP system
- `GET /api/health` - Health check for monitoring

### Authentication
- Session-based authentication for web interface
- JWT tokens available for API access
- Firebase Authentication integration ready

## 🎯 RPG System Goals

The Jarvis System is designed to gamify personal development:

1. **Daily Habits**: Turn daily tasks into quests
2. **Skill Development**: Progressive skill unlocking system
3. **Long-term Goals**: 3-month planning with weekly milestones
4. **Social Features**: Ready for multiplayer and leaderboards
5. **Achievements**: Unlock badges and rewards for consistency

Start your journey as an E-rank Hunter and work your way up to S-rank mastery! 🗡️✨