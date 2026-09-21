import { useMutation } from "@tanstack/react-query"
import { createFileRoute, redirect } from "@tanstack/react-router"
import { useRef, useState } from "react"

import { KioskService, UsersService } from "@/client"
import { Badge } from "@/components/ui/badge"
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

function VerifyQr() {
  const { showErrorToast, showSuccessToast } = useCustomToast()
  const [qrToken, setQrToken] = useState("")
  const [lastToken, setLastToken] = useState("")
  const [result, setResult] = useState<VerifyResult | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

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

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Verificar QR</h1>
        <p className="text-muted-foreground">
          Escanea el QR con el lector del parqueadero (funciona como
          teclado) o pégalo manualmente.
        </p>
      </div>

      <Card className="max-w-md">
        <CardHeader>
          <CardTitle>Lector</CardTitle>
        </CardHeader>
        <CardContent>
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
