// service-worker.js
self.addEventListener("push", function (event) {
  let data = {};
  if (event.data) {
    try {
      data = event.data.json();
    } catch (e) {
      data = { title: "Task Reminder", body: event.data.text() };
    }
  }

  const title = data.title || "Task Reminder";
  const options = {
    body: data.body || "You have a task due!",
    icon: "/static/icon.png",
    badge: "/static/icon.png",
    requireInteraction: true,
    data: data.url || "/"
  };

  event.waitUntil(self.registration.showNotification(title, options));
});

// Handle notification click
self.addEventListener("notificationclick", function (event) {
  event.notification.close();
  event.waitUntil(
    clients.matchAll({ type: "window", includeUncontrolled: true }).then((clientList) => {
      for (const client of clientList) {
        if ("focus" in client) return client.focus();
      }
      if (clients.openWindow) return clients.openWindow(event.notification.data);
    })
  );
});
