import { useQuery } from "@tanstack/react-query"
import { useState } from "react"

import type { PaymentMethodPublic, VehiclePublic } from "@/client"
import { PaymentsService } from "@/client"
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { LoadingButton } from "@/components/ui/loading-button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useWompiCheckout } from "@/hooks/useWompiCheckout"

interface Props {
  vehicle: VehiclePublic
  dailyRateCOP: number
}

export function PendingVehicleCard({ vehicle, dailyRateCOP }: Props) {
  const [methodId, setMethodId] = useState<string>("")

  const { data: methods } = useQuery<PaymentMethodPublic[]>({
    queryKey: ["payment-methods"],
    queryFn: async () => (await PaymentsService.listPaymentMethods()).data ?? [],
  })

  const checkout = useWompiCheckout([
    ["pending-vehicles"],
    ["payment-history"],
  ])

  const canPay = methodId.length > 0 && !checkout.isPending

  return (
    <Card>
      <CardHeader>
        <CardTitle>Placa {vehicle.plate}</CardTitle>
        <CardDescription>Tarifa diaria pendiente de pago</CardDescription>
        <CardAction className="text-lg font-semibold">
          ${dailyRateCOP.toLocaleString("es-CO")} COP
        </CardAction>
      </CardHeader>
      <CardContent className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <Select value={methodId} onValueChange={setMethodId}>
          <SelectTrigger className="w-full sm:w-56">
            <SelectValue placeholder="Método de pago" />
          </SelectTrigger>
          <SelectContent>
            {methods?.map((method) => (
              <SelectItem key={method.id} value={method.id}>
                {method.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <LoadingButton
          disabled={!canPay}
          loading={checkout.isPending}
          onClick={() =>
            checkout.mutate({
              concept: "daily_fee",
              vehicle_id: vehicle.id,
              method_id: methodId,
            })
          }
        >
          Pagar ahora
        </LoadingButton>
      </CardContent>
    </Card>
  )
}
