/* Service worker: receives pushes and opens the app when one is tapped. */

self.addEventListener("push", (event) => {
  let payload = {};

  try {
    payload = event.data ? event.data.json() : {};
  } catch {
    payload = { title: "Copium", body: "A new rejection was filed." };
  }

  event.waitUntil(
    Promise.all([
      self.registration.showNotification(payload.title || "Copium", {
        body: payload.body || "",
        icon: "/icon-192.png",
        badge: "/icon-192.png",
        tag: payload.tag || "copium",
        data: { url: payload.url || "/" },
      }),

      // Tell any open window to refetch. Without this a card arriving while
      // the app is in the foreground never appears, since standalone PWAs have
      // no reload button and visibilitychange never fires.
      self.clients
        .matchAll({ type: "window", includeUncontrolled: true })
        .then((windows) => {
          for (const win of windows) win.postMessage({ type: "new-card" });
        }),
    ]),
  );
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const target = event.notification.data?.url || "/";

  // Focus an already-open window rather than spawning another.
  event.waitUntil(
    self.clients
      .matchAll({ type: "window", includeUncontrolled: true })
      .then((windows) => {
        for (const win of windows) {
          if (win.url.includes(target) && "focus" in win) return win.focus();
        }
        return self.clients.openWindow(target);
      }),
  );
});