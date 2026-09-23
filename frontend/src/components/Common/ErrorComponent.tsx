import { Link } from "@tanstack/react-router"
import { Button } from "@/components/ui/button"

const ErrorComponent = () => {
  return (
    <div
      className="flex min-h-screen flex-col items-center justify-center p-4 text-center"
      data-testid="error-component"
    >
      <span className="text-2xl font-bold">Algo salió mal</span>
      <p className="text-muted-foreground mt-2 mb-6 max-w-sm text-sm">
        Puede que el servidor apenas se esté "despertando" (el plan gratis se
        duerme tras un rato sin uso) — intenta de nuevo en unos segundos.
      </p>
      <div className="flex gap-2">
        <Button variant="outline" onClick={() => window.location.reload()}>
          Reintentar
        </Button>
        <Link to="/">
          <Button>Ir al inicio</Button>
        </Link>
      </div>
    </div>
  )
}

export default ErrorComponent
