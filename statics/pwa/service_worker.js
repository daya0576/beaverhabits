const CACHE_NAME = 'beaverhabits_v1';
const CACHE_URLS = [
    '/media/', 
    '/statics/',
    '/_nicegui/'
];

// WebSocket connections to be excluded from the fetch handler
const WEBSOCKET_URLS = [
    'wss://',
    'ws://'
];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {

            return Promise.all(
                CACHE_URLS.map(url => {
                    return cache.add(url).catch(error => {
                        console.error('Failed to cache:', url, error);
                    });
                })
            );
        })
    );
});

self.addEventListener('fetch', (event) => {
    // Check if the request is for a WebSocket
    if (WEBSOCKET_URLS.some(wsUrl => event.request.url.startsWith(wsUrl))) {
        // Don't interfere with WebSocket connections
        return;
    }

    event.respondWith(
        caches.match(event.request).then((response) => {
            return response || fetch(event.request);
        })
    );
});

self.addEventListener('activate', (event) => {
    const cacheWhitelist = [CACHE_NAME];
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheWhitelist.indexOf(cacheName) === -1) {
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});

// Handle WebSocket keep-alive
self.addEventListener('message', (event) => {
    if (event.data === 'keepalive') {
        // Respond to keep-alive messages
        event.ports[0].postMessage('alive');
    }
});
