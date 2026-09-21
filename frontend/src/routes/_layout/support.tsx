import { useQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"

import type { FAQPublic, SupportTicketPublic } from "@/client"
import { FaqService, SupportService } from "@/client"
import { Badge } from "@/components/ui/badge"
import { NewTicketDialog } from "@/components/Support/NewTicketDialog"
import { formatDateTime } from "@/lib/format"

export const Route = createFileRoute("/_layout/support")({
  component: SupportPage,
  head: () => ({ meta: [{ title: "FAQ y soporte - Parqueadero UNIMINUTO" }] }),
})

const TICKET_STATUS_LABEL: Record<string, string> = {
  open: "Abierta",
  in_progress: "En proceso",
  resolved: "Resuelta",
  closed: "Cerrada",
}

function SupportPage() {
  const { data: faqs } = useQuery({
    queryKey: ["faqs"],
    queryFn: async () => (await FaqService.listFaq()).data,
  })

  const { data: tickets } = useQuery({
    queryKey: ["my-tickets"],
    queryFn: async () => (await SupportService.listMyTickets()).data,
  })

  const categories: string[] = Array.from(
    new Set(faqs?.data.map((faq: FAQPublic) => faq.category) ?? []),
  )

  return (
    <div className="flex flex-col gap-8">
      <div>
        <h1 className="text-2xl">Preguntas frecuentes</h1>
        <p className="text-muted-foreground">
          Resuelve dudas comunes sobre tarifas, planes y pagos.
        </p>
      </div>

      {categories.length === 0 && (
        <p className="text-muted-foreground">
          Aún no hay preguntas frecuentes cargadas.
        </p>
      )}

      {categories.map((category) => (
        <div key={category} className="flex flex-col gap-2">
          <h2 className="text-lg font-medium">{category}</h2>
          <div className="divide-y rounded-lg border">
            {faqs?.data
              .filter((faq: FAQPublic) => faq.category === category)
              .map((faq: FAQPublic) => (
                <details key={faq.id} className="group p-4">
                  <summary className="cursor-pointer list-none font-medium marker:content-none">
                    {faq.question}
                  </summary>
                  <p className="text-muted-foreground mt-2 text-sm">
                    {faq.answer}
                  </p>
                </details>
              ))}
          </div>
        </div>
      ))}

      <div className="flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-medium">Mis solicitudes</h2>
            <p className="text-muted-foreground text-sm">
              Haz seguimiento a tus casos de soporte.
            </p>
          </div>
          <NewTicketDialog />
        </div>

        <div className="flex flex-col gap-3">
          {tickets?.data.map((ticket: SupportTicketPublic) => (
            <div
              key={ticket.id}
              className="flex flex-col gap-1 rounded-lg border p-4"
            >
              <div className="flex items-center justify-between gap-2">
                <span className="font-mono text-xs text-muted-foreground">
                  {ticket.case_number}
                </span>
                <Badge variant="outline">
                  {TICKET_STATUS_LABEL[ticket.status] ?? ticket.status}
                </Badge>
              </div>
              <span className="font-medium">{ticket.subject}</span>
              <p className="text-muted-foreground text-sm">{ticket.message}</p>
              <span className="text-muted-foreground text-xs">
                {formatDateTime(ticket.created_at)}
              </span>
              {ticket.admin_reply && (
                <div className="bg-muted mt-2 rounded-md p-3">
                  <p className="text-xs font-medium">
                    Respuesta del parqueadero
                  </p>
                  <p className="mt-1 text-sm">{ticket.admin_reply}</p>
                  <span className="text-muted-foreground mt-1 block text-xs">
                    {formatDateTime(ticket.replied_at)}
                  </span>
                </div>
              )}
            </div>
          ))}
          {tickets?.data.length === 0 && (
            <p className="text-muted-foreground">
              No has creado solicitudes de soporte.
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
