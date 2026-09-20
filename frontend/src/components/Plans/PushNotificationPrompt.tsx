import { useMutation, useQuery } from "@tanstack/react-query"
import { BellRing } from "lucide-react"
import { useEffect, useState } from "react"

import { PushService } from "@/client"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import useCustomToast from "@/hooks/useCustomToast"

const isPushSupported = () =>
  typeof window !== "undefined" &&
  "serviceWorker" in navigator &&
  "PushManager" in window &&
  "Notification" in window

function urlBase64ToUint8Array(base64String: string) {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4)
  const base64 = (base64String + padding)
    .replace(/-/g, "+")
    .replace(/_/g, "/")
  const rawData = atob(base64)
  return Uint8Array.from([...rawData].map((char) => char.charCodeAt(0)))
}

export function PushNotificationPrompt() {
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const [permission, setPermission] = useState<NotificationPermission | null>(
    null,
  )
  const [dismissed, setDismissed] = useState(false)

  useEffect(() => {
    if (isPushSupported()) {
      setPermission(Notification.permission)
    }
  }, [])

  const { data: publicKey } = useQuery({
    queryKey: ["push-public-key"],
    queryFn: async () => {
      const res = await PushService.getPublicKey<false>({ throwOnError: false })
      return (res.data as { public_key?: string } | undefined)?.public_key ?? null
    },
    enabled: isPushSupported() && permission !== "denied",
  })

  const subscribeMutation = useMutation({
    mutationFn: async () => {
      const registration = await navigator.serviceWorker.register("/sw.js")
      const readyRegistration = await navigator.serviceWorker.ready
      const result = await Notification.requestPermission()
      setPermission(result)
      if (result !== "granted") {
        throw new Error("Permiso de notificaciones no concedido")
      }
      if (!publicKey) {
        throw new Error("Las notificaciones push no están disponibles")
      }
      const subscription = await (
        readyRegistration ?? registration
      ).pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(publicKey),
      })
      const json = subscription.toJSON()
      await PushService.subscribe({
        body: {
          endpoint: subscription.endpoint,
          p256dh: json.keys?.p256dh ?? "",
          auth: json.keys?.auth ?? "",
        },
      })
    },
    onSuccess: () => {
      showSuccessToast("Te avisaremos por notificación cuando tu plan esté por vencer.")
    },
    onError: (err: Error) => {
      showErrorToast(err.message)
    },
  })

  if (
    !isPushSupported() ||
    dismissed ||
    permission === "granted" ||
    permission === "denied"
  ) {
    return null
  }

  return (
    <Card>
      <CardContent className="flex flex-col items-start gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <BellRing className="text-primary size-5 shrink-0" />
          <p className="text-sm">
            Activa las notificaciones para recordar cuándo vence tu
            suscripción, como en Spotify.
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="ghost" size="sm" onClick={() => setDismissed(true)}>
            Ahora no
          </Button>
          <Button
            size="sm"
            disabled={!publicKey || subscribeMutation.isPending}
            onClick={() => subscribeMutation.mutate()}
          >
            Activar
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
