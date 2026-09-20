import { useQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { useState } from "react"

import type { PaymentStatusCode } from "@/client"
import { HistoryService } from "@/client"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { formatCOP, formatDateTime } from "@/lib/format"

export const Route = createFileRoute("/_layout/history")({
  component: HistoryPage,
  head: () => ({ meta: [{ title: "Historial - Parqueadero UNIMINUTO" }] }),
})

const STATUS_LABEL: Record<PaymentStatusCode, string> = {
  pending: "Pendiente",
  approved: "Aprobado",
  declined: "Rechazado",
  cancelled: "Cancelado",
}

const STATUS_VARIANT: Record<
  PaymentStatusCode,
  "default" | "secondary" | "destructive" | "outline"
> = {
  pending: "outline",
  approved: "default",
  declined: "destructive",
  cancelled: "secondary",
}

const CONCEPT_LABEL: Record<string, string> = {
  daily_fee: "Tarifa diaria",
  recharge: "Recarga",
  plan_purchase: "Compra de plan",
  plan_renewal: "Renovación de plan",
}

function HistoryPage() {
  const [dateFrom, setDateFrom] = useState("")
  const [dateTo, setDateTo] = useState("")
  const [status, setStatus] = useState<PaymentStatusCode | "all">("all")

  const { data } = useQuery({
    queryKey: ["payment-history", dateFrom, dateTo, status],
    queryFn: async () =>
      (
        await HistoryService.getPaymentHistory({
          query: {
            date_from: dateFrom || undefined,
            date_to: dateTo || undefined,
            status_code: status === "all" ? undefined : status,
          },
        })
      ).data,
  })

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl">Historial de pagos</h1>
        <p className="text-muted-foreground">
          Consulta tus pagos y recargas anteriores.
        </p>
      </div>

      <div className="flex flex-wrap items-end gap-3">
        <div className="flex flex-col gap-1.5">
          <span className="text-sm font-medium">Desde</span>
          <Input
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <span className="text-sm font-medium">Hasta</span>
          <Input
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <span className="text-sm font-medium">Estado</span>
          <Select
            value={status}
            onValueChange={(v) => setStatus(v as PaymentStatusCode | "all")}
          >
            <SelectTrigger className="w-44">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos</SelectItem>
              {Object.entries(STATUS_LABEL).map(([code, label]) => (
                <SelectItem key={code} value={code}>
                  {label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Fecha</TableHead>
            <TableHead>Concepto</TableHead>
            <TableHead>Método</TableHead>
            <TableHead>Referencia</TableHead>
            <TableHead className="text-right">Valor</TableHead>
            <TableHead>Estado</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data?.data.map((payment) => (
            <TableRow key={payment.id}>
              <TableCell>{formatDateTime(payment.created_at)}</TableCell>
              <TableCell>{CONCEPT_LABEL[payment.concept] ?? payment.concept}</TableCell>
              <TableCell>{payment.method_name}</TableCell>
              <TableCell className="font-mono text-xs">
                {payment.wompi_reference}
              </TableCell>
              <TableCell className="text-right">
                {formatCOP(payment.amount_cop)}
              </TableCell>
              <TableCell>
                <Badge variant={STATUS_VARIANT[payment.status_code]}>
                  {STATUS_LABEL[payment.status_code]}
                </Badge>
              </TableCell>
            </TableRow>
          ))}
          {data?.data.length === 0 && (
            <TableRow>
              <TableCell colSpan={6} className="text-muted-foreground text-center">
                No hay pagos en el rango seleccionado.
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </div>
  )
}
