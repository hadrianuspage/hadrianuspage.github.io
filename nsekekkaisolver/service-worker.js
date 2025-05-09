// service-worker.js
self.addEventListener('install', function(event) {
	event.waitUntil(
		caches.open('my-site-cache').then(function(cache) {
			return cache.addAll([
				'/',
				'/index.html',
				'/styles.css',
				'/js/main.js',
				'/js/timer.js',
				'/js/sound.js',
				'/js/instructions.js',
				'/js/encyclopedia.js',
				'/js/guess.js'
				// Add other static assets like images, fonts, etc.
			]);
		})
	);
});

self.addEventListener('fetch', function(event) {
	event.respondWith(
		caches.match(event.request).then(function(response) {
			return response || fetch(event.request);
		})
	);
});

self.addEventListener('activate', function(event) {
	var cacheWhitelist = ['my-site-cache'];
	event.waitUntil(
		caches.keys().then(function(cacheNames) {
			return Promise.all(
				cacheNames.map(function(cacheName) {
					if (cacheWhitelist.indexOf(cacheName) === -1) {
						return caches.delete(cacheName);
					}
				})
			);
		})
	);
});