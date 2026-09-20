self.addEventListener("push", (event) => {
  let data = { title: "Parqueadero UNIMINUTO", body: "" }
  if (event.data) {
    try {
      data = event.data.json()
    } catch {
      data.body = event.data.text()
    }
  }
  event.waitUntil(
    self.registration.showNotification(data.title || "Parqueadero UNIMINUTO", {
      body: data.body || "",
      icon: "/assets/images/favicon.png",
    }),
  )
})

self.addEventListener("notificationclick", (event) => {
  event.notification.close()
  event.waitUntil(clients.openWindow("/"))
})
