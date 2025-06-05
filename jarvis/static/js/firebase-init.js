// Firebase initialization and notification handling
import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";
import { getMessaging, getToken, onMessage } from "firebase/messaging";

const firebaseConfig = {
  apiKey: "AIzaSyAFhRXD0uuv9--e8O6gqB6MsV2Ms85AaUI",
  authDomain: "system-31e58.firebaseapp.com",
  projectId: "system-31e58",
  storageBucket: "system-31e58.firebasestorage.app",
  messagingSenderId: "1059252367741",
  appId: "1:1059252367741:web:bd5938787385b00957dc14",
  measurementId: "G-WJY4ET97CE"
};

class FirebaseManager {
    constructor() {
        this.app = null;
        this.messaging = null;
        this.analytics = null;
        this.token = null;
        this.isInitialized = false;
        this.vapidKey = null;
    }

    async initialize() {
        try {
            // Get VAPID key from backend
            const configResponse = await fetch('/api/firebase-config');
            const config = await configResponse.json();
            
            if (!config.success) {
                throw new Error(config.error || 'Failed to get Firebase configuration');
            }
            
            this.vapidKey = config.vapidKey;
            
            // Initialize Firebase
            this.app = initializeApp(firebaseConfig);
            this.analytics = getAnalytics(this.app);
            this.messaging = getMessaging(this.app);
            this.isInitialized = true;
            console.log('✅ Firebase initialized successfully');

            // Set up message handling
            this.setupMessageHandling();

            // Request permission and get token
            await this.requestNotificationPermission();

            return true;
        } catch (error) {
            console.error('❌ Error initializing Firebase:', error);
            this.isInitialized = false;
            return false;
        }
    }

    async requestNotificationPermission() {
        try {
            const permission = await Notification.requestPermission();
            if (permission === 'granted') {
                // Get token and save it
                await this.getAndSaveToken();
                return true;
            } else {
                console.warn('⚠️ Notification permission denied');
                return false;
            }
        } catch (error) {
            console.error('❌ Error requesting notification permission:', error);
            return false;
        }
    }

    async getAndSaveToken() {
        try {
            if (!this.vapidKey) {
                throw new Error('VAPID key not available');
            }

            const currentToken = await getToken(this.messaging, {
                vapidKey: this.vapidKey
            });

            if (currentToken) {
                this.token = currentToken;
                console.log('✅ FCM Token obtained');
                
                // Save token to backend
                await this.saveTokenToServer(currentToken);
                return currentToken;
            } else {
                console.warn('⚠️ No token available');
                return null;
            }
        } catch (error) {
            console.error('❌ Error getting FCM token:', error);
            return null;
        }
    }

    async saveTokenToServer(token) {
        try {
            const response = await fetch('/api/save-notification-token', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ token })
            });

            const data = await response.json();
            if (data.success) {
                console.log('✅ Token saved to server successfully');
                return true;
            } else {
                console.warn('⚠️ Failed to save token:', data.error);
                return false;
            }
        } catch (error) {
            console.error('❌ Error saving token to server:', error);
            return false;
        }
    }

    setupMessageHandling() {
        if (!this.messaging) return;

        onMessage(this.messaging, (payload) => {
            console.log('📨 Message received:', payload);

            // Create and show notification
            this.showNotification(payload);
        });
    }

    showNotification(payload) {
        try {
            const notificationTitle = payload.notification?.title || 'New Notification';
            const notificationOptions = {
                body: payload.notification?.body || '',
                icon: '/static/images/notification-icon.png',
                badge: '/static/images/badge-icon.png',
                vibrate: [200, 100, 200],
                data: payload.data || {},
                requireInteraction: true,
                actions: [
                    {
                        action: 'open',
                        title: 'Open App'
                    },
                    {
                        action: 'dismiss',
                        title: 'Dismiss'
                    }
                ]
            };

            // Show notification
            new Notification(notificationTitle, notificationOptions);
        } catch (error) {
            console.error('❌ Error showing notification:', error);
        }
    }

    // Helper method to check if notifications are supported
    static isSupported() {
        return 'Notification' in window && 'serviceWorker' in navigator && 'PushManager' in window;
    }
}

// Create and export Firebase manager instance
const firebaseManager = new FirebaseManager();

// Export functions and manager
export {
    firebaseManager,
    FirebaseManager
};

// Initialize Firebase when the script loads
if (FirebaseManager.isSupported()) {
    firebaseManager.initialize().catch(console.error);
} else {
    console.warn('⚠️ Push notifications are not supported in this browser');
} 