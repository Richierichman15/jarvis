// Firebase Cloud Messaging Service Worker
importScripts('https://www.gstatic.com/firebasejs/9.22.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/9.22.0/firebase-messaging-compat.js');

// Initialize Firebase with configuration from the backend
let firebaseApp = null;
let messaging = null;

// Function to initialize Firebase
async function initializeFirebase() {
    try {
        const response = await fetch('/api/firebase-config');
        const config = await response.json();
        
        if (config.success && config.config) {
            firebaseApp = firebase.initializeApp(config.config);
            messaging = firebase.messaging();
            
            console.log('🔥 Firebase initialized in service worker');
            return true;
        } else {
            console.error('❌ Failed to get Firebase configuration:', config.error);
            return false;
        }
    } catch (error) {
        console.error('❌ Error initializing Firebase in service worker:', error);
        return false;
    }
}

// Initialize Firebase when service worker loads
self.addEventListener('install', (event) => {
    console.log('🔧 Service worker installing...');
    event.waitUntil(initializeFirebase());
});

self.addEventListener('activate', (event) => {
    console.log('✅ Service worker activated');
    event.waitUntil(initializeFirebase());
});

// Handle background messages
self.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'FIREBASE_MESSAGING_BACKGROUND_MESSAGE') {
        initializeFirebase().then((initialized) => {
            if (initialized && messaging) {
                setupBackgroundMessageHandler();
            }
        });
    }
});

function setupBackgroundMessageHandler() {
    // Handle background messages
    messaging.onBackgroundMessage((payload) => {
        console.log('📨 Received background message:', payload);

        const notificationTitle = payload.notification?.title || 'Jarvis Notification';
        const notificationOptions = {
            body: payload.notification?.body || '',
            icon: payload.notification?.icon || '/static/images/notification-icon.png',
            badge: '/static/images/badge-icon.png',
            data: payload.data || {},
            vibrate: [200, 100, 200],
            requireInteraction: true,
            actions: [
                {
                    action: 'open',
                    title: '🚀 Open Jarvis',
                    icon: '/static/images/open-icon.png'
                },
                {
                    action: 'dismiss',
                    title: '✖️ Dismiss',
                    icon: '/static/images/dismiss-icon.png'
                }
            ],
            tag: 'jarvis-notification',
            renotify: true
        };

        // Add quest-specific styling for side quests
        if (payload.data?.type === 'side-quest') {
            notificationOptions.badge = '/static/images/quest-badge.png';
            notificationOptions.icon = '/static/images/quest-icon.png';
            notificationOptions.actions.unshift({
                action: 'accept-quest',
                title: '⚔️ Accept Quest',
                icon: '/static/images/sword-icon.png'
            });
        }

        return self.registration.showNotification(notificationTitle, notificationOptions);
    });
}

// Handle notification clicks
self.addEventListener('notificationclick', (event) => {
    console.log('🖱️ Notification clicked:', event.notification.tag);
    
    event.notification.close();
    
    const action = event.action;
    const data = event.notification.data || {};
    
    if (action === 'dismiss') {
        // Just close the notification
        return;
    }
    
    // Handle other actions
    event.waitUntil(
        clients.matchAll({ type: 'window' }).then((clientList) => {
            // Try to focus existing window
            for (const client of clientList) {
                if (client.url.includes('/notification') && 'focus' in client) {
                    return client.focus();
                }
            }
            
            // Open new window
            let targetUrl = '/notification';
            
            if (action === 'accept-quest' && data.questId) {
                targetUrl = `/notification?quest=${data.questId}`;
            } else if (action === 'open') {
                targetUrl = '/notification';
            }
            
            if (clients.openWindow) {
                return clients.openWindow(targetUrl);
            }
        })
    );
});

// Handle push events
self.addEventListener('push', (event) => {
    console.log('📥 Push received:', event);
    
    if (event.data) {
        const data = event.data.json();
        console.log('📦 Push data:', data);
        
        const title = data.notification?.title || 'Jarvis Notification';
        const options = {
            body: data.notification?.body || '',
            icon: data.notification?.icon || '/static/images/notification-icon.png',
            badge: '/static/images/badge-icon.png',
            data: data.data || {},
            vibrate: [200, 100, 200],
            requireInteraction: true
        };
        
        event.waitUntil(
            self.registration.showNotification(title, options)
        );
    }
});

// Handle sync events for offline functionality
self.addEventListener('sync', (event) => {
    if (event.tag === 'background-sync') {
        console.log('🔄 Background sync triggered');
        event.waitUntil(doBackgroundSync());
    }
});

async function doBackgroundSync() {
    try {
        // Sync any pending notifications or progress updates
        const response = await fetch('/api/sync-progress', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        if (response.ok) {
            console.log('✅ Background sync completed');
        }
    } catch (error) {
        console.error('❌ Background sync failed:', error);
    }
}

console.log('🚀 Jarvis Firebase Service Worker loaded');