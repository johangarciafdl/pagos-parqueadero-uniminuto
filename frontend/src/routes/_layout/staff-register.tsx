import { useMutation } from "@tanstack/react-query"
import { createFileRoute, redirect } from "@tanstack/react-router"
import { useState } from "react"

import { KioskService, UsersService } from "@/client"
import { QRDisplay } from "@/components/Kiosk/QRDisplay"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { LoadingButton } from "@/components/ui/loading-button"
import useCustomToast from "@/hooks/useCustomToast"

export const Route = createFileRoute("/_layout/staff-register")({
  component: StaffRegister,
  beforeLoad: async () => {
    const { data: user } = await UsersService.readUserMe()
    if (!user.is_superuser) {
      throw redirect({ to: "/" })
    }
  },
  head: () => ({
    meta: [{ title: "Registrar personal exento - Parqueadero UNIMINUTO" }],
  }),
})

function StaffRegister() {
  const { showErrorToast } = useCustomToast()
  const [studentId, setStudentId] = useState("")
  const [firstName, setFirstName] = useState("")
  const [lastName, setLastName] = useState("")
  const [qrToken, setQrToken] = useState<string | null>(null)

  const registerMutation = useMutation({
    mutationFn: async () =>
      (
        await KioskService.registerStaff({
          body: {
            student_id: studentId.trim(),
            first_name: firstName.trim(),
            last_name: lastName.trim(),
          },
        })
      ).data,
    onSuccess: (result) => {
      if (!result) return
      setQrToken(result.qr_token)
      setStudentId("")
      setFirstName("")
      setLastName("")
    },
    onError: (err: Error) => showErrorToast(err.message),
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!studentId.trim() || !firstName.trim() || !lastName.trim()) return
    registerMutation.mutate()
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">
          Registrar personal exento
        </h1>
        <p className="text-muted-foreground">
          Personal de UNIMINUTO que no paga el parqueadero. Genera su QR de
          acceso ilimitado.
        </p>
      </div>

      <div className="grid gap-6 sm:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Datos del funcionario</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="grid gap-4">
              <div className="grid gap-2">
                <Label htmlFor="staff_first_name">Nombres</Label>
                <Input
                  id="staff_first_name"
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="staff_last_name">Apellidos</Label>
                <Input
                  id="staff_last_name"
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="staff_student_id">ID / carné</Label>
                <Input
                  id="staff_student_id"
                  value={studentId}
                  onChange={(e) => setStudentId(e.target.value)}
                />
              </div>
              <LoadingButton type="submit" loading={registerMutation.isPending}>
                Registrar y generar QR
              </LoadingButton>
            </form>
          </CardContent>
        </Card>

        {qrToken && (
          <Card>
            <CardHeader>
              <CardTitle>QR de acceso ilimitado</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col items-center gap-4">
              <QRDisplay value={qrToken} />
              <Button variant="outline" onClick={() => setQrToken(null)}>
                Cerrar
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
