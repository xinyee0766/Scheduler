// service-worker.js
self.addEventListener("push", function (event) {
  console.log("[Service Worker] Push Received."); // Debugging log

  let data = {};
  if (event.data) {
    try {
      data = event.data.json();
    } catch (e) {
      console.warn("Push data was not JSON, using text fallback.");
      data = { title: "Task Reminder", body: event.data.text() };
    }
  }

  const title = data.title || "Task Reminder";
  const options = {
    body: data.body || "You have a task due!",
    icon: "/static/icon.png",
    badge: "/static/icon.png",
    requireInteraction: true,
    data: { url: data.url || "/" }, // ✅ wrap url in object to avoid undefined
    vibrate: [200, 100, 200],       // ✅ ensure visible vibration
    timestamp: Date.now(),          // ✅ helps re-trigger even with same notification
  };

  event.waitUntil(
    self.registration.showNotification(title, options).catch(err => {
      console.error("Notification failed: ", err);
    })
  );
});

// Handle notification click
self.addEventListener("notificationclick", function (event) {
  console.log("[Service Worker] Notification clicked.");
  event.notification.close();

  event.waitUntil(
    clients.matchAll({ type: "window", includeUncontrolled: true }).then((clientList) => {
      for (const client of clientList) {
        if ("focus" in client) {
          return client.focus();
        }
      }
      if (clients.openWindow && event.notification.data && event.notification.data.url) {
        return clients.openWindow(event.notification.data.url);
      }
    })
  );
});