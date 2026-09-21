import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { QrCode, Trash2 } from "lucide-react"
import { useState } from "react"

import type { VehiclePublic, VehicleTypePublic } from "@/client"
import { KioskService, VehiclesService } from "@/client"
import { QRDisplay } from "@/components/Kiosk/QRDisplay"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import useCustomToast from "@/hooks/useCustomToast"

function VehicleQRDialog({
  vehicleId,
  plate,
  onClose,
}: {
  vehicleId: string
  plate: string
  onClose: () => void
}) {
  const { data: qr } = useQuery({
    queryKey: ["vehicle-qr", vehicleId],
    queryFn: async () =>
      (await KioskService.vehicleQr({ path: { vehicle_id: vehicleId } }))
        .data as unknown as { qr_token: string; plate: string },
  })

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-xs">
        <DialogHeader>
          <DialogTitle>QR de acceso — placa {plate}</DialogTitle>
        </DialogHeader>
        <div className="flex flex-col items-center gap-3 py-2">
          {qr ? (
            <QRDisplay value={qr.qr_token} />
          ) : (
            <div className="size-[220px]" />
          )}
          <p className="text-muted-foreground text-center text-xs">
            Muestra este código al ingresar o salir con este vehículo.
          </p>
        </div>
      </DialogContent>
    </Dialog>
  )
}

export function VehicleList() {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const [qrVehicle, setQrVehicle] = useState<VehiclePublic | null>(null)

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
    <>
      <div className="flex flex-wrap gap-2">
        {vehicles.data.map((vehicle: VehiclePublic) => (
          <Badge key={vehicle.id} variant="secondary" className="gap-2 py-1.5 pl-3 pr-1.5">
            {vehicle.plate} · {typeName(vehicle.type_id)}
            <Button
              variant="ghost"
              size="icon"
              className="size-5"
              onClick={() => setQrVehicle(vehicle)}
            >
              <QrCode className="size-3" />
            </Button>
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
      {qrVehicle && (
        <VehicleQRDialog
          vehicleId={qrVehicle.id}
          plate={qrVehicle.plate}
          onClose={() => setQrVehicle(null)}
        />
      )}
    </>
  )
}
