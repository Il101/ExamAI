/* eslint-disable no-restricted-globals */

// Service Worker for ExamAI Pro
// Handles background push notifications

self.addEventListener('push', function (event) {
    if (!event.data) {
        console.log('Push event with no data');
        return;
    }

    try {
        const payload = event.data.json();
        const { title, body, icon, url, data } = payload;

        const options = {
            body: body || 'You have a new update!',
            icon: icon || '/icons/icon-192x192.png',
            badge: '/icons/badge-72x72.png',
            data: {
                url: url || '/',
                ...data
            },
            vibrate: [100, 50, 100],
            silent: false, // Enable notification sound
            requireInteraction: true, // Keep notification visible until user interacts
            actions: [
                {
                    action: 'open',
                    title: 'View'
                },
                {
                    action: 'close',
                    title: 'Dismiss'
                }
            ]
        };

        event.waitUntil(
            self.registration.showNotification(title || 'ExamAI Pro', options)
        );
    } catch (error) {
        console.error('Error handling push event:', error);

        // Fallback for non-JSON or malformed data
        event.waitUntil(
            self.registration.showNotification('ExamAI Pro', {
                body: event.data.text()
            })
        );
    }
});

self.addEventListener('notificationclick', function (event) {
    event.notification.close();

    if (event.action === 'close') {
        return;
    }

    const urlToOpen = event.notification.data?.url || '/';

    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function (clientList) {
            // Check if there is already a window open with the same URL
            for (let i = 0; i < clientList.length; i++) {
                const client = clientList[i];
                if (client.url === urlToOpen && 'focus' in client) {
                    return client.focus();
                }
            }
            // If no window found, open a new one
            if (clients.openWindow) {
                return clients.openWindow(urlToOpen);
            }
        })
    );
});
