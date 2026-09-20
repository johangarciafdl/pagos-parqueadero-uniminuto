import {
  createFileRoute,
  Link as RouterLink,
  redirect,
  useNavigate,
} from "@tanstack/react-router"
import { AnimatePresence, motion } from "motion/react"
import { useState } from "react"

import { AuthLayout } from "@/components/Common/AuthLayout"
import { QRDisplay } from "@/components/Kiosk/QRDisplay"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { LoadingButton } from "@/components/ui/loading-button"
import useAuth, { isLoggedIn } from "@/hooks/useAuth"

export const Route = createFileRoute("/login")({
  component: Kiosk,
  beforeLoad: async () => {
    if (isLoggedIn()) {
      throw redirect({ to: "/" })
    }
  },
  head: () => ({
    meta: [{ title: "Parqueadero UNIMINUTO" }],
  }),
})

type Mode = "enter" | "register" | "show-qr"

const fadeSlide = {
  initial: { opacity: 0, y: 8 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -8 },
  transition: { duration: 0.2, ease: "easeOut" as const },
}

function Kiosk() {
  const navigate = useNavigate()
  const { kioskSessionMutation, kioskRegisterMutation } = useAuth()
  const [mode, setMode] = useState<Mode>("enter")
  const [studentId, setStudentId] = useState("")
  const [firstName, setFirstName] = useState("")
  const [lastName, setLastName] = useState("")
  const [qrToken, setQrToken] = useState("")

  const handleEnter = (e: React.FormEvent) => {
    e.preventDefault()
    if (!studentId.trim()) return
    kioskSessionMutation.mutate({ student_id: studentId.trim() })
  }

  const handleRegister = (e: React.FormEvent) => {
    e.preventDefault()
    if (!studentId.trim() || !firstName.trim() || !lastName.trim()) return
    kioskRegisterMutation.mutate(
      {
        student_id: studentId.trim(),
        first_name: firstName.trim(),
        last_name: lastName.trim(),
      },
      {
        onSuccess: (result) => {
          setQrToken(result.qr_token)
          setMode("show-qr")
        },
      },
    )
  }

  return (
    <AuthLayout>
      <AnimatePresence mode="wait">
        {mode === "enter" && (
          <motion.div key="enter" {...fadeSlide} className="flex flex-col gap-6">
            <div className="flex flex-col items-center gap-2 text-center">
              <h1 className="text-2xl font-bold">Parqueadero UNIMINUTO</h1>
              <p className="text-muted-foreground text-sm">
                Ingresa con tu ID de estudiante o escanea tu QR
              </p>
            </div>
            <form onSubmit={handleEnter} className="grid gap-4">
              <div className="grid gap-2">
                <Label htmlFor="student_id">ID / carné de estudiante</Label>
                <Input
                  id="student_id"
                  placeholder="Ej. 0000123456"
                  autoFocus
                  value={studentId}
                  onChange={(e) => setStudentId(e.target.value)}
                />
              </div>
              <LoadingButton
                type="submit"
                loading={kioskSessionMutation.isPending}
              >
                Ingresar
              </LoadingButton>
            </form>
            <div className="text-center text-sm">
              ¿Primera vez aquí?{" "}
              <button
                type="button"
                className="underline underline-offset-4"
                onClick={() => setMode("register")}
              >
                Regístrate
              </button>
            </div>
          </motion.div>
        )}

        {mode === "register" && (
          <motion.div key="register" {...fadeSlide} className="flex flex-col gap-6">
            <div className="flex flex-col items-center gap-2 text-center">
              <h1 className="text-2xl font-bold">Crear cuenta</h1>
              <p className="text-muted-foreground text-sm">
                Solo necesitas tu ID de estudiante y tu nombre
              </p>
            </div>
            <form onSubmit={handleRegister} className="grid gap-4">
              <div className="grid gap-2">
                <Label htmlFor="new_first_name">Nombres</Label>
                <Input
                  id="new_first_name"
                  placeholder="Nombres"
                  autoFocus
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="new_last_name">Apellidos</Label>
                <Input
                  id="new_last_name"
                  placeholder="Apellidos"
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="new_student_id">ID / carné de estudiante</Label>
                <Input
                  id="new_student_id"
                  placeholder="Ej. 0000123456"
                  value={studentId}
                  onChange={(e) => setStudentId(e.target.value)}
                />
              </div>
              <LoadingButton
                type="submit"
                loading={kioskRegisterMutation.isPending}
              >
                Crear cuenta
              </LoadingButton>
            </form>
            <div className="text-center text-sm">
              ¿Ya tienes cuenta?{" "}
              <button
                type="button"
                className="underline underline-offset-4"
                onClick={() => setMode("enter")}
              >
                Ingresa aquí
              </button>
            </div>
          </motion.div>
        )}

        {mode === "show-qr" && (
          <motion.div
            key="show-qr"
            {...fadeSlide}
            className="flex flex-col items-center gap-6 text-center"
          >
            <div className="flex flex-col items-center gap-2">
              <h1 className="text-2xl font-bold">¡Cuenta creada!</h1>
              <p className="text-muted-foreground text-sm">
                Guarda este código QR: te sirve para volver a entrar sin
                escribir tu ID.
              </p>
            </div>
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.25, delay: 0.1 }}
              className="rounded-lg border p-4"
            >
              <QRDisplay value={qrToken} />
            </motion.div>
            <Button className="w-full" onClick={() => navigate({ to: "/" })}>
              Continuar
            </Button>
          </motion.div>
        )}
      </AnimatePresence>
      {mode !== "show-qr" && (
        <p className="text-muted-foreground mt-6 text-center text-xs">
          Personal del parqueadero:{" "}
          <RouterLink to="/staff" className="underline underline-offset-4">
            acceso administrador
          </RouterLink>
        </p>
      )}
    </AuthLayout>
  )
}
