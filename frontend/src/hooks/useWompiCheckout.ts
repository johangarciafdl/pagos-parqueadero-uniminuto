import { useMutation, useQueryClient } from "@tanstack/react-query"

import type { PaymentInitiate, PaymentInitiateResponse } from "@/client"
import { PaymentsService } from "@/client"
import type { WompiWidgetResult } from "@/types/wompi"
import useCustomToast from "./useCustomToast"

/**
 * Crea el pago en nuestro backend (que calcula el monto real) y abre el
 * Widget Checkout de Wompi con la firma que el backend generó. El resultado
 * que reporta el widget es solo informativo para el usuario: el estado real
 * del pago solo cambia cuando llega el webhook de Wompi al backend, así que
 * siempre volvemos a consultar el backend en vez de confiar en el widget.
 */
export function useWompiCheckout(onSettledQueryKeys: unknown[][]) {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  return useMutation({
    mutationFn: async (body: PaymentInitiate) => {
      const { data } = await PaymentsService.createPayment({ body })
      return data
    },
    onSuccess: (payment: PaymentInitiateResponse | undefined) => {
      if (!payment) return
      const checkout = new WidgetCheckout({
        currency: "COP",
        amountInCents: payment.amount_in_cents,
        reference: payment.wompi_reference,
        publicKey: payment.wompi_public_key,
        signature: { integrity: payment.integrity_signature },
      })
      checkout.open((result: WompiWidgetResult) => {
        const approved = result.transaction.status === "APPROVED"
        if (approved) {
          showSuccessToast(
            "Pago recibido por Wompi, confirmando con el parqueadero...",
          )
        } else {
          showErrorToast(`Wompi reportó: ${result.transaction.status}`)
        }
        // El estado real llega por webhook; refrescamos tras un breve
        // margen para darle tiempo de procesarse.
        setTimeout(() => {
          for (const queryKey of onSettledQueryKeys) {
            queryClient.invalidateQueries({ queryKey })
          }
        }, 2500)
      })
    },
    onError: (error: unknown) => {
      showErrorToast(
        error instanceof Error ? error.message : "No se pudo iniciar el pago",
      )
    },
  })
}
