import { useQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"

import type { VehiclePublic, VehicleTypePublic } from "@/client"
import { PaymentsService, VehiclesService } from "@/client"
import { PendingVehicleCard } from "@/components/Parking/PendingVehicleCard"
import { RegisterVehicleDialog } from "@/components/Parking/RegisterVehicleDialog"
import { VehicleList } from "@/components/Parking/VehicleList"
import useAuth from "@/hooks/useAuth"

export const Route = createFileRoute("/_layout/")({
  component: Dashboard,
  head: () => ({
    meta: [{ title: "Pago / recarga - Parqueadero UNIMINUTO" }],
  }),
})

function Dashboard() {
  const { user: currentUser } = useAuth()

  const { data: vehicleTypes } = useQuery({
    queryKey: ["vehicle-types"],
    queryFn: async () => (await VehiclesService.listVehicleTypes()).data,
  })

  const { data: myVehicles, isPending: loadingVehicles } = useQuery({
    queryKey: ["my-vehicles"],
    queryFn: async () => (await VehiclesService.listMyVehicles()).data,
  })

  const { data: pending = [] } = useQuery<VehiclePublic[]>({
    queryKey: ["pending-vehicles"],
    queryFn: async () =>
      (await PaymentsService.listVehiclesWithPendingFee()).data ?? [],
  })

  const rateFor = (typeId: string) =>
    vehicleTypes?.find((t: VehicleTypePublic) => t.id === typeId)?.daily_rate_cop ?? 0
  const hasVehicles = (myVehicles?.data.length ?? 0) > 0

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl truncate max-w-sm">
          Hola, {currentUser?.full_name || currentUser?.email} 👋
        </h1>
        <p className="text-muted-foreground">
          Consulta y paga el valor del parqueadero de tus vehículos.
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <RegisterVehicleDialog />
        <VehicleList />
      </div>

      <div>
        <h2 className="mb-3 text-lg font-medium">Valor pendiente</h2>
        {!hasVehicles && !loadingVehicles && (
          <p className="text-muted-foreground">
            Registra un vehículo para poder consultar y pagar el parqueadero.
          </p>
        )}
        {hasVehicles && pending.length === 0 && (
          <p className="text-muted-foreground">
            No tienes pagos pendientes hoy. ✅
          </p>
        )}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {pending.map((vehicle: VehiclePublic) => (
            <PendingVehicleCard
              key={vehicle.id}
              vehicle={vehicle}
              dailyRateCOP={rateFor(vehicle.type_id)}
            />
          ))}
        </div>
      </div>
    </div>
  )
}
