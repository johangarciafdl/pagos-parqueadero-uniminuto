import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, redirect } from "@tanstack/react-router"
import { useState } from "react"

import type { SupportTicketAdminPublic } from "@/client"
import { SupportService, UsersService } from "@/client"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { LoadingButton } from "@/components/ui/loading-button"
import useCustomToast from "@/hooks/useCustomToast"
import { formatDateTime } from "@/lib/format"

export const Route = createFileRoute("/_layout/support-admin")({
  component: SupportAdmin,
  beforeLoad: async () => {
    const { data: user } = await UsersService.readUserMe()
    if (!user.is_superuser) {
      throw redirect({ to: "/" })
    }
  },
  head: () => ({
    meta: [{ title: "Soporte (admin) - Parqueadero UNIMINUTO" }],
  }),
})

const TICKET_STATUS_LABEL: Record<string, string> = {
  open: "Abierta",
  in_progress: "En proceso",
  resolved: "Resuelta",
  closed: "Cerrada",
}

function TicketCard({ ticket }: { ticket: SupportTicketAdminPublic }) {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const [reply, setReply] = useState("")

  const replyMutation = useMutation({
    mutationFn: async () =>
      SupportService.replyTicket({
        path: { ticket_id: ticket.id },
        body: { admin_reply: reply.trim() },
      }),
    onSuccess: () => {
      showSuccessToast("Respuesta enviada")
      setReply("")
      queryClient.invalidateQueries({ queryKey: ["all-tickets"] })
    },
    onError: (err: Error) => showErrorToast(err.message),
  })

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <span className="font-mono text-xs text-muted-foreground">
              {ticket.case_number}
            </span>
            <p className="text-base font-medium">{ticket.subject}</p>
          </div>
          <Badge variant="outline">
            {TICKET_STATUS_LABEL[ticket.status] ?? ticket.status}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <div>
          <p className="text-muted-foreground text-xs">
            {ticket.user_full_name ?? "Sin nombre"} · ID{" "}
            {ticket.student_id ?? "—"} · {formatDateTime(ticket.created_at)}
          </p>
          <p className="mt-1 text-sm">{ticket.message}</p>
        </div>

        {ticket.admin_reply ? (
          <div className="bg-muted rounded-md p-3">
            <p className="text-xs font-medium">Ya respondida</p>
            <p className="mt-1 text-sm">{ticket.admin_reply}</p>
            <span className="text-muted-foreground mt-1 block text-xs">
              {formatDateTime(ticket.replied_at)}
            </span>
          </div>
        ) : (
          <div className="flex flex-col gap-2">
            <textarea
              className="border-input min-h-24 w-full rounded-md border bg-transparent px-3 py-2 text-sm shadow-xs outline-none"
              placeholder="Escribe la respuesta para el estudiante..."
              value={reply}
              onChange={(e) => setReply(e.target.value)}
            />
            <LoadingButton
              className="self-end"
              disabled={!reply.trim()}
              loading={replyMutation.isPending}
              onClick={() => replyMutation.mutate()}
            >
              Responder
            </LoadingButton>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function SupportAdmin() {
  const { data: tickets } = useQuery({
    queryKey: ["all-tickets"],
    queryFn: async () => (await SupportService.listAllTickets()).data,
  })

  const pending = tickets?.data.filter((t: SupportTicketAdminPublic) => !t.admin_reply) ?? []
  const answered = tickets?.data.filter((t: SupportTicketAdminPublic) => t.admin_reply) ?? []

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">
          Soporte — solicitudes de estudiantes
        </h1>
        <p className="text-muted-foreground">
          Responde los casos abiertos; el estudiante verá la respuesta en su
          página de FAQ y soporte.
        </p>
      </div>

      <div className="flex flex-col gap-3">
        <h2 className="text-lg font-medium">
          Pendientes por responder ({pending.length})
        </h2>
        {pending.length === 0 && (
          <p className="text-muted-foreground text-sm">
            No hay solicitudes pendientes.
          </p>
        )}
        {pending.map((ticket: SupportTicketAdminPublic) => (
          <TicketCard key={ticket.id} ticket={ticket} />
        ))}
      </div>

      {answered.length > 0 && (
        <div className="flex flex-col gap-3">
          <h2 className="text-lg font-medium">Ya respondidas</h2>
          {answered.map((ticket: SupportTicketAdminPublic) => (
            <TicketCard key={ticket.id} ticket={ticket} />
          ))}
        </div>
      )}
    </div>
  )
}
