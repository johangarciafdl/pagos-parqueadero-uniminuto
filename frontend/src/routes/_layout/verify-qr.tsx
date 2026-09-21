import { useMutation } from "@tanstack/react-query"
import { createFileRoute, redirect } from "@tanstack/react-router"
import jsQR from "jsqr"
import { ImageUp } from "lucide-react"
import { useRef, useState } from "react"

import { KioskService, UsersService } from "@/client"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { LoadingButton } from "@/components/ui/loading-button"
import useCustomToast from "@/hooks/useCustomToast"

export const Route = createFileRoute("/_layout/verify-qr")({
  component: VerifyQr,
  beforeLoad: async () => {
    const { data: user } = await UsersService.readUserMe()
    if (!user.is_superuser) {
      throw redirect({ to: "/" })
    }
  },
  head: () => ({
    meta: [{ title: "Verificar QR - Parqueadero UNIMINUTO" }],
  }),
})

type VerifyResult = {
  nombre: string
  apellido: string
  rol: string
  documento: string
  plan_until: string | null
  placa: string | null
  acceso_libre: boolean
}

function decodeQrFromFile(file: File): Promise<string | null> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      const img = new Image()
      img.onload = () => {
        const canvas = document.createElement("canvas")
        canvas.width = img.width
        canvas.height = img.height
        const ctx = canvas.getContext("2d")
        if (!ctx) {
          resolve(null)
          return
        }
        ctx.drawImage(img, 0, 0)
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height)
        const code = jsQR(imageData.data, imageData.width, imageData.height)
        resolve(code?.data ?? null)
      }
      img.onerror = () => reject(new Error("No se pudo leer la imagen"))
      img.src = reader.result as string
    }
    reader.onerror = () => reject(new Error("No se pudo leer el archivo"))
    reader.readAsDataURL(file)
  })
}

function VerifyQr() {
  const { showErrorToast, showSuccessToast } = useCustomToast()
  const [qrToken, setQrToken] = useState("")
  const [lastToken, setLastToken] = useState("")
  const [result, setResult] = useState<VerifyResult | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const verifyMutation = useMutation({
    mutationFn: async (token: string) =>
      (await KioskService.verifyQr({ body: { qr_token: token } }))
        .data as unknown as VerifyResult,
    onSuccess: (data, token) => {
      setResult(data)
      setLastToken(token)
      setQrToken("")
      inputRef.current?.focus()
    },
    onError: (err: Error) => {
      setResult(null)
      showErrorToast(err.message)
    },
  })

  const imageMutation = useMutation({
    mutationFn: decodeQrFromFile,
    onSuccess: (decoded) => {
      if (!decoded) {
        showErrorToast("No se encontró ningún QR en esa imagen")
        return
      }
      verifyMutation.mutate(decoded)
    },
    onError: (err: Error) => showErrorToast(err.message),
  })

  const logMutation = useMutation({
    mutationFn: async (direction: "entrada" | "salida") =>
      (
        await KioskService.verifyQr({
          body: { qr_token: lastToken, direction },
        })
      ).data as unknown as VerifyResult,
    onSuccess: (_data, direction) => {
      showSuccessToast(
        direction === "entrada" ? "Entrada registrada" : "Salida registrada",
      )
    },
    onError: (err: Error) => showErrorToast(err.message),
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!qrToken.trim()) return
    verifyMutation.mutate(qrToken.trim())
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    e.target.value = ""
    if (file) imageMutation.mutate(file)
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Verificar QR</h1>
        <p className="text-muted-foreground max-w-2xl">
          Este es el lector virtual del parqueadero: decodifica el mismo QR
          que usa el estudiante/personal para identificarse y te dice si
          puede entrar sin pagar (exento o con plan mensual vigente) y con
          qué vehículo, si aplica.
        </p>
        <p className="text-muted-foreground mt-1 max-w-2xl text-sm">
          Un lector físico de códigos de barras escribe el contenido del QR
          como si fuera un teclado, así que basta con dejar el cursor en el
          campo de abajo. Como todavía no tienes uno conectado, también
          puedes subir una foto o captura del QR y se decodifica solo.
        </p>
      </div>

      <Card className="max-w-md">
        <CardHeader>
          <CardTitle>Lector</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <form onSubmit={handleSubmit} className="grid gap-4">
            <div className="grid gap-2">
              <Label htmlFor="qr_token">Código QR</Label>
              <Input
                id="qr_token"
                ref={inputRef}
                autoFocus
                value={qrToken}
                onChange={(e) => setQrToken(e.target.value)}
                placeholder="Escanea o pega el código"
              />
            </div>
            <LoadingButton type="submit" loading={verifyMutation.isPending}>
              Verificar
            </LoadingButton>
          </form>

          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t" />
            </div>
            <div className="relative flex justify-center text-xs">
              <span className="bg-card text-muted-foreground px-2">o</span>
            </div>
          </div>

          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={handleFileChange}
          />
          <Button
            type="button"
            variant="outline"
            disabled={imageMutation.isPending || verifyMutation.isPending}
            onClick={() => fileInputRef.current?.click()}
          >
            <ImageUp className="mr-2 size-4" />
            {imageMutation.isPending ? "Leyendo imagen..." : "Subir imagen del QR"}
          </Button>
        </CardContent>
      </Card>

      {result && (
        <Card className="max-w-md">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>
                {result.nombre} {result.apellido}
              </span>
              <Badge variant={result.acceso_libre ? "default" : "destructive"}>
                {result.acceso_libre ? "Acceso permitido" : "Sin acceso"}
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <div className="grid gap-1 text-sm">
              <span>
                <span className="text-muted-foreground">Documento: </span>
                {result.documento}
              </span>
              <span>
                <span className="text-muted-foreground">Rol: </span>
                {result.rol}
              </span>
              <span>
                <span className="text-muted-foreground">Plan vigente hasta: </span>
                {result.plan_until ?? "Sin plan activo"}
              </span>
              <span>
                <span className="text-muted-foreground">Vehículo: </span>
                {result.placa ?? "Sin vehículo asociado a este QR"}
              </span>
            </div>
            <div className="flex gap-2">
              <LoadingButton
                className="flex-1"
                variant="outline"
                loading={
                  logMutation.isPending && logMutation.variables === "entrada"
                }
                onClick={() => logMutation.mutate("entrada")}
              >
                Registrar entrada
              </LoadingButton>
              <LoadingButton
                className="flex-1"
                variant="outline"
                loading={
                  logMutation.isPending && logMutation.variables === "salida"
                }
                onClick={() => logMutation.mutate("salida")}
              >
                Registrar salida
              </LoadingButton>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
