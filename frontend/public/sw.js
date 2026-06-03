const clearLegacyCaches = async () => {
  if (!("caches" in self)) return;

  const names = await caches.keys();
  await Promise.all(names.map((name) => caches.delete(name)));
};

self.addEventListener("install", (event) => {
  self.skipWaiting();
  event.waitUntil(clearLegacyCaches());
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    (async () => {
      await clearLegacyCaches();
      await self.registration.unregister();

      const clients = await self.clients.matchAll({
        includeUncontrolled: true,
        type: "window",
      });

      for (const client of clients) {
        client.navigate(client.url);
      }
    })(),
  );
});
