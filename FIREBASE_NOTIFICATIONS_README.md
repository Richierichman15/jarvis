# 🔥 Jarvis Firebase Notification System

This document explains how to set up and use the Firebase notification system in Jarvis for push notifications and progress tracking.

## 🚀 Features

- **Push Notifications**: Send alerts, reminders, and side quests to your phone/laptop
- **Progress Tracking**: XP system with levels and achievements stored in the cloud
- **Side Quests**: Gamified engagement system to keep you motivated
- **Cross-Device Sync**: Access your progress from any device
- **Scheduled Notifications**: Set delayed reminders and engagement notifications
- **Real-time Updates**: Instant notifications when events occur

## 📋 Prerequisites

1. **Firebase Project**: You'll need a Firebase project with the following services enabled:
   - Firestore Database
   - Cloud Messaging
   - (Optional) Authentication

2. **Firebase Admin SDK**: Service account credentials for server-side operations

## 🛠️ Setup Instructions

### Step 1: Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Create a project" or select an existing one
3. Follow the setup wizard

### Step 2: Enable Required Services

1. **Firestore Database**:
   - Go to "Firestore Database" in the sidebar
   - Click "Create database"
   - Choose "Start in production mode" or "test mode"
   - Select a location for your database

2. **Cloud Messaging**:
   - Go to "Cloud Messaging" in the sidebar
   - It should be enabled by default

### Step 3: Get Firebase Configuration

1. Go to "Project Settings" (gear icon)
2. Scroll down to "Your apps" section
3. Click "Add app" and select "Web" (if not already created)
4. Register your app with a nickname (e.g., "Jarvis Notifications")
5. Copy the config object values to your `.env` file

### Step 4: Generate VAPID Key

1. In "Project Settings", go to "Cloud Messaging" tab
2. Scroll down to "Web Push certificates"
3. Click "Generate key pair"
4. Copy the key to your `.env` file as `FIREBASE_VAPID_KEY`

### Step 5: Create Service Account

1. In "Project Settings", go to "Service accounts" tab
2. Click "Generate new private key"
3. Download the JSON file
4. Place it in your project directory
5. Set the path in your `.env` file as `FIREBASE_ADMIN_SDK_PATH`

### Step 6: Configure Environment Variables

Create a `.env` file in your project root:

```env
# Firebase Configuration
FIREBASE_API_KEY=your_api_key_here
FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
FIREBASE_PROJECT_ID=your_project_id
FIREBASE_STORAGE_BUCKET=your_project.firebasestorage.app
FIREBASE_MESSAGING_SENDER_ID=your_sender_id
FIREBASE_APP_ID=your_app_id
FIREBASE_MEASUREMENT_ID=your_measurement_id
FIREBASE_VAPID_KEY=your_vapid_key_here
FIREBASE_ADMIN_SDK_PATH=path/to/service-account.json
```

### Step 7: Install Dependencies

```bash
pip install firebase-admin
```

Or install all requirements:

```bash
pip install -r requirements.txt
```

## 📱 Usage

### Accessing the Notification Center

1. Start Jarvis web interface:
   ```bash
   python -m jarvis.web_interface
   ```

2. Open your browser and go to: `http://localhost:5000/notification`

### Setting Up Notifications

1. **Enable Notifications**: Click "Enable Notifications" and allow permissions
2. **Test Notification**: Click "Send Test Notification" to verify it works
3. **Custom Notifications**: Use the form to send custom notifications

### Progress Tracking

1. **Add XP**: Use the XP section to log accomplishments
2. **Save Progress**: Progress is automatically saved to Firebase
3. **Cross-Device**: Access your progress from any device with the same user ID

### Using the API

The system provides several API endpoints for integration:

#### Send Notification
```python
import requests

response = requests.post('http://localhost:5000/api/send-notification', json={
    'userId': 'your_user_id',
    'title': 'Hello from Jarvis!',
    'message': 'This is a test notification',
    'delay': 0  # seconds
})
```

#### Add XP
```python
response = requests.post('http://localhost:5000/api/add-xp', json={
    'userId': 'your_user_id',
    'amount': 50,
    'reason': 'Completed a task'
})
```

#### Create Side Quest
```python
response = requests.post('http://localhost:5000/api/create-side-quest', json={
    'userId': 'your_user_id',
    'title': 'Learn Firebase',
    'description': 'Set up Firebase notifications in Jarvis',
    'xpReward': 100,
    'difficulty': 'medium'
})
```

