// Firebase Cloud Messaging Service Worker
importScripts('https://www.gstatic.com/firebasejs/9.x.x/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/9.x.x/firebase-messaging-compat.js');

firebase.initializeApp({
    apiKey: "AIzaSyAFhRXD0uuv9--e8O6gqB6MsV2Ms85AaUI",
    authDomain: "system-31e58.firebaseapp.com",
    projectId: "system-31e58",
    storageBucket: "system-31e58.firebasestorage.app",
    messagingSenderId: "1059252367741",
    appId: "1:1059252367741:web:bd5938787385b00957dc14",
    measurementId: "G-WJY4ET97CE"
});

const messaging = firebase.messaging();

// Handle background messages
messaging.onBackgroundMessage((payload) => {
    console.log('Received background message:', payload);

    const notificationTitle = payload.notification.title;
    const notificationOptions = {
        body: payload.notification.body,
        icon: '/static/images/notification-icon.png',
        badge: '/static/images/badge-icon.png',
        data: payload.data,
        vibrate: [200, 100, 200]
    };

    self.registration.showNotification(notificationTitle, notificationOptions);
}); 