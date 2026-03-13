const CACHE = "valentine-v14";
const SHELL = ["/", "/static/manifest.json", "/static/icon-192.png", "/static/icon-512.png"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)));
  self.skipWaiting();
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    (async () => {
      // === EMERGENCY DATA RECOVERY ===
      // Read cached API responses and save them to the server
      // before they could be lost. This runs once on SW update.
      try {
        const cache = await caches.open(CACHE);
        const recovered = { wishlist: [], watchlist: [], halloween: [] };
        const apis = [
          { path: "/api/wishlist", key: "wishlist" },
          { path: "/api/watchlist", key: "watchlist" },
          { path: "/api/halloween-watchlist", key: "halloween" }
        ];

        for (const api of apis) {
          // Try path and full URL variants
          const urls = [
            api.path,
            self.location.origin + api.path,
            "https://katy-valentine.onrender.com" + api.path
          ];
          for (const url of urls) {
            try {
              const resp = await cache.match(url);
              if (resp) {
                const clone = resp.clone();
                const data = await clone.json();
                if (Array.isArray(data) && data.length > 0 && recovered[api.key].length === 0) {
                  recovered[api.key] = data;
                }
              }
            } catch (err) { /* skip */ }
          }
        }

        const total = recovered.wishlist.length + recovered.watchlist.length + recovered.halloween.length;
        if (total > 0) {
          await fetch("/api/recover", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(recovered)
          });
          // Notify any open clients
          const clients = await self.clients.matchAll();
          clients.forEach(c => c.postMessage({ type: "recovered", count: total }));
        }
      } catch (err) {
        // Don't block activation if recovery fails
      }

      // Normal cache cleanup (only delete OTHER cache names, keep valentine-v14)
      const keys = await caches.keys();
      await Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)));

      await self.clients.claim();
    })()
  );
});

self.addEventListener("fetch", (e) => {
  if (e.request.method !== "GET") return;

  // Cache first, fall back to network
  e.respondWith(
    caches.match(e.request).then(
      (r) =>
        r ||
        fetch(e.request).then((res) => {
          const clone = res.clone();
          caches.open(CACHE).then((c) => c.put(e.request, clone));
          return res;
        })
    )
  );
});
