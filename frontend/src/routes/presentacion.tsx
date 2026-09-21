import { createFileRoute, Link as RouterLink } from "@tanstack/react-router"
import {
  BellRing,
  CalendarClock,
  ParkingSquare,
  QrCode,
  ShieldCheck,
} from "lucide-react"

import { Logo } from "@/components/Common/Logo"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

export const Route = createFileRoute("/presentacion")({
  component: Presentacion,
  head: () => ({
    meta: [{ title: "Parqueadero UNIMINUTO — Presentación del proyecto" }],
  }),
})

const objetivos = [
  "Implementar un mecanismo de identificación sin contraseña para estudiantes, invitados y personal exento, basado en el documento y un código QR personal.",
  "Registrar vehículos por usuario y calcular la tarifa diaria automáticamente en el servidor, según el tipo de vehículo.",
  "Integrar una pasarela de pagos electrónicos (Wompi) con tarjeta, Nequi, PSE y transferencia.",
  "Ofrecer un plan mensual único, con activación y renovación automática y notificaciones push antes de su vencimiento.",
  "Diseñar un código QR con la misma estructura del código real del parqueadero de UNIMINUTO, para una futura integración institucional.",
  "Construir un panel de administración para gestionar usuarios, roles, el plan y el soporte a estudiantes.",
]

const funcionalidades = [
  "Kiosco de acceso por documento o código QR, sin contraseña.",
  "Pago y recarga con cálculo de tarifa hecho siempre en el servidor.",
  "Plan mensual con activación y renovación automática.",
  "QR de acceso por vehículo, con registro de entrada y salida.",
  "Historial de pagos y bitácora de eventos.",
  "Preguntas frecuentes y soporte con respuesta del administrador.",
  "Panel de administración con roles y búsqueda de usuarios.",
  "Notificaciones push antes de que venza el plan.",
]

const cronograma = [
  ["Día 1", "Configuración inicial del proyecto y modelo de datos."],
  ["Día 2", "Backend de pago y recarga (cálculo de tarifas, integración Wompi)."],
  ["Día 3", "Frontend de pago y recarga."],
  ["Día 4", "Planes mensuales: compra, activación y renovación."],
  ["Día 5", "Historial de pagos y módulo de FAQ/soporte."],
  ["Día 6", "Endurecimiento de seguridad (JWT, hashing, límite de intentos, CORS)."],
  ["Día 7", "Despliegue en Render + Neon y verificación en producción."],
]

const iconFeatures = [
  { icon: ParkingSquare, label: "Pago del parqueadero", desc: "Tarifa diaria calculada por el servidor, sin depender de efectivo." },
  { icon: QrCode, label: "QR de acceso", desc: "Un código por usuario y otro por vehículo, con la misma estructura del QR real." },
  { icon: CalendarClock, label: "Plan mensual", desc: "Suscripción con renovación automática al confirmarse el pago." },
  { icon: ShieldCheck, label: "Seguridad", desc: "Contraseñas con hash, JWT firmado y verificación de firma en los pagos." },
]

