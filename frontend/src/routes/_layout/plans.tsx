import { useQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { useState } from "react"

import type { PaymentMethodPublic, PlanPublic, VehicleTypePublic } from "@/client"
import { PaymentsService, PlansService, VehiclesService } from "@/client"
import { Badge } from "@/components/ui/badge"
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardFooter,
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
import { formatCOP } from "@/lib/format"

export const Route = createFileRoute("/_layout/plans")({
  component: PlansPage,
  head: () => ({ meta: [{ title: "Planes mensuales - Parqueadero UNIMINUTO" }] }),
})

function PlansPage() {
  const { data: plans } = useQuery({
    queryKey: ["plans"],
    queryFn: async () => (await PlansService.listPlans()).data,
  })

  const { data: vehicleTypes } = useQuery({
    queryKey: ["vehicle-types"],
    queryFn: async () => (await VehiclesService.listVehicleTypes()).data,
  })

  const { data: subscription } = useQuery({
    queryKey: ["my-subscription"],
    queryFn: async () => (await PlansService.myActiveSubscription()).data,
  })

  const { data: methods } = useQuery({
    queryKey: ["payment-methods"],
    queryFn: async () => (await PaymentsService.listPaymentMethods()).data ?? [],
  })

  const [methodId, setMethodId] = useState("")

  const checkout = useWompiCheckout([
    ["my-subscription"],
    ["payment-history"],
  ])

  const typeName = (id: string) =>
    vehicleTypes?.find((t: VehicleTypePublic) => t.id === id)?.name ?? ""

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl">Planes mensuales</h1>
        <p className="text-muted-foreground">
          Ahorra pagando un plan en vez de la tarifa diaria.
        </p>
      </div>

      {subscription && (
        <Card className="border-primary">
          <CardHeader>
            <CardTitle>Tu plan vigente</CardTitle>
            <CardDescription>
              Activo hasta {subscription.end_date}
            </CardDescription>
            <CardAction>
              <Badge>Activo</Badge>
            </CardAction>
          </CardHeader>
        </Card>
      )}

      <div className="flex flex-col gap-3 sm:max-w-xs">
        <span className="text-sm font-medium">Método de pago</span>
        <Select value={methodId} onValueChange={setMethodId}>
          <SelectTrigger>
            <SelectValue placeholder="Selecciona un método" />
          </SelectTrigger>
          <SelectContent>
            {methods?.map((method: PaymentMethodPublic) => (
              <SelectItem key={method.id} value={method.id}>
                {method.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {plans?.data.map((plan: PlanPublic) => (
          <Card key={plan.id}>
            <CardHeader>
              <CardTitle>{plan.name}</CardTitle>
              <CardDescription>{typeName(plan.vehicle_type_id)}</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-1">
              <span className="text-2xl font-semibold">
                {formatCOP(plan.price_cop)}
              </span>
              <span className="text-muted-foreground text-sm">
                Vigencia: {plan.duration_days} días
              </span>
              {plan.conditions && (
                <p className="text-muted-foreground mt-2 text-sm">
                  {plan.conditions}
                </p>
              )}
            </CardContent>
            <CardFooter>
              <LoadingButton
                className="w-full"
                disabled={!methodId || checkout.isPending}
                loading={checkout.isPending}
                onClick={() =>
                  checkout.mutate({
                    concept: subscription ? "plan_renewal" : "plan_purchase",
                    plan_id: plan.id,
                    method_id: methodId,
                  })
                }
              >
                {subscription ? "Renovar" : "Comprar"}
              </LoadingButton>
            </CardFooter>
          </Card>
        ))}
      </div>
    </div>
  )
}
