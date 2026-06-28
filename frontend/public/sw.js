self.addEventListener('push', function(event) {
    console.log('[Service Worker] Push Received.');
    
    let title = 'ParseOps Notification';
    let options = {
        body: 'You have a new update in your workspace.',
        icon: '/vite.svg'
    };

    if (event.data) {
        try {
            const data = event.data.json();
            title = data.title || title;
            options.body = data.body || options.body;
            if (data.url) {
                options.data = { url: data.url };
            }
        } catch (e) {
            console.log('Error parsing push data', e);
            options.body = event.data.text();
        }
    }

    // Forward the notification to any open tabs so they can show the Top-Center Toast!
    self.clients.matchAll().then(clients => {
        clients.forEach(client => {
            client.postMessage({
                type: 'PUSH_NOTIFICATION',
                title: title,
                body: options.body
            });
        });
    });

    event.waitUntil(
        self.registration.showNotification(title, options)
    );
});

self.addEventListener('notificationclick', function(event) {
    console.log('[Service Worker] Notification click Received.');
    event.notification.close();
    if (event.notification.data && event.notification.data.url) {
        event.waitUntil(self.clients.openWindow(event.notification.data.url));
    } else {
        event.waitUntil(self.clients.openWindow('/'));
    }
});