function Presentacion() {
  return (
    <div className="bg-background min-h-svh">
      <header className="border-b">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <Logo variant="responsive" asLink={false} />
          <Button asChild>
            <RouterLink to="/login">Continuar al sistema</RouterLink>
          </Button>
        </div>
      </header>

      <main className="mx-auto flex max-w-5xl flex-col gap-14 px-6 py-12">
        <section className="flex flex-col items-center gap-4 text-center">
          <h1 className="text-4xl font-bold tracking-tight">
            Parqueadero UNIMINUTO
          </h1>
          <h2 className="text-muted-foreground max-w-2xl text-xl">
            Pagos electrónicos y control de acceso por QR para el parqueadero
            de UNIMINUTO Bello
          </h2>
        </section>

        <section className="flex flex-col gap-4">
          <p>
            Parqueadero UNIMINUTO es un sistema de pagos electrónicos y
            control de acceso para el servicio de parqueadero de la
            Corporación Universitaria Minuto de Dios, sede Bello. Reemplaza la
            dependencia exclusiva del efectivo y de la máquina física por un
            flujo digital: cada persona se identifica con su documento o con
            un código QR personal, consulta y paga la tarifa diaria o
            adquiere un plan mensual, y el sistema deja registro de cada pago,
            entrada y salida.
          </p>
          <p>
            El proyecto usa una sesión de tipo kiosco (documento o QR, sin
            contraseña) en vez de un inicio de sesión institucional, porque
            integrar UWallet/Microsoft requiere credenciales que solo el área
            de TI de UNIMINUTO puede emitir. El diseño del QR, en cambio,
            replica la misma estructura del código real del parqueadero, para
            que una eventual integración oficial futura sea posible.
          </p>
        </section>

        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {iconFeatures.map(({ icon: Icon, label, desc }) => (
            <Card key={label}>
              <CardHeader>
                <Icon className="text-primary size-6" />
                <CardTitle className="text-base">{label}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground text-sm">{desc}</p>
              </CardContent>
            </Card>
          ))}
        </section>

        <section className="grid gap-8 md:grid-cols-2">
          <div>
            <h2 className="mb-3 text-2xl font-semibold">Objetivos específicos</h2>
            <ol className="list-decimal space-y-2 pl-5 text-sm">
              {objetivos.map((o) => (
                <li key={o}>{o}</li>
              ))}
            </ol>
          </div>
          <div>
            <h2 className="mb-3 text-2xl font-semibold">Funcionalidades</h2>
            <ul className="list-disc space-y-2 pl-5 text-sm">
              {funcionalidades.map((f) => (
                <li key={f}>{f}</li>
              ))}
            </ul>
          </div>
        </section>

        <section>
          <h2 className="mb-3 text-2xl font-semibold">Cronograma del proyecto</h2>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Etapa</TableHead>
                <TableHead>Entregable</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {cronograma.map(([dia, detalle]) => (
                <TableRow key={dia}>
                  <TableCell className="font-medium whitespace-nowrap">
                    <Badge variant="secondary">{dia}</Badge>
                  </TableCell>
                  <TableCell className="whitespace-normal">{detalle}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </section>

        <section>
          <h2 className="mb-3 text-2xl font-semibold">Video del proyecto</h2>
          <div className="overflow-hidden rounded-lg border">
            {/* eslint-disable-next-line jsx-a11y/media-has-caption */}
            <video controls className="w-full" preload="metadata">
              <source src="/assets/video/demo.webm" type="video/webm" />
              Tu navegador no soporta la reproducción de este video.
            </video>
          </div>
        </section>

        <section className="grid gap-8 md:grid-cols-2">
          <div>
            <h2 className="mb-3 text-2xl font-semibold">Audio introductorio</h2>
            <div className="flex items-center gap-3 rounded-lg border p-4">
              <BellRing className="text-primary size-5 shrink-0" />
              {/* eslint-disable-next-line jsx-a11y/media-has-caption */}
              <audio controls className="w-full">
                <source src="/assets/audio/intro.wav" type="audio/wav" />
                Tu navegador no soporta la reproducción de audio.
              </audio>
            </div>
          </div>
          <div>
            <h2 className="mb-3 text-2xl font-semibold">Ubicación</h2>
            <div className="overflow-hidden rounded-lg border">
              <iframe
                title="Ubicación de UNIMINUTO Bello"
                src="https://www.google.com/maps?q=Corporaci%C3%B3n%20Universitaria%20Minuto%20de%20Dios%2C%20Bello%2C%20Antioquia&output=embed"
                width="100%"
                height="220"
                style={{ border: 0 }}
                loading="lazy"
              />
            </div>
          </div>
        </section>

        <section>
          <h2 className="mb-3 text-2xl font-semibold">Conoce el sistema en vivo</h2>
          <p className="text-muted-foreground mb-3 text-sm">
            Vista previa en vivo de la pantalla de ingreso del sistema real.
          </p>
          <div className="overflow-hidden rounded-lg border" style={{ height: 480 }}>
            <iframe
              title="Vista previa del sistema"
              src="/login"
              width="100%"
              height="100%"
              style={{ border: 0 }}
              loading="lazy"
            />
          </div>
        </section>

        <section className="flex flex-col items-center gap-3 rounded-lg border bg-muted/30 py-10 text-center">
          <h2 className="text-2xl font-semibold">¿Listo para entrar?</h2>
          <p className="text-muted-foreground max-w-md">
            Continúa al sistema real: regístrate con tu ID de estudiante o
            escanea tu QR para volver a entrar.
          </p>
          <Button size="lg" asChild>
            <RouterLink to="/login">Continuar al sistema</RouterLink>
          </Button>
        </section>
      </main>
    </div>
  )
}
