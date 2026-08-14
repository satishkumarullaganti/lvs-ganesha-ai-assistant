// ============================================
// LVS Ganesha AI Assistant - Service Worker
// ============================================
// This exists mainly to satisfy PWA installability
// (Chrome/Android requires a registered service worker
// with a fetch handler before showing "Add to Home
// Screen"). It deliberately does NOT cache chat
// responses, schedule data, or any dynamic content -
// this app is actively evolving (backend/frontend get
// updated frequently), so a network-first strategy is
// used everywhere. Only a small set of truly static
// assets (CSS, JS, icons, images) get a cache fallback,
// and only if the network request fails outright (e.g.
// a brief connectivity drop), never as a first choice.
// ============================================

const CACHE_NAME = "lvs-ganesha-static-v1";

const STATIC_ASSET_PATTERNS = [
    /\/css\//,
    /\/js\//,
    /\/assets\//,
    /\/manifest\.json$/
];

function isStaticAsset(url) {
    return STATIC_ASSET_PATTERNS.some((pattern) => pattern.test(url));
}

self.addEventListener("install", (event) => {
    // Activate the new service worker as soon as it's
    // installed, instead of waiting for old tabs to close -
    // important since this app changes frequently during
    // active development.
    self.skipWaiting();
});

self.addEventListener("activate", (event) => {

    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames
                    .filter((name) => name !== CACHE_NAME)
                    .map((name) => caches.delete(name))
            );
        })
    );

    self.clients.claim();
});

self.addEventListener("fetch", (event) => {

    const requestUrl = event.request.url;

    // Only ever intercept GET requests for static assets.
    // Everything else (chat, schedule, registration,
    // donation, admin, etc.) always goes straight to the
    // network, untouched.
    if (event.request.method !== "GET" || !isStaticAsset(requestUrl)) {
        return;
    }

    event.respondWith(
        fetch(event.request)
            .then((networkResponse) => {

                const responseClone = networkResponse.clone();

                caches.open(CACHE_NAME).then((cache) => {
                    cache.put(event.request, responseClone);
                });

                return networkResponse;
            })
            .catch(() => {
                // Network failed (e.g. brief connectivity drop) -
                // fall back to the last cached version if we have
                // one, for static assets only.
                return caches.match(event.request);
            })
    );
});