## 🎮 Gamification Features

### XP System
- Earn XP for completing tasks and activities
- Level up every 100 XP
- Get notifications when you level up

### Side Quests
- Receive engaging challenges
- Different difficulty levels (easy, medium, hard)
- XP rewards for completion

### Achievements
- Unlock achievements for various milestones
- Track your progress over time
- Share achievements with friends

## 🔧 Customization

### Notification Types

The system supports different notification types:
- `reminder`: Scheduled reminders
- `side-quest`: Gamified challenges
- `level_up`: Level progression notifications
- `achievement`: Achievement unlocks
- `engagement`: Re-engagement notifications

### Custom Data

You can include custom data in notifications:

```python
firebase_service.send_notification(
    user_id='user123',
    title='Custom Notification',
    message='This has custom data',
    data={
        'type': 'custom',
        'action': 'open_url',
        'url': 'https://example.com',
        'custom_field': 'custom_value'
    }
)
```

## 🛡️ Security

### Firestore Rules

Set up security rules for your Firestore database:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Users can only access their own data
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
    
    match /user_progress/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
    
    match /notifications/{notificationId} {
      allow read: if request.auth != null && request.auth.uid == resource.data.user_id;
    }
    
    match /side_quests/{questId} {
      allow read: if request.auth != null && request.auth.uid == resource.data.user_id;
    }
  }
}
```

### Environment Variables

- Never commit your `.env` file to version control
- Use different Firebase projects for development and production
- Regularly rotate your API keys and service account credentials

## 🐛 Troubleshooting

### Common Issues

1. **Notifications not working**:
   - Check browser permissions
   - Verify VAPID key is correct
   - Ensure service worker is registered

2. **Firebase connection errors**:
   - Verify all environment variables are set
   - Check service account JSON file path
   - Ensure Firestore is enabled

3. **Permission errors**:
   - Check Firestore security rules
   - Verify service account has required permissions

### Debug Mode

Enable debug logging by setting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📊 Monitoring

### Firebase Console

Monitor your usage in the Firebase Console:
- **Cloud Messaging**: View sent messages and delivery rates
- **Firestore**: Monitor database usage and queries
- **Analytics**: Track user engagement (if enabled)

### Logs

Check application logs for notification delivery status:
- Successful deliveries are logged with ✅
- Failures are logged with ❌
- Scheduled notifications are logged with 📅

## 🚀 Advanced Features

### Batch Notifications

Send notifications to multiple users:

```python
# Send to multiple users
users = ['user1', 'user2', 'user3']
for user_id in users:
    firebase_service.send_notification(
        user_id, 
        'Group Notification', 
        'Message for everyone!'
    )
```

### Conditional Notifications

Send notifications based on user data:

```python
# Only notify users who haven't been active recently
user_data = firebase_service.get_user_progress(user_id)
if user_data.get('last_active') < threshold:
    firebase_service.send_engagement_notification(user_id)
```

### Background Sync

The service worker handles background synchronization for offline support.

## 📝 API Reference

### Endpoints

| Endpoint | Method | Description |
|----------|---------|-------------|
| `/api/firebase-config` | GET | Get Firebase configuration |
| `/api/save-notification-token` | POST | Save FCM token |
| `/api/send-notification` | POST | Send notification |
| `/api/add-xp` | POST | Add XP to user |
| `/api/load-progress` | POST | Load user progress |
| `/api/save-progress` | POST | Save user progress |
| `/api/create-side-quest` | POST | Create side quest |
| `/api/send-reminder` | POST | Schedule reminder |
| `/api/send-engagement` | POST | Send engagement notification |

### Data Models

#### User Progress
```json
{
  "totalXP": 250,
  "level": 3,
  "achievements": ["first_notification", "level_5"],
  "quests_completed": 5,
  "last_updated": "2024-01-15T10:30:00Z"
}
```

#### Notification
```json
{
  "title": "Notification Title",
  "message": "Notification body text",
  "data": {
    "type": "reminder",
    "action": "open_app"
  }
}
```

## 🤝 Contributing

To contribute to the notification system:

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## 📄 License

This notification system is part of the Jarvis project and follows the same license terms.

---

**Happy coding! 🚀** Your AI assistant is now ready to keep you engaged and motivated with smart notifications!