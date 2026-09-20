import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Trash2 } from "lucide-react"

import type { VehiclePublic, VehicleTypePublic } from "@/client"
import { VehiclesService } from "@/client"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import useCustomToast from "@/hooks/useCustomToast"

export function VehicleList() {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const { data: vehicles } = useQuery({
    queryKey: ["my-vehicles"],
    queryFn: async () => (await VehiclesService.listMyVehicles()).data,
  })

  const { data: vehicleTypes } = useQuery({
    queryKey: ["vehicle-types"],
    queryFn: async () => (await VehiclesService.listVehicleTypes()).data,
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => VehiclesService.deleteVehicle({ path: { vehicle_id: id } }),
    onSuccess: () => showSuccessToast("Vehículo eliminado"),
    onError: () => showErrorToast("No se pudo eliminar el vehículo"),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["my-vehicles"] })
      queryClient.invalidateQueries({ queryKey: ["pending-vehicles"] })
    },
  })

  if (!vehicles?.data.length) return null

  const typeName = (typeId: string) =>
    vehicleTypes?.find((t: VehicleTypePublic) => t.id === typeId)?.name ?? ""

  return (
    <div className="flex flex-wrap gap-2">
      {vehicles.data.map((vehicle: VehiclePublic) => (
        <Badge key={vehicle.id} variant="secondary" className="gap-2 py-1.5 pl-3 pr-1.5">
          {vehicle.plate} · {typeName(vehicle.type_id)}
          <Button
            variant="ghost"
            size="icon"
            className="size-5"
            onClick={() => deleteMutation.mutate(vehicle.id)}
          >
            <Trash2 className="size-3" />
          </Button>
        </Badge>
      ))}
    </div>
  )
}
